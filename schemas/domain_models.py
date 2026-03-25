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


class DashboardCounts(BaseModel):
    qa_sessions: int
    rlhf_sessions: int
    files: int
    knowledge_bases: int
    knowledge_packs: int


class DashboardAssets(BaseModel):
    files: int
    knowledge_bases: int
    knowledge_packs: int


class VllmServiceStatusItem(BaseModel):
    id: str
    label: str
    service_type: Literal["chat", "embedding"]
    served_model: str
    api_base: str
    status: Literal["online", "degraded", "offline"]
    latency_ms: Optional[int] = None
    message: Optional[str] = None


class GpuMemoryItem(BaseModel):
    index: int
    name: str
    memory_used_mb: int
    memory_total_mb: int
    utilization_gpu_percent: int


class GpuMemoryOverview(BaseModel):
    status: Literal["ok", "unavailable"]
    total_used_mb: int
    total_mb: int
    utilization_percent: int
    gpus: list[GpuMemoryItem] = Field(default_factory=list)


class DashboardOverview(BaseModel):
    counts: DashboardCounts
    assets: DashboardAssets
    vllm_services: list[VllmServiceStatusItem] = Field(default_factory=list)
    gpu_memory: GpuMemoryOverview
