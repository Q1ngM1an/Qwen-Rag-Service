import uuid

from core.domain_exceptions import NotFoundError, ValidationError


class KnowledgeBaseGroupService:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_group(self, name: str, description: str | None = None, owner_id: str | None = None):
        name = (name or "").strip()
        if not name:
            raise ValidationError("Knowledge base group name is required.")

        group_id = str(uuid.uuid4())
        self.db.create_knowledge_base_group(group_id, name, description, owner_id)
        return self.get_group(group_id)

    def list_groups(self, search: str | None = None):
        return [self._serialize_group(item) for item in self.db.list_knowledge_base_groups(search)]

    def get_group(self, group_id: str):
        group = self.db.get_knowledge_base_group(group_id)
        if not group:
            raise NotFoundError("Knowledge base group not found.")
        return self._serialize_group(group)

    def update_group(self, group_id: str, name: str | None = None, description: str | None = None, owner_id: str | None = None):
        self.get_group(group_id)
        fields = {}
        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise ValidationError("Knowledge base group name cannot be empty.")
            fields["name"] = normalized_name
        if description is not None:
            fields["description"] = description
        if owner_id is not None:
            fields["owner_id"] = owner_id

        self.db.update_knowledge_base_group(group_id, fields)
        return self.get_group(group_id)

    def delete_group(self, group_id: str):
        self.get_group(group_id)
        self.db.delete_knowledge_base_group(group_id)

    def replace_members(self, group_id: str, knowledge_base_ids: list[str]):
        self.get_group(group_id)
        self._validate_knowledge_base_ids(knowledge_base_ids)
        self.db.replace_group_members(group_id, knowledge_base_ids)
        return self.list_group_knowledge_bases(group_id)

    def list_group_knowledge_bases(self, group_id: str):
        self.get_group(group_id)
        knowledge_bases = self.db.list_group_knowledge_bases(group_id)
        return [
            {
                "id": knowledge_base["id"],
                "name": knowledge_base["name"],
                "description": knowledge_base.get("description"),
                "owner_id": knowledge_base.get("owner_id"),
                "file_count": knowledge_base.get("file_count", 0),
                "created_at": knowledge_base["created_at"],
                "updated_at": knowledge_base["updated_at"],
            }
            for knowledge_base in knowledge_bases
        ]

    def _validate_knowledge_base_ids(self, knowledge_base_ids: list[str]):
        if not knowledge_base_ids:
            return

        existing = self.db.get_knowledge_bases_by_ids(knowledge_base_ids)
        existing_ids = {item["id"] for item in existing}
        missing_ids = [kb_id for kb_id in knowledge_base_ids if kb_id not in existing_ids]
        if missing_ids:
            raise NotFoundError(f"Knowledge bases not found: {', '.join(missing_ids)}")

    def _serialize_group(self, group: dict):
        return {
            "id": group["id"],
            "name": group["name"],
            "description": group.get("description"),
            "owner_id": group.get("owner_id"),
            "knowledge_base_count": group.get("knowledge_base_count", 0),
            "created_at": group["created_at"],
            "updated_at": group["updated_at"],
        }
