import streamlit as st
import requests
import json
import tempfile
import cv2
from PIL import Image
import google.generativeai as genai

# =========================================================
# ⚙️ БЕТТІҢ ДИЗАЙНЫ МЕН БАПТАУЛАРЫ
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
        padding: 25px;
        border-radius: 18px;
        margin-bottom: 20px;
        border-bottom: 6px solid #d97706;
    }
    .header-title { font-size: 30px; font-weight: 900; color: #ffffff; margin: 0; }
    .header-subtitle { font-size: 15px; color: #e0f2fe; margin-top: 5px; }

    div.stButton > button {
        background: linear-gradient(90deg, #0f2b5c 0%, #1e40af 100%) !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        width: 100%;
    }

    .verdict-ai {
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b;
        padding: 15px; border-radius: 12px; font-weight: bold; margin-bottom: 15px;
    }
    .verdict-real {
        background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534;
        padding: 15px; border-radius: 12px; font-weight: bold; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🗝️ API КІЛТТЕРІ МЕН МОДЕЛЬ
# =========================================================
SIGHTENGINE_USER = st.secrets.get("SIGHTENGINE_USER", "1282198950")
SIGHTENGINE_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def call_gemini_chat(system_prompt, chat_history, user_new_msg, pil_img=None):
    """Сұраққа нақты, мағыналы әрі сауатты жауап беретін негізгі ЖИ функциясы"""
    if not GEMINI_KEY:
        return "⚠️ API кілті енгізілмеген. Streamlit secrets бөліміне GEMINI_KEY кілтін енгізіңіз."

    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            
            full_prompt = f"{system_prompt}\n\n--- АЛҒАШҚЫ СҰРАҚ-ЖАУАП ТАРИХЫ ---\n"
            for msg in chat_history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            
            full_prompt += f"\nПАЙДАЛАНУШЫНЫҢ ЖАҢА СҰРАҒЫ: {user_new_msg}\n"
            full_prompt += "\nЖАУАП БЕРУ ЕРЕЖЕСІ: Сұрақты мұқият түсініп, логикалық әрі мағыналы жауап бер. Бір апаттық дайын фразаны немесе шаблонды қайталай берме!"

            contents = [full_prompt]
            if pil_img is not None:
                contents.append(pil_img)

            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception:
            continue

    return "Сұрақты талдау кезінде қате орын алды. Қайтадан қойып көріңіз."

def analyze_image_sightengine(image_bytes):
    url = 'https://api.sightengine.com/1.0/check.json'
    params = {'models': 'genai', 'api_user': SIGHTENGINE_USER, 'api_secret': SIGHTENGINE_SECRET}
    files = {'media': image_bytes}
    try:
        res = requests.post(url, files=files, data=params, timeout=12)
        out = json.loads(res.text)
        if out.get('status') == 'success':
            score = out.get('type', {}).get('ai_generated', 0)
            return {"success": True, "percentage": round(score * 100, 2)}
        return {"success": False, "error": "Тексеру қатесі"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_with_gemini_vision(pil_img):
    prompt = (
        "Мына суретті мұқият талдаңыз:\n"
        "1. Бұл ЖИ (Canva, Midjourney), компьютерлік графика, инфографика, оқулық беті ма, әлде шынайы камера фотосы ма?\n"
        "2. Егер бұл сабақ түсіндіру, инфографика немесе компьютерлік дизайн болса, оны 'Жасанды интеллект немесе графика' деп бағалаңыз.\n\n"
        "Формат:\n"
        "SCORE: [0-100 аралығында сан]\n"
        "VERDICT: [Реалды камера немесе Жасанды интеллект]\n"
        "REASON: [Суретте не бейнеленгені және сипаттамасы]"
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
    "🖼️ / 🎥 Цифрлық сараптама (ЖИ & Камера)", 
    "📝 Мәтін сараптамасы (ChatGPT)", 
    "💬 Онлайн ҚР кибер-заңгері"
])

# ---------------------------------------------------------
# TAB 1: СУРЕТ ЖӘНЕ ВИДЕО САРАПТАМАСЫ
# ---------------------------------------------------------
with tab1:
    st.markdown("### 🖼️ Сурет немесе 🎥 видеоны цифрлық тексеру")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            col_img1, col_img2 = st.columns([1, 1])
            with col_img1:
                st.image(uploaded_file, caption="Жүктелген сурет", width=350)

            if st.button("🔍 Сюжеті мен түпнұсқалығын сараптау"):
                with st.spinner("Сурет талдануда..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        res_s = analyze_image_sightengine(uploaded_file.getvalue())
                        score1 = res_s.get("percentage", 0.0) if res_s.get("success") else 0.0
                        score2, verdict, reason = analyze_with_gemini_vision(pil_img)
                        pct = max(score1, score2)

                        st.session_state["photo_data"] = {
                            "pct": pct,
                            "verdict": verdict,
                            "reason": reason,
                            "img": pil_img
                        }

                        # Чат тарихын бастау
                        st.session_state["photo_chat_history"] = [
                            {"role": "assistant", "content": f"⚖️ **Сараптама қорытындысы дайын!**\n\n**Талдау мазмұны:** {reason}\n\nОсы сурет немесе талдау бойынша кез келген сұрағыңызды төменге жаза аласыз:"}
                        ]

                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

            if "photo_data" in st.session_state:
                p_data = st.session_state["photo_data"]
                pct = p_data["pct"]
                verdict = p_data["verdict"]

                if pct >= 45.0 or "ЖАСАНДЫ" in verdict.upper():
                    st.markdown(f'<div class="verdict-ai">⚠️ Сараптама актісі: Бұл файл жасанды интеллект (AI/Инфографика/Графика) арқылы жасалған! (Ықтималдығы: {pct}%)</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="verdict-real">✅ Сараптама актісі: Бұл реалды камераға түсірілген шынайы фотосурет! (ЖИ қаупі: {pct}%)</div>', unsafe_allow_html=True)

                st.info(f"🔍 **Сюжеттік сараптама сипаттамасы:**\n\n{p_data['reason']}")
                st.markdown("---")
                st.markdown("### 💬 Осы сараптама бойынша заңгерге сұрақ қою")

                # Чат тарихын көрсету
                for msg in st.session_state.get("photo_chat_history", []):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                # Жаңа сұрақ қою
                if user_q := st.chat_input("Сұрағыңызды жазыңыз (мысалы: Неге ЖИ дедің?, Точно ЖИ ма?)...", key="photo_input"):
                    st.session_state["photo_chat_history"].append({"role": "user", "content": user_q})
                    with st.chat_message("user"):
                        st.markdown(user_q)

                    with st.chat_message("assistant"):
                        with st.spinner("Заңгер ойлануда..."):
                            sys_p = (
                                f"Сіз цифрлық сарапшы әрі ҚР заңгерісіз. Мына сурет мазмұны: {p_data['reason']}.\n"
                                f"Пайдаланушының 'Точно ЖИ ма?' немесе 'Неге бұлай таптың?' деген сұрағына "
                                f"суреттің сипатына (инфографика, сабақ материалы, графика, пиксель) сүйеніп анық әрі сауатты жауап беріңіз. "
                                f"Бір жауапты немесе шаблондарды қайталай бермеңіз!"
                            )
                            ans = call_gemini_chat(
                                sys_p, 
                                st.session_state["photo_chat_history"][:-1], 
                                user_q, 
                                pil_img=p_data["img"]
                            )
                            st.markdown(ans)
                            st.session_state["photo_chat_history"].append({"role": "assistant", "content": ans})

# ---------------------------------------------------------
# TAB 2: МӘТІН САРАПТАМАСЫ
# ---------------------------------------------------------
with tab2:
    st.markdown("### 📝 Мәтінді ChatGPT-ге тексеру")
    text_input = st.text_area("Тексеретін мәтінді осы жерге енгізіңіз:", height=150)
    if st.button("🔍 Мәтінді сараптау"):
        if text_input.strip():
            with st.spinner("Мәтін талдануда..."):
                sys_p = "Сіз мәтінді стилистикалық сараптаушысыз. Мәтіннің ChatGPT арқылы жазылғанын анықтап беріңіз."
                ans = call_gemini_chat(sys_p, [], f"Мына мәтінді талдап бер: {text_input}")
                st.info(ans)

# ---------------------------------------------------------
# TAB 3: ОНЛАЙН КИБЕР-ЗАҢГЕР
# ---------------------------------------------------------
with tab3:
    st.markdown("### 💬 Онлайн ҚР кибер-заңгері")
    st.caption("Қазақстан Республикасының заңдары бойынша кез келген сұрағыңызды қойыңыз.")

    if "gen_chat_history" not in st.session_state:
        st.session_state["gen_chat_history"] = [
            {"role": "assistant", "content": "Сәлеметсіз бе! Мен ҚР Цифрлық заңгерімін. Кез келген сұрағыңызды қоя берсеңіз болады."}
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
                sys_p = "Сіз Қазақстан Республикасының заңгерісіз. Пайдаланушы сұрағына ҚР заңдарына сүйене отырып толық жауап беріңіз."
                ans = call_gemini_chat(sys_p, st.session_state["gen_chat_history"][:-1], user_q)
                st.markdown(ans)
                st.session_state["gen_chat_history"].append({"role": "assistant", "content": ans})
