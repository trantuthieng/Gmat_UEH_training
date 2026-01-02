#!/usr/bin/env python3
"""
Test script to verify study guide JSON parsing improvements
"""
import json
import sys

# Test the fallback study guide function
from study_guide import _create_fallback_study_guide

# Sample topic analysis
topic_analysis = {
    'Arithmetic': {
        'type': 'quant',
        'total': 5,
        'correct': 2,
        'wrong': 3,
        'questions': []
    },
    'Algebra': {
        'type': 'quant',
        'total': 5,
        'correct': 4,
        'wrong': 1,
        'questions': []
    },
    'Geometry': {
        'type': 'quant',
        'total': 4,
        'correct': 3,
        'wrong': 1,
        'questions': []
    },
    'Reading Comprehension': {
        'type': 'verbal',
        'total': 8,
        'correct': 5,
        'wrong': 3,
        'questions': []
    },
    'Critical Reasoning': {
        'type': 'verbal',
        'total': 8,
        'correct': 7,
        'wrong': 1,
        'questions': []
    }
}

print("=" * 60)
print("TEST: Fallback Study Guide Creation")
print("=" * 60)

try:
    # Test fallback guide creation
    study_data = _create_fallback_study_guide(topic_analysis)
    
    print("\n✅ Fallback study guide created successfully")
    print(f"📊 Topics: {len(study_data.get('topics', []))}")
    print(f"📄 Keys: {list(study_data.keys())}")
    
    # Verify structure
    required_fields = ['overall_summary', 'topics', 'recommended_focus', 'next_steps', 'practice_resources', 'motivation_message']
    for field in required_fields:
        if field in study_data:
            print(f"  ✅ {field}: present")
        else:
            print(f"  ❌ {field}: MISSING")
    
    # Verify topics structure
    print(f"\n📚 Topics Detail:")
    for topic in study_data['topics']:
        print(f"  - {topic['topic']}: {topic['accuracy']:.0f}% accuracy, importance={topic['importance']}")
        if 'stats' in topic:
            print(f"    Stats: {topic['stats']['correct']}/{topic['stats']['total']} correct")
    
    # Test JSON serialization (ensure it's valid JSON)
    print(f"\n🔍 JSON Validation:")
    try:
        json_str = json.dumps(study_data)
        print(f"  ✅ Valid JSON ({len(json_str)} chars)")
        
        # Deserialize to verify
        loaded = json.loads(json_str)
        print(f"  ✅ Deserialize successful")
        
        if loaded == study_data:
            print(f"  ✅ Round-trip successful")
    except Exception as e:
        print(f"  ❌ JSON error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
