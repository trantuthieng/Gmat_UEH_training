"""
Script khởi chạy ứng dụng GMAT trên local
"""
import os
import sys

def main():
    # Xác định nếu đang chạy trong PyInstaller EXE
    is_frozen = getattr(sys, 'frozen', False)
    
    if is_frozen:
        # Đang chạy trong EXE - lấy thư mục tạm của PyInstaller
        bundle_dir = sys._MEIPASS
        # Đường dẫn đến app.py trong bundle
        app_path = os.path.join(bundle_dir, "app.py")
    else:
        # Chạy từ source code
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(current_dir, "app.py")
    
    # Kiểm tra file app.py có tồn tại không
    if not os.path.exists(app_path):
        print(f"❌ Không tìm thấy file app.py tại {app_path}")
        if not is_frozen:
            input("Nhấn Enter để thoát...")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 ĐANG KHỞI ĐỘNG ỨNG DỤNG GMAT...")
    print("=" * 60)
    print(f"📂 Chế độ: {'EXE' if is_frozen else 'Source Code'}")
    print(f"📝 File app: {app_path}")
    print("=" * 60)
    print("🌐 Trình duyệt sẽ tự động mở trong giây lát...")
    print("⚠️  Để DỪNG ứng dụng, nhấn Ctrl+C trong cửa sổ này")
    print("=" * 60)
    
    try:
        if is_frozen:
            # Chạy Streamlit trực tiếp từ EXE (không dùng subprocess)
            from streamlit.web import cli as stcli
            sys.argv = [
                "streamlit",
                "run",
                app_path
            ]
            sys.exit(stcli.main())
        else:
            # Chạy từ source code - dùng subprocess như bình thường
            import subprocess
            subprocess.run([
                sys.executable, 
                "-m", 
                "streamlit", 
                "run", 
                app_path,
                "--server.port=8501",
                "--server.headless=false"
            ], check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Ứng dụng đã được dừng lại!")
    except Exception as e:
        print(f"\n❌ Lỗi khi chạy ứng dụng: {e}")
        if not is_frozen:
            input("Nhấn Enter để thoát...")
        sys.exit(1)

if __name__ == "__main__":
    main()
