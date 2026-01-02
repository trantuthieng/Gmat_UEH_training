#!/usr/bin/env python3
"""
Tìm và sửa các escape character không hợp lệ trong JSON strings
"""
import json
import re

def find_invalid_escapes(json_file: str):
    """
    Tìm các escape sequence không hợp lệ trong JSON file
    """
    print(f"Đang kiểm tra file: {json_file}")
    print("=" * 80)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Các escape sequence hợp lệ trong JSON: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    valid_escapes = r'\\["\\/bfnrt]|\\u[0-9a-fA-F]{4}'
    
    # Tìm tất cả backslash
    backslash_pattern = r'\\.'
    
    issues = []
    for match in re.finditer(backslash_pattern, content):
        escape_seq = match.group()
        # Kiểm tra xem có phải escape hợp lệ không
        if not re.match(valid_escapes, escape_seq):
            pos = match.start()
            # Tìm context (50 chars trước và sau)
            start = max(0, pos - 50)
            end = min(len(content), pos + 50)
            context = content[start:end]
            
            # Tìm line number
            line_num = content[:pos].count('\n') + 1
            
            issues.append({
                'position': pos,
                'line': line_num,
                'escape': escape_seq,
                'context': context
            })
    
    if issues:
        print(f"❌ Tìm thấy {len(issues)} escape sequence không hợp lệ:\n")
        for i, issue in enumerate(issues[:10], 1):  # Show first 10
            print(f"{i}. Position {issue['position']}, Line {issue['line']}")
            print(f"   Invalid escape: {repr(issue['escape'])}")
            print(f"   Context: {repr(issue['context'])}")
            print()
    else:
        print("✅ Không tìm thấy escape sequence không hợp lệ")
    
    # Try parsing
    print("\nThử parse JSON...")
    try:
        data = json.loads(content)
        print(f"✅ JSON hợp lệ - {len(data) if isinstance(data, list) else 'object'} items")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error:")
        print(f"   Message: {e.msg}")
        print(f"   Line: {e.lineno}, Column: {e.colno}")
        print(f"   Position: {e.pos}")
        
        # Show problematic area
        start = max(0, e.pos - 100)
        end = min(len(content), e.pos + 100)
        print(f"\n   Problematic area:")
        print(f"   {repr(content[start:e.pos])} >>> HERE >>> {repr(content[e.pos:end])}")
        return False


if __name__ == '__main__':
    json_files = ['seed_data.json', 'azure-webapp-config.json']
    
    for json_file in json_files:
        find_invalid_escapes(json_file)
        print("\n" + "=" * 80 + "\n")
