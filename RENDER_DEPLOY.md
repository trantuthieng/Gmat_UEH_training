# Deploy GMAT App lên Render

## Bước 1: Đăng ký Render
1. Truy cập: https://render.com
2. Sign up bằng GitHub account
3. Authorize Render truy cập GitHub repos

## Bước 2: Deploy từ Dashboard
1. Click **"New +"** → **"Web Service"**
2. Chọn repository: `trantuthieng/Gmat_UEH_training`
3. Render sẽ tự động detect file `render.yaml`
4. Click **"Apply"**

## Bước 3: Thêm API Key
1. Trong Render dashboard, vào service vừa tạo
2. Tab **"Environment"** → **"Environment Variables"**
3. Thêm biến:
   - Key: `GEMINI_API_KEY`
   - Value: `your_gemini_api_key_here`
4. Click **"Save Changes"**

## Bước 4: Deploy
1. Render sẽ tự động build và deploy
2. Đợi 3-5 phút
3. Link app sẽ có dạng: `https://gmat-ueh-training.onrender.com`

## Auto-Deploy
- Mỗi lần push code lên GitHub (branch `main`), Render sẽ tự động deploy lại
- Không cần setup thêm gì

## Free Tier Limitations
- 750 giờ/tháng (đủ dùng)
- App sẽ "ngủ" sau 15 phút không dùng
- Wake up lần đầu mất ~30 giây
- Performance tốt hơn Streamlit Cloud

## Troubleshooting
Nếu deploy fail, check logs trong Render dashboard:
- Tab **"Logs"** để xem lỗi
- Tab **"Events"** để xem deploy history
