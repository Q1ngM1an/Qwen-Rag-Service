from functools import lru_cache

import configs.config as config
from dao.chroma_manager import get_chroma_connection


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStoreService()

class VectorStoreService:
    def __init__(self):
        self._chroma = get_chroma_connection()

    def get_retriever(self):
        """返回向量检索器，方便加入chain"""
        return self._chroma.as_retriever(search_kwargs={"k": config.similarity_threshold})

    def __getattr__(self, item):
        """
        核心魔法：
        当外界调用 vector_service.add_texts() 时，
        Python 发现 VectorStoreService 没有这个方法，
        就会自动触发 __getattr__，
        我们在这里把它“转发”给 self._chroma。
        """
        return getattr(self._chroma, item)
