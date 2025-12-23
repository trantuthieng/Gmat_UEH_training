import os
import json
import hashlib
import sqlite3
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import streamlit as st

# Biến global để track database type
_db_type: Optional[str] = None
_db_path = "gmat.db"

# Try to import psycopg2, but don't fail if not available
try:
    import psycopg2
    from psycopg2 import pool, extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# --- CẤU HÌNH KẾT NỐI DATABASE ---
def _get_db_type():
    """Xác định loại database đang sử dụng"""
    global _db_type
    if _db_type is not None:
        return _db_type
    
    # Helper để lấy biến từ os.environ hoặc st.secrets
    def get_config(key):
        return os.getenv(key) or st.secrets.get(key)
    
    # Kiểm tra nếu có DB_HOST và psycopg2 available
    if PSYCOPG2_AVAILABLE and get_config("DB_HOST"):
        try:
            # Test connection
            conn = psycopg2.connect(
                host=get_config("DB_HOST"),
                database=get_config("DB_NAME"),
                user=get_config("DB_USER"),
                password=get_config("DB_PASSWORD"),
                port=get_config("DB_PORT")
            )
            conn.close()
            _db_type = "postgresql"
            return _db_type
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed: {e}")
            print("📁 Fallback to SQLite for local development")
    
    _db_type = "sqlite"
    return _db_type

def get_db_connection():
    """Lấy kết nối database (PostgreSQL hoặc SQLite)"""
    # Helper để lấy biến từ os.environ (Azure) hoặc st.secrets (Streamlit Cloud)
    def get_config(key):
        return os.getenv(key) or st.secrets.get(key)
    
    db_type = _get_db_type()
    
    if db_type == "postgresql":
        try:
            return psycopg2.connect(
                host=get_config("DB_HOST"),
                database=get_config("DB_NAME"),
                user=get_config("DB_USER"),
                password=get_config("DB_PASSWORD"),
                port=get_config("DB_PORT")
            )
        except Exception as e:
            print(f"❌ DB Connection Error: {e}")
            raise e
    else:
        # SQLite fallback
        return sqlite3.connect(_db_path, check_same_thread=False)

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
    """Khởi tạo bảng database (PostgreSQL hoặc SQLite)"""
    db_type = _get_db_type()
    
    with get_conn() as conn:
        c = conn.cursor()
        if db_type == "postgresql":
            # PostgreSQL dùng SERIAL cho auto-increment
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
            c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON questions(created_at DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_qtype ON questions(qtype);")
        else:
            # SQLite
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON questions(created_at DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_qtype ON questions(qtype);")
        conn.commit()

def _hash_question(q: Dict[str, Any]) -> str:
    base = (q.get('question','') + '|' + q.get('correct_answer','')).strip().lower()
    return hashlib.sha256(base.encode('utf-8')).hexdigest()

def save_questions(questions: List[Dict[str, Any]]) -> int:
    if not questions:
        return 0
    
    db_type = _get_db_type()
    saved = 0
    
    with get_conn() as conn:
        c = conn.cursor()
        for q in questions:
            qhash = _hash_question(q)
            options_json = json.dumps(q.get('options', []), ensure_ascii=False)
            
            if db_type == "postgresql":
                # PostgreSQL: dùng %s và ON CONFLICT
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
                # psycopg2: kiểm tra rowcount để xác định insert thành công
                if c.rowcount > 0:
                    saved += 1
            else:
                # SQLite: dùng ? và INSERT OR IGNORE
                c.execute(
                    """
                    INSERT OR IGNORE INTO questions (qhash, question, options, correct_answer, explanation, image_url, topic, qtype)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                if c.rowcount > 0:
                    saved += 1
        conn.commit()
    return saved

def get_cached_questions(limit: int = 30, randomize: bool = True) -> List[Dict[str, Any]]:
    db_type = _get_db_type()
    
    with get_conn() as conn:
        if db_type == "postgresql":
            # PostgreSQL: dùng RealDictCursor
            c = conn.cursor(cursor_factory=extras.RealDictCursor)
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
        else:
            # SQLite: dùng Row factory
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
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
                opts = json.loads(row['options']) if row['options'] else []
            except (json.JSONDecodeError, TypeError):
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
