import io
import uuid

from langchain_core.messages import HumanMessage, AIMessage

from controller.base_chat_controller import BaseChatController
import streamlit as st


class RLHFController(BaseChatController):
    """RLHF 业务逻辑 (对接 rlhf_history 表 和 dpo_dataset 表)"""

    TABLE_NAME = "rlhf_history"

    def get_sidebar_sessions(self):
        """获取 RLHF 历史会话"""
        return self.get_session_list(self.TABLE_NAME)

    def create_new_session(self):
        st.session_state["session_id"] = str(uuid.uuid4())
        # 清理 RLHF 缓存
        if "rlhf_data" in st.session_state:
            del st.session_state["rlhf_data"]
        st.rerun()

    def get_session_history(self, session_id):
        return self.db.get_messages(self.TABLE_NAME, session_id)

    def delete_session(self, session_id):
        self.db.clear_session(self.TABLE_NAME, session_id)
        if st.session_state.get("session_id") == session_id:
            self.create_new_session()
        else:
            st.rerun()

    def commit_interaction(self, session_id, prompt, answers, choice_idx):
        """提交到 RLHF 会话历史 (用于 UI 回显)"""
        winner_answer = answers[choice_idx]

        user_msg = {"type": "human", "data": {"content": prompt}}
        self.db.add_message(self.TABLE_NAME, session_id, user_msg)

        ai_msg = {"type": "ai", "data": {"content": winner_answer}}
        self.db.add_message(self.TABLE_NAME, session_id, ai_msg)

    def save_preference(self, session_id, prompt, answers, temperatures, choice_idx, context_text):
        """
        保存训练数据：分类 Chosen 和 Rejected
        """
        chosen_ans = answers[choice_idx]
        chosen_temp = temperatures[choice_idx]

        rejected_ans_list = []
        rejected_temp_list = []
        for i, ans in enumerate(answers):
            if i != choice_idx and ans is not None:
                rejected_ans_list.append(ans)
                rejected_temp_list.append(temperatures[i])

        # 调用 DB
        self.db.save_dpo_record(
            session_id, prompt, chosen_ans, rejected_ans_list, chosen_temp, rejected_temp_list, context_text
        )

    def export_session_to_text(self, session_id):
        msgs = self.get_session_history(session_id)
        output = io.StringIO()
        for msg in msgs:
            role = "AI" if (msg.get("type") == "ai" or msg.get("role") == "assistant") else "User"
            content = msg.get("data", {}).get("content") or msg.get("content", "")
            output.write(f"[{role}]:\n{content}\n\n{'-' * 20}\n\n")
        return output.getvalue().encode('utf-8')

    def generate_candidate_stream(self, prompt, session_id, temperature, selected_model):
        # 1. 准备历史数据 (Controller 负责从 DB 拿数据并转成对象)
        history_dicts = self.db.get_messages(self.TABLE_NAME, session_id)
        history_objs = []
        for msg in history_dicts:
            role = msg.get("type") or msg.get("role")
            content = msg.get("data", {}).get("content") or msg.get("content", "")
            if role in ["human", "user"]:
                history_objs.append(HumanMessage(content=content))
            elif role in ["ai", "assistant"]:
                history_objs.append(AIMessage(content=content))

        # 2. 场景 B：调用手动挡接口，传入明确的温度和整理好的历史
        return self.rag.stream_rlhf_response(
            model_name=selected_model,
            prompt=prompt,
            history_list=history_objs,
            temperature=temperature
        )

    def retrieve_context_text(self, prompt):
        return self.rag.get_retrieved_context(prompt)