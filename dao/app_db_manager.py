import json
import sqlite3
from functools import lru_cache
from typing import Any

import configs.config as config


@lru_cache(maxsize=1)
def get_db_manager():
    return DBManager(config.db_path)


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        config.ensure_runtime_directories()
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except sqlite3.OperationalError:
            conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rlhf_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dpo_dataset (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    prompt TEXT,
                    chosen_answer TEXT,
                    rejected_answers TEXT,
                    chosen_temp REAL,
                    rejected_temps TEXT,
                    context_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    original_name TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    content_type TEXT,
                    checksum TEXT NOT NULL UNIQUE,
                    text_length INTEGER NOT NULL DEFAULT 0,
                    byte_size INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'ready',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base_files (
                    knowledge_base_id TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (knowledge_base_id, file_id),
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base_group_members (
                    group_id TEXT NOT NULL,
                    knowledge_base_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, knowledge_base_id),
                    FOREIGN KEY (group_id) REFERENCES knowledge_base_groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS session_knowledge_base_groups (
                    session_type TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_type, session_id, group_id),
                    FOREIGN KEY (group_id) REFERENCES knowledge_base_groups(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_qa_history_session_id ON qa_history(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_rlhf_history_session_id ON rlhf_history(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_checksum ON files(checksum)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_files_file_id ON knowledge_base_files(file_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_group_members_kb_id ON knowledge_base_group_members(knowledge_base_id)"
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_session_scope_lookup
                ON session_knowledge_base_groups(session_type, session_id)
                """
            )
            conn.commit()

    def _rows_to_dicts(self, rows):
        return [dict(row) for row in rows]

    # Chat history
    def add_message(self, table_name: str, session_id: str, message_dict: dict):
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            conn.execute(
                f"INSERT INTO {table_name} (session_id, message_data) VALUES (?, ?)",
                (session_id, json.dumps(message_dict, ensure_ascii=False)),
            )

    def get_messages(self, table_name: str, session_id: str) -> list[dict]:
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT message_data FROM {table_name} WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        return [json.loads(row["message_data"]) for row in rows]

    def clear_session(self, table_name: str, session_id: str):
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            conn.execute(f"DELETE FROM {table_name} WHERE session_id = ?", (session_id,))

    def get_all_sessions(self, table_name: str):
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT session_id,
                       MIN(created_at) AS time,
                       (
                           SELECT message_data
                           FROM {table_name} AS detail
                           WHERE detail.session_id = summary.session_id
                           ORDER BY detail.id ASC
                           LIMIT 1
                       ) AS message_data
                FROM {table_name} AS summary
                GROUP BY session_id
                ORDER BY MAX(id) DESC
                """
            ).fetchall()
        return [(row["session_id"], row["time"], row["message_data"]) for row in rows]

    def save_dpo_record(
        self,
        session_id: str,
        prompt: str,
        chosen: str,
        rejected_list: list[str],
        chosen_temp: float,
        rejected_temp_list: list[float],
        context_text: str,
    ):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO dpo_dataset
                (session_id, prompt, chosen_answer, rejected_answers, chosen_temp, rejected_temps, context_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    prompt,
                    chosen,
                    json.dumps(rejected_list, ensure_ascii=False),
                    chosen_temp,
                    json.dumps(rejected_temp_list, ensure_ascii=False),
                    context_text,
                ),
            )

    def delete_last_message(self, table_name: str, session_id: str):
        if table_name not in ["qa_history", "rlhf_history"]:
            raise ValueError("Invalid table name")

        with self._get_conn() as conn:
            row = conn.execute(
                f"SELECT id FROM {table_name} WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            if row:
                conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (row["id"],))

    # File metadata
    def create_file(
        self,
        *,
        file_id: str,
        original_name: str,
        storage_path: str,
        content_type: str | None,
        checksum: str,
        text_length: int,
        byte_size: int,
        status: str = "ready",
    ):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO files
                (id, original_name, storage_path, content_type, checksum, text_length, byte_size, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    original_name,
                    storage_path,
                    content_type,
                    checksum,
                    text_length,
                    byte_size,
                    status,
                ),
            )

    def get_file_by_checksum(self, checksum: str):
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT f.*, COUNT(kbf.knowledge_base_id) AS reference_count
                FROM files AS f
                LEFT JOIN knowledge_base_files AS kbf ON kbf.file_id = f.id
                WHERE f.checksum = ?
                GROUP BY f.id
                """,
                (checksum,),
            ).fetchone()
        return dict(row) if row else None

    def get_file(self, file_id: str):
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT f.*, COUNT(kbf.knowledge_base_id) AS reference_count
                FROM files AS f
                LEFT JOIN knowledge_base_files AS kbf ON kbf.file_id = f.id
                WHERE f.id = ?
                GROUP BY f.id
                """,
                (file_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_files(self, search: str | None = None):
        search_term = f"%{search.strip()}%" if search else "%"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT f.*, COUNT(kbf.knowledge_base_id) AS reference_count
                FROM files AS f
                LEFT JOIN knowledge_base_files AS kbf ON kbf.file_id = f.id
                WHERE f.original_name LIKE ?
                GROUP BY f.id
                ORDER BY f.created_at DESC
                """,
                (search_term,),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def get_files_by_ids(self, file_ids: list[str]):
        if not file_ids:
            return []

        placeholders = ",".join("?" for _ in file_ids)
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM files WHERE id IN ({placeholders})",
                tuple(file_ids),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def list_file_knowledge_bases(self, file_id: str):
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT kb.*
                FROM knowledge_bases AS kb
                INNER JOIN knowledge_base_files AS kbf ON kbf.knowledge_base_id = kb.id
                WHERE kbf.file_id = ?
                ORDER BY kb.created_at DESC
                """,
                (file_id,),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def delete_file_record(self, file_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))

    # Knowledge bases
    def create_knowledge_base(self, kb_id: str, name: str, description: str | None, owner_id: str | None):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_bases (id, name, description, owner_id)
                VALUES (?, ?, ?, ?)
                """,
                (kb_id, name, description, owner_id),
            )

    def list_knowledge_bases(self, search: str | None = None):
        search_term = f"%{search.strip()}%" if search else "%"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT kb.*,
                       COUNT(DISTINCT kbf.file_id) AS file_count,
                       COUNT(DISTINCT gm.group_id) AS group_count
                FROM knowledge_bases AS kb
                LEFT JOIN knowledge_base_files AS kbf ON kbf.knowledge_base_id = kb.id
                LEFT JOIN knowledge_base_group_members AS gm ON gm.knowledge_base_id = kb.id
                WHERE kb.name LIKE ?
                GROUP BY kb.id
                ORDER BY kb.created_at DESC
                """,
                (search_term,),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def get_knowledge_base(self, kb_id: str):
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT kb.*,
                       COUNT(DISTINCT kbf.file_id) AS file_count,
                       COUNT(DISTINCT gm.group_id) AS group_count
                FROM knowledge_bases AS kb
                LEFT JOIN knowledge_base_files AS kbf ON kbf.knowledge_base_id = kb.id
                LEFT JOIN knowledge_base_group_members AS gm ON gm.knowledge_base_id = kb.id
                WHERE kb.id = ?
                GROUP BY kb.id
                """,
                (kb_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_knowledge_bases_by_ids(self, kb_ids: list[str]):
        if not kb_ids:
            return []

        placeholders = ",".join("?" for _ in kb_ids)
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM knowledge_bases WHERE id IN ({placeholders})",
                tuple(kb_ids),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def update_knowledge_base(self, kb_id: str, fields: dict[str, Any]):
        if not fields:
            return

        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [kb_id]
        with self._get_conn() as conn:
            conn.execute(
                f"""
                UPDATE knowledge_bases
                SET {assignments}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                values,
            )

    def delete_knowledge_base(self, kb_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))

    def attach_files_to_knowledge_base(self, kb_id: str, file_ids: list[str]):
        if not file_ids:
            return

        with self._get_conn() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO knowledge_base_files (knowledge_base_id, file_id)
                VALUES (?, ?)
                """,
                [(kb_id, file_id) for file_id in file_ids],
            )

    def detach_file_from_knowledge_base(self, kb_id: str, file_id: str):
        with self._get_conn() as conn:
            conn.execute(
                """
                DELETE FROM knowledge_base_files
                WHERE knowledge_base_id = ? AND file_id = ?
                """,
                (kb_id, file_id),
            )

    def list_knowledge_base_files(self, kb_id: str, search: str | None = None):
        search_term = f"%{search.strip()}%" if search else "%"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT f.*, 1 AS reference_count
                FROM files AS f
                INNER JOIN knowledge_base_files AS kbf ON kbf.file_id = f.id
                WHERE kbf.knowledge_base_id = ? AND f.original_name LIKE ?
                ORDER BY kbf.created_at DESC
                """,
                (kb_id, search_term),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def is_file_attached_to_knowledge_base(self, kb_id: str, file_id: str):
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM knowledge_base_files
                WHERE knowledge_base_id = ? AND file_id = ?
                LIMIT 1
                """,
                (kb_id, file_id),
            ).fetchone()
        return row is not None

    # Knowledge base groups
    def create_knowledge_base_group(
        self,
        group_id: str,
        name: str,
        description: str | None,
        owner_id: str | None,
    ):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_base_groups (id, name, description, owner_id)
                VALUES (?, ?, ?, ?)
                """,
                (group_id, name, description, owner_id),
            )

    def list_knowledge_base_groups(self, search: str | None = None):
        search_term = f"%{search.strip()}%" if search else "%"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT g.*,
                       COUNT(DISTINCT gm.knowledge_base_id) AS knowledge_base_count
                FROM knowledge_base_groups AS g
                LEFT JOIN knowledge_base_group_members AS gm ON gm.group_id = g.id
                WHERE g.name LIKE ?
                GROUP BY g.id
                ORDER BY g.created_at DESC
                """,
                (search_term,),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def get_knowledge_base_group(self, group_id: str):
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT g.*,
                       COUNT(DISTINCT gm.knowledge_base_id) AS knowledge_base_count
                FROM knowledge_base_groups AS g
                LEFT JOIN knowledge_base_group_members AS gm ON gm.group_id = g.id
                WHERE g.id = ?
                GROUP BY g.id
                """,
                (group_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_knowledge_base_groups_by_ids(self, group_ids: list[str]):
        if not group_ids:
            return []

        placeholders = ",".join("?" for _ in group_ids)
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM knowledge_base_groups WHERE id IN ({placeholders})",
                tuple(group_ids),
            ).fetchall()
        return self._rows_to_dicts(rows)

    def update_knowledge_base_group(self, group_id: str, fields: dict[str, Any]):
        if not fields:
            return

        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [group_id]
        with self._get_conn() as conn:
            conn.execute(
                f"""
                UPDATE knowledge_base_groups
                SET {assignments}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                values,
            )

    def delete_knowledge_base_group(self, group_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM knowledge_base_groups WHERE id = ?", (group_id,))

    def replace_group_members(self, group_id: str, knowledge_base_ids: list[str]):
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM knowledge_base_group_members WHERE group_id = ?",
                (group_id,),
            )
            conn.executemany(
                """
                INSERT INTO knowledge_base_group_members (group_id, knowledge_base_id)
                VALUES (?, ?)
                """,
                [(group_id, kb_id) for kb_id in knowledge_base_ids],
            )

    def list_group_knowledge_bases(self, group_id: str):
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT kb.*,
                       COUNT(DISTINCT kbf.file_id) AS file_count
                FROM knowledge_bases AS kb
                INNER JOIN knowledge_base_group_members AS gm ON gm.knowledge_base_id = kb.id
                LEFT JOIN knowledge_base_files AS kbf ON kbf.knowledge_base_id = kb.id
                WHERE gm.group_id = ?
                GROUP BY kb.id
                ORDER BY kb.created_at DESC
                """,
                (group_id,),
            ).fetchall()
        return self._rows_to_dicts(rows)

    # Session scope
    def replace_session_knowledge_base_groups(
        self,
        session_type: str,
        session_id: str,
        group_ids: list[str],
    ):
        with self._get_conn() as conn:
            conn.execute(
                """
                DELETE FROM session_knowledge_base_groups
                WHERE session_type = ? AND session_id = ?
                """,
                (session_type, session_id),
            )
            conn.executemany(
                """
                INSERT INTO session_knowledge_base_groups (session_type, session_id, group_id)
                VALUES (?, ?, ?)
                """,
                [(session_type, session_id, group_id) for group_id in group_ids],
            )

    def list_session_knowledge_base_groups(self, session_type: str, session_id: str):
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT g.*
                FROM knowledge_base_groups AS g
                INNER JOIN session_knowledge_base_groups AS s
                    ON s.group_id = g.id
                WHERE s.session_type = ? AND s.session_id = ?
                ORDER BY g.created_at DESC
                """,
                (session_type, session_id),
            ).fetchall()
        return self._rows_to_dicts(rows)
