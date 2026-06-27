import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class FeedbackStore:
    def __init__(self, db_path: str = "nova_feedback.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        session_id TEXT,
                        turn_index INTEGER,
                        user_text TEXT,
                        assistant_text TEXT,
                        tools_called_json TEXT,
                        action_taken INTEGER,
                        success INTEGER,
                        error_text TEXT,
                        latency_ms INTEGER
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        interaction_id INTEGER,
                        session_id TEXT,
                        rating INTEGER,
                        notes TEXT,
                        FOREIGN KEY(interaction_id) REFERENCES interactions(id)
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def log_interaction(
        self,
        session_id: str,
        turn_index: int,
        user_text: str,
        assistant_text: str,
        tools_called: Optional[List[str]] = None,
        action_taken: bool = False,
        success: bool = True,
        error_text: Optional[str] = None,
        latency_ms: int = 0,
    ) -> int:
        now = datetime.utcnow().isoformat()
        tools_json = json.dumps(tools_called or [])

        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """
                    INSERT INTO interactions (
                        timestamp, session_id, turn_index, user_text, assistant_text,
                        tools_called_json, action_taken, success, error_text, latency_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now,
                        session_id,
                        turn_index,
                        user_text,
                        assistant_text,
                        tools_json,
                        int(action_taken),
                        int(success),
                        error_text,
                        latency_ms,
                    ),
                )
                conn.commit()
                return int(cur.lastrowid)
            finally:
                conn.close()

    def log_feedback(
        self,
        session_id: str,
        rating: int,
        notes: Optional[str] = None,
        interaction_id: Optional[int] = None,
    ) -> int:
        now = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """
                    INSERT INTO feedback (timestamp, interaction_id, session_id, rating, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (now, interaction_id, session_id, rating, notes),
                )
                conn.commit()
                return int(cur.lastrowid)
            finally:
                conn.close()

    def mark_interaction_feedback(self, interaction_id: int, rating: int, notes: Optional[str] = None) -> int:
        now = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT session_id FROM interactions WHERE id = ?",
                    (interaction_id,),
                ).fetchone()
                session_id = row["session_id"] if row else ""
                cur = conn.execute(
                    """
                    INSERT INTO feedback (timestamp, interaction_id, session_id, rating, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (now, interaction_id, session_id, rating, notes),
                )
                conn.commit()
                return int(cur.lastrowid)
            finally:
                conn.close()

    def get_skill_success_stats(self, window_days: int = 30) -> Dict[str, Dict[str, float]]:
        since = (datetime.utcnow() - timedelta(days=window_days)).isoformat()
        stats: Dict[str, Dict[str, float]] = {}

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT tools_called_json, success
                    FROM interactions
                    WHERE timestamp >= ?
                    """,
                    (since,),
                ).fetchall()
            finally:
                conn.close()

        for row in rows:
            tools = json.loads(row["tools_called_json"] or "[]")
            success = int(row["success"])
            for tool in tools:
                if tool not in stats:
                    stats[tool] = {"total": 0.0, "success": 0.0, "success_rate": 0.0}
                stats[tool]["total"] += 1
                stats[tool]["success"] += success

        for tool, values in stats.items():
            total = values["total"]
            values["success_rate"] = (values["success"] / total) if total else 0.0

        return stats

    def get_recent_interactions(self, session_id: str, limit: int = 12) -> List[Dict[str, str]]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT user_text, assistant_text
                    FROM interactions
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, limit),
                ).fetchall()
            finally:
                conn.close()

        # Oldest first for chronological replay.
        ordered = list(reversed(rows))
        return [
            {
                "user_text": r["user_text"] or "",
                "assistant_text": r["assistant_text"] or "",
            }
            for r in ordered
        ]
