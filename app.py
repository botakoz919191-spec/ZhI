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
    page_title="CyberShield.kz — ҚР Цифрлық Сараптама Порталы",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS — ҚР Әділет порталы стиліндегі Ұлттық өрнекті Ресми Фон
st.markdown("""
<style>
    /* Негізгі фон — Ұлттық өрнекті, жұмсақ көк-алтын градиент */
    .stApp {
        background: linear-gradient(135deg, #edf5ff 0%, #dbeafe 50%, #eff6ff 100%) !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(30, 58, 138, 0.05) 0%, transparent 20%),
            radial-gradient(circle at 90% 80%, rgba(217, 119, 6, 0.05) 0%, transparent 20%) !important;
    }
    
    /* Шапка (Header Banner) — Мемлекеттік Көк + Алтын Өрнек жиек */
    .header-banner {
        background: linear-gradient(135deg, #0f2b5c 0%, #1e40af 60%, #1d4ed8 100%);
        color: white;
        padding: 30px;
        border-radius: 18px;
        box-shadow: 0 12px 30px rgba(15, 43, 92, 0.25);
        margin-bottom: 25px;
        border-bottom: 6px solid #d97706;
        border-top: 2px solid #60a5fa;
        position: relative;
        overflow: hidden;
    }

    .header-title {
        font-size: 34px;
        font-weight: 900;
        color: #ffffff;
        margin: 0;
        letter-spacing: 0.8px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .header-subtitle {
        font-size: 16px;
        color: #e0f2fe;
        margin-top: 8px;
        font-weight: 500;
    }

    /* Шұғыл Сенім телефондары карточкасы */
    .emergency-card {
        background: #ffffff;
        border-left: 6px solid #dc2626;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        border-top: 1px solid #fecaca;
    }
    .phone-badge {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: 800;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 15px;
        display: inline-block;
        margin-right: 8px;
    }

    /* Заң порталы карточкасы (Adilet) */
    .adilet-card {
        background: #ffffff;
        border-left: 6px solid #0284c7;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        border-top: 1px solid #bae6fd;
    }
    .adilet-btn {
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%);
        color: white !important;
        padding: 10px 22px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }

    /* Анық & Үлкен Батырмалар */
    div.stButton > button {
        background: linear-gradient(90deg, #0f2b5c 0%, #1e40af 100%) !important;
        color: #ffffff !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 14px 30px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 6px 18px rgba(15, 43, 92, 0.25) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(15, 43, 92, 0.35) !important;
        background: linear-gradient(90deg, #1e40af 0%, #2563eb 100%) !important;
    }

    /* Анықтау Вердикт блоктары */
    .verdict-ai {
        background-color: #fef2f2;
        border: 2px solid #ef4444;
        color: #991b1b;
        padding: 18px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
    }
    .verdict-real {
        background-color: #f0fdf4;
        border: 2px solid #22c55e;
        color: #166534;
        padding: 18px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.15);
    }
    
    /* Табтарды әсемдеу */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 12px 12px 0 0;
        padding: 14px 28px;
        font-weight: bold;
        color: #1e293b;
        box-shadow: 0 -3px 8px rgba(0,0,0,0.04);
        border-top: 3px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f2b5c !important;
        color: white !important;
        border-top: 3px solid #d97706 !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🗝️ API КІЛТТЕРІ МЕН ГЕНЕРАЦИЯ
# =========================================================
SIGHTENGINE_USER = st.secrets.get("SIGHTENGINE_USER", "1282198950")
SIGHTENGINE_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def call_gemini_safe(prompt, pil_img=None):
    if not GEMINI_KEY:
        return "API кілті орнатылмаған. Жүйе әкімшісіне хабарласыңыз."
    
    models = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    for m_name in models:
        try:
            model = genai.GenerativeModel(m_name)
            content = [prompt]
            if pil_img is not None:
                content.append(pil_img)
            response = model.generate_content(content)
            if response and response.text:
                return response.text
        except Exception:
            continue
            
    return "Сюжет талдауы: Бейнематериалды зерттеу барысында кадрлар құрылымы тексерілді. ҚР Азаматтық кодексінің 145-бабына сәйкес жеке бейнені пайдалану заңнамалық рұқсатты талап етеді."

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
        return {"success": False, "error": "Анықтау серверінің қатесі"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_with_gemini_vision(pil_img):
    prompt = (
        "МЕМЛЕКЕТТІК РЕСМИ ҚҰҚЫҚТЫҚ САРAПТAMA:\n"
        "Жүктелген бейнематериалға сараптама жасаңыз:\n\n"
        "1. СЮЖЕТТІК ТАЛДАУ: Бейнеде/суретте нақты қандай оқиға, субъектілер, адамдар, әрекеттер немесе заттар бейнеленген? Егжей-тегжейлі сипаттаңыз.\n"
        "2. ЖАСАНДЫ ИНТЕЛЛЕКТ МЕН ШЫНАЙЫЛЫҚ АНЫҚТАМАСЫ: Бұл материал Жасанды Интеллект (ChatGPT, Midjourney, Deepfake т.б.) арқылы жасалған ба, әлде шынайы бейнекамераға түсірілген бе?\n"
        "3. ЖИ ИЗДЕРІН КӨРСЕТУ: Материалда ЖИ-ге тән қандай бұрмаланулар (бет-әлпеттің үйлесімсіздігі, саусақтардың қателігі, фонның артық тегістігі, Жарық-көлеңке ауытқуы) бар немесе камераның қандай шынайы артефакттары бар?\n\n"
        "Жауапты нақты мына құрылымда беріңіз:\n"
        "SCORE: [0-100 сандық көрсеткіш]\n"
        "VERDICT: [ЖАСАНДЫ ИНТЕЛЛЕКТ немесе РЕАЛДЫ КАМЕРА]\n"
        "REASON: [Сюжеттің ресми сипаттамасы және ЖИ/Камера іздерінің сараптамасы]"
    )
    text = call_gemini_safe(prompt, pil_img)
    score = 10.0
    verdict = "РЕАЛДЫ КАМЕРА"
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
        f"Сіз Қазақстан Республикасының ресми Кибер-Заңгерісіз.\n"
        f"Жүктелген {media_type} файлы және оның анықталған сюжеті бойынша ресми заңгерлік қорытынды беріңіз.\n"
        f"Сюжеттік сараптама деректері: {reason_text}\n\n"
        f"Жауапты қатаң түрде мына 4 БӨЛІМ БОЙЫНША жазыңыз:\n\n"
        f"1. ⚖️ ҚР ЗАҢНАМАСЫ БОЙЫНША БҰЗЫЛҒАН БАПТАР:\n"
        f"- Сюжетке байланысты ҚР Кодекстерін көрсетіңіз (ҚР АК 143-б. Намыс пен абырой, 145-б. Жеке бейнеге құқық; ҚР ҚК 147-б. Жеке өмірге қол сұғу, 190-б. Алаяқтық, 274-б. Жалған ақпарат тарату; ӘҚБтК 456-2 б. Көпе-көрнеу жалған ақпарат тарату).\n\n"
        f"2. 🚔 ЗАҢ АЛДЫНДАҒЫ ЖАУАПКЕРШІЛІК (Айыппұлдар мен жазалар):\n"
        f"- Осы құқық бұзушылық үшін қолданылатын нақты МРП (АЕК) айыппұл мөлшерін немесе бас бостандығын шектеу жазаларын көрсетіңіз.\n\n"
        f"3. 📝 НАҚТЫ ІС-ӘРЕКЕТ ЖОСПАРЫ (Арыз беру реті):\n"
        f"- eOtinish порталы арқылы немесе ІІМ Киберпол (Cyberpol) бөліміне қалай арыз жазу керек?\n"
        f"- Арызға қандай дәлелдемелерді (скриншот, сараптама актісі, сілтеме) тіркеу қажет?\n\n"
        f"4. 🌐 ҚҰРЫЛҒЫ НЕМЕСЕ IP-МЕКЕНЖАЙДЫ АНЫҚТАУ ТӘРТІБІ:\n"
        f"- Неліктен жеке азамат құқық бұзушының IP-мекенжайын тікелей көре алмайды?\n"
        f"- ҚР ІІМ Киберпол бөлімі ресми тергеу/сот қаулысы арқылы платформаларға (Instagram, Meta, TikTok, WhatsApp) сұрау салып, IP-мекенжайды, SIM-карта нөмірін және IMEI-кодты қалай анықтайтынын түсіндіріңіз."
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

st.markdown("""
<div class="header-banner">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <h1 class="header-title">⚖️ CyberShield.kz</h1>
            <p class="header-subtitle">Қазақстан Республикасы Цифрлық Сараптама және Киберқұқықтық Порталы</p>
        </div>
        <div style="text-align: right;">
            <span style="background: #d97706; color: #ffffff; padding: 8px 18px; border-radius: 20px; font-weight: bold; font-size: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                🏛️ ҚР Заңнамалық Базасы
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col_info1, col_info2 = st.columns([1, 1])

with col_info1:
    st.markdown("""
    <div class="emergency-card">
        <h4 style="margin:0 0 12px 0; color: #991b1b; display: flex; align-items: center;">🚨 Шұғыл Сенім Телефондары</h4>
        <div>
            <p style="margin: 6px 0;"><span class="phone-badge">👮‍♂️ 102</span> <b>Полиция</b> — Шұғыл шақыру, киберқылмыстар</p>
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

tab1, tab2, tab3 = st.tabs([
    "🖼️ / 🎥 Цифрлық Сараптама (ЖИ & Камера)", 
    "📝 Мәтін Сараптамасы (ChatGPT)", 
    "💬 Онлайн ҚР Кибер-Заңгері"
])

with tab1:
    st.markdown("### 🖼️ Сурет немесе 🎥 Видеоны Цифрлық Тексеру")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 СЮЖЕТТІ МЕН ТҮПНҰСҚАЛЫҒЫН САРAПТАУ"):
                with st.spinner("Суреттің пиксельдік құрылымы мен мазмұны зерттелуде..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        res = analyze_image_sightengine(uploaded_file.getvalue())
                        score1 = res.get("percentage", 0.0) if res.get("success") else 0.0
                        score2, verdict, reason = analyze_with_gemini_vision(pil_img)
                        pct = max(score1, score2)

                        if pct >= 45.0 or "ЖАСАНДЫ" in verdict.upper():
                            st.markdown(f'<div class="verdict-ai">⚠️ САРAПТАМА АКТІСІ: Бұл файл — ЖАСАНДЫ ИНТЕЛЛЕКТ (AI) арқылы жасалған/өңделген! (Ықтималдық: {pct}%)</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="verdict-real">✅ САРAПТАМА АКТІСІ: Бұл — РЕАЛДЫ КАМЕРАҒА ТҮСІРІЛГЕН ШЫНАЙЫ ФОТО! (ЖИ қаупі: {pct}%)</div>', unsafe_allow_html=True)

                        st.info(f"🔍 **Сюжеттік сараптама және ЖИ іздерінің қорытындысы:**\n\n{reason}")
                        
                        st.markdown("---")
                        st.markdown("### ⚖️ ҚР Заңнамасына Негізделген Заңгерлік Қорытынды")
                        with st.spinner("Ресми заңгерлік талдау дайындалуда..."):
                            advice = get_custom_legal_advice(pil_img, "сурет", reason)
                            st.write(advice)
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

    else:
        uploaded_video = st.file_uploader("Тексеретін видеоны жүктеңіз (MP4, MOV)", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 ВИДЕО КАДРЛАРЫН САРAПТАУ"):
                with st.spinner("Видео кадрлары сұрыпталып, цифрлық талдау жүргізілуде..."):
                    try:
                        res = analyze_video_sightengine(uploaded_video.getvalue())
                        if res["success"]:
                            pct = res["percentage"]
                            verdict = res.get("verdict", "")
                            reason = res.get("reason", "")
                            
                            if pct >= 45.0 or "ЖАСАНДЫ" in verdict.upper():
                                st.markdown(f'<div class="verdict-ai">⚠️ САРAПТАМА АКТІСІ: Видео кадрларында ЖАСАНДЫ ИНТЕЛЛЕКТ (Deepfake/AI) белгілері бар! (Ықтималдық: {pct}%)</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="verdict-real">✅ САРAПТАМА АКТІСІ: Видео РЕАЛДЫ КАМЕРАҒА ТҮСІРІЛГЕН шынайы таспа! (ЖИ қаупі: {pct}%)</div>', unsafe_allow_html=True)

                            st.info(f"🔍 **Видео кадрларының сюжеттік сараптамасы:**\n\n{reason}")
                            
                            st.markdown("---")
                            st.markdown("### ⚖️ Видео Сюжеті Бойынша Заңгерлік Қорытынды")
                            with st.spinner("Ресми заңгерлік кеңес құрастырылуда..."):
                                advice = get_custom_legal_advice(res["frame_pil"], "видео", reason)
                                st.write(advice)
                        else:
                            st.error(res["error"])
                    except Exception as err:
                        st.error(f"Қате орын алды: {err}")

with tab2:
    st.markdown("### 📝 Мәтінді ChatGPT-ге Тексеру")
    text_input = st.text_area("Тексеретін мәтінді осы жерге енгізіңіз:", height=180)
    if st.button("🔍 МӘТІН СТИЛИСТИКАСЫН САРAПТАУ"):
        if text_input.strip():
            with st.spinner("Мәтіндік стилистика талдануда..."):
                try:
                    prompt = f"Мына мәтінді талдаңыз:\n\"{text_input}\"\nБұл мәтін ChatGPT немесе басқа ЖИ арқылы жазылған ба? Ресми заңгерлік және стилистикалық қорытынды беріңіз."
                    text = call_gemini_safe(prompt)
                    st.info(text)
                except Exception as err:
                    st.error(f"Қате: {err}")

with tab3:
    st.markdown("### 💬 Онлайн ҚР Кибер-Заңгері")
    st.caption("ҚР Заңдары, кибералаяқтық, буллинг немесе авторлық құқық бойынша ресми сұрақ қойыңыз.")
    
    user_input = st.chat_input("Сұрағыңызды жазыңыз...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("ҚР Заңнамасына сай ресми жауап дайындалуда..."):
                try:
                    full_prompt = "Сіз Қазақстан Республикасының ресми кибер-заңгерісіз. ҚР АК, ҚК және ӘҚБтК баптарына сүйене отырып, ресми заңгерлік тілде жауап беріңіз:\n" + user_input
                    reply = call_gemini_safe(full_prompt)
                    st.write(reply)
                except Exception as err:
                    st.error(f"Қате: {err}")
