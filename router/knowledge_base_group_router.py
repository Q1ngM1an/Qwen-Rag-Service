from fastapi import APIRouter, Depends, Query

from core.domain_exceptions import DomainError
from router.common import raise_http_error
from schemas.dependencies import get_knowledge_base_group_controller
from schemas.domain_models import (
    KnowledgeBaseGroupCreate,
    KnowledgeBaseGroupUpdate,
    UpdateKnowledgeBaseGroupMembersRequest,
)
from schemas.response import R


router = APIRouter(prefix="/api/knowledge-base-groups", tags=["KnowledgeBaseGroups"])


@router.post("")
def create_group(req: KnowledgeBaseGroupCreate, ctrl=Depends(get_knowledge_base_group_controller)):
    try:
        return R.success(data=ctrl.create_group(req.name, req.description, req.owner_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("")
def list_groups(
    search: str | None = Query(default=None),
    ctrl=Depends(get_knowledge_base_group_controller),
):
    try:
        return R.success(data=ctrl.list_groups(search))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{group_id}")
def get_group(group_id: str, ctrl=Depends(get_knowledge_base_group_controller)):
    try:
        return R.success(data=ctrl.get_group(group_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.patch("/{group_id}")
def update_group(
    group_id: str,
    req: KnowledgeBaseGroupUpdate,
    ctrl=Depends(get_knowledge_base_group_controller),
):
    try:
        return R.success(data=ctrl.update_group(group_id, req.name, req.description, req.owner_id))
    except DomainError as exc:
        raise_http_error(exc)


@router.delete("/{group_id}")
def delete_group(group_id: str, ctrl=Depends(get_knowledge_base_group_controller)):
    try:
        ctrl.delete_group(group_id)
        return R.success(message="Knowledge base group deleted successfully.")
    except DomainError as exc:
        raise_http_error(exc)


@router.put("/{group_id}/knowledge-bases")
def replace_group_members(
    group_id: str,
    req: UpdateKnowledgeBaseGroupMembersRequest,
    ctrl=Depends(get_knowledge_base_group_controller),
):
    try:
        return R.success(data=ctrl.replace_members(group_id, req.knowledge_base_ids))
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{group_id}/knowledge-bases")
def list_group_knowledge_bases(group_id: str, ctrl=Depends(get_knowledge_base_group_controller)):
    try:
        return R.success(data=ctrl.list_group_knowledge_bases(group_id))
    except DomainError as exc:
        raise_http_error(exc)
