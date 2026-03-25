import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = Path(tempfile.gettempdir()) / "qwen-rag-runtime"
FRONTEND_DIST_DIR = BASE_DIR / "frontend_dist"
FRONTEND_DEV_DIST_DIR = BASE_DIR.parent.parent / "JsProject" / "qwen-rag-vue" / "dist"

# App storage
db_path = str(RUNTIME_DIR / "chat_data_runtime.db")
output_directory = str(BASE_DIR / "output")
file_storage_directory = str(Path(output_directory) / "files")
md5_path = str(Path(output_directory) / "knowledge_md5.txt")

# Chroma
collection_name = "rag"
persist_directory = str(BASE_DIR / "chroma_db")

# Text splitting
chunk_size = 1000
chunk_overlap = 100
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

vllm_services = [
    {
        "id": "embedding",
        "label": "Embedding 服务",
        "service_type": "embedding",
        "served_model": embedding_model_name,
        "api_base": embedding_api_base,
        "api_key": embedding_api_key,
    },
    {
        "id": "qwen06b",
        "label": "Qwen 0.6B",
        "service_type": "chat",
        "served_model": chat_model_small_name,
        "api_base": chat_model_small_api_base,
        "api_key": chat_model_small_api_key,
    },
    {
        "id": "qwen32b",
        "label": "Qwen 32B",
        "service_type": "chat",
        "served_model": chat_model_large_name,
        "api_base": chat_model_large_api_base,
        "api_key": chat_model_large_api_key,
    },
]


def get_vllm_service(service_id: str):
    for service in vllm_services:
        if service["id"] == service_id:
            return service
    raise KeyError(f"Unknown vLLM service: {service_id}")


def get_frontend_dist_dir() -> Path | None:
    candidates = [FRONTEND_DIST_DIR, FRONTEND_DEV_DIST_DIR]
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return None


def ensure_runtime_directories() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    Path(file_storage_directory).mkdir(parents=True, exist_ok=True)
    Path(persist_directory).mkdir(parents=True, exist_ok=True)
