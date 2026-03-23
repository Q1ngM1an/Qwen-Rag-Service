from functools import lru_cache

from fastapi import Depends

from controller.file_controller import FileController
from controller.knowledge_base_controller import KnowledgeBaseController
from controller.knowledge_base_group_controller import KnowledgeBaseGroupController
from controller.qa_controller import QAChatController
from controller.rlhf_controller import RLHFCollectController
from controller.session_scope_controller import SessionScopeController
from dao.app_db_manager import get_db_manager

# 类似 Spring 中的单例 Bean
def get_db():
    return get_db_manager()


@lru_cache(maxsize=1)
def _get_rag_instance():
    from core.rag_service import RagService

    return RagService()


def get_rag():
    return _get_rag_instance()

# 自动装配 Controller
# 相当于给类打上了 @Service 注解
def get_qa_controller(db = Depends(get_db), rag = Depends(get_rag)) -> QAChatController:
    return QAChatController(db, rag)

def get_rlhf_controller(db = Depends(get_db), rag = Depends(get_rag)) -> RLHFCollectController:
    return RLHFCollectController(db, rag)


@lru_cache(maxsize=1)
def _get_vector_index_service():
    from core.vector_index_service import VectorIndexService

    return VectorIndexService()


@lru_cache(maxsize=1)
def _get_file_service():
    from core.file_service import FileService

    return FileService(get_db_manager(), _get_vector_index_service())


@lru_cache(maxsize=1)
def _get_knowledge_base_service():
    from core.knowledge_base_service import KnowledgeBaseService

    return KnowledgeBaseService(get_db_manager())


@lru_cache(maxsize=1)
def _get_knowledge_base_group_service():
    from core.knowledge_base_group_service import KnowledgeBaseGroupService

    return KnowledgeBaseGroupService(get_db_manager())


@lru_cache(maxsize=1)
def _get_session_scope_service():
    from core.session_scope_service import SessionScopeService

    return SessionScopeService(get_db_manager())


def get_file_controller() -> FileController:
    return FileController(_get_file_service())


def get_knowledge_base_controller() -> KnowledgeBaseController:
    return KnowledgeBaseController(_get_knowledge_base_service())


def get_knowledge_base_group_controller() -> KnowledgeBaseGroupController:
    return KnowledgeBaseGroupController(_get_knowledge_base_group_service())


def get_session_scope_controller() -> SessionScopeController:
    return SessionScopeController(_get_session_scope_service())
