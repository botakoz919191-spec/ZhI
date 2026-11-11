import streamlit as st
import time
import tempfile
import os
from PIL import Image
import google.generativeai as genai
import cv2

st.set_page_config(
    page_title="CyberShield.kz — Цифрлық сараптама порталы",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important; }
    
    .top-navbar {
        background: #ffffff;
        border: 1px solid #cbd5e1; 
        padding: 14px 24px; 
        border-radius: 14px;
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        margin-bottom: 24px; 
        font-size: 14px; 
        color: #1e293b;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        flex-wrap: wrap; 
        gap: 12px;
    }
    .top-navbar a { color: #2563eb; text-decoration: none; font-weight: 700; }
    .phone-item {
        background: #f8fafc; padding: 6px 12px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 13px; font-weight: 600;
    }
    
    .header-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white; padding: 28px; border-radius: 16px; margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
    }
    .header-title { font-size: 30px; font-weight: 800; color: #ffffff; margin: 0; letter-spacing: -0.5px; }
    .header-subtitle { font-size: 15px; color: #bfdbfe; margin-top: 6px; font-weight: 400; }

    div.stButton > button {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%) !important;
        color: #ffffff !important; font-size: 15px !important; font-weight: 700 !important;
        padding: 12px 24px !important; border-radius: 10px !important; width: 100%;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3);
    }

    .verdict-ai { 
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b; 
        padding: 18px; border-radius: 12px; font-weight: 700; font-size: 16px; margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.1);
    }
    .verdict-real { 
        background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534; 
        padding: 18px; border-radius: 12px; font-weight: 700; font-size: 16px; margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(34, 197, 94, 0.1);
    }
    
    .report-card {
        background: #ffffff; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px;
    }

    /* Streamlit жүктеу батырмасын қазақшаландыру стилі */
    [data-testid="stFileUploader"] section {
        border: 2px dashed #2563eb !important;
        background-color: #f8fafc !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploader"] section div span {
        color: transparent !important;
    }
    [data-testid="stFileUploader"] section div span::after {
        content: "Файлдарды осында сүйреп әкеліп тастаңыз";
        color: #1e293b;
        font-weight: 600;
        font-size: 14px;
        display: block;
    }
    [data-testid="stFileUploader"] section small {
        color: #64748b !important;
    }
    [data-testid="stFileUploader"] section button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    [data-testid="stFileUploader"] section button::after {
        content: " Файлды таңдау";
    }
    [data-testid="stFileUploader"] section button span {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-navbar">
    <div>🏛️ <b>Әділет министрлігі:</b> <a href="https://www.gov.kz/memleket/entities/adilet" target="_blank">gov.kz/adilet</a></div>
    <div>
        🛡️ <b>Шұғыл байланыс:</b> 
        <span class="phone-item">📞 <b>102</b> (Полиция)</span> | 
        <span class="phone-item">☎️ <b>1414</b> (eGov)</span> | 
        <span class="phone-item">🆘 <b>111</b> (Балалар құқығы)</span> | 
        <span class="phone-item">⛑️ <b>150</b> (Дағдарыс орталығы)</span>
    </div>
</div>
""", unsafe_allow_html=True)

GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def compress_image(pil_img, max_size=(1024, 1024)):
    img_copy = pil_img.copy()
    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img_copy

def extract_frames_from_video(video_file, max_frames=5):
    frames = []
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_file.getvalue())
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames <= 0:
            cap.release()
            return frames

        step = max(1, total_frames // max_frames)
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                frames.append(pil_img)
            if len(frames) >= max_frames:
                break
        cap.release()
    except Exception as e:
        st.error(f"Қате орын алды: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return frames

def call_gemini_chat(system_prompt, chat_history, user_new_msg, pil_imgs=None):
    if not GEMINI_KEY:
        return "⚠️ Gemini API кілті (GEMINI_KEY) Streamlit Secrets бөлімінде көрсетілмеген!"

    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-3.8-flash']
    
    last_error = ""
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            
            full_prompt = f"{system_prompt}\n\n--- ЧАТ ТАРИХЫ ---\n"
            for msg in chat_history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            
            full_prompt += f"\nПАЙДАЛАНУШЫ СҰРАҒЫ: {user_new_msg}\n"
            full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Нақты криминалистикалық сараптамалық жауап бер."

            contents = [full_prompt]
            if pil_imgs:
                for img in pil_imgs:
                    contents.append(compress_image(img))

            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return "⚠️ API қатесі орын алды."

def analyze_media(pil_imgs):
    prompt = (
        "Сіз жоғары санатты цифрлық криминалист-сарапшысыз. Берілген материалға (адамдар, табиғат, заттар, пейзаж немесе видео кадрлары) ЕРЕКШЕ МҰҚИЯТТЫЛЫҚПЕН сараптама жасаңыз:\n"
        "1. БАРЛЫҚ ЭЛЕМЕНТТЕРДІ ТЕКСЕРУ: Материалдағы жарық түсу бұрышын, көлеңкелерді, текстураны, фоның үйлесімділігін және пиксельдік құрылымды жіті тексеріңіз. Бұл таза камера түсірілімі ме, әлде цифрлық сүзгілер (filters), түс коррекциясы, ретуш немесе жасанды интеллект (ЖИ) генерациясы/монтаж бар ма?\n"
        "2. ПАЙЫЗДЫҚ ШКӘЛАСЫ:\n"
        "   - Ешқандай өзгеріссіз, таза оптикалық шынайы камера түсірілімі болса — ЖИ пайызы ҚАТАҢ ТҮРДЕ 0% болуы тиіс.\n"
        "   - Егер камера сүзгілері немесе жеңіл эффекттер қолданылған болса — нақты пайызды (мысалы, 10%-45% аралығындағы өңдеу деңгейі) көрсетіңіз.\n"
        "   - Толықтай ЖИ генерациясы немесе терең монтаж болса — ЖИ пайызын 85-100% аралығында белгілеңіз.\n"
        "3. ЖАУАПТЫ МІНДЕТТІ ТҮРДЕ МЫНА ФОРМАТТА БАСТАҢЫЗ:\n"
        "SCORE: [тек сан, мысалы: 0 немесе 25 немесе 95]\n"
        "VERDICT: [Қорытынды сараптамалық вердикт]\n"
        "REASON: [Барлық бөлшектерді, жарықты, текстураны және эффекттерді терең криминалистикалық тұрғыдан талдаған толық дәлелді сипаттама]"
    )
    
    sys_msg = "Сіз цифрлық криминалист-сарапшысыз."
    res_text = call_gemini_chat(sys_msg, [], prompt, pil_imgs=pil_imgs)
    
    score = 0.0
    verdict = "Шынайы камера материалы"
    reason = res_text

    if "SCORE:" in res_text:
        try:
            score_str = res_text.split("SCORE:")[1].split("\n")[0].strip()
            score = float(''.join(c for c in score_str if c.isdigit() or c=='.'))
        except: pass
    if "VERDICT:" in res_text:
        verdict = res_text.split("VERDICT:")[1].split("\n")[0].strip()
    if "REASON:" in res_text:
        reason = res_text.split("REASON:")[1].strip()

    return score, verdict, reason

st.markdown("""
<div class="header-banner">
    <h1 class="header-title">⚖️ CyberShield.kz</h1>
    <p class="header-subtitle">Қазақстан Республикасы цифрлық сараптама порталы</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Фото тексеру", "🎥 Видео сараптау", "📝 Мәтін тексеру", "💬 Сарапшы консультациясы"])

with tab1:
    st.markdown("### 🖼️ Фотосуретті тексеру")
    uploaded_photo = st.file_uploader("Фотосуретті жүктеңіз", type=["jpg", "jpeg", "png", "webp", "heic", "bmp", "tiff"], key="photo_upload")
    
    if uploaded_photo:
        try:
            pil_img = Image.open(uploaded_photo)
            col_img1, col_img2, col_img3 = st.columns([2, 1, 2])
            with col_img2:
                st.image(pil_img, caption="Жүктелген фотосурет", use_container_width=True)

            if st.button("Тексеру", key="photo_btn"):
                with st.spinner("Фото өте мұқият тексерілуде (барлық бөлшектер мен эффекттер қаралуда)..."):
                    score, verdict, reason = analyze_media([pil_img])
                    st.session_state["photo_data"] = {"pct": score, "verdict": verdict, "reason": reason, "img": pil_img}
                    st.session_state["photo_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Сараптама нәтижесі (ЖИ/Өңдеу көрсеткіші: {score}%):**\n\n{reason}"}]
        except Exception as e:
            st.error(f"Қате орын алды: {e}")

    if "photo_data" in st.session_state:
        p_data = st.session_state["photo_data"]
        pct = p_data["pct"]
        verdict = p_data["verdict"]

        if pct >= 50.0:
            st.markdown(f'<div class="verdict-ai">⚠️ САРАПТАМА ҚОРЫТЫНДЫСЫ — ЖИ / Монтаж көрсеткіші: {pct}%<br><b>Вердикт:</b> {verdict}</div>', unsafe_allow_html=True)
        elif pct > 0.0:
            st.markdown(f'<div class="verdict-ai" style="background-color: #fefce8; border-color: #eab308; color: #854d0e;">⚡ САРАПТАМА ҚОРЫТЫНДЫСЫ — Өңдеу / Эффекттер деңгейі: {pct}%<br><b>Вердикт:</b> {verdict}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-real">✅ САРАПТАМА ҚОРЫТЫНДЫСЫ — ЖИ көрсеткіші: {pct}%<br><b>Вердикт:</b> {verdict} (Шынайылық деңгейі: 100%)</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="report-card">
            <h4 style="margin-top:0; color:#1e3a8a;">🔍 Криминалистикалық дәлелдер (Бөлшектер мен эффекттер):</h4>
            <p style="font-size: 15px; line-height: 1.6; color: #334155;">{p_data['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💬 Сарапшымен диалог")

        if "photo_chat_history" not in st.session_state:
            st.session_state["photo_chat_history"] = []

        for msg in st.session_state["photo_chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_q := st.chat_input("Сұрағыңызды жазыңыз...", key="photo_chat_input"):
            st.session_state["photo_chat_history"].append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.markdown(user_q)
            with st.chat_message("assistant"):
                with st.spinner("Жауап дайындалуда..."):
                    sys_p = "Сіз цифрлық сарапшысыз. Нақты жауап беріңіз."
                    ans = call_gemini_chat(sys_p, st.session_state["photo_chat_history"][:-1], user_q, pil_imgs=[p_data["img"]])
                    st.markdown(ans)
                    st.session_state["photo_chat_history"].append({"role": "assistant", "content": ans})

with tab2:
    st.markdown("### 🎥 Видео сараптау")
    uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov", "avi", "mkv", "webm"], key="video_upload")
    
    if uploaded_video:
        col_v1, col_v2, col_v3 = st.columns([1.5, 2, 1.5])
        with col_v2:
            st.video(uploaded_video, format="video/mp4", start_time=0)
        
        if st.button("Сараптау", key="video_btn"):
            with st.spinner("Видео кадрлары аса мұқият сарапталуда..."):
                frames = extract_frames_from_video(uploaded_video, max_frames=5)
                if frames:
                    score, verdict, reason = analyze_media(frames)
                    st.session_state["video_data"] = {"pct": score, "verdict": verdict, "reason": reason, "imgs": frames}
                    st.session_state["video_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Видео сараптамасының нәтижесі (ЖИ/Өңдеу көрсеткіші: {score}%):**\n\n{reason}"}]
                else:
                    st.error("Видеодан деректерді оқып алу мүмкін болмады.")

    if "video_data" in st.session_state:
        v_data = st.session_state["video_data"]
        pct = v_data["pct"]
        verdict = v_data["verdict"]

        if pct >= 50.0:
            st.markdown(f'<div class="verdict-ai">⚠️ САРАПТАМА ҚОРЫТЫНДЫСЫ — ЖИ / Монтаж көрсеткіші: {pct}%<br><b>Вердикт:</b> {verdict}</div>', unsafe_allow_html=True)
        elif pct > 0.0:
            st.markdown(f'<div class="verdict-ai" style="background-color: #fefce8; border-color: #eab308; color: #854d0e;">⚡ САРАПТАМА ҚОРЫТЫНДЫСЫ — Өңдеу / Эффекттер деңгейі: {pct}%<br><b>Вердикт:</b> {verdict}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-real">✅ САРАПТАМА ҚОРЫТЫНДЫСЫ — ЖИ көрсеткіші: {pct}%<br><b>Вердикт:</b> {verdict} (Шынайылық деңгейі: 100%)</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="report-card">
            <h4 style="margin-top:0; color:#1e3a8a;">🔍 Криминалистикалық дәлелдер (Бөлшектер мен эффекттер):</h4>
            <p style="font-size: 15px; line-height: 1.6; color: #334155;">{v_data['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💬 Сарапшымен диалог")

        if "video_chat_history" not in st.session_state:
            st.session_state["video_chat_history"] = []

        for msg in st.session_state["video_chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_q_v := st.chat_input("Сұрағыңызды жазыңыз...", key="video_chat_input"):
            st.session_state["video_chat_history"].append({"role": "user", "content": user_q_v})
            with st.chat_message("user"):
                st.markdown(user_q_v)
            with st.chat_message("assistant"):
                with st.spinner("Жауап дайындалуда..."):
                    sys_p = "Сіз цифрлық сарапшысыз. Нақты жауап беріңіз."
                    ans_v = call_gemini_chat(sys_p, st.session_state["video_chat_history"][:-1], user_q_v, pil_imgs=v_data.get("imgs"))
                    st.markdown(ans_v)
                    st.session_state["video_chat_history"].append({"role": "assistant", "content": ans_v})

with tab3:
    st.markdown("### 📝 Мәтін тексеру")
    text_input = st.text_area("Тексеретін мәтінді енгізіңіз:", height=150, key="text_input_area")
    if st.button("Тексеру", key="text_btn"):
        if text_input.strip():
            with st.spinner("Талдануда..."):
                ans_t = call_gemini_chat("Сіз сарапшы-редакторсыз.", [], f"Мәтінді талдап бер: {text_input}")
                st.markdown(f"""
                <div class="report-card">
                    <h4 style="margin-top:0; color:#1e3a8a;">📝 Мәтінді талдау нәтижесі:</h4>
                    <p style="font-size: 15px; line-height: 1.6; color: #334155;">{ans_t}</p>
                </div>
                """, unsafe_allow_html=True)

with tab4:
    st.markdown("### 💬 Сарапшы консультациясы")
    if "gen_chat_history" not in st.session_state:
        st.session_state["gen_chat_history"] = [{"role": "assistant", "content": "Сәлеметсіз бе! Мен цифрлық сараптама саласындағы маманмын. Сұрақтарыңызды қоя аласыз."}]

    for msg in st.session_state["gen_chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_q_gen := st.chat_input("Сұрағыңызды жазыңыз...", key="gen_chat_input"):
        st.session_state["gen_chat_history"].append({"role": "user", "content": user_q_gen})
        with st.chat_message("user"):
            st.markdown(user_q_gen)
        with st.chat_message("assistant"):
            with st.spinner("Жауап дайындалуда..."):
                ans_gen = call_gemini_chat("Сіз цифрлық сарапшысыз.", st.session_state["gen_chat_history"][:-1], user_q_gen)
                st.markdown(ans_gen)
                st.session_state["gen_chat_history"].append({"role": "assistant", "content": ans_gen})
