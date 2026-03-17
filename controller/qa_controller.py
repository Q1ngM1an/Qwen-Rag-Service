import io
import uuid

from controller.base_chat_controller import BaseChatController

class QAChatController(BaseChatController):
    """QA 业务逻辑 """

    TABLE_NAME = "qa_history"

    def get_sidebar_sessions(self):
        return self.get_session_list(self.TABLE_NAME)

    def get_session_history(self, session_id):
        return self.db.get_messages(self.TABLE_NAME, session_id)

    def delete_session(self, session_id):
        return self.db.clear_session(self.TABLE_NAME, session_id)

    def regenerate_last_response(self, session_id):
        # 1. 拿到最后一条 User 消息的内容 (也就是倒数第二条，因为倒数第一是 AI)
        msgs = self.db.get_messages(self.TABLE_NAME, session_id)
        user_prompt = None

        if len(msgs) >= 2:
            # [..., User, AI]
            if msgs[-1].get("type") == "ai" or msgs[-1].get("role") == "assistant":
                # 1. 拿到 User 的内容
                last_user_msg = msgs[-2]
                user_prompt = last_user_msg.get("data", {}).get("content") or last_user_msg.get("content")

                # 2. 删除 AI 记录
                self.db.delete_last_message(self.TABLE_NAME, session_id)
                # 3. 删除 User 记录
                self.db.delete_last_message(self.TABLE_NAME, session_id)
            else:
                raise ValueError("对话顺序出现异常")

        return user_prompt

    def generate_response_stream(self, prompt, session_id, selected_model="qwen_0.6b"):
        # 在qa场景下，直接调用自动挡接口
        return self.rag.stream_qa_response(prompt, session_id, selected_model)