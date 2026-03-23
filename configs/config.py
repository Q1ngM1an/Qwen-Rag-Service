from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# App storage
db_path = str(BASE_DIR / "chat_data.db")
output_directory = str(BASE_DIR / "output")
file_storage_directory = str(Path(output_directory) / "files")

# Chroma
collection_name = "rag"
persist_directory = str(BASE_DIR / "chroma_db")

# Text splitting
chunk_size = 1000
chunk_overlap = 100
separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
max_split_char_number = 1000        # 文本分割的阈值

similarity_threshold = 1            # 检索返回匹配的文档数量

separators = ["\n\n", "\n", ".", "!", "?", "。", "，", "；", " ", ""]
max_split_char_number = 1000
similarity_threshold = 1

allowed_upload_extensions = {".txt", ".pdf"}

embedding_model_name = "embedding-model"
embedding_api_base = "http://localhost:8001/v1"
embedding_api_key = "token-embed123"

chat_model_small_name = "qwen06b"
chat_model_small_api_base = "http://localhost:8002/v1"
chat_model_small_api_key = "token-qwen06b123"

chat_model_large_name = "qwen32b"
chat_model_large_api_base = "http://localhost:8004/v1"
chat_model_large_api_key = "token-qwen32b123"


def ensure_runtime_directories() -> None:
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    Path(file_storage_directory).mkdir(parents=True, exist_ok=True)
    Path(persist_directory).mkdir(parents=True, exist_ok=True)
