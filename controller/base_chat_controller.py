import json
import uuid

from core.rag_service import RagService
from dao.db_manager import get_db_manager
import streamlit as st

class BaseChatController:
    """基础控制器：包含 DB 和 RAG 的通用操作"""

    def __init__(self):
        self.db = get_db_manager()
        # 懒加载 RAG 服务
        if "rag_service" not in st.session_state:
            st.session_state["rag_service"] = RagService()
        self.rag = st.session_state["rag_service"]

    def get_session_list(self, table_name):
        """获取侧边栏会话列表"""
        try:
            rows = self.db.get_all_sessions(table_name)

            sessions = []
            for r in rows:
                sid, time_str, msg_json = r
                try:
                    # 解析第一条消息作为标题
                    msg_data = json.loads(msg_json)
                    # 兼容 LangChain 格式
                    content = msg_data.get("data", {}).get("content", "新对话")
                    title = content[:20] + "..." if len(content) > 20 else content
                except:
                    title = "未命名对话"

                sessions.append({"id": sid, "title": title, "time": time_str})
            return sessions
        except Exception as e:
            st.error(f"读取历史失败: {e}")
            return []

    def get_sidebar_sessions(self):
        raise NotImplementedError()

    def create_new_session(self):
        # st.session_state["session_id"] = str(uuid.uuid4())
        # 清理 RLHF 缓存
        # if "rlhf_data" in st.session_state:
        #     del st.session_state["rlhf_data"]
        # st.rerun()
        raise NotImplementedError()

    def delete_session(self, session_id):
        # self.db.clear_session(session_id)
        # if st.session_state.get("session_id") == session_id:
        #     self.create_new_session()
        # else:
        #     st.rerun()
        raise NotImplementedError()

    def get_session_history(self, session_id):
        """获取某个会话的消息历史"""
        # return self.db.get_messages(session_id)
        raise NotImplementedError()