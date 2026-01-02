#!/usr/bin/env python3
"""
Script kiểm tra cấu trúc và tính hợp lệ của các file JSON trong project
"""
import json
import os
from pathlib import Path

def validate_json_file(filepath: str, allow_comments: bool = False) -> dict:
    """
    Validate một JSON file và trả về thông tin chi tiết
    
    Args:
        filepath: Đường dẫn tới file JSON
        allow_comments: True nếu cho phép comments (JSONC format)
    
    Returns:
        dict với keys: valid, error, size, structure, sample
    """
    result = {
        'valid': False,
        'error': None,
        'size': 0,
        'structure': None,
        'sample': None,
        'format': 'json'
    }
    
    try:
        # Kiểm tra file tồn tại
        if not os.path.exists(filepath):
            result['error'] = "File không tồn tại"
            return result
        
        # Lấy kích thước file
        result['size'] = os.path.getsize(filepath)
        
        # Đọc và parse JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Nếu cho phép comments, strip them ra (JSONC format)
            if allow_comments:
                import re
                result['format'] = 'jsonc'
                # Remove single-line comments //
                content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
                # Remove multi-line comments /* */
                content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            data = json.loads(content)
        
        result['valid'] = True
        
        # Phân tích cấu trúc
        if isinstance(data, list):
            result['structure'] = {
                'type': 'array',
                'length': len(data),
                'item_type': type(data[0]).__name__ if data else None
            }
            if data:
                # Nếu là array of objects, lấy keys của phần tử đầu tiên
                if isinstance(data[0], dict):
                    result['structure']['keys'] = list(data[0].keys())
                # Sample: 2 phần tử đầu
                result['sample'] = data[:2]
        elif isinstance(data, dict):
            result['structure'] = {
                'type': 'object',
                'keys': list(data.keys()),
                'key_count': len(data.keys())
            }
            result['sample'] = {k: v for k, v in list(data.items())[:5]}
        else:
            result['structure'] = {
                'type': type(data).__name__
            }
            result['sample'] = str(data)[:200]
        
    except json.JSONDecodeError as e:
        result['error'] = f"JSON parse error at line {e.lineno}, column {e.colno}: {e.msg}"
    except UnicodeDecodeError as e:
        result['error'] = f"Encoding error: {str(e)}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
    
    return result


def main():
    print("=" * 80)
    print("KIỂM TRA CẤU TRÚC FILE JSON")
    print("=" * 80)
    
    # Danh sách các JSON files cần kiểm tra
    json_files = [
        ('seed_data.json', False),
        ('azure-webapp-config.json', False),
        ('.devcontainer/devcontainer.json', True)  # JSONC format (có comments)
    ]
    
    project_root = Path(__file__).parent
    
    for json_file, allow_comments in json_files:
        filepath = project_root / json_file
        print(f"\n📄 File: {json_file}")
        print("-" * 80)
        
        result = validate_json_file(str(filepath), allow_comments=allow_comments)
        
        if result['valid']:
            print(f"✅ JSON hợp lệ ({result['format'].upper()} format)")
            print(f"📊 Kích thước: {result['size']:,} bytes ({result['size'] / 1024:.1f} KB)")
            
            if result['structure']:
                print(f"\n🔍 Cấu trúc:")
                structure = result['structure']
                
                if structure['type'] == 'array':
                    print(f"  - Loại: Array")
                    print(f"  - Số phần tử: {structure['length']}")
                    print(f"  - Kiểu dữ liệu phần tử: {structure['item_type']}")
                    if 'keys' in structure:
                        print(f"  - Keys trong mỗi object: {', '.join(structure['keys'])}")
                elif structure['type'] == 'object':
                    print(f"  - Loại: Object")
                    print(f"  - Số keys: {structure['key_count']}")
                    print(f"  - Keys: {', '.join(structure['keys'])}")
                
                if result['sample']:
                    print(f"\n📝 Sample data (first items):")
                    print(json.dumps(result['sample'], indent=2, ensure_ascii=False)[:500])
                    if len(json.dumps(result['sample'], indent=2)) > 500:
                        print("  ... (truncated)")
        else:
            print(f"❌ JSON không hợp lệ")
            if result['error']:
                print(f"⚠️ Lỗi: {result['error']}")
    
    print("\n" + "=" * 80)
    print("✅ HOÀN THÀNH KIỂM TRA")
    print("=" * 80)


if __name__ == '__main__':
    main()
