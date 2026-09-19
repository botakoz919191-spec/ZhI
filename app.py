import streamlit as st
import requests
import json
import tempfile
import cv2
import time
from PIL import Image
import google.generativeai as genai

# =========================================================
# ⚙️ БЕТТІҢ ДИЗАЙНЫ МЕН БАПТАУЛАРЫ
# =========================================================
st.set_page_config(
    page_title="CyberShield.kz — ҚР Киберқорғаныс және Заң Порталы",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS — Заң және құқық саласына арналған Ашық-Көк Премиум стиль
st.markdown("""
<style>
    /* Негізгі фон — Жұмсақ ашық-көк */
    .stApp {
        background: linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%) !important;
    }
    
    /* Шапка (Header) */
    .header-banner {
        background: linear-gradient(135deg, #0b2545 0%, #134074 50%, #8da9c4 100%);
        color: white;
        padding: 26px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(11, 37, 69, 0.2);
        margin-bottom: 25px;
        border-bottom: 5px solid #e0a96d;
    }
    .header-title {
        font-size: 34px;
        font-weight: 900;
        color: #ffffff;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .header-subtitle {
        font-size: 16px;
        color: #e0e1dd;
        margin-top: 6px;
    }

    /* Шұғыл Сенім телефондары карточкасы */
    .emergency-card {
        background-color: #ffffff;
        border-left: 6px solid #dc2626;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 20px;
    }
    .phone-badge {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: 800;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 15px;
        display: inline-block;
        margin-right: 8px;
    }

    /* Заң порталы карточкасы (Adilet) */
    .adilet-card {
        background-color: #ffffff;
        border-left: 6px solid #0284c7;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 20px;
    }
    .adilet-btn {
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%);
        color: white !important;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
    }

    /* Анық, үлкен & айқын батырмалар */
    div.stButton > button {
        background: linear-gradient(90deg, #0b2545 0%, #134074 100%) !important;
        color: #ffffff !important;
        font-size: 19px !important;
        font-weight: bold !important;
        padding: 14px 30px !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 6px 15px rgba(11, 37, 69, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(11, 37, 69, 0.4) !important;
        background: linear-gradient(90deg, #134074 0%, #8da9c4 100%) !important;
    }

    /* Анықтау Вердикт блоктары */
    .verdict-ai {
        background-color: #fef2f2;
        border: 2px solid #ef4444;
        color: #991b1b;
        padding: 16px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
    }
    .verdict-real {
        background-color: #f0fdf4;
        border: 2px solid #22c55e;
        color: #166534;
        padding: 16px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
    }
    
    /* Табтарды әсемдеу */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        padding: 14px 28px;
        font-weight: bold;
        color: #1e293b;
        box-shadow: 0 -2px 6px rgba(0,0,0,0.03);
    }
    .stTabs [aria-selected="true"] {
        background-color: #0b2545 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🗝️ API КІЛТТЕРІ МЕН ҚАТЕСІЗ ГЕНЕРАЦИЯ
# =========================================================
SIGHTENGINE_USER = st.secrets.get("SIGHTENGINE_USER", "1282198950")
SIGHTENGINE_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def call_gemini_safe(prompt, pil_img=None):
    """ Толықтай стабильді Gemini шақыру функциясы """
    if not GEMINI_KEY:
        return "API кілт енгізілмеген. Streamlit Secrets бөлімін тексеріңіз."
    
    # Модельдер тізімі (Ресми жұмыс істейтін атаулар)
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            inputs = [prompt]
            if pil_img is not None:
                inputs.append(pil_img)
            res = model.generate_content(inputs)
            if res and res.text:
                return res.text
        except Exception:
            continue
            
    return "ЖИ жауап дайындауда. Сұранысты қайталап көріңіз."

# ---------------------------------------------------------
# Сараптама Функциялары
# ---------------------------------------------------------
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
        return {"success": False, "error": "Sightengine қатесі"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_with_gemini_vision(pil_img):
    prompt = (
        "МАТЕРИАЛДЫ ДИНАМИКАЛЫҚ ТАЛДАҢЫЗ:\n"
        "1. Суретте/Кадрда не бейнеленген? Мазмұны мен сюжеті қандай?\n"
        "2. Бұл реальный видеокамераға/фотоаппаратқа түсірілген шынайы фото ма, әлде Жасанды Интеллект (ChatGPT, Midjourney, Deepfake т.б.) арқылы жасалған ба?\n"
        "Жауапты ТЕК МЫНА ФОРМАТТА беріңіз:\n"
        "SCORE: [0-100 аралығында ЖИ ықтималдығының саны]\n"
        "VERDICT: [ЖАСАНДЫ ИНТЕЛЛЕКТ немесе РЕАЛДЫ КАМЕРА]\n"
        "REASON: [Анықталған мазмұн, визуалды дәлелдер мен ЖИ немесе Камера белгілері]"
    )
    text = call_gemini_safe(prompt, pil_img)
    score = 0.0
    verdict = "БЕЛГІСІЗ"
    reason = text

    if "SCORE:" in text:
        try:
            score_str = text.split("SCORE:")[1].split("\n")[0].strip()
            score = float(''.join(c for c in score_str if c.isdigit() or c=='.'))
        except:
            score = 10.0
    if "VERDICT:" in text:
        verdict = text.split("VERDICT:")[1].split("\n")[0].strip()
    if "REASON:" in text:
        reason = text.split("REASON:")[1].strip()

    return score, verdict, reason

def get_custom_legal_advice(pil_img, media_type, reason_text):
    prompt = (
        f"Сіз Қазақстан Республикасының кәсіби Кибер-Заңгерісіз.\n"
        f"Жүктелген {media_type} материалын және оның сюжетін терең заңдық талдау жасаңыз.\n"
        f"Сараптама қорытындысы: {reason_text}\n\n"
        f"1. МАТЕРИАЛ СЮЖЕТІ: Жүктелген файлда не бейнеленгенін қысқаша сипаттаңыз.\n"
        f"2. ҚР ЗАҢНАМАСЫ: ҚР Азаматтық Кодексі (143, 145-баптар - жеке бас құқығы), ҚР Қылмыстық Кодексі (147, 190-баптар - алаяқтық, жеке өмірге қол сұғу) немесе ӘҚБтК 456-2 бабы бойынша бұзылуы мүмкін заңдарды көрсетіңіз.\n"
        f"3. 3-ҚАДАМДЫҚ ЗАҢДЫҚ КЕҢЕС: Азамат өз құқығын қорғау үшін қандай нақты іс-әрекет жасауы керек?"
    )
    return call_gemini_safe(prompt, pil_img)

def analyze_video_sightengine(video_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(video_bytes)
        tmp_file_path = tmp_file.name

    cap = cv2.VideoCapture(tmp_file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames <= 0:
        cap.release()
        return {"success": False, "error": "Видео оқылуда қате болды", "frame_pil": None, "reason": ""}

    # Орталық анық кадрды сурып алу
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.5))
    ret, frame = cap.read()
    cap.release()

    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        _, buffer = cv2.imencode('.jpg', frame)
        
        s_res = analyze_image_sightengine(buffer.tobytes())
        score1 = s_res.get("percentage", 0.0) if s_res.get("success") else 0.0
        score2, verdict, reason2 = analyze_with_gemini_vision(pil_img)

        curr_score = max(score1, score2)
        return {
            "success": True, 
            "percentage": round(curr_score, 2), 
            "verdict": verdict,
            "frame_pil": pil_img, 
            "reason": reason2
        }
    
    return {"success": False, "error": "Видео кадры алынбады", "frame_pil": None, "reason": ""}

# =========================================================
# 🏛️ ИНТЕРФЕЙС / ДИЗАЙН (CyberShield.kz)
# =========================================================

# Шапка (Header)
st.markdown("""
<div class="header-banner">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <h1 class="header-title">⚖️ CyberShield.kz</h1>
            <p class="header-subtitle">Қазақстан Республикасы Дижитал Сараптама және Киберқұқықтық Порталы</p>
        </div>
        <div style="text-align: right;">
            <span style="background: #e0a96d; color: #0b2545; padding: 8px 18px; border-radius: 20px; font-weight: bold; font-size: 15px;">
                🏛️ ҚР Заңнамалық Базасы
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Жоғарғы Блок: Сенім телефондары (Эмблемалармен) мен Әділет порталы
col_info1, col_info2 = st.columns([1, 1])

with col_info1:
    st.markdown("""
    <div class="emergency-card">
        <h4 style="margin:0 0 12px 0; color: #991b1b; display: flex; align-items: center;">🚨 Шұғыл Сенім Телефондары</h4>
        <div>
            <p style="margin: 6px 0;"><span class="phone-badge">👮‍♂️ 102</span> <b>Полиция</b> — Опер-шақыру, киберқылмыстар</p>
            <p style="margin: 6px 0;"><span class="phone-badge">🛡️ 1402</span> <b>ҚР ІІМ</b> — Азаматтардың құқығын қорғау</p>
            <p style="margin: 6px 0;"><span class="phone-badge">👨‍👩‍👧‍👦 111</span> <b>Сенім желісі</b> — Отбасы, әйелдер мен балалар</p>
            <p style="margin: 6px 0;"><span class="phone-badge">🏛️ 1424</span> <b>Антикор</b> — Сыбайлас жемқорлыққа қарсы</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_info2:
    st.markdown("""
    <div class="adilet-card">
        <h4 style="margin:0 0 10px 0; color: #0369a1;">📖 Ресми Ақпараттық-Құқықтық Портал</h4>
        <p style="margin-top: 6px; font-size: 14px; color: #334155; line-height: 1.5;">
            Қазақстан Республикасы Әділет министрлігінің нормативтік-құқықтық актілері, Кодекстері мен Заңдарының бірыңғай базасы:
        </p>
        <a href="https://adilet.zan.kz/kaz" target="_blank" class="adilet-btn">
            🔗 adilet.zan.kz Базасына Өту ↗
        </a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# 📑 МОДУЛЬДЕР
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "🖼️ / 🎥 Медиа Сараптама (ЖИ & Камера)", 
    "📝 Мәтін Сараптамасы (ChatGPT)", 
    "💬 Онлайн ҚР Кибер-Заңгері"
])

# 1-ТАБ: МЕДИА
with tab1:
    st.markdown("### 🖼️ Сурет немесе 🎥 Видеоны Дижитал Тексеру")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 СЮЖЕТТІ МЕН САПА САРAПТАМАСЫН БАСТАУ"):
                with st.spinner("Суреттің пиксельдері мен ішкі сюжеті тексерілуде..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        res = analyze_image_sightengine(uploaded_file.getvalue())
                        score1 = res.get("percentage", 0.0) if res.get("success") else 0.0
                        score2, verdict, reason = analyze_with_gemini_vision(pil_img)
                        pct = max(score1, score2)

                        # Анықтау вердикті
                        if pct >= 45.0 or "ЖАСАНДЫ" in verdict.upper():
                            st.markdown(f'<div class="verdict-ai">⚠️ АНЫҚТАМА: Бұл файл — ЖАСАНДЫ ИНТЕЛЛЕКТ (AI) арқылы жасалған/өңделген! (Ықтималдық: {pct}%)</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="verdict-real">✅ АНЫҚТАМА: Бұл — РЕАЛДЫ КАМЕРАҒА ТҮСІРІЛГЕН ШЫНАЙЫ ФОТО! (ЖИ қаупі: {pct}%)</div>', unsafe_allow_html=True)

                        st.info(f"🔍 **Сараптамалық қорытынды мен сюжет дәлелдері:**\n\n{reason}")
                        
                        st.markdown("---")
                        st.markdown("### ⚖️ ҚР Заңнамасына Негізделген Заңгерлік Қорытынды")
                        with st.spinner("Заңгерлік талдау жасалуда..."):
                            advice = get_custom_legal_advice(pil_img, "сурет", reason)
                            st.write(advice)
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

    else:
        uploaded_video = st.file_uploader("Тексеретін видеоны жүктеңіз (MP4, MOV)", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 ВИДЕО КАДРЛАРЫН ТАЛДАУ"):
                with st.spinner("Видео кадрлары сурып алынып, мазмұны сканерленуде..."):
                    try:
                        res = analyze_video_sightengine(uploaded_video.getvalue())
                        if res["success"]:
                            pct = res["percentage"]
                            verdict = res.get("verdict", "")
                            reason = res.get("reason", "")
                            
                            if pct >= 45.0 or "ЖАСАНДЫ" in verdict.upper():
                                st.markdown(f'<div class="verdict-ai">⚠️ АНЫҚТАМА: Видео кадрларында ЖАСАНДЫ ИНТЕЛЛЕКТ (Deepfake/AI) белгілері бар! (Ықтималдық: {pct}%)</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="verdict-real">✅ АНЫҚТАМА: Видео РЕАЛДЫ КАМЕРАҒА ТҮСІРІЛГЕН шынайы таспа! (ЖИ қаупі: {pct}%)</div>', unsafe_allow_html=True)

                            st.info(f"🔍 **Видео кадрларының сараптамасы:**\n\n{reason}")
                            
                            st.markdown("---")
                            st.markdown("### ⚖️ Видео Сюжеті Бойынша Заңгерлік Қорытынды")
                            with st.spinner("ҚР Заңдары бойынша кеңес құрастырылуда..."):
                                advice = get_custom_legal_advice(res["frame_pil"], "видео", reason)
                                st.write(advice)
                        else:
                            st.error(res["error"])
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

# 2-ТАБ: МӘТІН
with tab2:
    st.markdown("### 📝 Мәтінді ChatGPT-ге Тексеру")
    text_input = st.text_area("Тексеретін мәтінді осы жерге енгізіңіз:", height=180)
    if st.button("🔍 МӘТІН СТИЛИН ТЕКСЕРУ"):
        if text_input.strip():
            with st.spinner("Мәтіндік стилистика талдануда..."):
                try:
                    prompt = (
                        f"Мына мәтінді талда:\n\"{text_input}\"\n"
                        "Бұл мәтін ChatGPT немесе ЖИ арқылы жазылған ба? "
                        "Жауапты ТЕК МЫНА ФОРМАТТА бер:\n"
                        "SCORE: [0-100 аралығындағы сан]\n"
                        "REASON: [ЖИ-ге немесе адамға тән стилистикалық дәлелдер]"
                    )
                    text = call_gemini_safe(prompt)
                    st.info(text)
                except Exception as err:
                    st.error(f"Қате: {err}")

# 3-ТАБ: ЗАҢГЕР
with tab3:
    st.markdown("### 💬 Онлайн ҚР Кибер-Заңгері")
    st.caption("ҚР Заңдары, алаяқтық, буллинг немесе авторлық құқық бойынша сұрақ қойыңыз.")
    
    user_input = st.chat_input("Сұрағыңызды жазыңыз...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Заңнамалық жауап дайындалуда..."):
                try:
                    full_prompt = (
                        "Сіз Қазақстан Республикасының ресми кибер-заңгерісіз. "
                        "ҚР АК, ҚК, ӘҚБтК баптары мен adilet.zan.kz базасына сүйене отырып, қазақ тілінде нақты кеңес беріңіз:\n"
                        + user_input
                    )
                    reply = call_gemini_safe(full_prompt)
                    st.write(reply)
                except Exception as err:
                    st.error(f"Қате: {err}")
