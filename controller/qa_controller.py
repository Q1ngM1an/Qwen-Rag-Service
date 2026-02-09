import io
import json
import uuid

from controller.base_chat_controller import BaseChatController
from core.rag_service import RagService
from dao.db_manager import get_db_manager
import streamlit as st


# --- 逻辑层 (Controller) ---
class QAChatController(BaseChatController):
    """QA 业务逻辑 (对接 qa_history 表)"""

    TABLE_NAME = "qa_history"

    def get_sidebar_sessions(self):
        """获取 QA 历史会话"""
        return self.get_session_list(self.TABLE_NAME)

    def create_new_session(self):
        st.session_state["session_id"] = str(uuid.uuid4())
        # 清理 RLHF 缓存
        st.rerun()

    def get_session_history(self, session_id):
        return self.db.get_messages(self.TABLE_NAME, session_id)

    def delete_session(self, session_id):
        self.db.clear_session(self.TABLE_NAME, session_id)
        if st.session_state.get("session_id") == session_id:
            self.create_new_session()
        else:
            st.rerun()

    def regenerate_last_response(self, session_id):
        # 1. 拿到最后一条 User 消息的内容 (也就是倒数第二条，因为倒数第一是 AI)
        msgs = self.db.get_messages(self.TABLE_NAME, session_id)
        user_prompt = None

        # 简单的防御逻辑
        if len(msgs) >= 2:
            # 假设结构是 [..., User, AI]
            if msgs[-1].get("type") == "ai" or msgs[-1].get("role") == "assistant":
                # 拿到 User 的内容
                last_user_msg = msgs[-2]
                user_prompt = last_user_msg.get("data", {}).get("content") or last_user_msg.get("content")

                # 2. 删除 AI 记录
                self.db.delete_last_message(self.TABLE_NAME, session_id)
                # 3. 删除 User 记录 (因为 LangChain 会再次写入)
                self.db.delete_last_message(self.TABLE_NAME, session_id)

        return user_prompt

    def export_session_to_text(self, session_id):
        """将会话导出为文本流"""
        msgs = self.get_session_history(session_id)
        output = io.StringIO()

        for msg in msgs:
            role = "AI" if (msg.get("type") == "ai" or msg.get("role") == "assistant") else "User"
            content = msg.get("data", {}).get("content") or msg.get("content", "")
            output.write(f"[{role}]:\n{content}\n\n{'-' * 20}\n\n")

        return output.getvalue().encode('utf-8')

    def generate_response_stream(self, prompt, session_id, selected_model="qwen_0.6b"):
        # 场景 A：直接调用自动挡接口
        return self.rag.stream_qa_response(prompt, session_id, selected_model)