"""
文档管理 API
"""
import os
import shutil
import logging
import time
import asyncio
import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, Request
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from app.core.security import parse_auth_header, TokenPayload
from app.utils.database import AsyncSessionLocal
from app.models import Document as DocumentModel, User as UserModel
from app.api.auth import get_current_user_model
from app.services.document_parser import document_parser
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, DocumentUploadRequest,
    DocumentParseRequest, DocumentParseResponse, DocumentStatus, FileType
)


async def get_current_user_from_request(request: Request) -> UserModel:
    """从请求中获取当前用户（支持Header或Query参数，用于不支持自定义Header的SSE场景）"""
    auth_header = request.headers.get("Authorization")
    token_query = request.query_params.get("token")
    if not auth_header and token_query:
        auth_header = f"Bearer {token_query}"

    token_payload: Optional[TokenPayload] = parse_auth_header(auth_header)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或Token已过期"
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.id == token_payload.user_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


logger = logging.getLogger(__name__)
router = APIRouter()

# 文件上传配置
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/upload")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "20971520"))  # 20MB
ALLOWED_EXTENSIONS = {".doc", ".docx", ".pdf"}
ALLOWED_MIME_TYPES = {
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf"
}

# 解析超时时间（秒）
PARSE_TIMEOUT = int(os.getenv("PARSE_TIMEOUT", "120"))

# 确保上传目录存在
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def validate_file(file: UploadFile) -> None:
    """验证上传文件 - 检查大小、扩展名和内容类型"""
    # 检查文件大小
    file_size = getattr(file, 'size', None)
    if file_size and file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE} 字节)"
        )

    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 检查文件类型
    file_type = file_ext[1:]  # 去掉点号
    if file_type not in [ft.value for ft in FileType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_type}"
        )

    # 验证文件内容类型 - 检查文件头 (magic bytes)
    file_content = file.file.read(8192) if hasattr(file, 'file') and file.file else b""
    file.file.seek(0) if hasattr(file, 'file') and file.file else None

    if file_content:
        # Magic bytes 检查
        pdf_magic = b"%PDF-"
        docx_magic = b"PK\x03\x04"  # ZIP 格式 (docx 是 zip)
        msword_magic = b"\xD0\xCF\x11\xE0"

        if file_ext == ".pdf" and not file_content.startswith(pdf_magic):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容无效：PDF 文件头损坏"
            )
        elif file_ext == ".docx" and not file_content.startswith(docx_magic):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容无效：DOCX 文件头损坏"
            )
        elif file_ext == ".doc" and not file_content[:4] == msword_magic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容无效：DOC 文件头损坏"
            )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user_model)
):
    """
    上传专利文档
    """
    file_path = None
    try:
        logger.info(f"用户 {current_user.username} 上传文档: {file.filename}")

        # 验证文件
        validate_file(file)

        # 生成唯一文件名
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{current_user.id}_{int(time.time())}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 创建文档记录
        async with AsyncSessionLocal() as session:
            document = DocumentModel(
                user_id=current_user.id,
                title=title or Path(file.filename).stem,
                file_path=file_path,
                file_type=file_ext[1:],
                file_size=file.size if hasattr(file, 'size') else 0,
                status=DocumentStatus.UPLOADED
            )
            session.add(document)
            await session.commit()
            await session.refresh(document)

        logger.info(f"文档上传成功: ID={document.id}, 路径={file_path}")

        return DocumentResponse.from_orm(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    status: Optional[DocumentStatus] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: UserModel = Depends(get_current_user_model)
):
    """
    获取用户的文档列表
    """
    try:
        # 构建查询条件
        conditions = [DocumentModel.user_id == current_user.id]

        if status:
            conditions.append(DocumentModel.status == status)

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    DocumentModel.title.ilike(search_term),
                    DocumentModel.parsed_content['structured']['title'].astext.ilike(search_term)
                    if DocumentModel.parsed_content is not None
                    else DocumentModel.title.ilike(search_term)
                )
            )

        # 查询总数
        async with AsyncSessionLocal() as session:
            count_query = select(func.count(DocumentModel.id)).where(and_(*conditions))
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # 查询文档列表
            query = (
                select(DocumentModel)
                .where(and_(*conditions))
                .order_by(desc(DocumentModel.created_at))
                .offset((page - 1) * size)
                .limit(size)
            )

            result = await session.execute(query)
            documents = result.scalars().all()

            return DocumentListResponse(
                documents=[DocumentResponse.from_orm(doc) for doc in documents],
                total=total,
                page=page,
                size=size
            )

    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: UserModel = Depends(get_current_user_model)
):
    """
    获取文档详情
    """
    try:
        async with AsyncSessionLocal() as session:
            query = select(DocumentModel).where(
                and_(
                    DocumentModel.id == document_id,
                    DocumentModel.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )

            return DocumentResponse.from_orm(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档详情失败: {str(e)}"
        )


@router.post("/{document_id}/parse", response_model=DocumentParseResponse)
async def parse_document(
    document_id: int,
    current_user: UserModel = Depends(get_current_user_model)
):
    """
    解析文档内容
    """
    try:
        logger.info(f"用户 {current_user.username} 解析文档: ID={document_id}")

        # 获取文档
        async with AsyncSessionLocal() as session:
            query = select(DocumentModel).where(
                and_(
                    DocumentModel.id == document_id,
                    DocumentModel.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )

            if not os.path.exists(document.file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档文件不存在"
                )

            # 更新状态为解析中
            document.status = DocumentStatus.PARSING
            await session.commit()

            # 解析文档
            try:
                parsed_content = await asyncio.wait_for(
                    document_parser.parse_document(
                        document.file_path,
                        document.file_type
                    ),
                    timeout=PARSE_TIMEOUT
                )

                # 保存解析结果
                document.parsed_content = parsed_content
                document.status = DocumentStatus.PARSED
                await session.commit()
                await session.refresh(document)

                logger.info(f"文档解析成功: ID={document_id}, 质量={parsed_content['sections']['parsing_quality']}")

                return DocumentParseResponse(
                    document_id=document.id,
                    status=document.status,
                    parsed_content=parsed_content,
                    message="文档解析成功"
                )

            except asyncio.TimeoutError:
                logger.error(f"文档解析超时: ID={document_id}, 超过 {PARSE_TIMEOUT} 秒未完成")
                document.status = DocumentStatus.ERROR
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="文档解析超时，请检查文件内容或稍后重试"
                )

            except Exception as parse_error:
                logger.error(f"文档解析失败: {str(parse_error)}")
                document.status = DocumentStatus.ERROR
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文档解析失败: {str(parse_error)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析文档失败: {str(e)}"
        )


# SSE 事件流配置
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


@router.post("/{document_id}/parse/stream")
async def parse_document_stream(
    document_id: int,
    request: Request,
    token: Optional[str] = Query(None, description="认证Token（EventSource不支持自定义header，可通过Query参数传递）"),
    current_user: UserModel = Depends(get_current_user_from_request)
):
    """解析文档内容 (SSE 流式响应)

    通过SSE实时推送解析进度，包括以下阶段:
    - extracting_text: 提取文件文本内容
    - analyzing_structure: 分析文档结构
    - extracting_sections: 提取专利章节信息
    - assessing_quality: 评估解析质量
    - complete: 解析完成

    注意: 由于EventSource不支持自定义Header，可通过token查询参数传递认证信息
    """
    import json

    async def event_generator():
        try:
            # 获取文档
            async with AsyncSessionLocal() as session:
                query = select(DocumentModel).where(
                    and_(
                        DocumentModel.id == document_id,
                        DocumentModel.user_id == current_user.id
                    )
                )
                result = await session.execute(query)
                document = result.scalar_one_or_none()

                if not document:
                    error_data = {"stage": "error", "percent": 0, "message": "文档不存在"}
                    yield {"event": "progress", "data": json.dumps(error_data, ensure_ascii=False)}
                    return

                if not os.path.exists(document.file_path):
                    error_data = {"stage": "error", "percent": 0, "message": "文档文件不存在"}
                    yield {"event": "progress", "data": json.dumps(error_data, ensure_ascii=False)}
                    return

                # 更新状态为解析中
                document.status = DocumentStatus.PARSING
                await session.commit()

            # 阶段1: 提取文本
            yield {"event": "progress", "data": json.dumps({"stage": "extracting_text", "percent": 10, "message": "正在提取文件文本内容..."}, ensure_ascii=False)}
            await asyncio.sleep(0.1)

            # 阶段2: 分析结构
            yield {"event": "progress", "data": json.dumps({"stage": "analyzing_structure", "percent": 40, "message": "正在分析文档结构..."}, ensure_ascii=False)}
            await asyncio.sleep(0.1)

            # 阶段3: 提取章节
            yield {"event": "progress", "data": json.dumps({"stage": "extracting_sections", "percent": 70, "message": "正在提取专利章节信息..."}, ensure_ascii=False)}
            await asyncio.sleep(0.1)

            # 阶段4: 评估质量
            yield {"event": "progress", "data": json.dumps({"stage": "assessing_quality", "percent": 90, "message": "正在评估解析质量..."}, ensure_ascii=False)}

            # 实际解析
            try:
                parsed_content = await asyncio.wait_for(
                    document_parser.parse_document(
                        document.file_path,
                        document.file_type
                    ),
                    timeout=PARSE_TIMEOUT
                )

                # 更新数据库
                async with AsyncSessionLocal() as session:
                    doc_query = select(DocumentModel).where(DocumentModel.id == document_id)
                    doc_result = await session.execute(doc_query)
                    doc = doc_result.scalar_one_or_none()
                    if doc:
                        doc.parsed_content = parsed_content
                        doc.status = DocumentStatus.PARSED
                        await session.commit()

                # 发送完成事件
                yield {"event": "progress", "data": json.dumps({
                    "stage": "complete",
                    "percent": 100,
                    "message": "解析完成",
                    "result": {
                        "document_id": document_id,
                        "status": "parsed",
                        "quality": parsed_content.get("sections", {}).get("parsing_quality", "unknown")
                    }
                }, ensure_ascii=False)}
                yield {"event": "done", "data": "[DONE]"}

            except asyncio.TimeoutError:
                async with AsyncSessionLocal() as session:
                    doc_query = select(DocumentModel).where(DocumentModel.id == document_id)
                    doc_result = await session.execute(doc_query)
                    doc = doc_result.scalar_one_or_none()
                    if doc:
                        doc.status = DocumentStatus.ERROR
                        await session.commit()

                yield {"event": "progress", "data": json.dumps({"stage": "error", "percent": 0, "message": "解析超时"}, ensure_ascii=False)}

            except Exception as parse_error:
                async with AsyncSessionLocal() as session:
                    doc_query = select(DocumentModel).where(DocumentModel.id == document_id)
                    doc_result = await session.execute(doc_query)
                    doc = doc_result.scalar_one_or_none()
                    if doc:
                        doc.status = DocumentStatus.ERROR
                        await session.commit()

                yield {"event": "progress", "data": json.dumps({"stage": "error", "percent": 0, "message": str(parse_error)}, ensure_ascii=False)}

        except Exception as e:
            logger.error(f"SSE解析文档失败: {str(e)}")
            yield {"event": "progress", "data": json.dumps({"stage": "error", "percent": 0, "message": str(e)}, ensure_ascii=False)}

    return EventSourceResponse(event_generator(), headers=SSE_HEADERS)



@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: UserModel = Depends(get_current_user_model)
):
    """
    删除文档
    """
    try:
        async with AsyncSessionLocal() as session:
            # 获取文档
            query = select(DocumentModel).where(
                and_(
                    DocumentModel.id == document_id,
                    DocumentModel.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )

            # 删除文件
            if os.path.exists(document.file_path):
                os.remove(document.file_path)

            # 删除数据库记录
            await session.delete(document)
            await session.commit()

            logger.info(f"文档删除成功: ID={document_id}")

            return {"message": "文档删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: UserModel = Depends(get_current_user_model)
):
    """
    下载文档文件
    """
    try:
        # 获取文档
        async with AsyncSessionLocal() as session:
            query = select(DocumentModel).where(
                and_(
                    DocumentModel.id == document_id,
                    DocumentModel.user_id == current_user.id
                )
            )
            result = await session.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在"
                )

            if not os.path.exists(document.file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档文件不存在"
                )

            # 生成下载文件名
            filename = f"{document.title}.{document.file_type}"

            return FileResponse(
                path=document.file_path,
                filename=filename,
                media_type='application/octet-stream'
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载文档失败: {str(e)}"
        )
