#!/usr/bin/env python3
"""
Tìm lỗi escape character trong JSON file
"""
import json

try:
    with open('seed_data.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tìm vị trí lỗi
    error_pos = 37355
    start = max(0, error_pos - 200)
    end = min(len(content), error_pos + 200)
    
    print(f"Nội dung xung quanh vị trí {error_pos}:")
    print("=" * 80)
    print(content[start:end])
    print("=" * 80)
    
    # Tìm dòng chứa lỗi
    lines = content[:error_pos].split('\n')
    line_num = len(lines)
    
    print(f"\nDòng {line_num} (line chứa lỗi):")
    print("-" * 80)
    if line_num <= len(content.split('\n')):
        full_line = content.split('\n')[line_num - 1]
        print(full_line)
    
    # Try to parse JSON
    print("\n\nThử parse JSON...")
    try:
        data = json.loads(content)
        print("✅ JSON hợp lệ!")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        print(f"   Position: {e.pos}")
        print(f"   Line: {e.lineno}, Column: {e.colno}")
        print(f"   Message: {e.msg}")
        
        # Show context around error
        error_start = max(0, e.pos - 100)
        error_end = min(len(content), e.pos + 100)
        print(f"\n   Context around error position {e.pos}:")
        print(f"   {repr(content[error_start:error_end])}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
