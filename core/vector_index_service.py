from datetime import datetime

import configs.config as config
from core.vector_store_service import get_vector_store


class VectorIndexService:
    def __init__(self, vector_store=None):
        self.vector_store = vector_store or get_vector_store()
        self._splitter = None

    def _get_splitter(self):
        if self._splitter is None:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                separators=config.separators,
                length_function=len,
            )
        return self._splitter

    def index_file(self, file_id: str, filename: str, text: str) -> int:
        splitter = self._get_splitter()
        chunks = (
            splitter.split_text(text)
            if len(text) > config.max_split_char_number
            else [text]
        )
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadatas = [
            {
                "file_id": file_id,
                "source": filename,
                "create_time": timestamp,
            }
            for _ in chunks
        ]
        ids = [f"{file_id}:{index}" for index, _ in enumerate(chunks)]
        self.vector_store.add_texts(chunks, metadatas=metadatas, ids=ids)
        return len(chunks)

    def delete_file(self, file_id: str):
        self.vector_store.delete(where={"file_id": file_id})
