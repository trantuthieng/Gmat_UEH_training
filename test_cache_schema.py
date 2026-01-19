"""Test Supabase connection and study_guide_cache table"""
import json
from db import get_conn, _get_db_type

def test_cache_schema():
    """Kiểm tra bảng study_guide_cache đã được tạo chưa"""
    
    print("=" * 60)
    print("SUPABASE CACHE SCHEMA TEST")
    print("=" * 60)
    
    # 1. Check database type
    db_type = _get_db_type()
    print(f"\n✓ Database type: {db_type}")
    
    if db_type != "postgresql":
        print("⚠️  Not using PostgreSQL - cache test skipped")
        return
    
    # 2. Test connection
    try:
        with get_conn() as conn:
            print("✓ Connection successful")
            cursor = conn.cursor()
            
            # 3. Check if table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'study_guide_cache'
            """)
            result = cursor.fetchone()
            
            if result:
                print(f"✓ Table 'study_guide_cache' exists")
            else:
                print("❌ Table 'study_guide_cache' NOT FOUND")
                return
            
            # 4. Check table columns
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'study_guide_cache'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            print(f"\n✓ Table structure ({len(columns)} columns):")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
            
            # 5. Test INSERT and SELECT
            test_topic = "__TEST_TOPIC__"
            test_data = {
                "theory": "Test theory content",
                "detailed_concepts": [
                    {"concept_name": "Test concept", "explanation": "Test explanation", "example": "Test example"}
                ],
                "step_by_step_method": ["Step 1", "Step 2", "Step 3", "Step 4"],
                "common_mistakes": ["Mistake 1", "Mistake 2", "Mistake 3", "Mistake 4"],
                "tips_for_accuracy": ["Tip 1", "Tip 2", "Tip 3", "Tip 4"]
            }
            
            try:
                # Delete test record if exists
                cursor.execute("DELETE FROM study_guide_cache WHERE topic = %s", (test_topic,))
                
                # Insert test record
                import psycopg2.extras
                cursor.execute(
                    """INSERT INTO study_guide_cache (topic, guide_data) 
                       VALUES (%s, %s)""",
                    (test_topic, psycopg2.extras.Json(test_data))
                )
                conn.commit()
                print(f"\n✓ INSERT test record successful")
                
                # Select test record
                cursor.execute(
                    "SELECT guide_data, accessed_count, created_at FROM study_guide_cache WHERE topic = %s",
                    (test_topic,)
                )
                row = cursor.fetchone()
                
                if row:
                    guide_data, access_count, created_at = row
                    print(f"✓ SELECT test record successful")
                    print(f"  - Topic: {test_topic}")
                    print(f"  - Data keys: {list(guide_data.keys())}")
                    print(f"  - Access count: {access_count}")
                    print(f"  - Created at: {created_at}")
                    
                    # Verify data integrity
                    if guide_data.get('theory') == test_data['theory']:
                        print(f"✓ Data integrity verified")
                    else:
                        print(f"❌ Data mismatch!")
                else:
                    print(f"❌ SELECT returned no results")
                
                # Test UPDATE (increment access count)
                cursor.execute(
                    """UPDATE study_guide_cache 
                       SET accessed_count = accessed_count + 1, 
                           last_accessed_at = CURRENT_TIMESTAMP 
                       WHERE topic = %s 
                       RETURNING accessed_count""",
                    (test_topic,)
                )
                new_count = cursor.fetchone()[0]
                conn.commit()
                print(f"\n✓ UPDATE access count successful: {new_count}")
                
                # Cleanup test record
                cursor.execute("DELETE FROM study_guide_cache WHERE topic = %s", (test_topic,))
                conn.commit()
                print(f"✓ Cleanup test record successful")
                
            except Exception as e:
                print(f"\n❌ Cache operations failed: {e}")
                import traceback
                traceback.print_exc()
                conn.rollback()
            
            # 6. Check existing cached topics
            cursor.execute("SELECT topic, accessed_count, created_at FROM study_guide_cache ORDER BY created_at DESC LIMIT 5")
            existing = cursor.fetchall()
            
            if existing:
                print(f"\n✓ Found {len(existing)} existing cached topics:")
                for topic, count, created in existing:
                    print(f"  - {topic[:30]:30} | Access: {count:3} | Created: {created}")
            else:
                print(f"\nℹ️  No cached topics yet")
            
            cursor.close()
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY ✓")
    print("=" * 60)

if __name__ == "__main__":
    test_cache_schema()
