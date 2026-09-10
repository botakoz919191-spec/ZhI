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
    """Sightengine API арқылы визуалды ЖИ генерациясын тексеру"""
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
    """Мәтіндік тапсырмаларды, скриншоттарды және фото/видеоны ЖИ (ChatGPT, Deepfake т.б.) белгілеріне ҚАТАҢ тексеру"""
    try:
        if not GEMINI_KEY:
            return 0.0, ""
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        prompt = (
            "Осы суретті немесе тапсырма материалын МҰҚИЯТ ЖӘНЕ ӨТЕ ҚАТАҢ ТАЛДА.\n"
            "Егер бұл МӘТІН/ТАПСЫРМА/СКРИНШОТ болса, оның ChatGPT, Gemini, Claude сияқты ЖИ арқылы жасалған-жасалмағанын мына белгілермен тексер:\n"
            "1. Сөйлемдердің тым біркелкі, тегіс, академиялық құрылымы;\n"
            "2. ChatGPT-ге тән сөз тіркестері ('қорытындылай келе', 'маңызды рөл атқарады', 'атап өткен жөн', 'сонымен қатар');\n"
            "3. Тізімдер мен пункттердің ЖИ форматында реттелуі.\n\n"
            "Егер бұл ФОТО/ВИДЕО кадры болса, оның D-ID, Midjourney, HeyGen, Deepfake арқылы бұрмаланғанын тексер.\n\n"
            "Жауапты ТЕК МЫНА ФОРМАТТА БЕР (басқа артық сөз жазба):\n"
            "SCORE: [0-100 аралығындағы ЖИ ықтималдығының саны]\n"
            "REASON: [Анықталған ЖИ (ChatGPT немесе басқа ЖИ) белгілері мен дәлелдерінің нақты сипаттамасы]"
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


def analyze_text_chatgpt(text_content):
    """Жазбаша мәтінді ChatGPT/ЖИ генерациясына ҚАТАҢ ДЕТЕКЦИЯЛАУ"""
    try:
        if not GEMINI_KEY:
            return 0.0, ""
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        prompt = (
            f"Мына мәтінді МҰҚИЯТ САКТАП ТАЛДА:\n\n\"{text_content}\"\n\n"
            "Бұл мәтінді ChatGPT немесе өзге ЖИ (AI) жазған ба? "
            "ЖИ-ге тән сөз оралымдарын, стилистикасын, грамматикалық шаблонды тексер. "
            "Кішкене болсын ЖИ издері болса, оны төмен бағалама, нақты көрсет.\n"
            "Жауапты ТЕК МЫНА ФОРМАТТА бер:\n"
            "SCORE: [0-100 аралығындағы сан]\n"
            "REASON: [ЖИ-ге тән анықталған сөздер мен дәлелдер сипаттамасы]"
        )
        
        res = model.generate_content(prompt)
        text = res.text
        
        score = 0.0
        reason = ""
        if "SCORE:" in text:
            score_str = text.split("SCORE:")[1].split("\n")[0].strip()
            score = float(''.join(c for c in score_str if c.isdigit() or c=='.'))
        if "REASON:" in text:
            reason = text.split("REASON:")[1].strip()
            
        return score, reason
    except Exception as e:
        return 0.0, str(e)


def get_custom_legal_advice_gemini_with_pil(pil_img, media_type="сурет", reason_text=""):
    """Сюжетке және бұрмалауға негізделген заңгерлік кеңес"""
    try:
        if not GEMINI_KEY:
            return "Gemini API кілті орнатылмаған."

        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        prompt = (
            f"Жүктелген {media_type} материалында ЖИ белгілері анықталды: {reason_text}.\n\n"
            "Осы материалдың сюжеті мен мазмұнына сүйеніп, ҚР Заңнамасы (ҚР АК 143, 145; ҚР ҚК 147, 190, 194; ӘҚБтК 456-2) "
            "бойынша заңгерлік қорытынды беріңіз:\n"
            "1. Сюжет пен заңсыз әрекет мазмұны;\n"
            "2. Бұзылған құқықтар мен заң баптары;\n"
            "3. Шағымдану қадамдары мен дәлелдер жинау."
        )

        response = model.generate_content([prompt, pil_img])
        return response.text
    except Exception as e:
        return f"Gemini API қатесі: {str(e)}"


def analyze_video_sightengine(video_bytes):
    """Видеоны тексеру"""
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
            return {"success": False, "error": "Кадр алу мүмкін болмады", "frame_pil": None, "reason": ""}

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
tab1, tab2, tab3 = st.tabs(["🖼️ / 🎥 Медиа сараптама", "📝 Мәтіндік Тапсырмаларды (ChatGPT) Тексеру", "💬 ЖИ Заңгер Консультант"])

with tab1:
    st.subheader("🖼️ Фотосурет немесе 🎥 Видеоны ЖИ мен Сюжетке Тексеру")
    media_type = st.radio("Медиа типін таңдаңыз:", ["Фотосурет / Скриншот (JPG, PNG)", "Видеофайл (MP4, MOV)"])
    
    if media_type == "Фотосурет / Скриншот (JPG, PNG)":
        uploaded_file = st.file_uploader("Суретті немесе тапсырма скриншотын жүктеңіз", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Жүктелген сурет", use_container_width=True)
            if st.button("🔍 Толық Қатаң Талдау Жасау"):
                with st.spinner("Сурет/Скриншот ЖИ белгілеріне (ChatGPT, D-ID, Midjourney т.б.) терең тексерілуде..."):
                    pil_img = Image.open(uploaded_file)
                    
                    res = analyze_image_sightengine(uploaded_file.getvalue())
                    score1 = res.get("percentage", 0.0) if res.get("success") else 0.0
                    score2, reason = analyze_with_gemini_vision(pil_img)
                    
                    pct = max(score1, score2)

                    st.markdown(f"### 📊 ЖИ (AI/ChatGPT/Deepfake) ықтималдығы: **{pct}%**")
                    if reason:
                        st.info(f"🔍 **Сараптама қорытындысы мен анықталған белгілер:**\n\n{reason}")
                    
                    if pct > 40:
                        st.error("🚨 ЕСКЕРТУ: Осы материалда Жасанды Интеллект (ChatGPT немесе ЖИ-генератор) іздері анықталды!")
                        st.markdown("---")
                        st.subheader("⚖️ Заңгерлік Кеңес")
                        with st.spinner("Сюжет пен мазмұны талдануда..."):
                            advice = get_custom_legal_advice_gemini_with_pil(pil_img, "сурет", reason)
                            st.info(advice)
                    else:
                        st.success("✅ ЖИ белгілері анықталмады немесе материал табиғи.")

    else:
        uploaded_video = st.file_uploader("Видеоны жүктеңіз", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🎥 Видеоны Талдау"):
                with st.spinner("Видео кадрлары сканерленуде..."):
                    res = analyze_video_sightengine(uploaded_video.getvalue())
                    if res["success"]:
                        pct = res["percentage"]
                        reason = res.get("reason", "")
                        st.markdown(f"### 📊 Видеодағы ЖИ ықтималдығы: **{pct}%**")
                        if reason:
                            st.info(f"🔍 **Сараптама қорытындысы:**\n\n{reason}")
                        
                        if pct > 40:
                            st.error("🚨 ЕСКЕРТУ: Видеода ЖИ белгілері бар!")
                            st.markdown("---")
                            st.subheader("⚖️ Заңгерлік Кеңес")
                            with st.spinner("Талдануда..."):
                                advice = get_custom_legal_advice_gemini_with_pil(res["frame_pil"], "видео", reason)
                                st.info(advice)
                        else:
                            st.success("✅ Видео таза немесе ЖИ белгілері анықталмады.")
                    else:
                        st.error(f"Қате: {res['error']}")

with tab2:
    st.subheader("📝 Сабақ тапсырмаларының мәтінін ChatGPT-ге тексеру")
    st.write("Төменге сабақ тапсырмасының мәтінін көшіріп қойыңыз (Copy/Paste):")
    text_input = st.text_area("Тапсырма мәтінін осында енгізіңіз:", height=200)
    
    if st.button("🔍 Мәтінді ChatGPT-ге Тексеру"):
        if text_input.strip():
            with st.spinner("Мәтіннің құрылымы, стилі мен ChatGPT белгілері қатаң сарапталуда..."):
                pct, reason = analyze_text_chatgpt(text_input)
                st.markdown(f"### 📊 Мәтіннің ЖИ (ChatGPT) арқылы жазылу ықтималдығы: **{pct}%**")
                if reason:
                    st.info(f"🔍 **Анықталған дәлелдер мен талдау:**\n\n{reason}")
                
                if pct > 40:
                    st.error("🚨 Бұл тапсырма мәтіні Жасанды Интеллект (ChatGPT / Claude / Gemini) арқылы жазылған!")
                else:
                    st.success("✅ Мәтін адам тарапынан жазылғанға ұқсайды (ЖИ белгілері минималды).")
        else:
            st.warning("Өтініш, тексеру үшін мәтінді енгізіңіз.")

with tab3:
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
