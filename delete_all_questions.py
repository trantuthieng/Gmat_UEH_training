#!/usr/bin/env python3
"""
Script xóa toàn bộ câu hỏi từ Supabase (PostgreSQL)
Sử dụng: python delete_all_questions.py
"""

import os
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

def delete_all_questions():
    """Xóa toàn bộ câu hỏi từ database"""
    
    # Lấy thông tin kết nối từ .env hoặc nhập manual
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")
    
    # Nếu thiếu, nhập manual
    if not db_host:
        db_host = input("DB_HOST (e.g., db.xxx.supabase.co): ").strip()
    if not db_name:
        db_name = input("DB_NAME (e.g., postgres): ").strip()
    if not db_user:
        db_user = input("DB_USER (e.g., postgres): ").strip()
    if not db_password:
        db_password = input("DB_PASSWORD: ").strip()
    
    # Kiểm tra các biến env
    if not all([db_host, db_name, db_user, db_password]):
        print("❌ Lỗi: Thiếu thông tin kết nối")
        sys.exit(1)
    
    try:
        print(f"🔗 Kết nối tới database: {db_user}@{db_host}:{db_port}/{db_name}")
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        
        cursor = conn.cursor()
        
        # Lấy số lượng câu hỏi hiện tại
        cursor.execute("SELECT COUNT(*) FROM questions;")
        count = cursor.fetchone()[0]
        
        print(f"📊 Tổng câu hỏi hiện tại: {count}")
        
        if count == 0:
            print("✅ Database đã trống!")
            cursor.close()
            conn.close()
            return
        
        # Xác nhận trước khi xóa
        confirm = input(f"\n⚠️  Bạn sắp XÓA tất cả {count} câu hỏi. Tiếp tục? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Hủy bỏ.")
            cursor.close()
            conn.close()
            return
        
        # Xóa toàn bộ câu hỏi
        print("\n🗑️  Đang xóa tất cả câu hỏi...")
        cursor.execute("DELETE FROM questions;")
        conn.commit()
        
        # Xóa toàn bộ user_wrong_answers
        cursor.execute("SELECT COUNT(*) FROM user_wrong_answers;")
        wrong_count = cursor.fetchone()[0]
        
        if wrong_count > 0:
            print(f"🗑️  Đang xóa {wrong_count} user_wrong_answers...")
            cursor.execute("DELETE FROM user_wrong_answers;")
            conn.commit()
            print(f"📝 Đã xóa: {wrong_count} user_wrong_answers")
        
        # Kiểm tra lại
        cursor.execute("SELECT COUNT(*) FROM questions;")
        new_count = cursor.fetchone()[0]
        
        print(f"\n✅ Xóa thành công!")
        print(f"📝 Câu hỏi: Đã xóa {count}, còn lại {new_count}")
        if wrong_count > 0:
            print(f"📝 User errors: Đã xóa {wrong_count}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Lỗi Database: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    delete_all_questions()
