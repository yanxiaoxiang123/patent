"""
文档相关的 Pydantic schemas
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"


class FileType(str, Enum):
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"


class SectionInfo(BaseModel):
    """单个章节信息"""
    name: str
    content: str
    char_count: int


class SectionsInfo(BaseModel):
    """解析后的文档章节信息"""
    has_title: bool = False
    has_abstract: bool = False
    has_claims: bool = False
    has_description: bool = False
    claims_count: int = 0
    content_length: int = 0
    parsing_quality: str = "poor"  # excellent, good, fair, poor


class StructuredContent(BaseModel):
    """结构化文档内容"""
    title: str = ""
    abstract: str = ""
    claims: List[Dict[str, Any]] = []
    description: str = ""


class ParsedContent(BaseModel):
    """文档解析结果"""
    raw_content: str = ""
    structured: StructuredContent = StructuredContent()
    sections: SectionsInfo = SectionsInfo()


class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: int
    user_id: int
    title: str
    file_type: str
    file_size: int
    status: DocumentStatus
    parsed_content: Optional[ParsedContent] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int


class DocumentUploadRequest(BaseModel):
    """文档上传请求模型"""
    title: Optional[str] = None


class DocumentParseRequest(BaseModel):
    """文档解析请求模型"""
    parse_options: Optional[Dict[str, Any]] = None


class DocumentParseResponse(BaseModel):
    """文档解析响应模型"""
    document_id: int
    status: DocumentStatus
    parsed_content: Optional[ParsedContent] = None
    message: str = "解析成功"
