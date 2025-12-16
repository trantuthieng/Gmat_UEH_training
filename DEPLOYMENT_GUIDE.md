# 🚀 Hướng dẫn Deploy lên GitHub và Azure

## 📋 Checklist trước khi deploy

- [ ] Đã có tài khoản GitHub
- [ ] Đã có tài khoản Azure (Free tier OK)
- [ ] Git đã được cài đặt
- [ ] Azure CLI đã được cài đặt (optional)

---

## 🔧 Bước 1: Setup Git và Push lên GitHub

### 1.1. Khởi tạo Git repository

```bash
# Khởi tạo git trong thư mục project
git init

# Kiểm tra status
git status
```

### 1.2. Thêm remote repository

```bash
# Thêm remote (GitHub repo của bạn)
git remote add origin https://github.com/trantuthieng/Gmat_UEH_training.git

# Kiểm tra remote
git remote -v
```

### 1.3. Commit và Push code

```bash
# Add tất cả files
git add .

# Commit
git commit -m "Initial commit: GMAT Training System with mobile optimization"

# Push lên GitHub
git push -u origin main
```

**Lưu ý:** Nếu branch mặc định là `master`:
```bash
git branch -M main  # Đổi tên branch sang main
git push -u origin main
```

---

## ☁️ Bước 2: Deploy lên Azure App Service

### Option 1: Deploy qua Azure Portal (Dễ nhất) 🎯

#### 2.1. Tạo Azure App Service

1. **Đăng nhập Azure Portal**: https://portal.azure.com
2. **Tạo Resource Group**:
   - Tìm "Resource groups" → Create
   - Name: `gmat-rg`
   - Region: `Southeast Asia` hoặc `East US`
   - Review + Create

3. **Tạo App Service**:
   - Tìm "App Services" → Create
   - **Basics:**
     - Resource Group: `gmat-rg`
     - Name: `gmat-ueh-training` (unique name)
     - Publish: **Code**
     - Runtime stack: **Python 3.11**
     - Operating System: **Linux**
     - Region: `Southeast Asia`
   - **Pricing:**
     - Plan: `Basic B1` (hoặc `Free F1` cho test)
   - Review + Create

4. **Đợi deployment hoàn tất** (~2-3 phút)

#### 2.2. Configure App Settings

Vào App Service vừa tạo → **Configuration** → **Application settings**:

1. **Add New Application Setting:**
   ```
   Name: GEMINI_API_KEY
   Value: [Your API Key]
   ```

2. **Add Startup Command:**
   - Vào **Configuration** → **General settings**
   - Startup Command: 
   ```bash
   streamlit run app.py --server.port 8000 --server.address 0.0.0.0
   ```

3. **Click Save**

#### 2.3. Deploy từ GitHub

Vào App Service → **Deployment Center**:

1. **Source:** GitHub
2. **Authorize** GitHub account
3. **Organization:** Chọn username của bạn
4. **Repository:** `Gmat_UEH_training`
5. **Branch:** `main`
6. **Save**

✅ **Azure sẽ tự động build và deploy!**

---

### Option 2: Deploy qua Azure CLI (Nhanh) ⚡

#### 2.1. Cài đặt Azure CLI

**Windows:**
```powershell
# Dùng winget
winget install Microsoft.AzureCLI

# Hoặc dùng MSI installer từ:
# https://aka.ms/installazurecliwindows
```

**Mac:**
```bash
brew update && brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### 2.2. Login và Deploy

```bash
# Login vào Azure
az login

# Set subscription (nếu có nhiều subscriptions)
az account set --subscription "Your Subscription Name"

# Deploy (một lệnh duy nhất!)
az webapp up \
  --name gmat-ueh-training \
  --resource-group gmat-rg \
  --runtime "PYTHON:3.11" \
  --sku B1 \
  --location "southeastasia"
```

#### 2.3. Configure API Key

```bash
# Set environment variable
az webapp config appsettings set \
  --name gmat-ueh-training \
  --resource-group gmat-rg \
  --settings GEMINI_API_KEY="your_api_key_here"
```

#### 2.4. Configure Startup

```bash
az webapp config set \
  --name gmat-ueh-training \
  --resource-group gmat-rg \
  --startup-file "streamlit run app.py --server.port 8000 --server.address 0.0.0.0"
```

---

### Option 3: Auto Deploy với GitHub Actions (Tự động) 🤖

GitHub Actions workflow đã được tạo sẵn tại `.github/workflows/azure-deploy.yml`

#### 3.1. Lấy Publish Profile từ Azure

1. Vào Azure Portal → App Service
2. Click **Get publish profile** (download file .publishsettings)
3. Mở file và copy toàn bộ nội dung

#### 3.2. Add Secret vào GitHub

1. Vào GitHub repo: https://github.com/trantuthieng/Gmat_UEH_training
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret:**
   - Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Value: [Paste nội dung publish profile]
4. **Add secret**

#### 3.3. Trigger Deployment

Từ giờ, mỗi khi push code lên GitHub:
```bash
git add .
git commit -m "Update feature"
git push
```

→ **GitHub Actions tự động deploy lên Azure!** ✨

---

## 🔍 Bước 3: Verify Deployment

### 3.1. Kiểm tra App đang chạy

```bash
# Get app URL
az webapp show \
  --name gmat-ueh-training \
  --resource-group gmat-rg \
  --query defaultHostName -o tsv
```

Hoặc vào Azure Portal → App Service → **Overview** → **URL**

### 3.2. Test trên browser

Truy cập: `https://gmat-ueh-training.azurewebsites.net`

### 3.3. Check logs nếu có lỗi

```bash
# Stream logs
az webapp log tail \
  --name gmat-ueh-training \
  --resource-group gmat-rg
```

Hoặc vào Azure Portal → App Service → **Log stream**

---

## 📱 Bước 4: Test trên Mobile

1. Mở Safari trên iPhone
2. Truy cập: `https://gmat-ueh-training.azurewebsites.net`
3. **Add to Home Screen** để như native app!

---

## 🔄 Workflow Update Code

### Mỗi khi update code:

```bash
# 1. Sửa code trong các file
# 2. Test local
streamlit run app.py

# 3. Commit và push
git add .
git commit -m "Describe your changes"
git push

# 4. GitHub Actions tự động deploy
# 5. Đợi ~2-3 phút
# 6. Refresh browser để thấy changes
```

---

## 🐛 Troubleshooting

### Lỗi: "Application Error"

**Giải pháp:**
1. Check logs trong Azure Portal
2. Verify `requirements.txt` có đầy đủ dependencies
3. Check startup command đúng chưa

### Lỗi: "Module not found"

**Giải pháp:**
```bash
# Update requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### Lỗi: "API Key not found"

**Giải pháp:**
```bash
# Set environment variable
az webapp config appsettings set \
  --name gmat-ueh-training \
  --resource-group gmat-rg \
  --settings GEMINI_API_KEY="your_key"
```

### App chậm/timeout

**Giải pháp:**
1. Upgrade plan từ F1 (Free) lên B1 (Basic)
2. Enable Application Insights để monitor
3. Check database cache đang hoạt động

---

## 💰 Cost Estimation

### Free Tier (F1)
- **Cost:** $0/month
- **Limitations:** 
  - 60 CPU minutes/day
  - 1GB RAM
  - App sleep sau 20 phút idle

### Basic Tier (B1)
- **Cost:** ~$13/month (~300,000 VNĐ)
- **Benefits:**
  - 100 ACU
  - 1.75GB RAM
  - Always on
  - Custom domain
  - SSL certificate

### Khuyến nghị:
- **Development/Testing:** Free F1
- **Production:** Basic B1 trở lên

---

## 📊 Monitoring

### Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app gmat-insights \
  --location southeastasia \
  --resource-group gmat-rg

# Link to App Service
az webapp config appsettings set \
  --name gmat-ueh-training \
  --resource-group gmat-rg \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="[Connection String]"
```

### Metrics to Monitor:
- Response time
- CPU/Memory usage
- Request count
- Error rate

---

## 🎯 Next Steps

- [ ] Setup custom domain (optional)
- [ ] Enable SSL certificate
- [ ] Configure Azure CDN for static files
- [ ] Setup staging environment
- [ ] Configure auto-scaling
- [ ] Setup alerts for errors/downtime

---

## 📞 Support

### Azure Support:
- **Portal:** https://portal.azure.com
- **CLI Help:** `az webapp --help`
- **Documentation:** https://docs.microsoft.com/azure/app-service/

### Project Issues:
- **GitHub Issues:** https://github.com/trantuthieng/Gmat_UEH_training/issues

---

## ✅ Quick Commands Reference

```bash
# Login Azure
az login

# Deploy app
az webapp up --name gmat-ueh-training --resource-group gmat-rg --runtime "PYTHON:3.11"

# View logs
az webapp log tail --name gmat-ueh-training --resource-group gmat-rg

# Restart app
az webapp restart --name gmat-ueh-training --resource-group gmat-rg

# Delete app (cleanup)
az webapp delete --name gmat-ueh-training --resource-group gmat-rg

# Delete resource group (cleanup all)
az group delete --name gmat-rg --yes
```

---

**🎉 Chúc bạn deploy thành công!**
