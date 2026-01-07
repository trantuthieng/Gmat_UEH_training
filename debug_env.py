#!/usr/bin/env python3
"""Debug environment variables loading"""

import os
from dotenv import load_dotenv

print("=" * 80)
print("🔍 DEBUG: Environment Variables Loading")
print("=" * 80)

# Before load_dotenv
print("\n1️⃣ BEFORE load_dotenv():")
print(f"   DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT SET')}")
print(f"   DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")

# Load dotenv
print("\n2️⃣ Calling load_dotenv()...")
result = load_dotenv()
print(f"   Result: {result}")

# After load_dotenv
print("\n3️⃣ AFTER load_dotenv():")
db_pass = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')

print(f"   DB_PASSWORD: {db_pass}")
print(f"   DB_PASSWORD length: {len(db_pass) if db_pass else 0}")
print(f"   DB_HOST: {db_host}")
print(f"   DB_USER: {db_user}")

# Check .env file directly
print("\n4️⃣ Reading .env file directly:")
try:
    with open('.env', 'r') as f:
        for line in f:
            if 'DB_' in line:
                print(f"   {line.strip()}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 80)
