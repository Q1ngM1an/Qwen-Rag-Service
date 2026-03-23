from core.domain_exceptions import NotFoundError, ValidationError


class SessionScopeService:
    VALID_SESSION_TYPES = {"qa", "rlhf"}

    def __init__(self, db_manager):
        self.db = db_manager

    def update_session_knowledge_base_groups(self, session_type: str, session_id: str, group_ids: list[str]):
        self._validate_session_identity(session_type, session_id)
        self._validate_group_ids(group_ids)
        self.db.replace_session_knowledge_base_groups(session_type, session_id, group_ids)
        return self.list_session_knowledge_base_groups(session_type, session_id)

    def list_session_knowledge_base_groups(self, session_type: str, session_id: str):
        self._validate_session_identity(session_type, session_id)
        groups = self.db.list_session_knowledge_base_groups(session_type, session_id)
        return [
            {
                "id": group["id"],
                "name": group["name"],
                "description": group.get("description"),
                "owner_id": group.get("owner_id"),
                "created_at": group["created_at"],
                "updated_at": group["updated_at"],
            }
            for group in groups
        ]

    def _validate_session_identity(self, session_type: str, session_id: str):
        if session_type not in self.VALID_SESSION_TYPES:
            raise ValidationError("Invalid session type.")
        if not session_id.strip():
            raise ValidationError("Session id is required.")

    def _validate_group_ids(self, group_ids: list[str]):
        if not group_ids:
            return

        existing_groups = self.db.get_knowledge_base_groups_by_ids(group_ids)
        existing_ids = {group["id"] for group in existing_groups}
        missing_ids = [group_id for group_id in group_ids if group_id not in existing_ids]
        if missing_ids:
            raise NotFoundError(f"Knowledge base groups not found: {', '.join(missing_ids)}")
