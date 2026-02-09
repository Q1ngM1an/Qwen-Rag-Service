from typing import Sequence
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from dao import db_manager
from dao.db_manager import get_db_manager


def get_qa_chat_history(session_id: str):
    """QA 页面专用的历史加载器"""
    return ChatMessageHistory(session_id, table_name="qa_history")

def get_rlhf_chat_history(session_id: str):
    """RLHF 页面专用的历史加载器 (虽然 RLHF 主要用手动挡，但备用)"""
    return ChatMessageHistory(session_id, table_name="rlhf_history")

class ChatMessageHistory(BaseChatMessageHistory):
    """
    LangChain 的适配器层
    只负责对象转换 (Object Mapping)，不负责 SQL 细节
    """

    def __init__(self, session_id: str, table_name: str):
        self.session_id = session_id
        self.table_name = table_name
        self.db = get_db_manager()

    @property
    def messages(self):
        # 传入 table_name
        message_dicts = self.db.get_messages(self.table_name, self.session_id)
        return messages_from_dict(message_dicts)

    def add_message(self, message: BaseMessage):
        msg_dict = message_to_dict(message)
        # 传入 table_name
        self.db.add_message(self.table_name, self.session_id, msg_dict)

    def clear(self):
        self.db.clear_session(self.table_name, self.session_id)