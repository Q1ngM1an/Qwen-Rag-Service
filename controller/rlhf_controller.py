from langchain_core.messages import HumanMessage, AIMessage

from controller.base_chat_controller import BaseChatController

class RLHFCollectController(BaseChatController):
    """RLHF 业务逻辑 """

    TABLE_NAME = "rlhf_history"

    def create_session(self):
        return self.create_session_stub("新建偏好会话")

    def get_sidebar_sessions(self):
        return self.get_session_list(self.TABLE_NAME)

    def get_session_history(self, session_id):
        return self.serialize_history(session_id, self.db.get_messages(self.TABLE_NAME, session_id))

    def delete_session(self, session_id):
        return self.db.clear_session(self.TABLE_NAME, session_id)

    def commit_interaction(self, session_id, prompt, answers, choice_idx):
        winner_answer = answers[choice_idx]

        user_msg = {"type": "human", "data": {"content": prompt}}
        self.db.add_message(self.TABLE_NAME, session_id, user_msg)

        ai_msg = {"type": "ai", "data": {"content": winner_answer}}
        self.db.add_message(self.TABLE_NAME, session_id, ai_msg)

        return True

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

        self.db.save_dpo_record(
            session_id, prompt, chosen_ans, rejected_ans_list, chosen_temp, rejected_temp_list, context_text
        )

        return True

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

        # 2. 在数据搜集场景下，调用手动挡接口，传入明确的温度和整理好的历史
        return self.rag.stream_rlhf_response(
            model_name=selected_model,
            prompt=prompt,
            history_list=history_objs,
            temperature=temperature
        )

    # def retrieve_context_text(self, prompt):
    #     return self.rag.get_retrieved_context(prompt)

