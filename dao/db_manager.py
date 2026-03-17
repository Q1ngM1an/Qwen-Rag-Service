import sqlite3
import json
import os

def get_db_manager():
    """
    全局单例模式获取 DBManager。
    注意：DBManager 内部必须不能持有 self.conn 这种永久连接，
    必须在每次方法调用时 with sqlite3.connect(...)。
    """
    return DBManager(db_path="./chat_data.db")

class DBManager:
    def __init__(self, db_path="./chat_data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL;')
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # 1. QA 专用历史表 (原 chat_history 改名或废弃，这里新建以示区分)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qa_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. RLHF 专用会话表 (用于在 RLHF 页面回显多轮对话)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rlhf_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 3. DPO/RLHF 偏好数据集 (核心资产)
            # 存储：提示词、被选中的答案、被拒绝的答案(JSON list)、对应的温度参数
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dpo_dataset (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    prompt TEXT,
                    chosen_answer TEXT,
                    rejected_answers TEXT, -- JSON List string
                    chosen_temp REAL,
                    rejected_temps TEXT,   -- JSON List string
                    context_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    # --- 通用方法：支持传入 table_name ---
    def add_message(self, table_name: str, session_id: str, message_dict: dict):
        """向指定表写入消息"""
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        json_str = json.dumps(message_dict, ensure_ascii=False)
        with self._get_conn() as conn:
            conn.execute(
                f"INSERT INTO {table_name} (session_id, message_data) VALUES (?, ?)",
                (session_id, json_str)
            )

    def get_messages(self, table_name: str, session_id: str) -> list[dict]:
        """从指定表读取消息"""
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT message_data FROM {table_name} WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows] if rows else []

    def clear_session(self, table_name: str, session_id: str):
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            conn.execute(f"DELETE FROM {table_name} WHERE session_id = ?", (session_id,))

    def get_all_sessions(self, table_name: str):
        """获取所有会话的摘要信息（按时间倒序）"""
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT session_id, MIN(created_at) as time, message_data 
                FROM {table_name} 
                GROUP BY session_id 
                ORDER BY id DESC
            ''')
            return cursor.fetchall()

    # RLHF专属方法
    def save_dpo_record(self, session_id, prompt, chosen, rejected_list, chosen_temp, rejected_temp_list, context_text):
        """保存一条高质量的训练数据"""
        with self._get_conn() as conn:
            conn.execute(
                '''INSERT INTO dpo_dataset 
                   (session_id, prompt, chosen_answer, rejected_answers, chosen_temp, rejected_temps, context_text) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (session_id, prompt, chosen, json.dumps(rejected_list), chosen_temp, json.dumps(rejected_temp_list), context_text)
            )

    # QA专属方法
    def delete_last_message(self, table_name, session_id):
        """删除会话中最新的一条消息 (不分角色)"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {table_name} WHERE session_id = ? ORDER BY id DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            if row:
                conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (row[0],))
