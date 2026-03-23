class SessionScopeController:
    def __init__(self, session_scope_service):
        self.session_scope_service = session_scope_service

    def update_session_knowledge_base_groups(self, session_type: str, session_id: str, group_ids: list[str]):
        return self.session_scope_service.update_session_knowledge_base_groups(session_type, session_id, group_ids)

    def list_session_knowledge_base_groups(self, session_type: str, session_id: str):
        return self.session_scope_service.list_session_knowledge_base_groups(session_type, session_id)
