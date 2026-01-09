#!/usr/bin/env python3
"""Test different SSL modes with Supabase"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("=" * 80)
print("🔍 TESTING SSL MODES")
print("=" * 80)

ssl_modes = ['disable', 'allow', 'prefer', 'require']

for mode in ssl_modes:
    print(f"\n🔧 Testing sslmode={mode}...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            sslmode=mode
        )
        conn.close()
        print(f"   ✅ SUCCESS with sslmode={mode}")
        break
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")

print("\n" + "=" * 80)
