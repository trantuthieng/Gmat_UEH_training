# 🔐 Supabase Password Fix

## ⚠️ Vấn đề
PostgreSQL connection đang fail vì password incomplete hoặc sai.

```
FATAL: password authentication failed for user "postgres"
```

## 🔍 Kiểm tra
Password hiện tại trong `.env`:
```
DB_PASSWORD="6yFHqCMg9ATcCRZt"  (16 ký tự)
```

Supabase thường generate password **24+ ký tự**. Này là bị cut off.

## ✅ Cách Fix

### Option 1: Lấy Password Mới từ Supabase
1. Vào https://supabase.com/dashboard
2. Chọn project
3. Vào **Settings → Database → Password**
4. Click **Reset password** hoặc reveal full password
5. Copy password đầy đủ
6. Update `.env`:
   ```
   DB_PASSWORD="<PASTE_NEW_PASSWORD_HERE>"
   ```

### Option 2: Tạo Database User Mới
Nếu không tìm được password cũ:
1. Vào Supabase Dashboard → **SQL Editor**
2. Chạy:
   ```sql
   ALTER USER postgres WITH PASSWORD 'new_password_here';
   ```
3. Update `.env` với password mới

### Option 3: Dùng SQLite (Tạm thời)
App tự động fallback sang SQLite nếu PostgreSQL fail:
```
📁 Fallback to SQLite for local development
```

Dữ liệu sẽ lưu local trong `gmat.db`, không sync với Supabase.

## 📝 Verification
Sau khi update password, test:
```bash
python test_supabase_connection.py
```

Output phải là:
```
✅ Connection successful!
✅ PostgreSQL version: PostgreSQL 17.x...
✅ Database type: postgresql
```

## 🎯 Current Status
- **Database**: SQLite (fallback từ PostgreSQL auth fail)
- **Data Persistence**: Local trong `gmat.db`
- **App Status**: ✅ Running, fully functional
- **Password Fix**: ⏳ Pending - user action needed

---

**Khi password fixed:**
- Restart app: `streamlit run app.py`
- App sẽ connect PostgreSQL automatically
- Data sẽ sync với Supabase cloud
