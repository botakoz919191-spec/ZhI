import streamlit as st
import time
from PIL import Image
import google.generativeai as genai

# =========================================================
# ⚙️ НАСТРОЙКИ СТРАНИЦЫ И СТИЛИ
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
    .header-banner {
        background: linear-gradient(135deg, #0f2b5c 0%, #1e40af 60%, #1d4ed8 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border-bottom: 5px solid #d97706;
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
    }

    .verdict-ai {
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b;
        padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 12px;
    }
    .verdict-real {
        background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534;
        padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 12px;
    }
    .footer-box {
        margin-top: 40px;
        padding: 15px;
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        text-align: center;
        font-size: 13px;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🗝️ ИНИЦИАЛИЗАЦИЯ КЛЮЧА
# =========================================================
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def compress_image(pil_img, max_size=(600, 600)):
    img_copy = pil_img.copy()
    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img_copy

def call_gemini_chat(system_prompt, chat_history, user_new_msg, pil_img=None):
    if not GEMINI_KEY:
        return "⚠️ Gemini API кілті (GEMINI_KEY) Streamlit Secrets бөлімінде көрсетілмеген!"

    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
    prepared_img = compress_image(pil_img) if pil_img is not None else None

    for m_name in models_to_try:
        for attempt in range(2):
            try:
                model = genai.GenerativeModel(m_name)
                
                full_prompt = f"{system_prompt}\n\n--- ЧАТ ТАРИХЫ ---\n"
                for msg in chat_history:
                    full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
                
                full_prompt += f"\nПАЙДАЛАНУШЫ СҰРАҒЫ: {user_new_msg}\n"
                full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Шаблон қолданбай, қойылған сұраққа нақты әрі мағыналы жауап бер."

                contents = [full_prompt]
                if prepared_img is not None:
                    contents.append(prepared_img)

                response = model.generate_content(contents)
                if response and response.text:
                    return response.text
            except Exception as e:
                time.sleep(1)
                continue

    return "⚠️ API лимиті немесе байланыс қатесі орын алды. Бірнеше секунд күтіп, қайта басып көріңіз."

def analyze_with_gemini_vision(pil_img):
    prompt = (
        "Мына суретті мұқият талдап бер:\n"
        "1. Бұл ЖИ (Canva, Midjourney), инфографика, оқулық материалы, компьютерлік графика ма, әлде камерадан түсірілген реалды фото ма?\n"
        "2. Не себепті олай бағалағаныңды қысқаша түсіндір.\n\n"
        "Формат:\n"
        "SCORE: [0-100 (ЖИ жасағанына сенімділік пайызы)]\n"
        "VERDICT: [Реалды камера немесе Жасанды интеллект / Графика]\n"
        "REASON: [Сурет мазмұны мен түпнұсқалығының сипаттамасы]"
    )
    res_text = call_gemini_chat("Сіз цифрлық сарапшысыз.", [], prompt, pil_img)
    
    score = 50.0
    verdict = "Жасанды интеллект"
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
# 🏛️ ИНТЕРФЕЙС
# =========================================================
st.markdown("""
<div class="header-banner">
    <h1 class="header-title">⚖️ CyberShield.kz</h1>
    <p class="header-subtitle">Қазақстан Республикасы цифрлық сараптама және киберқұқықтық порталы</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "🖼️ / 🎥 Цифрлық сараптама (Gemini AI)", 
    "📝 Мәтін сараптамасы", 
    "💬 Онлайн ҚР кибер-заңгері"
])

# ---------------------------------------------------------
# TAB 1: СУРЕТ ЖӘНЕ ВИДЕО САРАПТАМАСЫ (Тек Gemini арқылы)
# ---------------------------------------------------------
with tab1:
    st.markdown("### 🖼️ Сурет немесе 🎥 видеоны Gemini арқылы тексеру")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", width=220)

            if st.button("🔍 Суретті толық сараптау"):
                with st.spinner("Gemini арқылы талдануда..."):
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
                            {"role": "assistant", "content": f"⚖️ **Сараптама қорытындысы:**\n\n{reason}\n\nСурет бойынша сұрағыңызды төменде қоя аласыз:"}
                        ]
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

            if "photo_data" in st.session_state:
                p_data = st.session_state["photo_data"]
                pct = p_data["pct"]
                verdict = p_data["verdict"]

                if pct >= 45.0 or "ЖАСАНДЫ" in verdict.upper() or "ГРАФИКА" in verdict.upper():
                    st.markdown(f'<div class="verdict-ai">⚠️ Сараптама актісі: ЖИ / Графика / Инфографика белгілері анықталды! ({pct}%)</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="verdict-real">✅ Сараптама актісі: Реалды камера фотосы! ({pct}%)</div>', unsafe_allow_html=True)

                st.info(f"🔍 **Сараптама сипаттамасы:**\n\n{p_data['reason']}")
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
                        with st.spinner("Өңделуде..."):
                            sys_p = (
                                f"Сіз білікті ҚР кибер-заңгерісіз. Сараптама нәтижесі / Сурет сипаттамасы: {p_data['reason']}.\n"
                                "МАҢЫЗДЫ ЕРЕЖЕ: Пайдаланушының нақты қойған сұрағына (авторлық құқық, өз еңбегі, суретте не берілгені немесе сабаққа қолдану туралы) "
                                "дайын шаблон қолданбай, әр сұрақтың жеке мағынасына сай тікелей, толық әрі нақты жауап беріңіз. "
                                "Барлық сұраққа бірдей шаблонды жауап қайтаруға қатаң тыйым салынады."
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

            if st.button("🔍 Видеоны сараптау"):
                with st.spinner("Видео атауы мен мазмұны талдануда..."):
                    try:
                        video_name = uploaded_video.name
                        sys_p = "Сіз видеоны сараптаушы сарапшысыз. Жүктелген видеоның атауы мен сипатына қарай оның мазмұнын талдап беріңіз."
                        ans = call_gemini_chat(sys_p, [], f"Мына видеофайлды сарапта: {video_name}")
                        st.session_state["video_reason"] = ans
                    except Exception as err:
                        st.error(f"Видеоны талдау қатесі: {err}")

            if "video_reason" in st.session_state:
                st.info(f"🎥 **Видео сараптамасының нәтижесі:**\n\n{st.session_state['video_reason']}")

# ---------------------------------------------------------
# TAB 2: МӘТІН САРАПТАМАСЫ
# ---------------------------------------------------------
with tab2:
    st.markdown("### 📝 Мәтінді тексеру")
    text_input = st.text_area("Тексеретін мәтінді осы жерге енгізіңіз:", height=150)
    if st.button("🔍 Мәтінді сараптау"):
        if text_input.strip():
            with st.spinner("Мәтін талдануда..."):
                sys_p = "Сіз мәтінді сараптаушысыз. Мәтіннің жасанды түрде жазылғанын немесе адам тарапынан жазылғанын талдап беріңіз."
                ans = call_gemini_chat(sys_p, [], f"Мәтінді талдап бер: {text_input}")
                st.info(ans)

# ---------------------------------------------------------
# TAB 3: ОНЛАЙН КИБЕР-ЗАҢГЕР
# ---------------------------------------------------------
with tab3:
    st.markdown("### 💬 Онлайн ҚР кибер-заңгері")
    st.caption("ҚР заңнамасы бойынша кез келген сұрағыңызды қойыңыз.")

    if "gen_chat_history" not in st.session_state:
        st.session_state["gen_chat_history"] = [
            {"role": "assistant", "content": "Сәлеметсіз бе! Мен ҚР Цифрлық заңгерімін. Сұрағыңызды қоя берсеңіз болады."}
        ]

    for msg in st.session_state["gen_chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_q := st.chat_input("Сұрағыңызды жазыңыз...", key="gen_chat_input"):
        st.session_state["gen_chat_history"].append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)

        with st.chat_message("assistant"):
            with st.spinner("Жауап дайындалуда..."):
                sys_p = "Сіз ҚР заңгерісіз. Сұраққа шаблон қолданбай, ҚР заңнамасына сай нақты әрі жеке жауап бер."
                ans = call_gemini_chat(sys_p, st.session_state["gen_chat_history"][:-1], user_q)
                st.markdown(ans)
                st.session_state["gen_chat_history"].append({"role": "assistant", "content": ans})

# =========================================================
# 📌 САЙТ ТӨМЕНГІ БӨЛІМІ (ФУТЕР)
# =========================================================
st.markdown("""
<div class="footer-box">
    <b>Қазақстан Республикасы Әділет министрлігі:</b> 
    <a href="https://www.gov.kz/memleket/entities/adilet" target="_blank">gov.kz/memleket/entities/adilet</a><br>
    <b>Сенім телефоны / Бірыңғай байланыс орталығы:</b> 1414
</div>
""", unsafe_allow_html=True)