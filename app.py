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

# Custom CSS — adilet.zan.kz стиліндегі ресми & заманауи дизайн
st.markdown("""
<style>
    /* Негізгі фон мен шрифт */
    .main {
        background-color: #f8fafc;
    }
    
    /* Шапка (Header) */
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        border-bottom: 4px solid #f59e0b;
    }
    .header-title {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .header-subtitle {
        font-size: 16px;
        color: #cbd5e1;
        margin-top: 5px;
    }

    /* Шұғыл Сенім телефондары блогы */
    .emergency-card {
        background-color: #ffffff;
        border-left: 5px solid #dc2626;
        padding: 18px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .phone-badge {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 15px;
        display: inline-block;
        margin-right: 8px;
    }

    /* Заң порталы блогы (Adilet) */
    .adilet-card {
        background-color: #ffffff;
        border-left: 5px solid #0284c7;
        padding: 18px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .adilet-btn {
        background-color: #0284c7;
        color: white !important;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-top: 8px;
    }

    /* Анық & Айқын Батырмалар */
    div.stButton > button {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%) !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 12px 28px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* Табтарды әсемдеу */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: bold;
        color: #334155;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🗝️ API КІЛТТЕРІ МЕН МОДЕЛЬДЕР
# =========================================================
SIGHTENGINE_USER = st.secrets.get("SIGHTENGINE_USER", "1282198950")
SIGHTENGINE_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def call_gemini_safe(prompt, pil_img=None):
    """ Қатесіз жұмыс істейтін автоматикалық модель таңдау """
    if not GEMINI_KEY:
        return "API кілт енгізілмеген. Streamlit Secrets тексеріңіз."
    
    time.sleep(1)
    
    # 404/429 қателерін болдырмау үшін модельдерді кезекпен тексеру
    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-flash']
    
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
            
    return "ЖИ жауап беруде уақытша іркіліс болды. Қайталап көріңіз."

# ---------------------------------------------------------
# Талдау Функциялары
# ---------------------------------------------------------
def analyze_image_sightengine(image_bytes):
    url = 'https://api.sightengine.com/1.0/check.json'
    params = {'models': 'genai', 'api_user': SIGHTENGINE_USER, 'api_secret': SIGHTENGINE_SECRET}
    files = {'media': image_bytes}
    try:
        res = requests.post(url, files=files, data=params, timeout=10)
        out = json.loads(res.text)
        if out.get('status') == 'success':
            score = out.get('type', {}).get('ai_generated', 0)
            return {"success": True, "percentage": round(score * 100, 2)}
        return {"success": False, "error": "Sightengine қатесі"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_with_gemini_vision(pil_img):
    prompt = (
        "Осы суретті немесе тапсырманы ТАЛДА.\n"
        "1. Суретте не бейнеленген? Мазмұны мен сюжеті қандай?\n"
        "2. Бұл сурет Жасанды Интеллект (ChatGPT, Midjourney, Deepfake т.б.) арқылы жасалған ба?\n"
        "Жауапты ТЕК МЫНА ФОРМАТТА бер:\n"
        "SCORE: [0-100 аралығындағы сан]\n"
        "REASON: [Сурет мазмұнына сүйене отырып, анықталған ЖИ белгілері мен дәлелдері]"
    )
    text = call_gemini_safe(prompt, pil_img)
    score = 0.0
    reason = text
    if "SCORE:" in text:
        try:
            score_str = text.split("SCORE:")[1].split("\n")[0].strip()
            score = float(''.join(c for c in score_str if c.isdigit() or c=='.'))
        except:
            score = 50.0
    if "REASON:" in text:
        reason = text.split("REASON:")[1].strip()
    return score, reason

def get_custom_legal_advice(pil_img, media_type, reason_text):
    prompt = (
        f"Сіз Қазақстан Республикасының тәжірибелі кибер-заңгерісіз.\n"
        f"Жүктелген {media_type} материалын және оның ішіндегі СЮЖЕТТІ ТЕРЕҢ ТАЛДАҢЫЗ.\n"
        f"Анықталған ЖИ белгілері: {reason_text}\n\n"
        f"1. СУРЕТТІҢ/ВИДЕОНЫҢ ІШКІ СЮЖЕТІН сипаттаңыз.\n"
        f"2. Осы сюжетке байланысты ҚР Заңдары (ҚР АК 143, 145; ҚР ҚК 147, 190; ӘҚБтК 456-2) бойынша бұзылған құқықтарды көрсетіңіз.\n"
        f"3. Осы жағдайда азаматқа нақты 3 қадамдық заңдық кеңес беріңіз."
    )
    return call_gemini_safe(prompt, pil_img)

def analyze_text_chatgpt(text_content):
    prompt = (
        f"Мына мәтінді талда:\n\"{text_content}\"\n"
        "Бұл мәтін ChatGPT немесе ЖИ арқылы жазылған ба? "
        "Жауапты ТЕК МЫНА ФОРМАТТА бер:\n"
        "SCORE: [0-100 аралығындағы сан]\n"
        "REASON: [ЖИ-ге тән стилистикалық дәлелдер]"
    )
    text = call_gemini_safe(prompt)
    score = 0.0
    reason = text
    if "SCORE:" in text:
        try:
            score_str = text.split("SCORE:")[1].split("\n")[0].strip()
            score = float(''.join(c for c in score_str if c.isdigit() or c=='.'))
        except:
            score = 50.0
    if "REASON:" in text:
        reason = text.split("REASON:")[1].strip()
    return score, reason

def analyze_video_sightengine(video_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(video_bytes)
        tmp_file_path = tmp_file.name

    cap = cv2.VideoCapture(tmp_file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames <= 0:
        cap.release()
        return {"success": False, "error": "Видео оқылмады", "frame_pil": None, "reason": ""}

    # Видеодан сапалы кадр сурып алу
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.5))
    ret, frame = cap.read()
    cap.release()

    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        _, buffer = cv2.imencode('.jpg', frame)
        
        s_res = analyze_image_sightengine(buffer.tobytes())
        score1 = s_res.get("percentage", 0.0) if s_res.get("success") else 0.0
        score2, reason2 = analyze_with_gemini_vision(pil_img)

        curr_score = max(score1, score2)
        return {"success": True, "percentage": round(curr_score, 2), "frame_pil": pil_img, "reason": reason2}
    
    return {"success": False, "error": "Видеодан кадр алынбады", "frame_pil": None, "reason": ""}

# =========================================================
# 🏛️ ИНТЕРФЕЙС / ДИЗАЙН (CyberShield.kz)
# =========================================================

# Шапка (Header)
st.markdown("""
<div class="header-banner">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <h1 class="header-title">⚖️ CyberShield.kz</h1>
            <p class="header-subtitle">Қазақстан Республикасы Киберқорғаныс және ЖИ Дижитал Сараптама Порталы</p>
        </div>
        <div style="text-align: right;">
            <span style="background: #f59e0b; color: #0f172a; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px;">
                🏛️ ҚР Заңнамасына сай
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Жоғарғы Барабан: Сенім телефондары мен Әділет порталы
col_info1, col_info2 = st.columns([1, 1])

with col_info1:
    st.markdown("""
    <div class="emergency-card">
        <h4 style="margin-0; color: #991b1b; display: flex; align-items: center;">🚨 Шұғыл Көмек & Сенім Телефондары</h4>
        <div style="margin-top: 10px;">
            <p style="margin: 4px 0;"><span class="phone-badge">102</span> <b>Полиция</b> (Қылмыс пен киберқұқық бұзушылықтар)</p>
            <p style="margin: 4px 0;"><span class="phone-badge">1402</span> <b>ҚР ІІМ Сенім телефоны</b> (Азаматтық қорғау)</p>
            <p style="margin: 4px 0;"><span class="phone-badge">111</span> <b>Отбасы, әйелдер мен балаларды қорғау</b></p>
            <p style="margin: 4px 0;"><span class="phone-badge">1424</span> <b>Антикор</b> (Сыбайлас жемқорлыққа қарсы)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_info2:
    st.markdown("""
    <div class="adilet-card">
        <h4 style="margin-0; color: #0369a1;">📚 ҚР Нормативтік-Құқықтық Базасы</h4>
        <p style="margin-top: 8px; font-size: 14px; color: #334155;">
            Ресми заңдар, кодекстер мен құқықтық актілердің толық базасымен <b>«Әділет» (adilet.zan.kz)</b> ақпараттық-құқықтық порталынан таныса аласыз.
        </p>
        <a href="https://adilet.zan.kz/kaz" target="_blank" class="adilet-btn">
            🔗 adilet.zan.kz Порталына Өту ↗
        </a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# 📑 НЕГІЗГІ МОДУЛЬДЕР (ТИН)
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "🖼️ / 🎥 Медиа Сараптама (ЖИ & Сюжет)", 
    "📝 Мәтінді Тексеру (ChatGPT)", 
    "💬 Онлайн ЖИ Заңгер Көмекшісі"
])

# 1-ТАБ: МЕДИА
with tab1:
    st.markdown("### 🖼️ Сурет немесе 🎥 Видеоны Терең Сараптау")
    media_type = st.radio("Материал түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 СЮЖЕТТІ МЕН ЖИ-ДІ ТАЛДАУ"):
                with st.spinner("ЖИ суреттің ішкі сюжетін оқып, дижитал сараптама жасауда..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        res = analyze_image_sightengine(uploaded_file.getvalue())
                        score1 = res.get("percentage", 0.0) if res.get("success") else 0.0
                        score2, reason = analyze_with_gemini_vision(pil_img)
                        pct = max(score1, score2)

                        st.markdown(f"### 📊 ЖИ Ықтималдығы: **{pct}%**")
                        st.info(f"🔍 **Анықталған сюжет пен ЖИ белгілері:**\n\n{reason}")
                        
                        st.markdown("---")
                        st.markdown("### ⚖️ Сюжетке Негізделген ҚР Заңгерлік Қорытындысы")
                        with st.spinner("ҚР Заңнамасына (АК, ҚК, ӘҚБтК) сүйене отырып заңдық кеңес дайындалуда..."):
                            advice = get_custom_legal_advice(pil_img, "сурет", reason)
                            st.write(advice)
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

    else:
        uploaded_video = st.file_uploader("Тексеретін видеоны жүктеңіз (MP4, MOV)", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 ВИДЕО СЮЖЕТІН ТАЛДАУ"):
                with st.spinner("Видео кадрлары сканерленіп, мазмұны оқылуда..."):
                    try:
                        res = analyze_video_sightengine(uploaded_video.getvalue())
                        if res["success"]:
                            pct = res["percentage"]
                            reason = res.get("reason", "")
                            st.markdown(f"### 📊 Видеодағы ЖИ Ықтималдығы: **{pct}%**")
                            st.info(f"🔍 **Видео кадрларының сараптамасы:**\n\n{reason}")
                            
                            st.markdown("---")
                            st.markdown("### ⚖️ Видео Сюжеті Бойынша Заңгерлік Қорытынды")
                            with st.spinner("Заңгерлік кеңес құрастырылуда..."):
                                advice = get_custom_legal_advice(res["frame_pil"], "видео", reason)
                                st.write(advice)
                        else:
                            st.error(res["error"])
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

# 2-ТАБ: МӘТІН
with tab2:
    st.markdown("### 📝 Мәтінді ChatGPT және ЖИ-ге Тексеру")
    text_input = st.text_area("Тексеретін мәтінді осы жерге қойыңыз:", height=200)
    if st.button("🔍 МӘТІНДІ ТЕКСЕРУ"):
        if text_input.strip():
            with st.spinner("Мәтіннің стилистикалық ЖИ белгілері талдануда..."):
                try:
                    pct, reason = analyze_text_chatgpt(text_input)
                    st.markdown(f"### 📊 Мәтіннің ЖИ арқылы жазылу ықтималдығы: **{pct}%**")
                    st.info(f"🔍 **Сараптамалық дәлелдер:**\n\n{reason}")
                except Exception as err:
                    st.error(f"Қате: {err}")

# 3-ТАБ: ЗАҢГЕР
with tab3:
    st.markdown("### 💬 Онлайн ҚР Кибер-Заңгер Көмекшісі")
    st.caption("Құқық бұзушылық, кибер-алаяқтық немесе заң баптары бойынша сұрағыңызды қойыңыз.")
    
    user_input = st.chat_input("Сұрағыңызды жазыңыз...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("ҚР Заңнамалары бойынша кеңес дайындалуда..."):
                try:
                    full_prompt = (
                        "Сіз Қазақстан Республикасының кәсіби кибер-заңгерісіз. "
                        "ҚР АК, ҚК, ӘҚБтК баптары мен adilet.zan.kz базасына сүйене отырып, қазақ тілінде нақты, ресми кеңес беріңіз:\n"
                        + user_input
                    )
                    reply = call_gemini_safe(full_prompt)
                    st.write(reply)
                except Exception as err:
                    st.error(f"Қате: {err}")
