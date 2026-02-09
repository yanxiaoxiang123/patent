"""
文档管理 API
"""
import os
import shutil
import logging
import time
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from ..utils.database import AsyncSessionLocal
from ..models import Document as DocumentModel, User
from ..api.auth import get_current_user_model
from ..services.document_parser import document_parser
from ..schemas.document import (
    DocumentResponse, DocumentListResponse, DocumentUploadRequest,
    DocumentParseRequest, DocumentParseResponse, DocumentStatus, FileType
)

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
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
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
    current_user: User = Depends(get_current_user_model)
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
    current_user: User = Depends(get_current_user_model)
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
    current_user: User = Depends(get_current_user_model)
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
    current_user: User = Depends(get_current_user_model)
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


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user_model)
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
    current_user: User = Depends(get_current_user_model)
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
