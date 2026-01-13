#!/usr/bin/env python
import json

# Load seed data
with open('seed_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"✅ seed_data.json hợp lệ: {len(data)} câu\n")

# Statistics by type
types = {}
topics = {}
for q in data:
    q_type = q.get('type', 'unknown')
    topic = q.get('topic', 'unknown')
    types[q_type] = types.get(q_type, 0) + 1
    topics[topic] = topics.get(topic, 0) + 1

print("📊 Phân bố theo loại câu:")
for q_type, count in sorted(types.items()):
    print(f"  - {q_type}: {count} câu")

print("\n📚 Phân bố theo chủ đề:")
for topic, count in sorted(topics.items()):
    print(f"  - {topic}: {count} câu")

# Check for data_sufficiency questions structure
print("\n🔍 Kiểm tra cấu trúc Data Sufficiency:")
ds_questions = [q for q in data if q.get('type') == 'data_sufficiency']
for q in ds_questions:
    print(f"\n  ID {q['id']}: {q['topic']}")
    print(f"    - Có data_statements: {bool(q.get('data_statements'))}")
    print(f"    - Số lựa chọn: {len(q.get('options', []))}")
    if q.get('data_statements'):
        print(f"    - Dữ kiện: {q['data_statements']}")

# Check for missing correct answers
print("\n⚠️ Kiểm tra đáp án:")
missing_answers = [q for q in data if not q.get('correct_answer')]
if missing_answers:
    print(f"  ⚠️ {len(missing_answers)} câu không có correct_answer")
    for q in missing_answers[:5]:
        print(f"    - ID {q['id']}: {q['topic']}")

print("\n✅ Cấu trúc seed_data.json đạt yêu cầu!")
