📖 HƯỚNG DẪN SETUP SUPABASE TRỊ LOCAL
═════════════════════════════════════════════════════════

**Bước 1: Cập nhật .env với Supabase credentials**

Mở file `.env` và thêm:

```
# Supabase PostgreSQL Database Configuration
DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_actual_password_here
```

⚠️ LƯU Ý: Thay `your_actual_password_here` bằng password thực tế của Supabase

**Bước 2: Lấy Supabase credentials**

1. Đăng nhập vào Supabase (https://app.supabase.com)
2. Chọn project của bạn
3. Vào Settings > Database
4. Tìm phần "Connection string" hoặc "Connection pooler"
5. Sao chép connection details:
   - Host
   - Port (mặc định 5432)
   - Database (postgres)
   - User (postgres)
   - Password

**Bước 3: Cập nhật .env**

Dán các giá trị vào .env:

```
DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

**Bước 4: Chạy app**

```bash
streamlit run app.py
```

App sẽ:
- Tự động kết nối đến Supabase
- Nếu kết nối thất bại, sẽ fallback sang SQLite

**Bước 5: Verify kết nối**

Chạy test để verify:

```bash
python -c "from db import _get_db_type, init_db; print('DB Type:', _get_db_type()); init_db(); print('✅ Database connected')"
```

═════════════════════════════════════════════════════════

✅ Khi tất cả được setup đúng:
  - App sẽ kết nối đến Supabase PostgreSQL
  - Dữ liệu sẽ được lưu trên cloud
  - Có thể truy cập từ bất kỳ thiết bị nào

📱 Hiện tại:
  - Code hỗ trợ cả SQLite (local) và PostgreSQL (cloud)
  - Fallback tự động nếu Supabase không available
