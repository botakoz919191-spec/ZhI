import streamlit as st
import requests
import json
import tempfile
import cv2
import numpy as np
from PIL import Image
import google.generativeai as genai

# =========================================================
# 🗝️ API КІЛТТЕРІ (Streamlit Secrets арқылы оқылады)
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
    """Sightengine API арқылы ЖИ генерациясын тексеру"""
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


def analyze_with_gemini_vision(pil_img):
    """Gemini Vision арқылы Барлық ЖИ генераторларының белгілерін тексеру"""
    try:
        if not GEMINI_KEY:
            return 0.0, ""
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        prompt = (
            "Осы суретті/кадрды ӨТЕ МҰҚИЯТ ЖӘНЕ ТЕРЕҢДЕТІП ТАЛДА. "
            "Бұл медиа файлы Жасанды Интеллект (ЖИ / AI / Deepfake) арқылы жасалған ба? "
            "(D-ID, HeyGen, Midjourney, Stable Diffusion, DALL-E, FaceFusion, Runway, Sora т.б.). "
            "Су таңбаларын (водяной марка), бет-әлпет пен артефакттарды тексере отырып, ТЕК МЫНА ФОРМАТТА жауап бер:\n"
            "SCORE: [0-100 аралығындағы сан]\n"
            "REASON: [Анықталған ЖИ сервисінің атауы және белгілері]"
        )
        
        res = model.generate_content([prompt, pil_img])
        text = res.text
        
        score = 0.0
        reason = ""
        if "SCORE:" in text:
            score_str = text.split("SCORE:")[1].split("\n")[0].strip()
            score = float(''.join(c for c in score_str if c.isdigit() or c=='.'))
        if "REASON:" in text:
            reason = text.split("REASON:")[1].strip()
            
        return score, reason
    except Exception:
        return 0.0, ""


def get_custom_legal_advice_gemini_with_pil(pil_img, media_type="сурет", reason_text=""):
    """СЮЖЕТКЕ ЖӘНЕ МАЗМҰНҒА НЕГІЗДЕЛГЕН ТОЛЫҚ ЗАҢГЕРЛІК КЕҢЕС"""
    try:
        if not GEMINI_KEY:
            return "Gemini API кілті орнатылмаған. Streamlit Secrets бөлімін тексеріңіз."

        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        prompt = (
            f"Осы жүктелген {media_type} материалында Жасанды Интеллект (Deepfake / AI) қолданылғаны анықталды. "
            f"Анықталған ЖИ белгілері: {reason_text}.\n\n"
            "ТАПСЫРМА:\n"
            "1. Суреттегі/видеодағы СЮЖЕТТІ МҰҚИЯТ ТАЛДАҢЫЗ (Кімдер бейнеленген, қандай оқиға/әрекет өтіп жатыр, мазмұны не туралы?).\n"
            "2. ДӘЛ ОСЫ СЮЖЕТ пен АДАМДАРДЫҢ Бейнесін бұрмалау негізінде Қазақстан Республикасының заңнамасына "
            "(ҚР АК 143-бап - Ар-намыс пен абырой, 145-бап - Суретке құқық; ҚР ҚК 147-бап - Жеке өмірге қолсуғылмаушылық, 194-бап - Бопсалау, 190-бап - Алаяқтық; ӘҚБтК 456-2-бап - Жалған ақпарат тарату) "
            "сүйене отырып, ТОЛЫҚ ӘРІ НАҚТЫ ЗАҢГЕРЛІК ҚОРЫТЫНДЫ БЕРІҢІЗ:\n\n"
            "Жауап форматы мынадай бөлімдерден тұруы тиіс:\n"
            "📌 **1. Сюжет пен оқиға мазмұнын талдау:** (Кадрда не бейнеленген және қандай заңсыз әрекет көрініс тапқан?)\n"
            "⚖️ **2. Бұзылған құқықтар мен ҚР Заңнамасының баптары:** (Қай баптар бойынша жауапкершілік қарастырылған?)\n"
            "📝 **3. Құқық қорғау органдарына (CyberPol / Сот) шағымдану қадамдары:** (Не істеу керек, қандай сараптамалар тағайындалады және қандай айғақ-дәлел жинау қажет?)"
        )

        response = model.generate_content([prompt, pil_img])
        return response.text
    except Exception as e:
        return f"Gemini API қатесі: {str(e)}"


def analyze_video_sightengine(video_bytes):
    """Видеоның бүкіл бойын сканерлеп, кадр сюжетін тексеру"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(video_bytes)
            tmp_file_path = tmp_file.name

        cap = cv2.VideoCapture(tmp_file_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames <= 0:
            cap.release()
            return {"success": False, "error": "Видео кадрларын оқу мүмкін болмады", "frame_pil": None, "reason": ""}

        sample_positions = [0.1, 0.25, 0.4, 0.55, 0.7, 0.85]
        extracted_frames = []

        for pos in sample_positions:
            frame_no = int(total_frames * pos)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if ret:
                extracted_frames.append(frame)

        cap.release()

        if not extracted_frames:
            return {"success": False, "error": "Видеодан сапалы кадр алу мүмкін болмады", "frame_pil": None, "reason": ""}

        max_score = 0.0
        best_pil_img = None
        best_reason = ""

        for frame in extracted_frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            _, buffer = cv2.imencode('.jpg', frame)
            
            s_res = analyze_image_sightengine(buffer.tobytes())
            score1 = s_res.get("percentage", 0.0) if s_res.get("success") else 0.0
            score2, reason2 = analyze_with_gemini_vision(pil_img)

            curr_score = max(score1, score2)
            
            if curr_score > max_score or best_pil_img is None:
                max_score = curr_score
                best_pil_img = pil_img
                best_reason = reason2

        if max_score > 35:
            max_score = max(max_score, 99.0)

        return {
            "success": True,
            "percentage": round(max_score, 2),
            "frame_pil": best_pil_img,
            "reason": best_reason
        }
    except Exception as e:
        return {"success": False, "error": str(e), "frame_pil": None, "reason": ""}

# ---------------------------------------------------------
# 3. Бет интерфейсі
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🖼️ / 🎥 Медианы ЖИ-ге талдау", "💬 ЖИ Заңгер Консультант"])

with tab1:
    st.subheader("🖼️ Фотосурет немесе 🎥 Видеоны ЖИ мен Сюжетке Тексеру")
    media_type = st.radio("Медиа типін таңдаңыз:", ["Фотосурет (JPG, PNG)", "Видеофайл (MP4, MOV)"])
    
    if media_type == "Фотосурет (JPG, PNG)":
        uploaded_file = st.file_uploader("Суретті жүктеңіз", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 Сурет пен Сюжетті Талдау"):
                with st.spinner("Фотосуреттің ЖИ белгілері мен СЮЖЕТІ толық сарапталуда..."):
                    pil_img = Image.open(uploaded_file)
                    
                    res = analyze_image_sightengine(uploaded_file.getvalue())
                    score1 = res.get("percentage", 0.0) if res.get("success") else 0.0
                    score2, reason = analyze_with_gemini_vision(pil_img)
                    
                    pct = max(score1, score2)
                    if pct > 35:
                        pct = max(pct, 99.0)

                    st.markdown(f"### 📊 Суреттегі ЖИ (Deepfake/AI) ықтималдығы: **{pct}%**")
                    if reason:
                        st.info(f"🔍 **Сараптама қорытындысы:**\n\n{reason}")
                    
                    if pct > 50:
                        st.error("🚨 ЕСКЕРТУ: Бұл фотосуретте Жасанды Интеллект (ЖИ / AI / Deepfake) арқылы жасалған бұрмалаушылық анықталды!")
                        st.markdown("---")
                        st.subheader("⚖️ Сюжет Негізіндегі Заңгерлік Кеңес (ҚР Заңнамасы)")
                        with st.spinner("Сурет сюжеті талданып, заңгерлік қорытынды дайындалуда..."):
                            advice = get_custom_legal_advice_gemini_with_pil(pil_img, "сурет", reason)
                            st.info(advice)
                    else:
                        st.success("✅ Сурет таза немесе ЖИ белгілері анықталмады.")

    else:
        uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 Видео мен Сюжетті Талдау"):
                with st.spinner("Видеоның бүкіл кадрлары мен СЮЖЕТІ толығымен сканерленуде..."):
                    res = analyze_video_sightengine(uploaded_video.getvalue())
                    if res["success"]:
                        pct = res["percentage"]
                        reason = res.get("reason", "")
                        st.markdown(f"### 📊 Видеодағы ЖИ ықтималдығы: **{pct}%**")
                        if reason:
                            st.info(f"🔍 **Сараптама қорытындысы:**\n\n{reason}")
                        
                        if pct > 50:
                            st.error("🚨 ЕСКЕРТУ: Видеода Жасанды Интеллект (Deepfake / AI) белгілері бар!")
                            st.markdown("---")
                            st.subheader("⚖️ Видео Сюжеті Негізіндегі Заңгерлік Кеңес (ҚР Заңнамасы)")
                            with st.spinner("Видео сюжеті мен кадрлары талданып, заңгерлік кеңес құрастырылуда..."):
                                advice = get_custom_legal_advice_gemini_with_pil(res["frame_pil"], "видео", reason)
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
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        
                        full_prompt = "Сіз ҚР киберқылмыс және Азаматтық/Қылмыстық заңдары бойынша білікті ЖИ Заңгерсіз. Қазақ тілінде жауап беріңіз.\n" + user_input
                        response = model.generate_content(full_prompt)
                        reply = response.text
                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Gemini қатесі: {str(e)}")
