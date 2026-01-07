"""
Test kết nối đến Supabase PostgreSQL Database
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("🔗 TESTING SUPABASE CONNECTION")
print("="*80)

# Check environment variables
print("\n1️⃣ Checking Environment Variables...")
required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
env_vars = {}
missing = []

for var in required_vars:
    value = os.getenv(var)
    if value:
        env_vars[var] = value
        if var == "DB_PASSWORD":
            print(f"   ✅ {var}: {value[:10]}***")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        missing.append(var)
        print(f"   ❌ {var}: NOT FOUND")

if missing:
    print(f"\n⚠️ Missing variables: {', '.join(missing)}")
    print("\n📝 Add these to .env file:")
    print("""
DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
    """)
    exit(1)

# Test connection
print("\n2️⃣ Testing PostgreSQL Connection...")
try:
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host=env_vars["DB_HOST"],
            port=int(env_vars["DB_PORT"]),
            database=env_vars["DB_NAME"],
            user=env_vars["DB_USER"],
            password=env_vars["DB_PASSWORD"]
        )
        
        print("   ✅ Connection successful!")
        
        # Get connection info
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   ✅ PostgreSQL version: {version[0][:50]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg:
            print(f"   ❌ Authentication failed - wrong password?")
            print(f"      Error: {error_msg}")
        elif "could not resolve" in error_msg:
            print(f"   ❌ Host not found - wrong host?")
            print(f"      Error: {error_msg}")
        else:
            print(f"   ❌ Connection failed: {error_msg}")
        exit(1)
        
except ImportError:
    print("   ❌ psycopg2 not installed")
    exit(1)

# Test with db module
print("\n3️⃣ Testing Database Module...")
try:
    from db import _get_db_type, init_db
    
    db_type = _get_db_type()
    print(f"   ✅ Database type: {db_type}")
    
    if db_type == "postgresql":
        print("   ✅ Using PostgreSQL (Supabase)")
    else:
        print(f"   ⚠️  Using {db_type} (fallback)")
    
    init_db()
    print("   ✅ Database initialized")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n" + "="*80)
print("✅ SUPABASE CONNECTION SUCCESSFUL!")
print("="*80)
print("\n🚀 Ready to run: streamlit run app.py")
print("="*80)
