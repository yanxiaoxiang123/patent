"""
文档相关的 Pydantic 模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"


class FileType(str, Enum):
    """文件类型枚举"""
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    title: Optional[str] = Field(None, description="文档标题")

    class Config:
        schema_extra = {
            "example": {
                "title": "智能家居控制系统专利申请"
            }
        }


class ClaimItem(BaseModel):
    """权利要求项"""
    number: int = Field(..., description="权利要求编号")
    content: str = Field(..., description="权利要求内容")

    class Config:
        schema_extra = {
            "example": {
                "number": 1,
                "content": "一种智能家居控制系统，其特征在于，包括：中央控制器；多个智能设备；无线通信模块。"
            }
        }


class StructuredContent(BaseModel):
    """结构化文档内容"""
    title: Optional[str] = Field(None, description="文档标题")
    abstract: Optional[str] = Field(None, description="摘要或技术领域")
    claims: List[ClaimItem] = Field(default_factory=list, description="权利要求书")
    description: Optional[str] = Field(None, description="说明书内容")

    class Config:
        schema_extra = {
            "example": {
                "title": "智能家居控制系统",
                "abstract": "本发明涉及智能家居技术领域...",
                "claims": [
                    {
                        "number": 1,
                        "content": "一种智能家居控制系统..."
                    }
                ],
                "description": "本发明提供了一种智能家居控制系统..."
            }
        }


class SectionsInfo(BaseModel):
    """文档部分信息"""
    has_title: bool = Field(..., description="是否包含标题")
    has_abstract: bool = Field(..., description="是否包含摘要")
    has_claims: bool = Field(..., description="是否包含权利要求书")
    claims_count: int = Field(..., description="权利要求数量")
    has_description: bool = Field(..., description="是否包含说明书")
    content_length: int = Field(..., description="说明书内容长度")
    parsing_quality: str = Field(..., description="解析质量: excellent/good/fair/poor")

    class Config:
        schema_extra = {
            "example": {
                "has_title": True,
                "has_abstract": True,
                "has_claims": True,
                "claims_count": 3,
                "has_description": True,
                "content_length": 1500,
                "parsing_quality": "excellent"
            }
        }


class ParsedDocument(BaseModel):
    """解析后的文档内容"""
    raw_content: str = Field(..., description="原始文本内容")
    structured: StructuredContent = Field(..., description="结构化内容")
    sections: SectionsInfo = Field(..., description="文档部分信息")

    class Config:
        schema_extra = {
            "example": {
                "raw_content": "完整的文档文本...",
                "structured": {
                    "title": "智能家居控制系统",
                    "claims": []
                },
                "sections": {
                    "has_claims": True,
                    "claims_count": 3,
                    "parsing_quality": "excellent"
                }
            }
        }


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int = Field(..., description="文档ID")
    user_id: int = Field(..., description="用户ID")
    title: Optional[str] = Field(None, description="文档标题")
    file_type: FileType = Field(..., description="文件类型")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    status: DocumentStatus = Field(..., description="文档状态")
    parsed_content: Optional[Dict[str, Any]] = Field(None, description="解析后的内容")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "智能家居控制系统",
                "file_type": "docx",
                "file_size": 1024000,
                "status": "parsed",
                "created_at": "2025-12-15T12:00:00",
                "updated_at": "2025-12-15T12:00:00"
            }
        }


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentResponse] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")

    class Config:
        schema_extra = {
            "example": {
                "documents": [],
                "total": 10,
                "page": 1,
                "size": 10
            }
        }


class DocumentParseRequest(BaseModel):
    """文档解析请求"""
    document_id: int = Field(..., description="文档ID")

    class Config:
        schema_extra = {
            "example": {
                "document_id": 1
            }
        }


class DocumentParseResponse(BaseModel):
    """文档解析响应"""
    document_id: int = Field(..., description="文档ID")
    status: DocumentStatus = Field(..., description="文档状态")
    parsed_content: Optional[ParsedDocument] = Field(None, description="解析后的内容")
    message: str = Field(..., description="处理消息")

    class Config:
        schema_extra = {
            "example": {
                "document_id": 1,
                "status": "parsed",
                "parsed_content": {
                    "structured": {},
                    "sections": {}
                },
                "message": "文档解析成功"
            }
        }