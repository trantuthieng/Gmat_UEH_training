import os
import json
import hashlib
import psycopg2
from psycopg2 import pool, extras
from typing import List, Dict, Any
from contextlib import contextmanager
import streamlit as st

# --- CẤU HÌNH KẾT NỐI SUPABASE ---
# Lấy thông tin từ Streamlit Secrets (sẽ cấu hình ở bước 4)
def get_db_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"]
        )
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        raise e

@contextmanager
def get_conn():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Khởi tạo bảng trên PostgreSQL (Supabase)"""
    with get_conn() as conn:
        with conn.cursor() as c:
            # PostgreSQL dùng SERIAL cho auto-increment thay vì AUTOINCREMENT
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id SERIAL PRIMARY KEY,
                    qhash TEXT UNIQUE,
                    question TEXT NOT NULL,
                    options TEXT,
                    correct_answer TEXT,
                    explanation TEXT,
                    image_url TEXT,
                    topic TEXT,
                    qtype TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            # Tạo index (Postgres tự tạo index cho Primary Key và Unique)
            c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON questions(created_at DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_qtype ON questions(qtype);")
            conn.commit()

def _hash_question(q: Dict[str, Any]) -> str:
    base = (q.get('question','') + '|' + q.get('correct_answer','')).strip().lower()
    return hashlib.sha256(base.encode('utf-8')).hexdigest()

def save_questions(questions: List[Dict[str, Any]]) -> int:
    if not questions:
        return 0
    
    saved = 0
    with get_conn() as conn:
        with conn.cursor() as c:
            for q in questions:
                qhash = _hash_question(q)
                options_json = json.dumps(q.get('options', []), ensure_ascii=False)
                
                # Postgres dùng cú pháp %s thay vì ?
                # Dùng ON CONFLICT DO NOTHING thay cho INSERT OR IGNORE
                c.execute(
                    """
                    INSERT INTO questions (qhash, question, options, correct_answer, explanation, image_url, topic, qtype)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (qhash) DO NOTHING
                    """,
                    (
                        qhash,
                        q.get('question', ''),
                        options_json,
                        q.get('correct_answer'),
                        q.get('explanation'),
                        q.get('image_url'),
                        q.get('topic'),
                        q.get('type')
                    )
                )
                # Rowcount trong ON CONFLICT hơi khác, nhưng ta tạm tính đơn giản
                if c.statusmessage.startswith("INSERT"):
                     saved += 1
            conn.commit()
    return saved

def get_cached_questions(limit: int = 30, randomize: bool = True) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        # Sử dụng RealDictCursor để lấy kết quả dạng Dictionary giống SQLite Row
        with conn.cursor(cursor_factory=extras.RealDictCursor) as c:
            order_by = "RANDOM()" if randomize else "created_at DESC"
            
            c.execute(
                f"""
                SELECT question, options, correct_answer, explanation, image_url, topic, qtype
                FROM questions
                ORDER BY {order_by}
                LIMIT %s
                """,
                (limit,)
            )
            rows = c.fetchall()
            
            result: List[Dict[str, Any]] = []
            for row in rows:
                opts = []
                try:
                    # Postgres trả về string, cần parse JSON
                    opts = json.loads(row['options']) if row['options'] else []
                except json.JSONDecodeError:
                    opts = []
                
                result.append({
                    'type': row['qtype'] or 'general',
                    'question': row['question'],
                    'options': opts,
                    'correct_answer': row['correct_answer'],
                    'explanation': row['explanation'],
                    'image_url': row['image_url'],
                    'topic': row['topic']
                })
            return result