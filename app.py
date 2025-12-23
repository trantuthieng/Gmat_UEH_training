import streamlit as st
import json
import time
import random

# --- CẤU HÌNH TRANG (Phải để đầu tiên) ---
st.set_page_config(
    page_title="Hệ thống thi thử GMAT", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="auto"
)

# --- IMPORT CÁC MODULE KHÁC ---
# Đặt trong try-except để bắt lỗi thiếu thư viện hoặc lỗi code
try:
    from ai_logic import generate_full_exam
    from db import init_db, get_cached_questions, save_questions
except Exception as e:
    st.error(f"❌ Lỗi Import module: {e}")
    st.stop()

# --- KHỞI TẠO DB AN TOÀN ---
# Đây là đoạn quan trọng nhất giúp app không bị connection refused
try:
    init_db()
except Exception as e:
    st.error(f"⚠️ KHÔNG THỂ KẾT NỐI DATABASE (SUPABASE)")
    st.error(f"Chi tiết lỗi: {e}")
    st.info("👉 Hãy kiểm tra lại Streamlit Secrets (Password, Host, User...)")
    # Không gọi st.stop() để app vẫn hiện giao diện (dù không lưu được DB)

# Mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile-first responsive design for iPhone 15 Pro and other devices */
    @media (max-width: 768px) {
        /* Main content adjustments */
        .main .block-container {
            padding: max(1rem, env(safe-area-inset-top)) 1.25rem max(1.25rem, env(safe-area-inset-bottom)) 1.25rem !important;
            max-width: 100% !important;
        }
        
        /* Prevent horizontal scroll */
        body {
            overflow-x: hidden !important;
        }

        /* Ngăn sidebar đè lên nội dung khi mở trên mobile */
        [data-testid="stSidebar"] {
            max-width: 80vw !important;
        }
        
        /* Title adjustments */
        h1 {
            font-size: 1.5rem !important;
            line-height: 1.3 !important;
            margin-bottom: 1rem !important;
            word-wrap: break-word !important;
        }
        
        h2 {
            font-size: 1.25rem !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
            font-weight: 600 !important;
        }
        
        /* Button optimizations - larger touch targets */
        .stButton > button {
            width: 100% !important;
            padding: 1rem 1.25rem !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            margin: 0.75rem 0 !important;
            border-radius: 12px !important;
            min-height: 48px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        
        /* Radio buttons - larger touch areas */
        .stRadio > div {
            font-size: 1rem !important;
            gap: 0.5rem !important;
        }
        
        .stRadio > div > label {
            padding: 1rem 1rem !important;
            margin: 0.5rem 0 !important;
            border-radius: 12px !important;
            background-color: rgba(240, 242, 246, 0.15) !important;
            border: 2px solid rgba(49, 51, 63, 0.2) !important;
            min-height: 52px !important;
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            box-sizing: border-box !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        
        .stRadio > div > label:hover {
            background-color: rgba(240, 242, 246, 0.25) !important;
            border-color: rgba(49, 51, 63, 0.4) !important;
        }
        
        /* Timer display */
        #timer {
            font-size: 2.5rem !important;
            padding: 1rem !important;
        }
        
        /* Sidebar optimizations */
        [data-testid="stSidebar"] {
            min-width: 280px !important;
        }
        
        /* Questions - better readability */
        .stMarkdown p {
            font-size: 1rem !important;
            line-height: 1.6 !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        
        /* Question containers */
        .element-container {
            margin-bottom: 1rem !important;
        }
        
        /* Images - responsive */
        img {
            max-width: 100% !important;
            height: auto !important;
            border-radius: 8px !important;
        }
        
        /* Metrics - stack vertically */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
        }
        
        /* Metric container spacing */
        [data-testid="metric-container"] {
            padding: 0.75rem !important;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            height: 8px !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-size: 1rem !important;
            padding: 1rem !important;
        }
        
        /* Divider spacing */
        hr {
            margin: 1.5rem 0 !important;
        }
        
        /* Info/Warning boxes */
        .stAlert {
            font-size: 0.95rem !important;
            padding: 1rem !important;
        }
        
        /* Column layout - stack on mobile */
        [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
        }
    }
    
    /* Medium screens (tablets) */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding: 2rem 1rem !important;
        }
        
        .stButton > button {
            min-height: 44px !important;
        }
    }
    
    /* Touch-friendly enhancements for all screen sizes */
    .stButton > button:active {
        transform: scale(0.98);
        transition: transform 0.1s;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Better focus states for accessibility */
    button:focus, input:focus {
        outline: 2px solid #1f77b4 !important;
        outline-offset: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HÀM HỖ TRỢ ---
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def load_seed_data():
    try:
        with open('seed_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{int(mins):02d}:{int(secs):02d}"

# --- KHỞI TẠO STATE ---
if 'exam_state' not in st.session_state:
    st.session_state.exam_state = "READY" # READY, GENERATED, RUNNING, FINISHED
if 'exam_questions' not in st.session_state:
    st.session_state.exam_questions = []
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'end_time' not in st.session_state:
    st.session_state.end_time = 0
if 'exam_mode' not in st.session_state:
    st.session_state.exam_mode = None

# --- GIAO DIỆN CHÍNH ---
st.title("📝 Hệ thống Thi thử GMAT")

# --- KẾT NỐI DB AN TOÀN ---
try:
    init_db()
except Exception as e:
    st.error(f"⚠️ Không thể kết nối Database: {e}")
    st.info("Kiểm tra lại Streamlit Secrets (DB_PASSWORD, DB_HOST...)")

# 1. MÀN HÌNH CHỜ (READY)
if st.session_state.exam_state == "READY":
    st.markdown("""
    ### Chào mừng bạn đến với kỳ thi mô phỏng
    Hệ thống sẽ sử dụng AI để tạo ra một bộ đề thi mới hoàn toàn dựa trên cấu trúc đề gốc.
    
    **Cấu trúc đề thi:**
    - **Đề chính thức:** 30 câu - 60 phút
    - **Thang điểm:** Thang 10 điểm (tính theo tỷ lệ câu đúng)
    """)
    
# Hàm hiển thị một câu hỏi kèm hình nếu có
@st.cache_data(show_spinner=False)
def check_visual_keywords(text):
    visual_keywords = ['hình', 'shape', 'ảnh', 'diagram', 'figure', 'biểu đồ']
    return any(k in text.lower() for k in visual_keywords)

def render_question(q, idx):
    # Mobile-optimized question display
    st.markdown(f"### Câu {idx+1}")
    st.markdown(q.get('question', 'Câu hỏi'))
    
    # Hiển thị hình nếu có
    image_url = q.get('image_url')
    if image_url:
        st.image(image_url, use_container_width=True, caption=f"Hình minh họa câu {idx+1}")
    else:
        # Nếu câu hỏi có vẻ là câu hình nhưng thiếu hình, cảnh báo nhẹ
        text = q.get('question', '')
        if check_visual_keywords(text):
            st.info("⚠️ Câu hỏi yêu cầu hình ảnh nhưng không kèm hình.")
# Khu vực khởi tạo đề thi
if st.session_state.exam_state == "READY":
    exam_mode = "Đề chính thức (30 câu - 60 phút)"
    if st.button("🚀 KHỞI TẠO ĐỀ THI", type="primary"):
        seeds = load_seed_data()
        if not seeds:
            st.error("Chưa có dữ liệu gốc! Hãy chạy file ingest_pdf.py trước.")
        else:
            num_questions = 30
            st.session_state.exam_mode = exam_mode
            progress_bar = st.progress(0)
            status_text = st.empty()
            def update_bar(percent):
                progress_bar.progress(percent)
                status_text.text(f"Đang AI khởi tạo đề thi... {int(percent*100)}%")
            with st.spinner("⏳ Đang tạo đề thi..."):
                # SỬA LẠI CÁCH GỌI HÀM CHO RÕ RÀNG
                generated_exam = generate_full_exam(
                    seed_data=seeds, 
                    num_questions=num_questions, 
                    progress_callback=update_bar
                )
            if not generated_exam:
                st.warning("⚠️ API quota hết. Dùng ngân hàng câu hỏi đã lưu để tạo đề...")
                cached = get_cached_questions(num_questions)
                if cached:
                    generated_exam = cached
                else:
                    st.info("📦 Ngân hàng câu hỏi trống. Sử dụng seed_data tạm thời.")
                    generated_exam = random.choices(seeds, k=num_questions)
                    formatted_exam = []
                    for i, seed in enumerate(generated_exam):
                        formatted_exam.append({
                            'id': seed.get('id', i),
                            'type': 'general',
                            'question': seed['content'],
                            'options': ['A. Chưa biết', 'B. Chưa biết', 'C. Chưa biết', 'D. Chưa biết'],
                            'correct_answer': 'A. Chưa biết',
                            'explanation': f"Chủ đề: {seed.get('topic', 'Chưa xác định')}"
                        })
                    generated_exam = formatted_exam
            st.session_state.exam_questions = generated_exam
            st.session_state.exam_state = "GENERATED"
            progress_bar.empty()
            status_text.empty()
            st.rerun()

# 1.5. MÀN HÌNH ĐỀ ĐÃ TẠO - CHỜ BẮT ĐẦU (GENERATED)
elif st.session_state.exam_state == "GENERATED":
    st.success("✅ Đề thi đã được khởi tạo thành công!")
    
    questions = st.session_state.exam_questions
    math_count = len([q for q in questions if q['type'] == 'math'])
    gen_count = len([q for q in questions if q['type'] == 'general'])
    
    # Tính thời gian dựa trên chế độ
    exam_time = 60
    
    st.markdown(f"""
    ### 📋 Thông tin đề thi
    - **Chế độ:** {st.session_state.exam_mode}
    - **Tổng số câu:** {len(questions)} câu
    - **Thời gian:** {exam_time} phút
    
    ---
    
    ### 🔒 Nội dung đề thi đang được che
    Nhấn nút bên dưới để bắt đầu làm bài. Đồng hồ đếm ngược sẽ chạy ngay khi bạn bắt đầu.
    """)
    
    # Mobile-friendly button layout
    if st.button("🎯 BẮT ĐẦU LÀM BÀI", type="primary", use_container_width=True):
        # Tính thời gian dựa trên chế độ
        exam_duration = 60  # 60 phút
        st.session_state.start_time = time.time()
        st.session_state.end_time = st.session_state.start_time + (exam_duration * 60)
        st.session_state.exam_state = "RUNNING"
        st.session_state.user_answers = {}
        st.rerun()
    
    if st.button("🔄 Tạo đề thi mới"):
        st.session_state.exam_state = "READY"
        st.session_state.exam_questions = []
        st.rerun()

# 2. MÀN HÌNH LÀM BÀI (RUNNING)
elif st.session_state.exam_state == "RUNNING":
    
    # --- LOGIC KIỂM TRA THỜI GIAN (SERVER SIDE) ---
    # Tính toán chính xác thời gian còn lại dựa trên giờ hệ thống
    remaining_seconds = st.session_state.end_time - time.time()
    
    # Nếu hết giờ trên server -> Thu bài ngay lập tức
    if remaining_seconds <= 0:
        st.error("⏰ ĐÃ HẾT GIỜ LÀM BÀI!")
        st.session_state.exam_state = "FINISHED"
        st.rerun()

    # --- SIDEBAR: ĐỒNG HỒ ĐẾM NGƯỢC (CLIENT SIDE - JAVASCRIPT) ---
    with st.sidebar:
        st.header("⏳ Thời gian còn lại")
        
        # Chuyển đổi thời gian kết thúc sang milliseconds cho JS
        end_time_ms = st.session_state.end_time * 1000
        
        # HTML & JS cho đồng hồ
        # Script này chạy độc lập trên trình duyệt, không làm phiền server
        timer_html = f"""
        <div style="
            text-align: center; 
            padding: 15px; 
            background-color: #f0f2f6; 
            border: 2px solid #1f77b4; 
            border-radius: 10px; 
            margin-bottom: 20px;">
            <div style="font-size: 1.2rem; color: #555;">Còn lại</div>
            <div id="countdown" style="
                font-size: 2.8rem; 
                font-weight: bold; 
                color: #1f77b4; 
                font-family: monospace;">
                --:--
            </div>
        </div>
        
        <script>
            // Lấy thời gian đích từ Python
            var dest = {end_time_ms};
            
            var x = setInterval(function() {{
                var now = new Date().getTime();
                var diff = dest - now;
                
                // Tính toán phút và giây
                var m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                var s = Math.floor((diff % (1000 * 60)) / 1000);
                
                // Thêm số 0 ở đầu nếu < 10
                m = m < 10 ? "0" + m : m;
                s = s < 10 ? "0" + s : s;
                
                var elem = document.getElementById("countdown");
                
                if (diff > 0) {{
                    if(elem) {{
                        elem.innerHTML = m + ":" + s;
                        // Đổi màu khi còn dưới 5 phút (300000ms)
                        if (diff < 300000) {{
                            elem.style.color = "#ff4b4b"; // Màu đỏ báo động
                        }}
                    }}
                }} else {{
                    clearInterval(x);
                    if(elem) {{
                        elem.innerHTML = "00:00";
                        elem.style.color = "red";
                    }}
                    // Tự động reload trang khi hết giờ để Server xử lý nộp bài
                    // window.parent.location.reload(); 
                }}
            }}, 1000);
        </script>
        """
        
        # Render đồng hồ (chiều cao cố định để không bị nhảy layout)
        st.components.v1.html(timer_html, height=150)
        
        st.info("⚠️ Hệ thống sẽ tự động thu bài khi đồng hồ về 00:00.")

    # --- KHU VỰC LÀM BÀI (DÙNG FORM ĐỂ KHÔNG BỊ RELOAD KHI CHỌN) ---
    st.subheader("📝 BÀI LÀM")
    
    questions = st.session_state.exam_questions
    if not questions:
        st.error("❌ Không có câu hỏi! Vui lòng tạo đề thi lại.")
    else:
        # Progress indicator
        answered = len(st.session_state.user_answers)
        total_questions = len(questions)
        st.progress(answered / total_questions if total_questions > 0 else 0)
        st.caption(f"Đã trả lời: {answered}/{total_questions} câu")
        
        # --- BẮT ĐẦU FORM ---
        # Mọi thao tác trong khối này sẽ KHÔNG gửi về server cho đến khi bấm Submit
        with st.form(key='exam_form'):
            for idx, q in enumerate(questions):
                # Container for better mobile spacing
                with st.container():
                    st.markdown(f"**Câu {idx+1}:** {q['question']}")
                    
                    if q.get('image_url'):
                        st.image(q.get('image_url'), use_container_width=True)
                    
                    options = q.get('options', [])
                    
                    # Widget Radio: Key unique giúp Streamlit tự nhớ trạng thái
                    st.radio(
                        "Chọn đáp án:",
                        options,
                        key=f"radio_{idx}", 
                        index=None,
                        label_visibility="visible"
                    )
                    st.divider()
            
            # --- NÚT NỘP BÀI (Duy nhất) ---
            # Khi bấm nút này, toàn bộ đáp án mới được gửi đi 1 lần
            submit_button = st.form_submit_button("📤 NỘP BÀI THI", type="primary", use_container_width=True)
            
            if submit_button:
                # 1. Lưu đáp án từ các widget vào session_state chính
                for i in range(len(questions)):
                    answer = st.session_state.get(f"radio_{i}")
                    if answer:
                        st.session_state.user_answers[f"q_{i}"] = answer
                
                # 2. Kết thúc bài thi
                st.session_state.exam_state = "FINISHED"
                st.rerun()

# 3. MÀN HÌNH KẾT QUẢ (FINISHED)
elif st.session_state.exam_state == "FINISHED":
    st.balloons()
    st.header("📊 KẾT QUẢ BÀI THI")
    
    questions = st.session_state.exam_questions
    answers = st.session_state.user_answers
    
    # --- Logic Chấm điểm (Thang 10) ---
    # Điểm = (Số câu đúng / Tổng số câu) * 10
    if 'score_calculated' not in st.session_state:
        correct_count = 0
        wrong_count = 0
        unanswered_count = 0
        details = []
        
        for idx, q in enumerate(questions):
            user_choice = answers.get(f"q_{idx}")
            is_correct = False
            
            if user_choice:
                # So sánh string (cần xử lý chuỗi cẩn thận vì AI sinh ra có thể khác format)
                # Lấy ký tự đầu (A, B, C, D) để so sánh cho chắc chắn
                if user_choice.split('.')[0] == q['correct_answer'].split('.')[0]:
                    correct_count += 1
                    is_correct = True
                else:
                    wrong_count += 1
            else:
                unanswered_count += 1
            
            details.append({
                "question": q['question'],
                "user_ans": user_choice if user_choice else "Không trả lời",
                "correct_ans": q['correct_answer'],
                "explanation": q['explanation'],
                "is_correct": is_correct
            })
        
        # Tính điểm theo thang 10
        total_questions = len(questions)
        score = (correct_count / total_questions * 10) if total_questions > 0 else 0
        
        # Cache results to avoid recalculation
        st.session_state.score_calculated = {
            'score': score,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'unanswered_count': unanswered_count,
            'details': details
        }
    else:
        # Use cached results
        cached = st.session_state.score_calculated
        score = cached['score']
        correct_count = cached['correct_count']
        wrong_count = cached['wrong_count']
        unanswered_count = cached['unanswered_count']
        details = cached['details']
    
    # Hiển thị Dashboard - responsive columns
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("TỔNG ĐIỂM", f"{score:.2f}/10", delta=None, help="Thang điểm 10")
    with col2:
        st.metric("Số câu đúng", f"{correct_count}/{len(questions)}", delta=None)
    with col3:
        st.metric("Số câu sai", f"{wrong_count}", delta=None)
    
    st.divider()
    
    # Chi tiết lời giải
    with st.expander("🔍 XEM CHI TIẾT LỜI GIẢI VÀ ĐÁP ÁN"):
        for idx, d in enumerate(details):
            color = "green" if d['is_correct'] else "red"
            st.markdown(f"**Câu {idx+1}:** :{color}[{d['question']}]")
            st.write(f"Bạn chọn: {d['user_ans']} | Đáp án: {d['correct_ans']}")
            st.info(f"Giải thích: {d['explanation']}")
            st.markdown("---")
            
    if st.button("🔄 Làm bài thi mới"):
        st.session_state.exam_state = "READY"
        if 'score_calculated' in st.session_state:
            del st.session_state.score_calculated
        st.rerun()