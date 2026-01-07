#!/usr/bin/env python3
"""Xóa bảng user_wrong_answers từ Supabase"""
import psycopg2
import sys
from dotenv import load_dotenv
import os

load_dotenv()

# Thông tin kết nối - từ .env
db_host = os.getenv("DB_HOST", "db.gtlojusiykbjvuzsrgdi.supabase.co")
db_name = os.getenv("DB_NAME", "postgres")
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD")
db_port = os.getenv("DB_PORT", "5432")

try:
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )
    
    cursor = conn.cursor()
    
    # Lấy số lượng records
    cursor.execute("SELECT COUNT(*) FROM user_wrong_answers;")
    count = cursor.fetchone()[0]
    
    print(f"📊 Tổng user_wrong_answers: {count}")
    
    if count > 0:
        print(f"🗑️  Đang xóa...")
        cursor.execute("DELETE FROM user_wrong_answers;")
        conn.commit()
        print(f"✅ Xóa thành công! Đã xóa {count} records")
    else:
        print("✅ Bảng đã trống!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    sys.exit(1)
