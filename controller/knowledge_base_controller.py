class KnowledgeBaseController:
    def __init__(self, knowledge_base_service):
        self.knowledge_base_service = knowledge_base_service

    def create_knowledge_base(self, name: str, description: str | None = None, owner_id: str | None = None):
        return self.knowledge_base_service.create_knowledge_base(name, description, owner_id)

    def list_knowledge_bases(self, search: str | None = None):
        return self.knowledge_base_service.list_knowledge_bases(search)

    def get_knowledge_base(self, kb_id: str):
        return self.knowledge_base_service.get_knowledge_base(kb_id)

    def update_knowledge_base(self, kb_id: str, name: str | None = None, description: str | None = None, owner_id: str | None = None):
        return self.knowledge_base_service.update_knowledge_base(kb_id, name, description, owner_id)

    def delete_knowledge_base(self, kb_id: str):
        self.knowledge_base_service.delete_knowledge_base(kb_id)

    def attach_files(self, kb_id: str, file_ids: list[str]):
        return self.knowledge_base_service.attach_files(kb_id, file_ids)

    def detach_file(self, kb_id: str, file_id: str):
        self.knowledge_base_service.detach_file(kb_id, file_id)

    def list_files(self, kb_id: str, search: str | None = None):
        return self.knowledge_base_service.list_files(kb_id, search)
