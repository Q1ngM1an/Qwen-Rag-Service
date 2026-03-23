from typing import Literal, Optional

from pydantic import BaseModel, Field


class FileUploadResult(BaseModel):
    file_id: Optional[str] = None
    filename: str
    status: Literal["success", "skipped", "failed"]
    message: str


class UploadBatchResult(BaseModel):
    total: int
    success_count: int
    skipped_count: int
    failed_count: int
    items: list[FileUploadResult]


class FileItem(BaseModel):
    id: str
    filename: str
    content_type: Optional[str] = None
    text_length: int
    byte_size: int
    status: str
    reference_count: int = 0
    created_at: str


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None


class KnowledgeBaseItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    file_count: int = 0
    group_count: int = 0
    created_at: str
    updated_at: str


class AttachFilesRequest(BaseModel):
    file_ids: list[str] = Field(default_factory=list)


class KnowledgeBaseGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None


class KnowledgeBaseGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None


class KnowledgeBaseGroupItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    knowledge_base_count: int = 0
    created_at: str
    updated_at: str


class UpdateKnowledgeBaseGroupMembersRequest(BaseModel):
    knowledge_base_ids: list[str] = Field(default_factory=list)


class SessionKnowledgeBaseGroupItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: str
    updated_at: str


class UpdateSessionKnowledgeBaseGroupsRequest(BaseModel):
    knowledge_base_group_ids: list[str] = Field(default_factory=list)
