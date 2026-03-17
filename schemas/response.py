from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

# 相当于 Java 中的 <T>
T = TypeVar('T')

class R(BaseModel, Generic[T]):
    """统一响应体"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "success"):
        return cls(code=200, message=message, data=data)

    @classmethod
    def fail(cls, code: int = 500, message: str = "error", data: Any = None):
        return cls(code=code, message=message, data=data)