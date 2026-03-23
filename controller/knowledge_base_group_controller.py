class KnowledgeBaseGroupController:
    def __init__(self, knowledge_base_group_service):
        self.knowledge_base_group_service = knowledge_base_group_service

    def create_group(self, name: str, description: str | None = None, owner_id: str | None = None):
        return self.knowledge_base_group_service.create_group(name, description, owner_id)

    def list_groups(self, search: str | None = None):
        return self.knowledge_base_group_service.list_groups(search)

    def get_group(self, group_id: str):
        return self.knowledge_base_group_service.get_group(group_id)

    def update_group(self, group_id: str, name: str | None = None, description: str | None = None, owner_id: str | None = None):
        return self.knowledge_base_group_service.update_group(group_id, name, description, owner_id)

    def delete_group(self, group_id: str):
        self.knowledge_base_group_service.delete_group(group_id)

    def replace_members(self, group_id: str, knowledge_base_ids: list[str]):
        return self.knowledge_base_group_service.replace_members(group_id, knowledge_base_ids)

    def list_group_knowledge_bases(self, group_id: str):
        return self.knowledge_base_group_service.list_group_knowledge_bases(group_id)
