import psycopg2
import streamlit as st

# Test connection to Supabase Pooler
def test_connection():
    try:
        print("🔄 Testing connection to Supabase Pooler...")
        
        # Load secrets
        host = st.secrets["DB_HOST"]
        database = st.secrets["DB_NAME"]
        user = st.secrets["DB_USER"]
        password = st.secrets["DB_PASSWORD"]
        port = st.secrets["DB_PORT"]
        
        print(f"📡 Connecting to: {host}:{port}")
        print(f"👤 User: {user}")
        print(f"🗄️  Database: {database}")
        
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        
        print("✅ Connection successful!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 PostgreSQL version: {version[0]}")
        
        # Check if questions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'questions'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM questions;")
            count = cursor.fetchone()[0]
            print(f"📦 Questions table exists with {count} records")
        else:
            print("⚠️  Questions table does not exist yet")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
