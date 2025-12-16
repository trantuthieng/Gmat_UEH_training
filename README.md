# 🎓 GMAT UEH Training System

Hệ thống thi thử GMAT được tối ưu hóa cho tuyển sinh Thạc sĩ - Đại học Kinh tế TP.HCM

## ✨ Features

- 🤖 **AI-Powered**: Tự động tạo đề thi mới bằng Gemini AI
- 📱 **Mobile Optimized**: Hiển thị hoàn hảo trên iPhone 15 Pro và các thiết bị mobile
- ⚡ **High Performance**: Xử lý song song, cache thông minh, nhanh hơn 70%
- 💾 **Smart Caching**: Database optimization với indexing và batch operations
- ⏱️ **Real-time Timer**: Đồng hồ đếm ngược JavaScript
- 📊 **Instant Results**: Chấm điểm tự động với giải thích chi tiết

## 🚀 Demo

**Live Demo:** [https://gmat-ueh-training.azurewebsites.net](https://gmat-ueh-training.azurewebsites.net)

## 📱 Mobile Support

Ứng dụng được tối ưu đặc biệt cho:
- ✅ iPhone 15 Pro / Pro Max
- ✅ iPhone SE và các dòng iPhone khác
- ✅ Android devices (mọi kích thước)
- ✅ iPad và tablets
- ✅ Desktop browsers

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI Engine**: Google Gemini AI (Gemma 3 12B)
- **Database**: SQLite với optimization
- **Deployment**: Azure App Service
- **CI/CD**: GitHub Actions

## 📦 Installation

### Local Development

```bash
# Clone repository
git clone https://github.com/trantuthieng/Gmat_UEH_training.git
cd Gmat_UEH_training

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

### Test on Mobile

```bash
# Run with network access
streamlit run app.py --server.address 0.0.0.0

# Access from phone (same WiFi)
http://[YOUR-IP]:8501
```

## 🔧 Configuration

### API Key

Tạo file `.env`:
```env
GEMINI_API_KEY=your_api_key_here
```

### Streamlit Config

File `.streamlit/config.toml` đã được cấu hình sẵn cho production.

## 📊 Performance

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Exam Generation | 60-90s | 15-25s | **70% faster** |
| Cache Load | 2-3s | < 1s | **200% faster** |
| DB Operations | 5-8s | < 1s | **500% faster** |
| Mobile Load | N/A | < 1s | **Optimized** |

## 🎯 Features Roadmap

- [x] AI question generation
- [x] Concurrent API calls
- [x] Database optimization
- [x] Mobile responsive design
- [x] Cache system
- [x] Progress tracking
- [x] Real-time timer
- [x] Azure deployment
- [ ] User authentication
- [ ] Result history
- [ ] Advanced analytics
- [ ] Multi-language support

## 📝 Documentation

- [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - Performance optimizations
- [MOBILE_OPTIMIZATION.md](MOBILE_OPTIMIZATION.md) - Mobile design details
- [IPHONE_TESTING.md](IPHONE_TESTING.md) - iPhone testing guide
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - User guide

## 🧪 Testing

```bash
# Test performance optimizations
python test_optimizations.py

# Test mobile responsiveness
python test_mobile.py
```

## 🚀 Deployment

### Azure App Service

Ứng dụng tự động deploy qua GitHub Actions khi push lên `main` branch.

**Requirements:**
- Azure App Service (Python 3.11)
- GitHub Secrets configured:
  - `AZURE_WEBAPP_PUBLISH_PROFILE`

### Manual Deployment

```bash
# Login to Azure
az login

# Create resource group
az group create --name gmat-rg --location eastus

# Create App Service plan
az appservice plan create --name gmat-plan --resource-group gmat-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group gmat-rg --plan gmat-plan --name gmat-ueh-training --runtime "PYTHON:3.11"

# Deploy
az webapp up --name gmat-ueh-training --resource-group gmat-rg
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Tran Tu Thieng**
- GitHub: [@trantuthieng](https://github.com/trantuthieng)

## 🙏 Acknowledgments

- Đại học Kinh tế TP.HCM (UEH)
- Google Gemini AI
- Streamlit Community

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ for UEH Master's Program**
