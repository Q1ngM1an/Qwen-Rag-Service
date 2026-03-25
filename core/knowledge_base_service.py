from typing import Any
import uuid

from core.domain_exceptions import NotFoundError, ValidationError


class KnowledgeBaseService:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_knowledge_base(
        self,
        name: str,
        description: str | None = None,
        owner_id: str | None = None,
    ):
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValidationError("Knowledge base name is required.")

        kb_id = str(uuid.uuid4())
        self.db.create_knowledge_base(kb_id, normalized_name, description, owner_id)
        return self.get_knowledge_base(kb_id)

    def list_knowledge_bases(self, search: str | None = None):
        return [
            self._serialize_knowledge_base(item)
            for item in self.db.list_knowledge_bases(search)
        ]

    def get_knowledge_base(self, kb_id: str):
        knowledge_base = self.db.get_knowledge_base(kb_id)
        if not knowledge_base:
            raise NotFoundError("Knowledge base not found.")
        return self._serialize_knowledge_base(knowledge_base)

    def update_knowledge_base(
        self,
        kb_id: str,
        name: str | None = None,
        description: str | None = None,
        owner_id: str | None = None,
    ):
        self.get_knowledge_base(kb_id)

        fields: dict[str, Any] = {}
        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise ValidationError("Knowledge base name cannot be empty.")
            fields["name"] = normalized_name
        if description is not None:
            fields["description"] = description
        if owner_id is not None:
            fields["owner_id"] = owner_id

        self.db.update_knowledge_base(kb_id, fields)
        return self.get_knowledge_base(kb_id)

    def delete_knowledge_base(self, kb_id: str):
        self.get_knowledge_base(kb_id)
        self.db.delete_knowledge_base(kb_id)

    def attach_files(self, kb_id: str, file_ids: list[str]):
        self.get_knowledge_base(kb_id)
        self._validate_file_ids(file_ids)
        self.db.attach_files_to_knowledge_base(kb_id, file_ids)
        return self.list_files(kb_id)

    def detach_file(self, kb_id: str, file_id: str):
        self.get_knowledge_base(kb_id)
        if not self.db.is_file_attached_to_knowledge_base(kb_id, file_id):
            raise NotFoundError("File is not attached to this knowledge base.")
        self.db.detach_file_from_knowledge_base(kb_id, file_id)

    def list_files(self, kb_id: str, search: str | None = None):
        self.get_knowledge_base(kb_id)
        return [
            self._serialize_file(item)
            for item in self.db.list_knowledge_base_files(kb_id, search)
        ]

    def _validate_file_ids(self, file_ids: list[str]):
        if not file_ids:
            raise ValidationError("At least one file id is required.")

        existing_files = self.db.get_files_by_ids(file_ids)
        existing_ids = {item["id"] for item in existing_files}
        missing_ids = [file_id for file_id in file_ids if file_id not in existing_ids]
        if missing_ids:
            raise NotFoundError(f"Files not found: {', '.join(missing_ids)}")

    def _serialize_knowledge_base(self, knowledge_base: dict[str, Any]):
        return {
            "id": knowledge_base["id"],
            "name": knowledge_base["name"],
            "description": knowledge_base.get("description"),
            "owner_id": knowledge_base.get("owner_id"),
            "file_count": knowledge_base.get("file_count", 0),
            "group_count": knowledge_base.get("group_count", 0),
            "created_at": knowledge_base["created_at"],
            "updated_at": knowledge_base["updated_at"],
        }

    def _serialize_file(self, file_record: dict[str, Any]):
        return {
            "id": file_record["id"],
            "filename": file_record["original_name"],
            "content_type": file_record["content_type"],
            "text_length": file_record["text_length"],
            "byte_size": file_record["byte_size"],
            "status": file_record["status"],
            "reference_count": file_record.get("reference_count", 0),
            "created_at": file_record["created_at"],
        }
