import streamlit as st
import requests
import json
import tempfile
import cv2
import openai

# ---------------------------------------------------------
# 1. Бет параметрлері мен стилін баптау
# ---------------------------------------------------------
st.set_page_config(
    page_title="CyberShield KZ — КИБЕРҚОРҒАНЫС",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ CyberShield KZ — ЖИ Талдау және КИБЕРҚОРҒАНЫС Жүйесі")

# ---------------------------------------------------------
# 2. Sidebar (Жүйелік API Кілттерін енгізу)
# ---------------------------------------------------------
st.sidebar.header("⚙️ Жүйелік API Кілттері")
sightengine_user = st.sidebar.text_input("Sightengine API User", type="password")
sightengine_secret = st.sidebar.text_input("Sightengine API Secret", type="password")
serpapi_key = st.sidebar.text_input("SerpAPI Key (Іздеу үшін)", type="password")
openai_key = st.sidebar.text_input("OpenAI / ChatGPT API Key", type="password")

st.sidebar.info("💡 API кілттерін қойғаннан кейін жүйенің барлық мүмкіндіктері толық іске қосылады.")

# ---------------------------------------------------------
# 3. Функциялар (Sightengine Талдау Модельдері)
# ---------------------------------------------------------

def analyze_image_sightengine(image_bytes, api_user, api_secret):
    """Суреттегі ЖИ/Deepfake пайызын анықтау"""
    url = 'https://api.sightengine.com/1.0/check.json'
    params = {'models': 'genai', 'api_user': api_user, 'api_secret': api_secret}
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


def analyze_video_sightengine(video_bytes, api_user, api_secret):
    """Видеодан 1-кадрды кесіп алып тексеру (Тегін тарифті қолдау үшін)"""
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

        # Сурет ретінде Sightengine-ге жіберу
        return analyze_image_sightengine(frame_bytes, api_user, api_secret)
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------------------------------------------------------
# 4. Негізгі Табтар (Мүмкіндіктер)
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
                if not sightengine_user or not sightengine_secret:
                    st.warning("⚠️ Өтініш, сол жақтағы Sidebar-ға Sightengine API кілттерін енгізіңіз!")
                else:
                    with st.spinner("ЖИ сараптамасы жүріп жатыр..."):
                        bytes_data = uploaded_file.getvalue()
                        res = analyze_image_sightengine(bytes_data, sightengine_user, sightengine_secret)
                        
                        if res["success"]:
                            pct = res["percentage"]
                            st.markdown(f"### 📊 ЖИ (Deepfake) генерация ықтималдығы: **{pct}%**")
                            
                            # БОЛСА: ЖИ Заңгерлік Консультациясын автоматты шығару
                            if pct > 50:
                                st.error("🚨 ЕСКЕРТУ: Бұл суретте Жасанды Интеллект (Deepfake) белгілері анықталды!")
                                st.markdown("---")
                                st.subheader("⚖️ ЖИ Заңгерлік Консультациясы және Құқықтық Кеңес")
                                
                                st.warning("""
                                **⚠️ Бұзылған құқықтар:**
                                Азаматтың бейнесін ЖИ арқылы рұқсатсыз өңдеу, бұрмалау және тарату Қазақстан Республикасының заңнамасына қайшы келеді.
                                """)
                                
                                st.markdown("#### 🏛️ Сотқа немесе Полицияға (CyberPol) беретін ҚР Заң баптары:")
                                st.table([
                                    {"Заң / Кодекс": "ҚР Азаматтық кодексі 145-бап", "Құқық бұзышылық": "Жеке бейнеге құқық", "Соттық шешімі": "Медианы өшірткізу және тыйым салу"},
                                    {"Заң / Кодекс": "ҚР Азаматтық кодексі 143-бап", "Құқық бұзышылық": "Ар-намыс пен беделді қорғау", "Соттық шешімі": "Моральдық зиянды өндіріп алу (өтемақы)"},
                                    {"Заң / Кодекс": "ҚР Қылмыстық кодексі 147-бап", "Құқық бұзышылық": "Дербес деректерді бұзу", "Соттық шешімі": "Полиция арқылы қылмыстық іс қозғау"},
                                    {"Заң / Кодекс": "ҚР Қылмыстық кодексі 194-бап", "Құқық бұзышылық": "Бопсалау (Вымогательство)", "Соттық шешімі": "Ақша сұрап қорқытқан жағдайда"},
                                    {"Заң / Кодекс": "ҚР ӘҚБтК 456-2-бап", "Құқық бұзышылық": "Жалған ақпарат тарату", "Соттық шешімі": "Әкімшілік айыппұл салу"}
                                ])
                                
                                st.markdown("#### 📋 Іс-әрекет Алгоритмі (Не істеу керек?):")
                                st.markdown("""
                                1. **Дәлелдерді тіркеңіз:** Чаттарды, парақша сілтемелерін (URL) және скриншоттарды сақтаңыз.
                                2. **Полицияға (CyberPol) арызданыңыз:** **eOtinish.kz** арқылы немесе АІІБ-не ҚР ҚК 147-бабы бойынша арызданыңыз.
                                3. **Азаматтық сотқа беріңіз:** Авторы анықталған соң ҚР АК 143, 145-баптарымен моральдық өтемақы өндіру талап-арызын түсіріңіз.
                                """)
                            else:
                                st.success("✅ Сурет таза немесе ЖИ белгілері анықталмады (шынайы медиа болуы мүмкін).")
                        else:
                            st.error(f"Талдау қатесі: {res['error']}")

    else: # Видеофайл
        uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 Видеоны талдау"):
                if not sightengine_user or not sightengine_secret:
                    st.warning("⚠️ Өтініш, сол жақтағы Sidebar-ға Sightengine API кілттерін енгізіңіз!")
                else:
                    with st.spinner("Видео кадрлары ЖИ сараптамасынан өтуде..."):
                        v_bytes = uploaded_video.getvalue()
                        res = analyze_video_sightengine(v_bytes, sightengine_user, sightengine_secret)
                        
                        if res["success"]:
                            pct = res["percentage"]
                            st.markdown(f"### 📊 Видеодағы ЖИ (Deepfake) ықтималдығы: **{pct}%**")
                            
                            if pct > 50:
                                st.error("🚨 ЕСКЕРТУ: Видеода Жасанды Интеллект (Deepfake/FaceSwap) белгілері бар!")
                                st.markdown("---")
                                st.subheader("⚖️ ЖИ Заңгерлік Консультациясы және Құқықтық Кеңес")
                                
                                st.warning("⚠️ Бұл видео дипфейк технологиясымен жасалған. ҚР Заңнамасына сәйкес бұл азаматтың дербес деректерін бұзу саналады.")
                                
                                st.markdown("#### 🏛️ Сотқа немесе Полицияға (CyberPol) беретін ҚР Заң баптары:")
                                st.table([
                                    {"Заң / Кодекс": "ҚР Азаматтық кодексі 145-бап", "Құқық бұзышылық": "Жеке бейнеге құқық", "Соттық шешімі": "Видеоны бұғаттау/өшірткізу"},
                                    {"Заң / Кодекс": "ҚР Азаматтық кодексі 143-бап", "Құқық бұзышылық": "Ар-намысты қорғау", "Соттық шешімі": "Моральдық өтемақы өндіру"},
                                    {"Заң / Кодекс": "ҚР Қылмыстық кодексі 147-бап", "Құқық бұзышылық": "Дербес деректерді бұзу", "Соттық шешімі": "Қылмыстық жауапқа тарту"}
                                ])
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

        if not openai_key:
            st.warning("⚠️ Ассистент жұмыс істеуі үшін Sidebar-ға OpenAI API Key енгізіңіз.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Заңгерлік талдау жасалуда..."):
                    try:
                        client = openai.OpenAI(api_key=openai_key)
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
