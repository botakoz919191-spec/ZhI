import streamlit as st
import requests
import json
import tempfile
import cv2
import openai

# =========================================================
# 🗝️ АВТОМАТТАНДЫРЫЛҒАН API КІЛТТЕРІ
# =========================================================
SIGHTENGINE_USER = "1282198950"
SIGHTENGINE_SECRET = "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng"
SERPAPI_KEY = "d7ae383bc732173b646bbc2fefa6ec5080a28bb63eb43030c25f739c542552e8"
OPENAI_KEY = "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"

# ---------------------------------------------------------
# 1. Бет параметрлері
# ---------------------------------------------------------
st.set_page_config(
    page_title="CyberShield KZ — КИБЕРҚОРҒАНЫС",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ CyberShield KZ — ЖИ Талдау және КИБЕРҚОРҒАНЫС Жүйесі")

# ---------------------------------------------------------
# 2. Талдау және OpenAI Консультация Функциялары
# ---------------------------------------------------------

def analyze_image_sightengine(image_bytes):
    """Суреттегі ЖИ/Deepfake пайызын анықтау"""
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
            error_msg = out.get('error', {}).get('message', 'Sightengine API қатесі')
            return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_custom_legal_advice(media_type_str, image_url_or_desc="Жүктелген ЖИ медиасы"):
    """OpenAI арқылы суреттегі/видеодағы жағдайға арнайы жеке консультация генерациялау"""
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        prompt = f"""
        Пайдаланушы {media_type_str} жүктеді және оның ЖИ (Deepfake) екені анықталды.
        Сіз ҚР Заңгерісіз. Төмендегі талаптар бойынша Қазақстан Республикасының заңдарына (ҚР АК, ҚК, ӘҚБтК) сүйеніп, дайын шаблонсыз, жеке кеңес дайындаңыз:
        1. Осы медиадағы жағдай бойынша қандай азаматтық/қылмыстық құқықтар бұзылған болуы мүмкін?
        2. Полицияға (CyberPol) және сотқа шағымдану үшін нақты қандай баптарды (ҚР АК 143, 145, ҚР ҚК 147, 194, ӘҚБтК 456-2 т.б.) қолданған дұрыс?
        3. Бұл жағдай бойынша пайдаланушы не істеуі керек (қадамдық алгоритм)?
        Жауапты қазақ тілінде, түсінікті және заңдық тұрғыдан нақты жазыңыз.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Сіз ҚР киберқылмыс және құқық қорғау саласындағы тәжірибелі ЖИ Заңгерсіз."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Консультациясын алуда қате шықты: {str(e)}"


def analyze_video_sightengine(video_bytes):
    """Видеодан 1-кадрды кесіп алып тексеру"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(video_bytes)
            tmp_file_path = tmp_file.name

        cap = cv2.VideoCapture(tmp_file_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"success": False, "error": "Видеодан кадрды оқу мүмкін болмады."}

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        return analyze_image_sightengine(frame_bytes)
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------------------------------------------------------
# 3. Негізгі Табтар
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🖼️ / 🎥 Медианы ЖИ-ге талдау", "💬 ЖИ Заңгер Консультант"])

# =========================================================
# ТАБ 1: Фотосурет немесе Видеоны ЖИ-ге тексеру
# =========================================================
with tab1:
    st.subheader("🖼️ Фотосурет немесе 🎥 Видеоны ЖИ-ге (Deepfake) тексеру")
    
    media_type = st.radio("Медиа типін таңдаңыз:", ["Фотосурет (JPG, PNG)", "Видеофайл (MP4, MOV)"])
    
    if media_type == "Фотосурет (JPG, PNG)":
        uploaded_file = st.file_uploader("Суретті жүктеңіз", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 Суретті талдау"):
                with st.spinner("ЖИ сараптамасы жүріп жатыр..."):
                    bytes_data = uploaded_file.getvalue()
                    res = analyze_image_sightengine(bytes_data)
                    
                    if res["success"]:
                        pct = res["percentage"]
                        st.markdown(f"### 📊 ЖИ (Deepfake) генерация ықтималдығы: **{pct}%**")
                        
                        # Егер ЖИ болса: OpenAI арқылы жеке заңгерлік кеңес құрастыру
                        if pct > 50:
                            st.error("🚨 ЕСКЕРТУ: Бұл суретте Жасанды Интеллект (Deepfake) белгілері анықталды!")
                            st.markdown("---")
                            st.subheader("⚖️ OpenAI ЖИ Арнайы Заңгерлік Консультациясы")
                            
                            with st.spinner("OpenAI осы суретке байланысты жеке заңгерлік кеңес дайындауда..."):
                                advice = get_custom_legal_advice("сурет")
                                st.info(advice)
                        else:
                            st.success("✅ Сурет таза немесе ЖИ белгілері анықталмады (шынайы медиа болуы мүмкін).")
                    else:
                        st.error(f"Талдау қатесі: {res['error']}")

    else: # Видеофайл
        uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 Видеоны талдау"):
                with st.spinner("Видео кадрлары ЖИ сараптамасынан өтуде..."):
                    v_bytes = uploaded_video.getvalue()
                    res = analyze_video_sightengine(v_bytes)
                    
                    if res["success"]:
                        pct = res["percentage"]
                        st.markdown(f"### 📊 Видеодағы ЖИ (Deepfake) ықтималдығы: **{pct}%**")
                        
                        if pct > 50:
                            st.error("🚨 ЕСКЕРТУ: Видеода Жасанды Интеллект (Deepfake/FaceSwap) белгілері бар!")
                            st.markdown("---")
                            st.subheader("⚖️ OpenAI ЖИ Арнайы Заңгерлік Консультациясы")
                            
                            with st.spinner("OpenAI осы видеоға байланысты жеке заңгерлік кеңес дайындауда..."):
                                advice = get_custom_legal_advice("видеофайл")
                                st.info(advice)
                        else:
                            st.success("✅ Видео таза немесе ЖИ белгілері анықталмады.")
                    else:
                        st.error(f"Талдау қатесі: {res['error']}")

# =========================================================
# ТАБ 2: ЖИ Заңгер Консультант (ChatGPT Chat)
# =========================================================
with tab2:
    st.subheader("💬 Онлайн ЖИ Заңгер Консультант")
    st.write("ҚР заңдары бойынша сұрақ қойыңыз немесе арыз жазуға көмек сұраңыз.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Сұрағыңызды немесе жағдайды жазыңыз...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Заңгерлік талдау жасалуда..."):
                try:
                    client = openai.OpenAI(api_key=OPENAI_KEY)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Сіз Қазақстан Республикасының киберқылмыс және Азаматтық/Қылмыстық заңдары бойынша маманданған білікті ЖИ Заңгерсіз. Пайдаланушыларға ҚР АК 143, 145-баптары, ҚР ҚК 147, 194-баптары бойынша нақты әрі түсінікті кеңес беріңіз."},
                            *st.session_state.messages
                        ],
                        temperature=0.3
                    )
                    reply = response.choices[0].message.content
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"OpenAI API Қатесі: {str(e)}")
