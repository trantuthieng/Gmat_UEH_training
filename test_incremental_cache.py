"""Test incremental cache updates with version tracking"""
import json
import time
from db import get_conn, _get_db_type

def test_incremental_updates():
    print("=" * 70)
    print("TEST: INCREMENTAL CACHE UPDATES (VERSION TRACKING)")
    print("=" * 70)
    
    db_type = _get_db_type()
    if db_type != "postgresql":
        print("⚠️  Test requires PostgreSQL")
        return
    
    test_topic = "Permutations"
    
    with get_conn() as conn:
        cursor = conn.cursor()
        import psycopg2.extras
        
        # Delete existing
        cursor.execute("DELETE FROM study_guide_cache WHERE topic = %s", (test_topic,))
        conn.commit()
        
        # ===== DAY 1 =====
        print("\n" + "="*70)
        print("DAY 1: User 1 làm bài, lỗi 'thiếu công thức'")
        print("="*70)
        
        v1_data = {
            "theory": "V1: Permutation là sắp xếp có thứ tự\nP(n,k) = n!/(n-k)!",
            "common_mistakes": ["Lỗi 1: Nhầm permutation với combination"],
            "tips_for_accuracy": ["Mẹo 1: Luôn hỏi 'thứ tự có quan trọng không?'"],
            "detailed_concepts": [{"concept_name": "Basic permutation", "explanation": "Sắp xếp k phần tử từ n"}],
            "step_by_step_method": ["Bước 1: Xác định n", "Bước 2: Xác định k", "Bước 3: Áp dụng công thức"]
        }
        
        cursor.execute(
            """INSERT INTO study_guide_cache (topic, guide_data, version) 
               VALUES (%s, %s, 1)""",
            (test_topic, psycopg2.extras.Json(v1_data))
        )
        conn.commit()
        
        cursor.execute(
            """SELECT version, created_at, updated_at FROM study_guide_cache 
               WHERE topic = %s""",
            (test_topic,)
        )
        v1_info = cursor.fetchone()
        print(f"\n✓ V{v1_info[0]} created at {v1_info[1]}")
        print(f"  Content: {v1_data['theory'][:50]}...")
        print(f"  Mistakes: {v1_data['common_mistakes']}")
        
        time.sleep(2)  # Ensure timestamp difference
        
        # ===== DAY 2 =====
        print("\n" + "="*70)
        print("DAY 2: User 2 làm bài, cùng topic nhưng lỗi 'circular permutation'")
        print("="*70)
        
        v2_data = {
            "theory": "V1: Permutation là sắp xếp có thứ tự\nP(n,k) = n!/(n-k)!\nV2 ADDED: Circular permutation = (n-1)!",
            "common_mistakes": [
                "Lỗi 1: Nhầm permutation với combination",
                "Lỗi 2: QUÊN TRỪ 1 ở circular permutation"
            ],
            "tips_for_accuracy": [
                "Mẹo 1: Luôn hỏi 'thứ tự có quan trọng không?'",
                "Mẹo 2: Kiểm tra xem có phải circular arrangement không"
            ],
            "detailed_concepts": [
                {"concept_name": "Basic permutation", "explanation": "Sắp xếp k phần tử từ n"},
                {"concept_name": "Circular permutation", "explanation": "Sắp xếp vòng tròn, (n-1)!"}
            ],
            "step_by_step_method": [
                "Bước 1: Xác định n",
                "Bước 2: Xác định k",
                "Bước 3: Kiểm tra có phải circular không",
                "Bước 4: Áp dụng công thức phù hợp"
            ]
        }
        
        # Simulate AI enrichment + save
        cursor.execute(
            """INSERT INTO study_guide_cache (topic, guide_data, version) 
               VALUES (%s, %s, 1) 
               ON CONFLICT (topic) DO UPDATE SET 
                   guide_data = EXCLUDED.guide_data,
                   version = study_guide_cache.version + 1,
                   updated_at = CURRENT_TIMESTAMP""",
            (test_topic, psycopg2.extras.Json(v2_data))
        )
        conn.commit()
        
        cursor.execute(
            """SELECT version, created_at, updated_at FROM study_guide_cache 
               WHERE topic = %s""",
            (test_topic,)
        )
        v2_info = cursor.fetchone()
        print(f"\n✓ V{v2_info[0]} updated at {v2_info[2]}")
        print(f"  Created: {v2_info[1]} (UNCHANGED)")
        print(f"  Updated: {v2_info[2]} (NEW)")
        print(f"  Content: {v2_data['theory'][:100]}...")
        print(f"  Mistakes: {len(v2_data['common_mistakes'])} (tăng từ 1)")
        
        time.sleep(2)
        
        # ===== DAY 3 =====
        print("\n" + "="*70)
        print("DAY 3: User 3 làm bài, cùng topic nhưng lỗi 'repetition allowed'")
        print("="*70)
        
        v3_data = {
            "theory": v2_data['theory'] + "\nV3 ADDED: Với repetition: n^k",
            "common_mistakes": v2_data['common_mistakes'] + [
                "Lỗi 3: QUÊN CASE khi lặp lại được phép"
            ],
            "tips_for_accuracy": v2_data['tips_for_accuracy'] + [
                "Mẹo 3: Luôn xác nhận 'có thể lặp lại không?'"
            ],
            "detailed_concepts": v2_data['detailed_concepts'] + [
                {"concept_name": "Permutation with repetition", "explanation": "Khi có thể lặp: n^k"}
            ],
            "step_by_step_method": v2_data['step_by_step_method']
        }
        
        cursor.execute(
            """INSERT INTO study_guide_cache (topic, guide_data, version) 
               VALUES (%s, %s, 1) 
               ON CONFLICT (topic) DO UPDATE SET 
                   guide_data = EXCLUDED.guide_data,
                   version = study_guide_cache.version + 1,
                   updated_at = CURRENT_TIMESTAMP""",
            (test_topic, psycopg2.extras.Json(v3_data))
        )
        conn.commit()
        
        cursor.execute(
            """SELECT version, created_at, updated_at FROM study_guide_cache 
               WHERE topic = %s""",
            (test_topic,)
        )
        v3_info = cursor.fetchone()
        print(f"\n✓ V{v3_info[0]} updated at {v3_info[2]}")
        print(f"  Created: {v3_info[1]} (UNCHANGED - still Day 1)")
        print(f"  Updated: {v3_info[2]} (LATEST)")
        print(f"  Mistakes: {len(v3_data['common_mistakes'])} (tăng từ 2 → 3)")
        
        # ===== FINAL REPORT =====
        print("\n" + "="*70)
        print("FINAL RESULT AFTER 3 DAYS")
        print("="*70)
        
        cursor.execute(
            """SELECT topic, version, created_at, updated_at, accessed_count 
               FROM study_guide_cache WHERE topic = %s""",
            (test_topic,)
        )
        final = cursor.fetchone()
        
        print(f"\nTopic: {final[0]}")
        print(f"Current Version: {final[1]}")
        print(f"Created: {final[2]} (ngày đầu tiên)")
        print(f"Updated: {final[3]} (cập nhật gần nhất)")
        print(f"Access count: {final[4]}")
        
        print("\n📊 EVOLUTION:")
        print("  V1 (Day 1): Basic permutation formula")
        print("  V2 (Day 2): + Circular permutation case")
        print("  V3 (Day 3): + Permutation with repetition case")
        print("\n✅ Guide hoàn thiện dần qua mỗi lần user khác làm bài!")
        
        # Cleanup
        cursor.execute("DELETE FROM study_guide_cache WHERE topic = %s", (test_topic,))
        conn.commit()
        cursor.close()
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_incremental_updates()
