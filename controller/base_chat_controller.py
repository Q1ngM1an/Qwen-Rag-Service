import json
import io

class BaseChatController:

    def __init__(self, db_manager, rag_service):
        self.db = db_manager
        self.rag = rag_service

    def get_session_list(self, table_name):
        """获取侧边栏会话列表"""
        try:
            rows = self.db.get_all_sessions(table_name)
            sessions = []
            for r in rows:
                sid, time_str, msg_json = r
                try:
                    msg_data = json.loads(msg_json)
                    content = msg_data.get("data", {}).get("content", "新对话")
                    title = content[:20] + "..." if len(content) > 20 else content
                except:
                    title = "未命名对话"
                sessions.append({"id": sid, "title": title, "time": time_str})
            return sessions
        except Exception as e:
            # 实际项目中这里可以使用 logging
            print(f"读取历史失败: {e}")
            return []

    def get_sidebar_sessions(self):
        raise NotImplementedError()

    def create_new_session(self):
        raise NotImplementedError()

    def delete_session(self, session_id):
        raise NotImplementedError()

    def get_session_history(self, session_id):
        raise NotImplementedError()

    def export_session_to_text(self, session_id):
        msgs = self.get_session_history(session_id)
        output = io.StringIO()
        for msg in msgs:
            role = "AI" if (msg.get("type") == "ai" or msg.get("role") == "assistant") else "User"
            content = msg.get("data", {}).get("content") or msg.get("content", "")
            output.write(f"[{role}]:\n{content}\n\n{'-' * 20}\n\n")
        return output.getvalue().encode('utf-8')