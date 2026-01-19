# HƯỚNG DẪN TẠO FILE EXE CHO ỨNG DỤNG GMAT

## 📋 Yêu cầu
- Python đã được cài đặt
- Tất cả các thư viện trong `requirements.txt` đã được cài đặt

## 🚀 Cách 1: Sử dụng script tự động (KHUYẾN NGHỊ)

### Bước 1: Chạy script build_exe.py
```bash
# Build bản ẩn console (mặc định)
python build_exe.py

# Build bản hiển thị console (debug)
python build_exe.py console
```

Script sẽ tự động:
- Kiểm tra PyInstaller (cài đặt nếu chưa có)
- Xóa các file build cũ
- Build file EXE
- Copy file `.env` vào thư mục `dist/`
- Thông báo vị trí file EXE đã tạo

### Bước 2: Tìm file EXE
Sau khi build thành công, file EXE sẽ nằm trong thư mục `dist/`:
```
gmat/
  └── dist/
      ├── .env                     <-- File cấu hình
      ├── GMAT_App.exe            <-- Bản ẩn console (chạy im lặng)
      └── GMAT_App_Console.exe    <-- Bản hiện console (debug)
```

### Bước 3: Chạy ứng dụng
Double-click vào file EXE để khởi động ứng dụng!

**Lưu ý:**
- File `.env` phải ở cùng thư mục với EXE
- Lần đầu chạy có thể mất 10-20 giây để khởi động
- Trình duyệt sẽ tự động mở địa chỉ `http://localhost:8501`

---

## 🛠️ Cách 2: Build thủ công với PyInstaller

### Bước 1: Cài đặt PyInstaller
```bash
pip install pyinstaller
```

### Bước 2: Build file EXE với lệnh đơn giản
```bash
pyinstaller --onefile --name=GMAT_App run_app.py
```

### Bước 3: Build với đầy đủ tùy chọn (nếu cần)
```bash
pyinstaller --onefile ^
  --name=GMAT_App ^
  --add-data="app.py;." ^
  --add-data="ai_logic.py;." ^
  --add-data="db.py;." ^
  --add-data="study_guide.py;." ^
  --add-data=".env;." ^
  --hidden-import=streamlit ^
  --hidden-import=google.generativeai ^
  --hidden-import=psycopg2 ^
  --collect-all=streamlit ^
  run_app.py
```

### Bước 4: Tìm file EXE
File sẽ nằm trong `dist/GMAT_App.exe`

---

## ⚙️ Tùy chỉnh nâng cao

### Thêm icon cho EXE
Nếu bạn có file icon (`.ico`), thêm tham số:
```bash
--icon=path/to/icon.ico
```

### Không hiển thị console
Thêm tham số (đã có sẵn trong script):
```bash
--windowed
```

### Hiển thị console (để debug)
Bỏ tham số `--windowed` hoặc thêm:
```bash
--console
```

---

## 🔧 Xử lý lỗi thường gặp

### Lỗi: "PyInstaller not found"
**Giải pháp:** Cài đặt PyInstaller
```bash
pip install pyinstaller
```

### Lỗi: "Failed to execute script"
**Giải pháp:** 
- Kiểm tra file `.env` có trong thư mục không
- Chạy với `--console` để xem lỗi chi tiết
- Đảm bảo tất cả dependencies đã được cài đặt

### Lỗi: "Module not found"
**Giải pháp:** Thêm module vào lệnh build:
```bash
--hidden-import=ten_module
```

### File EXE quá lớn
**Giải pháp:** 
- Sử dụng `--exclude-module` để loại bỏ các module không cần thiết
- Sử dụng `--onedir` thay vì `--onefile` (tạo thư mục thay vì 1 file duy nhất)

---

## 📦 Phân phối ứng dụng

### Cách 1: Phân phối file EXE đơn lẻ
- Copy file `GMAT_App.exe` từ thư mục `dist/`
- Gửi file này cho người dùng
- ⚠️ **LƯU Ý:** File `.env` phải ở cùng thư mục với EXE

### Cách 2: Phân phối thư mục đầy đủ (nếu dùng --onedir)
- Copy toàn bộ thư mục `dist/GMAT_App/`
- Gửi thư mục này cho người dùng
- Chạy file `GMAT_App.exe` bên trong thư mục

### Cách 3: Tạo installer (nâng cao)
Sử dụng Inno Setup hoặc NSIS để tạo file cài đặt `.exe`

---

## 🎯 File quan trọng cần có

Đảm bảo các file sau tồn tại trước khi build:
- ✅ `run_app.py` - Script khởi chạy
- ✅ `app.py` - Ứng dụng chính
- ✅ `ai_logic.py` - Logic AI
- ✅ `db.py` - Kết nối database
- ✅ `study_guide.py` - Module study guide
- ✅ `.env` - Biến môi trường (API keys, database config)
- ✅ `requirements.txt` - Danh sách dependencies

---

## ⚡ Quick Start

**Cách nhanh nhất:**
```bash
# Bước 1: Cài PyInstaller (chỉ cần 1 lần)
pip install pyinstaller

# Bước 2: Build EXE
python build_exe.py

# Bước 3: Chạy
cd dist
GMAT_App.exe
```

**Hoặc sử dụng terminal:**
```bash
python run_app.py
```

---

## 💡 Mẹo

1. **Test trước khi build:** Luôn test `run_app.py` trước khi build EXE
2. **File nhỏ hơn:** Dùng virtual environment để giảm kích thước EXE
3. **Debug dễ hơn:** Build với `--console` trong quá trình phát triển
4. **Bảo mật:** Không commit file `.env` lên Git!

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra file log trong thư mục `build/`
2. Chạy với `--console` để xem lỗi
3. Đảm bảo tất cả dependencies đã được cài đặt đúng

Good luck! 🚀
