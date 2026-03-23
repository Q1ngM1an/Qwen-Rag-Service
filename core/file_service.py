import hashlib
import io
import time
from pathlib import Path
from uuid import uuid4

import configs.config as config
from core.domain_exceptions import ConflictError, DependencyError, NotFoundError, ValidationError


class FileService:
    def __init__(self, db_manager, vector_index_service):
        self.db = db_manager
        self.vector_index = vector_index_service
        config.ensure_runtime_directories()

    def upload_files(self, files: list[dict]):
        results = []
        for file_payload in files:
            results.append(self._upload_single_file(file_payload))
        return self._summarize_upload_results(results)

    def list_files(self, search: str | None = None):
        return [self._serialize_file(item) for item in self.db.list_files(search)]

    def get_file(self, file_id: str):
        file_record = self.db.get_file(file_id)
        if not file_record:
            raise NotFoundError("File not found.")
        return self._serialize_file(file_record)

    def delete_file(self, file_id: str):
        file_record = self.db.get_file(file_id)
        if not file_record:
            raise NotFoundError("File not found.")

        references = self.db.list_file_knowledge_bases(file_id)
        if references:
            raise ConflictError("File is still referenced by one or more knowledge bases.")

        storage_path = Path(file_record["storage_path"])
        try:
            self.vector_index.delete_file(file_id)
        except Exception as exc:
            raise DependencyError(f"Failed to delete file index: {exc}") from exc

        self._delete_storage_file(storage_path)
        self.db.delete_file_record(file_id)

    def _upload_single_file(self, file_payload: dict):
        filename = file_payload["filename"]
        content = file_payload["content"]
        content_type = file_payload.get("content_type")

        try:
            suffix = Path(filename).suffix.lower()
            if suffix not in config.allowed_upload_extensions:
                raise ValidationError("Unsupported file type.")

            text = self._extract_text(filename, content)
            checksum = hashlib.md5(text.encode("utf-8")).hexdigest()
            existing_file = self.db.get_file_by_checksum(checksum)
            if existing_file:
                return {
                    "file_id": existing_file["id"],
                    "filename": existing_file["original_name"],
                    "status": "skipped",
                    "message": "The same content already exists in the global file library.",
                }

            file_id = str(uuid4())
            storage_path = self._build_storage_path(file_id, filename)
            storage_path.write_bytes(content)
            try:
                self.vector_index.index_file(file_id=file_id, filename=filename, text=text)
                self.db.create_file(
                    file_id=file_id,
                    original_name=filename,
                    storage_path=str(storage_path),
                    content_type=content_type,
                    checksum=checksum,
                    text_length=len(text),
                    byte_size=len(content),
                )
            except Exception as exc:
                if storage_path.exists():
                    storage_path.unlink()
                raise DependencyError(f"Failed to index file: {exc}") from exc

            return {
                "file_id": file_id,
                "filename": filename,
                "status": "success",
                "message": "File uploaded successfully.",
            }
        except (ValidationError, DependencyError) as exc:
            return {
                "file_id": None,
                "filename": filename,
                "status": "failed",
                "message": exc.message,
            }

    def _extract_text(self, filename: str, content: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".txt":
            text = content.decode("utf-8", errors="ignore")
        elif suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise DependencyError("pypdf is required to process PDF files.") from exc

            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            raise ValidationError("Unsupported file type.")

        text = text.strip()
        if not text:
            raise ValidationError("File content is empty after parsing.")
        return text

    def _build_storage_path(self, file_id: str, filename: str) -> Path:
        suffix = Path(filename).suffix.lower()
        return Path(config.file_storage_directory) / f"{file_id}{suffix}"

    def _delete_storage_file(self, storage_path: Path):
        if not storage_path.exists():
            return

        last_error = None
        for _ in range(5):
            try:
                storage_path.unlink()
                return
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.1)

        if last_error:
            raise DependencyError(f"Failed to delete file from disk: {last_error}") from last_error

    def _serialize_file(self, file_record: dict):
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

    def _summarize_upload_results(self, items: list[dict]):
        success_count = sum(1 for item in items if item["status"] == "success")
        skipped_count = sum(1 for item in items if item["status"] == "skipped")
        failed_count = sum(1 for item in items if item["status"] == "failed")
        return {
            "total": len(items),
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "items": items,
        }
