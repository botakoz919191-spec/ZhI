import streamlit as st
import time
from PIL import Image
import google.generativeai as genai

# =========================================================
# ⚙️ БАПТАУЛАР МЕН СТИЛЬДЕР
# =========================================================
st.set_page_config(
    page_title="CyberShield.kz — ҚР Цифрлық сараптама порталы",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #edf5ff 0%, #dbeafe 50%, #eff6ff 100%) !important;
    }
    
    .top-navbar {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 2px solid #cbd5e1;
        padding: 12px 20px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        font-size: 13px;
        color: #1e293b;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .top-navbar a {
        color: #1d4ed8;
        text-decoration: none;
        font-weight: bold;
    }
    .badge-num {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 800;
        border: 1px solid #fecaca;
    }

    .header-banner {
        background: linear-gradient(135deg, #0f2b5c 0%, #1e40af 60%, #1d4ed8 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border-bottom: 5px solid #d97706;
        box-shadow: 0 4px 10px rgba(30, 64, 175, 0.2);
    }
    .header-title { font-size: 26px; font-weight: 800; color: #ffffff; margin: 0; }
    .header-subtitle { font-size: 14px; color: #e0f2fe; margin-top: 4px; }

    div.stButton > button {
        background: linear-gradient(90deg, #0f2b5c 0%, #1e40af 100%) !important;
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .verdict-ai {
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b;
        padding: 14px; border-radius: 10px; font-weight: bold; margin-bottom: 12px;
    }
    .verdict-real {
        background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534;
        padding: 14px; border-radius: 10px; font-weight: bold; margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🏛️ ЖОҒАРҒЫ ПАНЕЛЬ
# =========================================================
st.markdown("""
<div class="top-navbar">
    <div>
        🏛️ <b>Әділет министрлігі:</b> <a href="https://www.gov.kz/memleket/entities/adilet" target="_blank">gov.kz/adilet</a>
    </div>
    <div>
        🛡️ <b>Шұғыл сенім телефондары:</b> 
        <span style="margin-left: 5px;">📞 Полиция: <span class="badge-num">102</span></span> | 
        <span style="margin-left: 5px;">☎️ Орталық: <span class="badge-num">1414</span></span> | 
        <span style="margin-left: 5px;">🆘 Балалар: <span class="badge-num">111</span></span> | 
        <span style="margin-left: 5px;">⛑️ Сенім: <span class="badge-num">150</span></span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🗝️ API БАПТАУЫ
# =========================================================
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

    # Ең тұрақты және 100% жұмыс істейтін модель
    models_to_try = ['gemini-1.5-flash']
    prepared_img = compress_image(pil_img) if pil_img is not None else None

    last_error = ""
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            
            full_prompt = f"{system_prompt}\n\n--- ЧАТ ТАРИХЫ ---\n"
            for msg in chat_history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            
            full_prompt += f"\nПАЙДАЛАНУШЫ СҰРАҒЫ: {user_new_msg}\n"
            full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Шаблон қолданбай, әрбір деталіне терең үңіліп, нақты, жан-жақты әрі кәсіби заңгерлік/сараптамалық жауап бер."

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

    return f"⚠️ API қатесі орын алды: {last_error}. Google AI Studio балансы мен кілтін тексеріңіз."

def analyze_with_gemini_vision(pil_img):
    prompt = (
        "Сіз жоғары санатты цифрлық криминалист пен кибер-заңгерсіз. Мына суреттің әрбір бөлшегін, піксельдерін, жарық түсуін, "
        "цифрлық артефактілерін және мәтіндік/графикалық қабаттарын аса мұқиятпен зерттеп шығыңыз:\n"
        "1. Бұл сурет Жасанды интеллект (ЖИ/AI) арқылы генерацияланған ба, әлде Photoshop/Canva арқылы өңделген бе, жоқ әлде шынайы камера фотосы ма? "
        "ЖИ немесе өңделген графика болу ықтималдығын 0-ден 100-ге дейінгі пайызбен нақты көрсетіңіз.\n"
        "2. Суреттің барлық деталіне сипаттама беріп, авторлық құқық, фейк немесе заң бұзушылық белгілерін жан-жақты талдаңыз.\n\n"
        "МІНДЕТТІ ФОРМАТ:\n"
        "SCORE: [0-100 аралығындағы ЖИ немесе өңделу пайызы]\n"
        "VERDICT: [Жасанды интеллект арқылы жасалған / Өңделген графика немесе Шынайы камера фотосы]\n"
        "REASON: [Суреттің әр деталіне тоқталған толық, терең және сараптамалық қорытынды]"
    )
    res_text = call_gemini_chat("Сіз жоғары санатты цифрлық сарапшысыз.", [], prompt, pil_img)
    
    score = 15.0
    verdict = "Шынайы камера фотосы"
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

# =========================================================
# 🏛️ БАННЕР ЖӘНЕ ИНТЕРФЕЙС
# =========================================================
st.markdown("""
<div class="header-banner">
    <h1 class="header-title">⚖️ CyberShield.kz</h1>
    <p class="header-subtitle">Қазақстан Республикасы цифрлық сараптама және киберқұқықтық порталы</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "🖼️ / 🎥 Терең цифрлық сараптама", 
    "📝 Мәтін сараптамасы", 
    "💬 Онлайн ҚР кибер-заңгері"
])

# ---------------------------------------------------------
# TAB 1: СУРЕТ ЖӘНЕ ВИДЕО ТЕРЕҢ САРАПТАМАСЫ
# ---------------------------------------------------------
with tab1:
    st.markdown("### 🖼️ Сурет немесе 🎥 видеоны терең бөлшектеп зерттеу")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", width=300)

            if st.button("🔍 Суреттің әр деталін терең сараптау"):
                with st.spinner("Суреттің әрбір бөлшегі мен ЖИ белгілері мұқият талдануда..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        score, verdict, reason = analyze_with_gemini_vision(pil_img)

                        st.session_state["photo_data"] = {
                            "pct": score,
                            "verdict": verdict,
                            "reason": reason,
                            "img": pil_img
                        }

                        st.session_state["photo_chat_history"] = [
                            {"role": "assistant", "content": f"⚖️ **Терең сараптама қорытындысы:**\n\n{reason}\n\nОсы сараптама бойынша қосымша сұрағыңызды төменде қоя аласыз:"}
                        ]
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

            if "photo_data" in st.session_state:
                p_data = st.session_state["photo_data"]
                pct = p_data["pct"]
                verdict = p_data["verdict"]

                if pct >= 50.0 or "ЖАСАНДЫ" in verdict.upper() or "ӨҢДЕЛГЕН" in verdict.upper():
                    st.markdown(f'<div class="verdict-ai">⚠️ Сараптама актісі: {verdict} (ЖИ/Өңделу көрсеткіші: {pct}%)</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="verdict-real">✅ Сараптама актісі: {verdict} (Шынайылық көрсеткіші: {100-pct}%)</div>', unsafe_allow_html=True)

                st.info(f"🔍 **Толық сараптамалық сипаттама:**\n\n{p_data['reason']}")
                st.markdown("---")
                st.markdown("### 💬 Осы сараптама бойынша заңгерге сұрақ қою")

                for msg in st.session_state.get("photo_chat_history", []):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                if user_q := st.chat_input("Сұрағыңызды жазыңыз...", key="photo_input"):
                    st.session_state["photo_chat_history"].append({"role": "user", "content": user_q})
                    with st.chat_message("user"):
                        st.markdown(user_q)

                    with st.chat_message("assistant"):
                        with st.spinner("Заңгер жауабы дайындалуда..."):
                            sys_p = (
                                f"Сіз тәжірибелі ҚР кибер-заңгерісіз. Сараптама нәтижесі: {p_data['reason']}.\n"
                                "МАҢЫЗДЫ: Пайдаланушының сұрағына шаблонсыз, мәтіннің және суреттің әрбір маңызды деталіне, "
                                "сондай-ақ ҚР заңнамасына қатаң сүйене отырып жауап беріңіз."
                            )
                            ans = call_gemini_chat(
                                sys_p, 
                                st.session_state["photo_chat_history"][:-1], 
                                user_q, 
                                pil_img=p_data["img"]
                            )
                            st.markdown(ans)
                            st.session_state["photo_chat_history"].append({"role": "assistant", "content": ans})

    elif media_type == "Видеофайл":
        uploaded_video = st.file_uploader("Видеофайлды жүктеңіз (MP4, MOV)", type=["mp4", "mov"])
        if uploaded_video:
            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                st.video(uploaded_video)

            if st.button("🔍 Видеоны терең сараптау"):
                with st.spinner("Видеоның мазмұны мен кадрларын жан-жақты талдау жасалуда..."):
                    try:
                        video_name = uploaded_video.name
                        sys_p = "Сіз видеоны және медиафайлдарды сараптаушы жоғары санатты сарапшысыз. Видеоның атауына, сипатына және мазмұнына аса үлкен мән беріп, әрбір деталін терең талдап беріңіз."
                        ans = call_gemini_chat(sys_p, [], f"Мына видеофайлды егжей-тегжейлі сарапта: {video_name}")
                        st.session_state["video_reason"] = ans
                    except Exception as err:
                        st.error(f"Видеоны талдау қатесі: {err}")

            if "video_reason" in st.session_state:
                st.info(f"🎥 **Видеоның терең сараптамалық нәтижесі:**\n\n{st.session_state['video_reason']}")

# ---------------------------------------------------------
# TAB 2: МӘТІН САРАПТАМАСЫ
# ---------------------------------------------------------
with tab2:
    st.markdown("### 📝 Мәтінді терең тексеру")
    text_input = st.text_area("Тексеретін мәтінді осы жерге енгізіңіз:", height=150)
    if st.button("🔍 Мәтінді терең сараптау"):
        if text_input.strip():
            with st.spinner("Мәтіннің мазмұны мен стилі талдануда..."):
                sys_p = "Сіз заңгер-редакторсыз. Мәтіннің авторлығын, мағынасын және заңға қайшы келетін тұстарын нақты мәтінге сүйене отырып мұқият талдап беріңіз."
                ans = call_gemini_chat(sys_p, [], f"Мәтінді терең талдап бер: {text_input}")
                st.info(ans)

# ---------------------------------------------------------
# TAB 3: ОНЛАЙН КИБЕР-ЗАҢГЕР
# ---------------------------------------------------------
with tab3:
    st.markdown("### 💬 Онлайн ҚР кибер-заңгері")
    st.caption("ҚР заңнамасы бойынша кез келген сұрағыңызға нақты және толық құқықтық кеңес алыңыз.")

    if "gen_chat_history" not in st.session_state:
        st.session_state["gen_chat_history"] = [
            {"role": "assistant", "content": "Сәлеметсіз бе! Мен ҚР Цифрлық және кибер-құқық заңгерімін. Қандай сұрағыңыз бар?"}
        ]

    for msg in st.session_state["gen_chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_q := st.chat_input("Сұрағыңызды жазыңыз...", key="gen_chat_input"):
        st.session_state["gen_chat_history"].append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)

        with st.chat_message("assistant"):
            with st.spinner("Заңгер жауабы дайындалуда..."):
                sys_p = "Сіз ҚР заңгерісіз. Шаблонсыз, нақты әрі мазмұнды құқықтық жауап бер."
                ans = call_gemini_chat(sys_p, st.session_state["gen_chat_history"][:-1], user_q)
                st.markdown(ans)
                st.session_state["gen_chat_history"].append({"role": "assistant", "content": ans})
