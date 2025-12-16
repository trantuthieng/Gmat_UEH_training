import json
from ai_logic import generate_full_exam

# Load seed data
with open('seed_data.json', 'r', encoding='utf-8') as f:
    seed_data = json.load(f)

print(f"Loaded {len(seed_data)} seed questions")

# Test creating 5 questions
print("\nTesting question generation...")
questions = generate_full_exam(seed_data, num_questions=5)

print(f"\n✅ Generated {len(questions)} questions")
for i, q in enumerate(questions):
    print(f"\nCâu {i+1}:")
    print(f"  Question: {q.get('question', 'N/A')[:80]}")
    print(f"  Options: {len(q.get('options', []))} options")
    print(f"  Answer: {q.get('correct_answer', 'N/A')[:50]}")
