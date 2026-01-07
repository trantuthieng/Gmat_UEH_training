# 📝 Hệ thống Thi Thử GMAT

Ứng dụng web tương tác để tạo và giải bài thi thử GMAT bằng AI, hỗ trợ tiếng Việt.

## ✨ Tính năng chính

- **Tạo đề thi thử** - Sinh ra đề thi GMAT ngẫu nhiên sử dụng Google Gemini AI
- **Giải thích chi tiết** - Cung cấp giải thích cho từng câu hỏi
- **Lưu trữ đối tượng** - Lưu câu hỏi vào database PostgreSQL/Supabase
- **Giao diện di động** - Tối ưu cho iPhone, iPad và các thiết bị khác
- **Ôn tập thông minh** - Hệ thống gợi ý câu hỏi dựa trên kết quả học tập
- **Hỗ trợ PDF** - Nhập dữ liệu từ tệp PDF

## 🛠️ Công nghệ sử dụng

- **Backend**: Python
- **Frontend**: Streamlit
- **AI Model**: Google Gemini API
- **Database**: PostgreSQL/Supabase
- **Containerization**: Docker
- **Deployment**: Azure Web App

## 📋 Yêu cầu hệ thống

- Python 3.8+
- pip (Python package manager)
- Khóa API Google Gemini
- Database PostgreSQL (hoặc Supabase)

## 🚀 Cài đặt và chạy

### 1. Clone repository và cài đặt dependencies

```bash
cd c:\Users\trant\OneDrive\Project\gmat
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường

Tạo tệp `.env` hoặc sử dụng Streamlit secrets:

```env
GEMINI_API_KEY=your_google_gemini_api_key
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
DB_PORT=5432
```

### 3. Chạy ứng dụng Streamlit

```bash
streamlit run app.py
```

Ứng dụng sẽ mở tại `http://localhost:8501`

### 4. Chạy bằng Docker

```bash
docker build -t gmat-app .
docker run -p 8501:8501 --env-file .env gmat-app
```

## 📁 Cấu trúc dự án

```
gmat/
├── app.py                        # Ứng dụng Streamlit chính
├── ai_logic.py                   # Logic sinh đề và giải thích AI
├── study_guide.py                # Chức năng ôn tập thông minh
├── db.py                         # Kết nối và truy vấn database
├── ingest_pdf.py                 # Nhập dữ liệu từ PDF
├── requirements.txt              # Dependencies Python
├── Dockerfile                    # Cấu hình Docker
├── startup.sh                    # Script khởi động
├── azure-webapp-config.json      # Cấu hình Azure
├── seed_data.json                # Dữ liệu mẫu ban đầu
└── test_*.py                     # Các tệp test
```

## 🧪 Chạy tests

```bash
# Test kết nối database
python test_db_connection.py

# Test model Gemini
python test_gemini_model.py

# Test tính năng ôn tập
python test_study_guide_fix.py

# Kiểm tra JSON validation
python validate_json.py
```

## 🔑 Biến môi trường

| Biến | Mô tả | Bắt buộc |
|------|-------|---------|
| `GEMINI_API_KEY` | Khóa API Google Gemini | ✅ |
| `DB_HOST` | Địa chỉ host database | ✅ |
| `DB_USER` | Tên người dùng database | ✅ |
| `DB_PASSWORD` | Mật khẩu database | ✅ |
| `DB_NAME` | Tên database | ✅ |
| `DB_PORT` | Cổng database (mặc định: 5432) | ❌ |

## 🌐 Triển khai trên Azure

Ứng dụng được cấu hình để triển khai trên Azure Web App. Xem `azure-webapp-config.json` để biết chi tiết.

### Các bước triển khai:

1. Tạo Azure Web App
2. Cấu hình connection strings trong Application Settings
3. Đặt Startup Command thành `./startup.sh`
4. Deploy từ GitHub hoặc Container Registry

## 📱 Tính năng di động

- ✅ Giao diện responsive trên mọi kích thước màn hình
- ✅ Tối ưu cho Safari trên iOS
- ✅ Hỗ trợ dark mode
- ✅ Tương thích với home screen webapp

## 🐛 Khắc phục sự cố

### Lỗi "KHÔNG THỂ KẾT NỐI DATABASE"

- Kiểm tra biến môi trường trong Streamlit Secrets
- Xác minh thông tin đăng nhập database
- Đảm bảo database server đang chạy
- Kiểm tra firewall rules nếu sử dụng cloud database

### Lỗi Import module

- Cài đặt lại dependencies: `pip install -r requirements.txt --upgrade`
- Xóa thư mục `__pycache__`: `rm -r __pycache__`
- Kiểm tra phiên bản Python: `python --version`

### API Gemini không hoạt động

- Xác minh `GEMINI_API_KEY` hợp lệ
- Kiểm tra quota API của Google
- Xem logs để biết thêm chi tiết

## 📚 Tài liệu thêm

- [Streamlit Documentation](https://docs.streamlit.io)
- [Google Gemini API](https://ai.google.dev)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
- [Docker Documentation](https://docs.docker.com)

## 📄 License

Dự án này không có giấy phép được chỉ định. Liên hệ tác giả để biết chi tiết.

## 👤 Tác giả

Tran T.

## 🤝 Đóng góp

Các đóng góp được chào đón! Hãy:

1. Fork repository
2. Tạo branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📞 Liên hệ

Nếu có câu hỏi hoặc cần hỗ trợ, vui lòng liên hệ tác giả.

---

**Chúc bạn học tập hiệu quả! 🎓**
