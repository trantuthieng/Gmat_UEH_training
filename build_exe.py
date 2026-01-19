"""
Script để build file EXE cho ứng dụng GMAT
Sử dụng PyInstaller để tạo executable
"""
import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """Kiểm tra PyInstaller đã cài đặt chưa"""
    try:
        import PyInstaller
        print("✅ PyInstaller đã được cài đặt")
        return True
    except ImportError:
        print("❌ PyInstaller chưa được cài đặt")
        return False

def install_pyinstaller():
    """Cài đặt PyInstaller"""
    print("📦 Đang cài đặt PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ Cài đặt PyInstaller thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi cài đặt PyInstaller: {e}")
        return False

def build_exe(console: bool = False):
    """Build file EXE
    :param console: True để build EXE hiển thị console (debug), False để windowed
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n" + "=" * 60)
    print("🔨 BẮT ĐẦU BUILD FILE EXE")
    print("=" * 60)
    
    # Xóa thư mục build cũ nếu có (tránh xóa dist khi EXE đang chạy)
    for folder in ['build']:
        folder_path = os.path.join(current_dir, folder)
        if os.path.exists(folder_path):
            print(f"🗑️  Xóa thư mục cũ: {folder}")
            try:
                shutil.rmtree(folder_path)
            except Exception as e:
                print(f"⚠️  Không thể xóa {folder}: {e}")
    
    # Xóa file .spec cũ nếu có
    spec_file = os.path.join(current_dir, "run_app.spec")
    if os.path.exists(spec_file):
        print("🗑️  Xóa file .spec cũ")
        try:
            os.remove(spec_file)
        except Exception as e:
            print(f"⚠️  Không thể xóa .spec: {e}")
    
    # Tạo lệnh PyInstaller
    exe_name = "GMAT_App_Console" if console else "GMAT_App"
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Tạo 1 file exe duy nhất
        *([] if console else ["--windowed"]),  # Hiển thị console nếu chế độ console
        f"--name={exe_name}",  # Tên file exe
        "--icon=NONE",  # Không có icon (có thể thêm nếu có file .ico)
        "--add-data=app.py;.",  # Thêm app.py vào exe
        "--add-data=ai_logic.py;.",  # Thêm ai_logic.py
        "--add-data=db.py;.",  # Thêm db.py
        "--add-data=study_guide.py;.",  # Thêm study_guide.py
        "--add-data=.env;.",  # Thêm file .env (nếu có)
        "--add-data=.streamlit;.streamlit",  # Thêm thư mục .streamlit với cấu hình
        "--hidden-import=streamlit",
        "--hidden-import=google.generativeai",
        "--hidden-import=psycopg2",
        "--hidden-import=dotenv",
        "--collect-all=streamlit",
        "run_app.py"
    ]
    
    print(f"📝 Lệnh build: {' '.join(pyinstaller_cmd)}")
    print("\n⏳ Đang build... (Có thể mất vài phút)")
    
    try:
        subprocess.check_call(pyinstaller_cmd, cwd=current_dir)
        print("\n" + "=" * 60)
        print("✅ BUILD THÀNH CÔNG!")
        print("=" * 60)
        
        exe_path = os.path.join(current_dir, "dist", f"{exe_name}.exe")
        if os.path.exists(exe_path):
            print(f"📦 File EXE: {exe_path}")
            print(f"📏 Kích thước: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
            print("\n✨ Bạn có thể chạy file GMAT_App.exe để khởi động ứng dụng!")
            # Sao chép .env vào thư mục dist để EXE đọc được (ngoài việc nhúng vào _MEIPASS)
            env_src = os.path.join(current_dir, ".env")
            env_dst = os.path.join(current_dir, "dist", ".env")
            if os.path.exists(env_src):
                try:
                    shutil.copy2(env_src, env_dst)
                    print(f"📄 Đã sao chép .env vào: {env_dst}")
                except Exception as copy_err:
                    print(f"⚠️  Không thể sao chép .env: {copy_err}")
            else:
                print("ℹ️ Không thấy file .env ở thư mục dự án — EXE sẽ dùng biến môi trường hệ thống nếu có.")
            
            # Sao chép .streamlit folder vào dist để cấu hình Streamlit
            streamlit_src = os.path.join(current_dir, ".streamlit")
            streamlit_dst = os.path.join(current_dir, "dist", ".streamlit")
            if os.path.exists(streamlit_src):
                try:
                    if os.path.exists(streamlit_dst):
                        shutil.rmtree(streamlit_dst)
                    shutil.copytree(streamlit_src, streamlit_dst)
                    print(f"⚙️  Đã sao chép cấu hình Streamlit vào: {streamlit_dst}")
                except Exception as copy_err:
                    print(f"⚠️  Không thể sao chép .streamlit: {copy_err}")
            else:
                print("ℹ️ Không thấy thư mục .streamlit")
        else:
            print("⚠️  Không tìm thấy file exe trong thư mục dist")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Lỗi khi build: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🎯 SCRIPT BUILD FILE EXE CHO ỨNG DỤNG GMAT")
    print("=" * 60)
    
    # Kiểm tra và cài đặt PyInstaller nếu cần
    if not check_pyinstaller():
        print("\n⚠️  Cần cài đặt PyInstaller để tiếp tục")
        response = input("Bạn có muốn cài đặt PyInstaller không? (y/n): ")
        if response.lower() == 'y':
            if not install_pyinstaller():
                print("\n❌ Không thể tiếp tục vì PyInstaller chưa được cài đặt")
                input("\nNhấn Enter để thoát...")
                return
        else:
            print("\n❌ Không thể build mà không có PyInstaller")
            input("\nNhấn Enter để thoát...")
            return
    
    # Xác định chế độ build: console hay windowed
    console = any(arg.lower() in {"--console", "console"} for arg in sys.argv[1:])
    if console:
        print("\n🛠️ Chế độ build: CONSOLE (hiển thị console để debug)")
    else:
        print("\n🛠️ Chế độ build: WINDOWED (ẩn console)")

    # Build EXE
    success = build_exe(console=console)
    
    if success:
        print("\n✨ HOÀN THÀNH!")
    else:
        print("\n❌ BUILD THẤT BẠI!")
    
    input("\nNhấn Enter để thoát...")

if __name__ == "__main__":
    main()
