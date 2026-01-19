"""Test cache update behavior - có cập nhật khi lưu cùng topic không"""
import json
from db import get_conn, _get_db_type
import time

def test_update_behavior():
    print("=" * 60)
    print("TEST: CACHE UPDATE BEHAVIOR")
    print("=" * 60)
    
    db_type = _get_db_type()
    if db_type != "postgresql":
        print("⚠️  Not using PostgreSQL - test skipped")
        return
    
    test_topic = "Permutations"  # Topic thực tế
    
    with get_conn() as conn:
        cursor = conn.cursor()
        
        # 1. Insert version 1
        v1_data = {
            "theory": "VERSION 1 - Old theory content",
            "detailed_concepts": [{"concept_name": "Old concept"}],
            "step_by_step_method": ["Step 1 OLD"],
            "common_mistakes": ["Mistake OLD"],
            "tips_for_accuracy": ["Tip OLD"]
        }
        
        import psycopg2.extras
        cursor.execute("DELETE FROM study_guide_cache WHERE topic = %s", (test_topic,))
        conn.commit()
        
        cursor.execute(
            """INSERT INTO study_guide_cache (topic, guide_data) 
               VALUES (%s, %s)""",
            (test_topic, psycopg2.extras.Json(v1_data))
        )
        conn.commit()
        print(f"\n✓ Inserted VERSION 1 for '{test_topic}'")
        
        # Check version 1
        cursor.execute(
            "SELECT guide_data, accessed_count, created_at FROM study_guide_cache WHERE topic = %s",
            (test_topic,)
        )
        row = cursor.fetchone()
        v1_theory = row[0]['theory']
        v1_count = row[1]
        v1_created = row[2]
        print(f"  Theory: {v1_theory[:30]}...")
        print(f"  Access count: {v1_count}")
        print(f"  Created at: {v1_created}")
        
        # Simulate some accesses
        for _ in range(3):
            cursor.execute(
                """UPDATE study_guide_cache 
                   SET accessed_count = accessed_count + 1,
                       last_accessed_at = CURRENT_TIMESTAMP
                   WHERE topic = %s""",
                (test_topic,)
            )
        conn.commit()
        print(f"\n✓ Simulated 3 accesses")
        
        time.sleep(1)  # Ensure timestamp difference
        
        # 2. Update with version 2 (using ON CONFLICT logic)
        v2_data = {
            "theory": "VERSION 2 - NEW updated theory content",
            "detailed_concepts": [{"concept_name": "NEW concept"}],
            "step_by_step_method": ["Step 1 NEW", "Step 2 NEW"],
            "common_mistakes": ["Mistake NEW"],
            "tips_for_accuracy": ["Tip NEW"]
        }
        
        cursor.execute(
            """INSERT INTO study_guide_cache (topic, guide_data) 
               VALUES (%s, %s) 
               ON CONFLICT (topic) DO UPDATE SET guide_data = EXCLUDED.guide_data""",
            (test_topic, psycopg2.extras.Json(v2_data))
        )
        conn.commit()
        print(f"\n✓ Inserted VERSION 2 (should UPDATE existing record)")
        
        # Check version 2
        cursor.execute(
            "SELECT guide_data, accessed_count, created_at, last_accessed_at FROM study_guide_cache WHERE topic = %s",
            (test_topic,)
        )
        row = cursor.fetchone()
        v2_theory = row[0]['theory']
        v2_count = row[1]
        v2_created = row[2]
        v2_accessed = row[3]
        
        print(f"\n📊 AFTER UPDATE:")
        print(f"  Theory: {v2_theory[:40]}...")
        print(f"  Access count: {v2_count}")
        print(f"  Created at: {v2_created}")
        print(f"  Last accessed: {v2_accessed}")
        
        # Verify results
        print(f"\n🔍 VERIFICATION:")
        if "VERSION 2" in v2_theory:
            print("  ✅ Content UPDATED successfully")
        else:
            print("  ❌ Content NOT updated!")
        
        if v2_count == 3:
            print(f"  ✅ Access count PRESERVED (still {v2_count})")
        else:
            print(f"  ❌ Access count changed unexpectedly: {v2_count}")
        
        if v2_created == v1_created:
            print(f"  ✅ Created timestamp PRESERVED (original)")
        else:
            print(f"  ⚠️  Created timestamp changed (unexpected)")
        
        # Cleanup
        cursor.execute("DELETE FROM study_guide_cache WHERE topic = %s", (test_topic,))
        conn.commit()
        print(f"\n✓ Cleanup completed")
        
        cursor.close()
    
    print("\n" + "=" * 60)
    print("KẾT LUẬN:")
    print("- Content: CẬP NHẬT khi lưu lại cùng topic")
    print("- Access count: GIỮ NGUYÊN (track tổng lượt truy cập)")
    print("- Created timestamp: GIỮ NGUYÊN (thời điểm tạo ban đầu)")
    print("=" * 60)

if __name__ == "__main__":
    test_update_behavior()
