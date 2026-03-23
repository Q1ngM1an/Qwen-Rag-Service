from fastapi import APIRouter, Depends

from core.domain_exceptions import DomainError
from router.common import raise_http_error
from schemas.dependencies import get_session_scope_controller
from schemas.domain_models import UpdateSessionKnowledgeBaseGroupsRequest
from schemas.response import R


router = APIRouter(prefix="/api/session-scopes", tags=["SessionScopes"])


@router.put("/{session_type}/{session_id}/knowledge-base-groups")
def update_session_knowledge_base_groups(
    session_type: str,
    session_id: str,
    req: UpdateSessionKnowledgeBaseGroupsRequest,
    ctrl=Depends(get_session_scope_controller),
):
    try:
        return R.success(
            data=ctrl.update_session_knowledge_base_groups(
                session_type,
                session_id,
                req.knowledge_base_group_ids,
            )
        )
    except DomainError as exc:
        raise_http_error(exc)


@router.get("/{session_type}/{session_id}/knowledge-base-groups")
def list_session_knowledge_base_groups(
    session_type: str,
    session_id: str,
    ctrl=Depends(get_session_scope_controller),
):
    try:
        return R.success(data=ctrl.list_session_knowledge_base_groups(session_type, session_id))
    except DomainError as exc:
        raise_http_error(exc)
