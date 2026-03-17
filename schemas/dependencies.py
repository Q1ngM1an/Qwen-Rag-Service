from fastapi import Depends
from core.rag_service import RagService
from dao.db_manager import get_db_manager
from controller.qa_controller import QAChatController
from controller.rlhf_controller import RLHFCollectController

# 类似 Spring 中的单例 Bean
_db_instance = get_db_manager()
_rag_instance = RagService()

def get_db():
    return _db_instance

def get_rag():
    return _rag_instance

# 自动装配 Controller
# 相当于给类打上了 @Service 注解
def get_qa_controller(db = Depends(get_db), rag = Depends(get_rag)) -> QAChatController:
    return QAChatController(db, rag)

def get_rlhf_controller(db = Depends(get_db), rag = Depends(get_rag)) -> RLHFCollectController:
    return RLHFCollectController(db, rag)