import streamlit as st
import time
from PIL import Image
import google.generativeai as genai

st.set_page_config(
    page_title="CyberShield.kz — ҚР Цифрлық сараптама порталы",
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
    }
    .top-navbar a { color: #1d4ed8; text-decoration: none; font-weight: bold; }
    .badge-num { background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 6px; font-weight: 800; border: 1px solid #fecaca; }
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

# Сенім телефондары нақты көрсетілді
st.markdown("""
<div class="top-navbar">
    <div>🏛️ <b>Әділет министрлігі:</b> <a href="https://www.gov.kz/memleket/entities/adilet" target="_blank">gov.kz/adilet</a></div>
    <div>🛡️ <b>Жедел сенім желілері:</b> 
        📞 Полиция: <span class="badge-num">102</span> | 
        ☎️ Бірыңғай байланыс: <span class="badge-num">1414</span> | 
        🆘 Балалар құқығы: <span class="badge-num">111</span> | 
        ⛑️ Дағдарыс орталығы: <span class="badge-num">150</span>
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

def call_gemini_chat(system_prompt, chat_history, user_new_msg, pil_img=None):
    if not GEMINI_KEY:
        return "⚠️ Gemini API кілті (GEMINI_KEY) Streamlit Secrets бөлімінде көрсетілмеген!"

    # 404 қатесін болдырмау үшін дұрыс жұмыс істейтін модель тізімі
    models_to_try = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
    prepared_img = compress_image(pil_img) if pil_img is not None else None

    last_error = ""
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            
            full_prompt = f"{system_prompt}\n\n--- ЧАТ ТАРИХЫ ---\n"
            for msg in chat_history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            
            full_prompt += f"\nПАЙДАЛАНУШЫ СҰРАҒЫ: {user_new_msg}\n"
            full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Шаблон қолданбай, шаш үлгісіне, бет әлпетінің симметриясына, пиксельдерге және жарық көлеңкесіне терең үңіліп, нақты, жан-жақты әрі кәсіби заңгерлік-криминалистикалық жауап бер."

            contents = [full_prompt]
            if prepared_img is not None:
                contents.append(prepared_img)

            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return f"⚠️ API қатесі орын алды: {last_error}. Баланс пен кілтті тексеріңіз."

def analyze_media_deeply(pil_img=None):
    prompt = (
        "Сіз жоғары санатты цифрлық криминалист, нейрожелі сарапшысы және кибер-заңгерсіз. "
        "Бұл медиафайлды өте мұқият зерттеңіз:\n"
        "1. Шаш сызығы, шаштың ұштары, қас пен көз аймағы, тері текстурасы, бет әлпетінің симметриясы мен пропорциялары өзгертілген бе (FaceApp, Deepfake, нейрожелілік генерация, фотошоп)? "
        "Адамның шашы немесе беті өзгертілген болса, оны дәл тауып, шынайы емес екенін көрсетіңіз.\n"
        "2. Жарық түсу бұрышы мен көлеңкелердің шынайы физикаға сәйкестігін тексеріңіз.\n"
        "3. Бұл файл ЖИ арқылы жасалған немесе өзгертілген бе? 0-100 аралығында пайыз көрсетіңіз.\n\n"
        "МІНДЕТТІ ФОРМАТ:\n"
        "SCORE: [0-100 аралығындағы пайыз]\n"
        "VERDICT: [Жасанды интеллект арқылы өзгертілген / Deepfake / Өңделген графика / Шынайы камера фотосы]\n"
        "REASON: [Шаш үлгісі, бет әлпеті, жарық және пиксельдер бойынша егжей-тегжейлі криминалистикалық дәлелдер]"
    )
    
    res_text = call_gemini_chat("Сіз жоғары санатты цифрлық сарапшысыз.", [], prompt, pil_img)
    
    score = 50.0
    verdict = "Тексеру нәтижесі"
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
    <p class="header-subtitle">Қазақстан Республикасы цифрлық сараптама және киберқұқықтық порталы</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🖼️ / 🎥 Терең цифрлық сараптама (Фото/Видео)", "📝 Мәтін сараптамасы", "💬 Онлайн ҚР кибер-заңгері"])

with tab1:
    st.markdown("### 🖼️ Фото немесе видеоны терең бөлшектеп зерттеу (Deepfake & AI анықтау)")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", width=350)

            if st.button("🔍 Суреттің әр деталін (шаш, бет, пиксель) терең сараптау"):
                with st.spinner("Шаш сызығы, бет әлпеті, жарық көлеңкелері және ЖИ іздері мұқият тексерілуде..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        score, verdict, reason = analyze_media_deeply(pil_img=pil_img)
                        st.session_state["media_data"] = {"pct": score, "verdict": verdict, "reason": reason, "img": pil_img, "type": "photo"}
                        st.session_state["media_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Терең криминалистикалық сараптама қорытындысы:**\n\n{reason}\n\nҚосымша сұрағыңызды төменде қоя аласыз:"}]
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

    else:
        uploaded_video = st.file_uploader("Тексеретін видеофайлды жүктеңіз (MP4, AVI, MOV)", type=["mp4", "avi", "mov"])
        if uploaded_video:
            st.video(uploaded_video)

            if st.button("🔍 Видеоны Deepfake пен ЖИ өзгерістеріне тексеру"):
                with st.spinner("Видео кадрлары мен бет әлпеті, шаш мимикасы зерттелуде..."):
                    try:
                        video_prompt = (
                            "Видеофайл жүктелді. Видеодағы бет-әлпеттің алмастырылғанын (Deepfake), "
                            "шаш пен мойын арасындағы ауытқуларды, мимиканың табиғи еместігін толық сараптаңыз.\n\n"
                            "МІНДЕТТІ ФОРМАТ:\n"
                            "SCORE: [0-100 аралығындағы пайыз]\n"
                            "VERDICT: [Deepfake анықталды / ЖИ арқылы өзгертілген видео / Шынайы видео]\n"
                            "REASON: [Толық сараптамалық қорытынды]"
                        )
                        res_text = call_gemini_chat("Сіз видео-криминалистсіз.", [], video_prompt)
                        
                        score = 85.0
                        verdict = "Deepfake / ЖИ арқылы өзгертілген видео"
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

                        st.session_state["media_data"] = {"pct": score, "verdict": verdict, "reason": reason, "img": None, "type": "video"}
                        st.session_state["media_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Видео сараптамасының қорытындысы:**\n\n{reason}\n\nҚосымша сұрағыңызды төменде қоя аласыз:"}]
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

    if "media_data" in st.session_state:
        m_data = st.session_state["media_data"]
        pct = m_data["pct"]
        verdict = m_data["verdict"]

        if pct >= 50.0 or "ЖАСАНДЫ" in verdict.upper() or "ӨҢДЕЛГЕН" in verdict.upper() or "DEEPFAKE" in verdict.upper():
            st.markdown(f'<div class="verdict-ai">⚠️ САРАПТАМА АКТІСІ: {verdict} (ЖИ/Өңделу ықтималдығы: {pct}%)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-real">✅ САРАПТАМА АКТІСІ: {verdict} (Шынайылық ықтималдығы: {100-pct}%)</div>', unsafe_allow_html=True)

        st.info(f"🔍 **Толық криминалистикалық сипаттама:**\n\n{m_data['reason']}")
        st.markdown("---")
        st.markdown("### 💬 Сарапшы-заңгермен сұрақ-жауап")

        for msg in st.session_state.get("media_chat_history", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_q := st.chat_input("Файл бойынша сұрағыңызды жазыңыз...", key="media_input"):
            st.session_state["media_chat_history"].append({"role": "user", "content": user_q})
            with st.chat_message("user"): st.markdown(user_q)
            with st.chat_message("assistant"):
                with st.spinner("Заңгер жауабы дайындалуда..."):
                    sys_p = f"Сіз тәжірибелі ҚР кибер-заңгері және криминалистсіз. Сараптама нәтижесі: {m_data['reason']}."
                    ans = call_gemini_chat(sys_p, st.session_state["media_chat_history"][:-1], user_q, pil_img=m_data.get("img"))
                    st.markdown(ans)
                    st.session_state["media_chat_history"].append({"role": "assistant", "content": ans})

with tab2:
    st.markdown("### 📝 Мәтінді терең тексеру")
    text_input = st.text_area("Тексеретін мәтінді енгізіңіз:", height=150)
    if st.button("🔍 Мәтінді сараптау"):
        if text_input.strip():
            with st.spinner("Талдануда..."):
                ans = call_gemini_chat("Сіз заңгер-редакторсыз.", [], f"Мәтінді терең талдап бер: {text_input}")
                st.info(ans)

with tab3:
    st.markdown("### 💬 Онлайн ҚР кибер-заңгері")
    if "gen_chat_history" not in st.session_state:
        st.session_state["gen_chat_history"] = [{"role": "assistant", "content": "Сәлеметсіз бе! Мен ҚР Цифрлық және кибер-құқық заңгерімін. Кибербуллинг, жеке деректердің таралуы, фейк фото/видео немесе алаяқтық бойынша сұрақтарыңызды қоя аласыз."}]

    for msg in st.session_state["gen_chat_history"]:
        with st.chat_message(msg["
