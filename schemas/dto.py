from typing import List

from pydantic import BaseModel

# --- 定义 DTO (Data Transfer Object) ---
class SessionRequest(BaseModel):
    session_id: str

class QAStreamRequest(BaseModel):
    session_id: str
    prompt: str
    selected_model: str = "qwen_0.6b"

class RLHFStreamRequest(BaseModel):
    session_id: str
    prompt: str
    temperature: float
    selected_model: str

class RLHFSavePreferenceRequest(BaseModel):
    session_id: str
    prompt: str
    answers: List[str]          # 三个回答
    temperatures: List[float]   # 对应的温度
    choice_idx: int             # 选中的索引 (0, 1, 2)
    context_text: str           # RAG 文档切片内容