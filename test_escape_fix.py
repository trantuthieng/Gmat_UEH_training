#!/usr/bin/env python3
"""
Test escape sequence fixing in study guide JSON responses
"""
import re
import json

# Sample AI responses with invalid escapes
test_cases = [
    {
        'name': 'Invalid \\x escape',
        'text': '{"topic": "Math\\xem", "value": 123}'
    },
    {
        'name': 'Invalid \\a escape in Vietnamese',
        'text': '{"content": "Bài to\\án này"}'
    },
    {
        'name': 'Valid escapes',
        'text': '{"text": "Line 1\\nLine 2\\tTabbed"}'
    },
    {
        'name': 'Invalid \\u escape (incomplete)',
        'text': '{"unicode": "Test\\u12"}'
    },
    {
        'name': 'Valid \\u escape',
        'text': '{"unicode": "Test\\u0041BC"}'
    },
    {
        'name': 'Backslash in path',
        'text': '{"path": "C:\\Users\\Documents"}'
    }
]

def fix_escapes(match):
    """Fix invalid escape sequences"""
    escape_char = match.group(1)
    # Valid JSON escapes: " \ / b f n r t u
    if escape_char in ['"', '\\', '/', 'b', 'f', 'n', 'r', 't']:
        return match.group(0)  # Keep valid escapes
    elif escape_char == 'u':
        # Check if followed by 4 hex digits
        if len(match.group(0)) >= 6 and re.match(r'\\u[0-9a-fA-F]{4}', match.group(0)):
            return match.group(0)  # Valid unicode escape
        else:
            return '\\\\u'  # Invalid unicode escape, fix it
    else:
        # Invalid escape, double the backslash
        return '\\\\' + escape_char

print("=" * 80)
print("TEST: Escape Sequence Fixing")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['name']}")
    print("-" * 80)
    
    original = test['text']
    print(f"Original: {original}")
    
    # Apply fix
    fixed = re.sub(r'\\(.)', fix_escapes, original)
    print(f"Fixed:    {fixed}")
    
    # Try parsing
    try:
        data = json.loads(fixed)
        print(f"✅ Parse OK: {data}")
    except json.JSONDecodeError as e:
        print(f"❌ Parse failed: {e.msg} at position {e.pos}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETED")
print("=" * 80)
