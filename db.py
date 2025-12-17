import os
import sqlite3
import json
import hashlib
from typing import List, Dict, Any
from contextlib import contextmanager
import threading

# Use Render persistent disk if available, otherwise local
if os.path.exists('/data'):
    DB_PATH = '/data/gmat.db'
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'gmat.db')

# Connection pool for better performance
_local = threading.local()

@contextmanager
def get_conn():
    """Context manager for database connections with connection reuse"""
    if not hasattr(_local, 'conn') or _local.conn is None:
        try:
            _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5.0)
            _local.conn.row_factory = sqlite3.Row
        except sqlite3.OperationalError as e:
            print(f"⚠️ DB connection error: {e}. Path: {DB_PATH}")
            raise
    try:
        yield _local.conn
    except Exception:
        _local.conn.rollback()
        raise

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qhash TEXT UNIQUE,
                question TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                image_url TEXT,
                topic TEXT,
                qtype TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Add indexes for better query performance
        c.execute("CREATE INDEX IF NOT EXISTS idx_qhash ON questions(qhash)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON questions(created_at DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_qtype ON questions(qtype)")
        conn.commit()

def _hash_question(q: Dict[str, Any]) -> str:
    base = (q.get('question','') + '|' + q.get('correct_answer','')).strip().lower()
    return hashlib.sha256(base.encode('utf-8')).hexdigest()

def save_questions(questions: List[Dict[str, Any]]) -> int:
    if not questions:
        return 0
    with get_conn() as conn:
        saved = 0
        c = conn.cursor()
        # Batch insert for better performance
        batch_data = []
        for q in questions:
            qhash = _hash_question(q)
            options_json = json.dumps(q.get('options', []), ensure_ascii=False)
            batch_data.append((
                qhash,
                q.get('question', ''),
                options_json,
                q.get('correct_answer'),
                q.get('explanation'),
                q.get('image_url'),
                q.get('topic'),
                q.get('type')
            ))
        
        # Use executemany with INSERT OR IGNORE for better performance
        c.executemany(
            """
            INSERT OR IGNORE INTO questions (qhash, question, options, correct_answer, explanation, image_url, topic, qtype)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch_data
        )
        saved = c.rowcount
        conn.commit()
        return saved

def get_cached_questions(limit: int = 30, randomize: bool = True) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        # Use RANDOM() for better variety in cached questions
        order_by = "RANDOM()" if randomize else "created_at DESC"
        c.execute(
            f"""
            SELECT question, options, correct_answer, explanation, image_url, topic, qtype
            FROM questions
            ORDER BY {order_by}
            LIMIT ?
            """,
            (limit,)
        )
        rows = c.fetchall()
        result: List[Dict[str, Any]] = []
        for row in rows:
            opts = []
            try:
                opts = json.loads(row[1]) if row[1] else []
            except json.JSONDecodeError:
                opts = []
            result.append({
                'type': row[6] or 'general',
                'question': row[0],
                'options': opts,
                'correct_answer': row[2],
                'explanation': row[3],
                'image_url': row[4],
                'topic': row[5]
            })
        return result
