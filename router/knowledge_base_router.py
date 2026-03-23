from fastapi import APIRouter, Depends, Query

from core.domain_exceptions import DomainError
from router.common import raise_http_error
from schemas.dependencies import get_knowledge_base_controller
from schemas.domain_models import AttachFilesRequest, KnowledgeBaseCreate, KnowledgeBaseUpdate
from schemas.response import R


router = APIRouter(prefix="/api/knowledge-bases", tags=["KnowledgeBases"])


@router.post("")
def create_knowledge_base(
    req: KnowledgeBaseCreate,
    ctrl=Depends(get_knowledge_base_controller),
):
    try:
        return R.success(data=ctrl.create_knowledge_base(req.name, req.description, req.owner_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("")
def list_knowledge_bases(
    search: str | None = Query(default=None),
    ctrl=Depends(get_knowledge_base_controller),
):
    try:
        return R.success(data=ctrl.list_knowledge_bases(search))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{kb_id}")
def get_knowledge_base(kb_id: str, ctrl=Depends(get_knowledge_base_controller)):
    try:
        return R.success(data=ctrl.get_knowledge_base(kb_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.patch("/{kb_id}")
def update_knowledge_base(
    kb_id: str,
    req: KnowledgeBaseUpdate,
    ctrl=Depends(get_knowledge_base_controller),
):
    try:
        return R.success(data=ctrl.update_knowledge_base(kb_id, req.name, req.description, req.owner_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{kb_id}")
def delete_knowledge_base(kb_id: str, ctrl=Depends(get_knowledge_base_controller)):
    try:
        ctrl.delete_knowledge_base(kb_id)
        return R.success(message="Knowledge base deleted successfully.")
    except DomainError as exc:
        raise_http_error(exc)


@router.post("/{kb_id}/files/attach")
def attach_files(
    kb_id: str,
    req: AttachFilesRequest,
    ctrl=Depends(get_knowledge_base_controller),
):
    try:
        return R.success(data=ctrl.attach_files(kb_id, req.file_ids))
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{kb_id}/files/{file_id}")
def detach_file(kb_id: str, file_id: str, ctrl=Depends(get_knowledge_base_controller)):
    try:
        ctrl.detach_file(kb_id, file_id)
        return R.success(message="File detached successfully.")
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{kb_id}/files")
def list_knowledge_base_files(
    kb_id: str,
    search: str | None = Query(default=None),
    ctrl=Depends(get_knowledge_base_controller),
):
    try:
        return R.success(data=ctrl.list_files(kb_id, search))
    except DomainError as exc:
        raise_http_error(exc)
