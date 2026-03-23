class FileController:
    def __init__(self, file_service):
        self.file_service = file_service

    def upload_files(self, files: list[dict]):
        return self.file_service.upload_files(files)

    def list_files(self, search: str | None = None):
        return self.file_service.list_files(search)

    def get_file(self, file_id: str):
        return self.file_service.get_file(file_id)

    def delete_file(self, file_id: str):
        self.file_service.delete_file(file_id)
