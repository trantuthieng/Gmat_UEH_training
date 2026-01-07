🚀 GMAT APP - LOCAL STARTUP GUIDE
════════════════════════════════════════════════════════════

**QUICK START (Nhanh nhất - Chạy ngay)**

```bash
streamlit run app.py
```

App sẽ tự động:
✅ Kết nối đến Supabase PostgreSQL (nếu credentials hợp lệ)
✅ Hoặc fallback sang SQLite nếu Supabase không available
✅ Khởi tạo database schema
✅ Bắt đầu chạy trên http://localhost:8501

═══════════════════════════════════════════════════════════

**ĐẦY ĐỦ SETUP (Cần làm lần đầu)**

1️⃣ **Chuẩn bị môi trường**
```bash
# Activate virtual environment
.venv/Scripts/Activate.ps1

# Cài đặt dependencies
pip install -r requirements.txt
```

2️⃣ **Cấu hình Supabase (tùy chọn)**

Nếu muốn dùng Supabase:
- Mở file `.env`
- Điền Supabase credentials (DB_HOST, DB_USER, DB_PASSWORD, ...)
- Chạy test: `python test_supabase_connection.py`

3️⃣ **Chạy Tests**

Verify mọi thứ hoạt động:

```bash
# Test workflow
python test_workflow.py

# Test Supabase (nếu có setup)
python test_supabase_connection.py
```

4️⃣ **Chạy App**

```bash
streamlit run app.py
```

═══════════════════════════════════════════════════════════

**DATABASE OPTIONS**

❌ **Không có Supabase credentials:**
   → Tự động dùng SQLite (gmat.db)
   → Dữ liệu lưu local
   → Không cần internet

✅ **Có Supabase credentials:**
   → Sử dụng PostgreSQL (Supabase)
   → Dữ liệu lưu trên cloud
   → Có thể truy cập từ mọi nơi

═══════════════════════════════════════════════════════════

**TROUBLESHOOTING**

❌ Lỗi: "ModuleNotFoundError: No module named..."
✅ Cách fix: pip install -r requirements.txt

❌ Lỗi: "GEMINI_API_KEY not found"
✅ Cách fix: Thêm GEMINI_API_KEY vào .env

❌ Lỗi: "PostgreSQL connection failed"
✅ Cách fix: Kiểm tra DB credentials, hoặc dùng SQLite fallback

❌ App không mở được trên browser
✅ Cách fix: Truy cập http://localhost:8501

═══════════════════════════════════════════════════════════

**ENVIRONMENT VARIABLES CẦN THIẾT**

```
# Bắt buộc
GEMINI_API_KEY=your_gemini_api_key

# Tùy chọn (cho Supabase)
DB_HOST=your_supabase_host
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

═══════════════════════════════════════════════════════════

**APP FEATURES**

📝 **Question Generation** (AI tạo câu hỏi từ topic)
📊 **Study Guide** (AI phân tích điểm yếu và gợi ý)
📈 **Progress Tracking** (Theo dõi điểm số)
📱 **Responsive Design** (Dùng trên phone/tablet)

═══════════════════════════════════════════════════════════

**MODEL SPECIFICATIONS**

🤖 AI Model: gemini-2.5-pro
  - Quality Score: 100/100
  - Supports: Text analysis, long documents
  - Cost: Moderate per request

📦 Package: google-generativeai v0.8.5
🗄️  Database: PostgreSQL (Supabase) hoặc SQLite
🎨 UI: Streamlit

═══════════════════════════════════════════════════════════

Ready to go! 🚀

```bash
streamlit run app.py
```

Enjoy! 😊
