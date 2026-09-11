import streamlit as st
import requests
import json
import tempfile
import cv2
import time
from PIL import Image
import google.generativeai as genai

# =========================================================
# 🗝️ API КІЛТТЕРІ (БІР ГАНА АККАУНТ КІЛТІ ЖЕТЕДІ)
# =========================================================
SIGHTENGINE_USER = st.secrets.get("SIGHTENGINE_USER", "1282198950")
SIGHTENGINE_SECRET = st.secrets.get("SIGHTENGINE_SECRET", "VFvoLLmm7Z97MU95LddGTbuNrhhYuZng")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

st.set_page_config(page_title="CyberShield KZ", page_icon="🛡️", layout="wide")
st.title("🛡️ CyberShield KZ — ЖИ Талдау және КИБЕРҚОРҒАНЫС Жүйесі")

# Gemini API баптау (1500 сұраныстық тегін режим)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def call_gemini_safe(prompt, pil_img=None):
    """
    Күніне 1500 сұраныс беретін gemini-1.5-flash моделін қолдану.
    Ешқандай лимит таусылмайды.
    """
    if not GEMINI_KEY:
        return "API кілт енгізілмеген."
    
    # Сұраныстар арасында аздап кідіріс жасау (429 қатесін болдырмау үшін)
    time.sleep(1)
    
    # ӨТЕ МАҢЫЗДЫ: gemini-1.5-flash — күніне 1,500 тегін сұраныс береді
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    inputs = [prompt]
    if pil_img is not None:
        inputs.append(pil_img)
        
    res = model.generate_content(inputs)
    return res.text if res else ""

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
        return {"success": False, "error": "Sightengine error"}
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
        f"Алдағы жүктелген {media_type} материалын және оның ішіндегі СЮЖЕТТІ ТЕРЕҢ ТАЛДАҢЫЗ.\n"
        f"Анықталған ЖИ белгілері: {reason_text}\n\n"
        f"1. СУРЕТТІҢ/ВИДЕОНЫҢ ІШКІ СЮЖЕТІН сипаттаңыз (Суретте не/кім бейнеленген, қандай фейк/заңсыздық бар).\n"
        f"2. Осы сюжетке байланысты ҚР Заңдары (ҚР АК 143, 145; ҚР ҚК 147, 190; ӘҚБтК 456-2) бойынша бұзылған құқықтарды көрсетіңіз.\n"
        f"3. Осы жағдайда азаматқа нақты 3 қадамдық заңдық кеңес беріңіз."
    )
    return call_gemini_safe(prompt, pil_img)

def analyze_text_chatgpt(text_content):
    prompt = (
        f"Мына тапсырма мәтінін талда:\n\"{text_content}\"\n"
        "Бұл мәтін ChatGPT арқылы жазылған ба? "
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

    # Ортаңғы кадрды алу (квотаны үнемдеу үшін 1 кадр жетеді)
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
    
    return {"success": False, "error": "Кадр алынбады", "frame_pil": None, "reason": ""}

# ---------------------------------------------------------
# Интерфейс
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🖼️ / 🎥 Медиа сараптама", "📝 Мәтінді Тексеру", "💬 ЖИ Заңгер"])

with tab1:
    st.subheader("🖼️ Фотосурет немесе 🎥 Видеоны ЖИ мен Сюжетке Тексеру")
    media_type = st.radio("Таңдаңыз:", ["Фотосурет / Скриншот", "Видеофайл"])
    
    if media_type == "Фотосурет / Скриншот":
        uploaded_file = st.file_uploader("Сурет жүктеңіз", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 Талдау Жасау"):
                with st.spinner("ЖИ суретті және оның сюжетін оқып жатыр..."):
                    try:
                        pil_img = Image.open(uploaded_file)
                        res = analyze_image_sightengine(uploaded_file.getvalue())
                        score1 = res.get("percentage", 0.0) if res.get("success") else 0.0
                        score2, reason = analyze_with_gemini_vision(pil_img)
                        pct = max(score1, score2)

                        st.markdown(f"### 📊 ЖИ ықтималдығы: **{pct}%**")
                        st.info(f"🔍 **Анықталған мазмұн мен ЖИ белгілері:**\n\n{reason}")
                        
                        st.markdown("---")
                        st.subheader("⚖️ Сюжетке Негізделген ЖИ Заңгерлік Кеңесі")
                        with st.spinner("Заңгер сурет сюжетіне талдау жасауда..."):
                            advice = get_custom_legal_advice(pil_img, "сурет", reason)
                            st.write(advice)
                    except Exception as err:
                        st.error(f"Қате: {err}")

    else:
        uploaded_video = st.file_uploader("Видео жүктеңіз", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 Видеоны Талдау"):
                with st.spinner("Видео кадрлары сканерленуде..."):
                    try:
                        res = analyze_video_sightengine(uploaded_video.getvalue())
                        if res["success"]:
                            pct = res["percentage"]
                            reason = res.get("reason", "")
                            st.markdown(f"### 📊 Видеодағы ЖИ ықтималдығы: **{pct}%**")
                            st.info(f"🔍 **Сараптама қорытындысы:**\n\n{reason}")
                            
                            st.markdown("---")
                            st.subheader("⚖️ Видео Сюжеті Бойынша Заңгерлік Қорытынды")
                            with st.spinner("Видео мазмұны бойынша заң талдануда..."):
                                advice = get_custom_legal_advice(res["frame_pil"], "видео", reason)
                                st.write(advice)
                        else:
                            st.error(res["error"])
                    except Exception as err:
                        st.error(f"Қате: {err}")

with tab2:
    st.subheader("📝 Мәтінді ChatGPT-ге тексеру")
    text_input = st.text_area("Мәтінді енгізіңіз:", height=200)
    if st.button("🔍 Мәтінді Тексеру"):
        if text_input.strip():
            with st.spinner("Мәтін сарапталуда..."):
                try:
                    pct, reason = analyze_text_chatgpt(text_input)
                    st.markdown(f"### 📊 ЖИ ықтималдығы: **{pct}%**")
                    st.info(f"🔍 **Дәлелдер:**\n\n{reason}")
                except Exception as err:
                    st.error(f"Қате: {err}")

with tab3:
    st.subheader("💬 Онлайн ЖИ Заңгер")
    user_input = st.chat_input("Сұрақ жазыңыз...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Жауап дайындалуда..."):
                try:
                    full_prompt = "Сіз ҚР киберқылмыс бойынша ЖИ Заңгерсіз. Қазақ тілінде нақты жауап беріңіз:\n" + user_input
                    reply = call_gemini_safe(full_prompt)
                    st.write(reply)
                except Exception as err:
                    st.error(f"Қате: {err}")
