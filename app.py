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
    .stApp { background: linear-gradient(135deg, #edf5ff 0%, #dbeafe 50%, #eff6ff 100%) !important; }
    .top-navbar {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 2px solid #cbd5e1; padding: 12px 20px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 13px; color: #1e293b;
        flex-wrap: wrap; gap: 10px;
    }
    .top-navbar a { color: #1d4ed8; text-decoration: none; font-weight: bold; }
    .phone-item {
        background: #f1f5f9; padding: 4px 8px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 12px;
    }
    .header-banner {
        background: linear-gradient(135deg, #0f2b5c 0%, #1e40af 60%, #1d4ed8 100%);
        color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; border-bottom: 5px solid #d97706;
    }
    .header-title { font-size: 26px; font-weight: 800; color: #ffffff; margin: 0; }
    .header-subtitle { font-size: 14px; color: #e0f2fe; margin-top: 4px; }
    div.stButton > button {
        background: linear-gradient(90deg, #0f2b5c 0%, #1e40af 100%) !important;
        color: #ffffff !important; font-size: 15px !important; font-weight: bold !important;
        padding: 10px 20px !important; border-radius: 8px !important; width: 100%;
    }
    .verdict-ai { background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b; padding: 14px; border-radius: 10px; font-weight: bold; margin-bottom: 12px; }
    .verdict-real { background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534; padding: 14px; border-radius: 10px; font-weight: bold; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# Жоғарғы панель: Сенім телефондары мен мекемелер
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
            full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Шаш сызықтарына, бетке, көзге, дене пропорцияларына, киім текстурасына, фонға, жарық түсуіне және бет алмастыру (face-swap/deepfake) іздеріне мұқият үңіліп, нақты пайыздармен және дәлелдермен жауап бер."

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

    return f"⚠️ API қатесі орын алды: {last_error}."

def analyze_media(pil_imgs):
    prompt = (
        "Сіз жоғары санатты цифрлық криминалист-сарапшысыз. Берілген материалдарға (фото/видео кадрларына) ең жоғары мұқияттылықпен сараптама жасаңыз:\n"
        "1. Шаш сызықтары мен түйісетін орындарын (маңдай, желке, фонмен шектесетін жерлері), бет-әлпетті, мимиканы, тері текстурасын, көздің жарық шағылуын (зрачок рефлексі), дене пропорцияларын, киімнің тігістері мен текстурасын және фонның шынайылығын қатаң тексеріңіз. Біреудің бетін немесе денесін басқа біреуге жапсырған (face-swap / deepfake) немесе ЖИ арқылы жасалған/өңделген іздері бар ма?\n"
        "2. ЖИ арқылы өңделу немесе монтаждалу көрсеткішін 0-100% аралығындағы нақты SCORE пайызымен көрсетіңіз.\n"
        "3. Материалдың қай жерінде ауытқу бар екенін (мысалы: киім текстурасының бұрмалануы, шаштың шетіндегі артефактілер, фонның біркелкі еместігі) дөп басып түсіндіріңіз.\n\n"
        "МІНДЕТТІ ФОРМАТ:\n"
        "SCORE: [0-100 аралығындағы пайыз]\n"
        "VERDICT: [Қорытынды сараптамалық вердикт]\n"
        "REASON: [Шаш, бет, көз, дене, киім және фон бойынша жасалған егжей-тегжейлі криминалистикалық сараптама сипаттамасы]"
    )
    
    sys_msg = "Сіз жоғары санатты цифрлық криминалистсіз."
    res_text = call_gemini_chat(sys_msg, [], prompt, pil_imgs=pil_imgs)
    
    score = 15.0
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

# Вкладкалар нақты бөлінді
tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Фото сараптамасы", "🎥 Видео сараптамасы", "📝 Мәтін сараптамасы", "💬 Сарапшы консультациясы"])

with tab1:
    st.markdown("### 🖼️ Фотосуретті тексеру және сараптау")
    uploaded_photo = st.file_uploader("Фотосуретті жүктеңіз", type=["jpg", "jpeg", "png", "webp", "heic", "bmp", "tiff"], key="photo_upload")
    
    if uploaded_photo:
        try:
            pil_img = Image.open(uploaded_photo)
            st.image(pil_img, caption="Жүктелген фотосурет", width=300)

            if st.button("Тексеру", key="photo_btn"):
                with st.spinner("Фотосуреттің шашы, беті, көзі, денесі, киімі мен фоны мұқият тексерілуде..."):
                    score, verdict, reason = analyze_media([pil_img])
                    st.session_state["photo_data"] = {"pct": score, "verdict": verdict, "reason": reason, "img": pil_img}
                    st.session_state["photo_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Сараптама нәтижесі:**\n\n{reason}"}]
        except Exception as e:
            st.error(f"Қате орын алды: {e}")

    if "photo_data" in st.session_state:
        p_data = st.session_state["photo_data"]
        pct = p_data["pct"]
        verdict = p_data["verdict"]

        if pct >= 50.0 or "ЖАСАНДЫ" in verdict.upper() or "МОНТАЖ" in verdict.upper() or "DEEPFAKE" in verdict.upper():
            st.markdown(f'<div class="verdict-ai">⚠️ САРАПТАМА ҚОРЫТЫНДЫСЫ: {verdict} (ЖИ/Монтаж ықтималдығы: {pct}%)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-real">✅ САРАПТАМА ҚОРЫТЫНДЫСЫ: {verdict} (Шынайылық көрсеткіші: {100-pct}%)</div>', unsafe_allow_html=True)

        st.info(f"🔍 **Дәлелдер мен сипаттама:**\n\n{p_data['reason']}")
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
                    sys_p = "Сіз цифрлық криминалистсіз. Нақты жауап беріңіз."
                    ans = call_gemini_chat(sys_p, st.session_state["photo_chat_history"][:-1], user_q, pil_imgs=[p_data["img"]])
                    st.markdown(ans)
                    st.session_state["photo_chat_history"].append({"role": "assistant", "content": ans})

with tab2:
    st.markdown("### 🎥 Видеоны тексеру және сараптау")
    uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov", "avi", "mkv", "webm"], key="video_upload")
    
    if uploaded_video:
        # Видео көлемі үлкен болмау үшін кішірек өлшемде көрсетіледі
        st.video(uploaded_video, format="video/mp4", start_time=0)
        
        if st.button("Сараптау", key="video_btn"):
            with st.spinner("Видео кадрларының шашы, беті, көзі, киімі мен фоны мұқият талдануда..."):
                frames = extract_frames_from_video(uploaded_video, max_frames=5)
                if frames:
                    score, verdict, reason = analyze_media(frames)
                    st.session_state["video_data"] = {"pct": score, "verdict": verdict, "reason": reason, "imgs": frames}
                    st.session_state["video_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Видео сараптамасының нәтижесі:**\n\n{reason}"}]
                else:
                    st.error("Видеодан деректерді оқып алу мүмкін болмады.")

    if "video_data" in st.session_state:
        v_data = st.session_state["video_data"]
        pct = v_data["pct"]
        verdict = v_data["verdict"]

        if pct >= 50.0 or "ЖАСАНДЫ" in verdict.upper() or "МОНТАЖ" in verdict.upper() or "DEEPFAKE" in verdict.upper():
            st.markdown(f'<div class="verdict-ai">⚠️ САРАПТАМА ҚОРЫТЫНДЫСЫ: {verdict} (ЖИ/Монтаж ықтималдығы: {pct}%)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-real">✅ САРАПТАМА ҚОРЫТЫНДЫСЫ: {verdict} (Шынайылық көрсеткіші: {100-pct}%)</div>', unsafe_allow_html=True)

        st.info(f"🔍 **Дәлелдер мен сипаттама:**\n\n{v_data['reason']}")
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
                    sys_p = "Сіз цифрлық криминалистсіз. Нақты жауап беріңіз."
                    ans_v = call_gemini_chat(sys_p, st.session_state["video_chat_history"][:-1], user_q_v, pil_imgs=v_data.get("imgs"))
                    st.markdown(ans_v)
                    st.session_state["video_chat_history"].append({"role": "assistant", "content": ans_v})

with tab3:
    st.markdown("### 📝 Мәтінді тексеру")
    text_input = st.text_area("Тексеретін мәтінді енгізіңіз:", height=150, key="text_input_area")
    if st.button("Тексеру", key="text_btn"):
        if text_input.strip():
            with st.spinner("Талдануда..."):
                ans_t = call_gemini_chat("Сіз сарапшы-редакторсыз.", [], f"Мәтінді талдап бер: {text_input}")
                st.info(ans_t)

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
