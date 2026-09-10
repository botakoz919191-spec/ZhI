import streamlit as st
import requests
import json
import tempfile
import cv2
import google.generativeai as genai

# =========================================================
# 🗝️ API КІЛТТЕРІ (Streamlit Secrets арқылы қауіпсіз оқылады)
# =========================================================
SIGHTENGINE_USER = st.secrets.get("SIGHTENGINE_USER", "1282198950")
SIGHTENGINE_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# ---------------------------------------------------------
# 1. Бет параметрлері
# ---------------------------------------------------------
st.set_page_config(
    page_title="CyberShield KZ",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ CyberShield KZ — ЖИ Талдау және КИБЕРҚОРҒАНЫС Жүйесі")

# ---------------------------------------------------------
# 2. Талдау Функциялары
# ---------------------------------------------------------

def analyze_image_sightengine(image_bytes):
    url = 'https://api.sightengine.com/1.0/check.json'
    params = {'models': 'genai', 'api_user': SIGHTENGINE_USER, 'api_secret': SIGHTENGINE_SECRET}
    files = {'media': image_bytes}
    try:
        res = requests.post(url, files=files, data=params, timeout=12)
        out = json.loads(res.text)
        if out.get('status') == 'success':
            type_info = out.get('type', {})
            score = type_info.get('ai_generated', 0)
            return {"success": True, "percentage": round(score * 100, 2)}
        else:
            return {"success": False, "error": out.get('error', {}).get('message', 'Sightengine API Error')}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_custom_legal_advice_gemini(media_type):
    """Google Gemini арқылы тегін заңгерлік кеңес алу"""
    try:
        if not GEMINI_KEY:
            return "Gemini API кілті орнатылмаған. Streamlit Secrets бөлімін тексеріңіз."

        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            f"Жүктелген {media_type} арқылы ЖИ (Deepfake) анықталды. "
            "Қазақстан Республикасының заңнамасына (ҚР АК 143, 145-баптары, ҚР ҚК 147, 194-баптары, ӘҚБтК 456-2) "
            "сүйене отырып, мына сұрақтарға заңгерлік жауап беріңіз:\n"
            "1. Бұл жағдайда қандай құқықтар бұзылған?\n"
            "2. Азамат полицияға (CyberPol) және сотқа шағымдану үшін не істеуі керек?"
        )

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API қатесі: {str(e)}"


def analyze_video_sightengine(video_bytes):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(video_bytes)
            tmp_file_path = tmp_file.name

        cap = cv2.VideoCapture(tmp_file_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"success": False, "error": "Cannot read video frame"}

        _, buffer = cv2.imencode('.jpg', frame)
        return analyze_image_sightengine(buffer.tobytes())
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------------------------------------------------------
# 3. Бет интерфейсі
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🖼️ / 🎥 Медианы ЖИ-ге талдау", "💬 ЖИ Заңгер Консультант"])

with tab1:
    st.subheader("🖼️ Фотосурет немесе 🎥 Видеоны ЖИ-ге (Deepfake) тексеру")
    media_type = st.radio("Медиа типін таңдаңыз:", ["Фотосурет (JPG, PNG)", "Видеофайл (MP4, MOV)"])
    
    if media_type == "Фотосурет (JPG, PNG)":
        uploaded_file = st.file_uploader("Суретті жүктеңіз", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 Суретті талдау"):
                with st.spinner("ЖИ сараптамасы жүріп жатыр..."):
                    res = analyze_image_sightengine(uploaded_file.getvalue())
                    if res["success"]:
                        pct = res["percentage"]
                        st.markdown(f"### 📊 ЖИ (Deepfake) ықтималдығы: **{pct}%**")
                        
                        if pct > 50:
                            st.error("🚨 ЕСКЕРТУ: Бұл суретте Жасанды Интеллект (Deepfake) белгілері бар!")
                            st.markdown("---")
                            st.subheader("⚖️ Google Gemini Заңгерлік Консультациясы")
                            with st.spinner("Заңгерлік кеңес құрастырылуда..."):
                                advice = get_custom_legal_advice_gemini("сурет")
                                st.info(advice)
                        else:
                            st.success("✅ Сурет таза немесе ЖИ белгілері анықталмады.")
                    else:
                        st.error(f"Қате: {res['error']}")

    else:
        uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 Видеоны талдау"):
                with st.spinner("ЖИ сараптамасы жүріп жатыр..."):
                    res = analyze_video_sightengine(uploaded_video.getvalue())
                    if res["success"]:
                        pct = res["percentage"]
                        st.markdown(f"### 📊 Видеодағы ЖИ ықтималдығы: **{pct}%**")
                        
                        if pct > 50:
                            st.error("🚨 ЕСКЕРТУ: Видеода Жасанды Интеллект (Deepfake) белгілері бар!")
                            st.markdown("---")
                            st.subheader("⚖️ Google Gemini Заңгерлік Консультациясы")
                            with st.spinner("Заңгерлік кеңес құрастырылуда..."):
                                advice = get_custom_legal_advice_gemini("видео")
                                st.info(advice)
                        else:
                            st.success("✅ Видео таза немесе ЖИ белгілері анықталмады.")
                    else:
                        st.error(f"Қате: {res['error']}")

with tab2:
    st.subheader("💬 Онлайн ЖИ Заңгер Консультант (Gemini)")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Сұрағыңызды жазыңыз...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Талдануда..."):
                try:
                    if not GEMINI_KEY:
                        st.error("Gemini API кілті бапталмаған.")
                    else:
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        full_prompt = "Сіз ҚР киберқылмыс және Азаматтық/Қылмыстық заңдары бойынша білікті ЖИ Заңгерсіз. Қазақ тілінде жауап беріңіз.\n" + user_input
                        response = model.generate_content(full_prompt)
                        reply = response.text
                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Gemini қатесі: {str(e)}")
