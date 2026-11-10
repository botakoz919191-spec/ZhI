import streamlit as st
import time
from PIL import Image
import google.generativeai as genai

st.set_page_config(
    page_title="CyberShield.kz — ҚР Цифрлық сараптама порталы",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #edf5ff 0%, #dbeafe 50%, #eff6ff 100%) !important; }
    .top-navbar {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 2px solid #cbd5e1; padding: 12px 20px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 13px; color: #1e293b;
        flex-wrap: wrap; gap: 10px;
    }
    .top-navbar a { color: #1d4ed8; text-decoration: none; font-weight: bold; }
    .phone-item {
        background: #f1f5f9; padding: 4px 8px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 12px;
    }
    .header-banner {
        background: linear-gradient(135deg, #0f2b5c 0%, #1e40af 60%, #1d4ed8 100%);
        color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; border-bottom: 5px solid #d97706;
    }
    .header-title { font-size: 26px; font-weight: 800; color: #ffffff; margin: 0; }
    .header-subtitle { font-size: 14px; color: #e0f2fe; margin-top: 4px; }
    div.stButton > button {
        background: linear-gradient(90deg, #0f2b5c 0%, #1e40af 100%) !important;
        color: #ffffff !important; font-size: 15px !important; font-weight: bold !important;
        padding: 10px 20px !important; border-radius: 8px !important; width: 100%;
    }
    .verdict-ai { background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b; padding: 14px; border-radius: 10px; font-weight: bold; margin-bottom: 12px; }
    .verdict-real { background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534; padding: 14px; border-radius: 10px; font-weight: bold; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# Жоғарғы панельдегі сенім телефондары және мекемелері
st.markdown("""
<div class="top-navbar">
    <div>🏛️ <b>Әділет министрлігі:</b> <a href="https://www.gov.kz/memleket/entities/adilet" target="_blank">gov.kz/adilet</a></div>
    <div>
        🛡️ <b>Шұғыл байланыс:</b> 
        <span class="phone-item">📞 <b>102</b> (Полиция)</span> | 
        <span class="phone-item">☎️ <b>1414</b> (eGov)</span> | 
        <span class="phone-item">🆘 <b>111</b> (Балалар құқығы)</span> | 
        <span class="phone-item">⛑️ <b>150</b> (Дағдарыс орталығы)</span>
    </div>
</div>
""", unsafe_allow_html=True)

GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def compress_image(pil_img, max_size=(1024, 1024)):
    img_copy = pil_img.copy()
    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img_copy

def call_gemini_chat(system_prompt, chat_history, user_new_msg, pil_img=None, video_file=None):
    if not GEMINI_KEY:
        return "⚠️ Gemini API кілті (GEMINI_KEY) Streamlit Secrets бөлімінде көрсетілмеген!"

    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-3.8-flash']
    prepared_img = compress_image(pil_img) if pil_img is not None else None

    last_error = ""
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            
            full_prompt = f"{system_prompt}\n\n--- ЧАТ ТАРИХЫ ---\n"
            for msg in chat_history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            
            full_prompt += f"\nПАЙДАЛАНУШЫ СҰРАҒЫ: {user_new_msg}\n"
            full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Шаблон қолданбай, әрбір деталіне, әсіресе шаш сызықтарына, бет пішініне, пиксельдерге, жасанды түрде өзгертілген (deepfake/face-swap) іздеріне терең үңіліп, нақты дәлелдермен кәсіби заңгерлік және криминалистикалық жауап бер."

            contents = [full_prompt]
            if prepared_img is not None:
                contents.append(prepared_img)
            if video_file is not None:
                contents.append(video_file)

            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return f"⚠️ API қатесі орын алды: {last_error}. Баланс пен кілтті тексеріңіз."

def analyze_media_deeply(pil_img=None, video_file=None):
    prompt = (
        "Сіз тәжірибелі жоғары санатты цифрлық криминалист, кибер-сарапшы және киберқұқық заңгерісіз. "
        "Қазіргі кезде адамдарды шантаж жасау үшін қолданылатын ЖИ арқылы жасалған немесе өзгертілген (deepfake, face-swap, шашты немесе бетті нейрожелі арқылы ауыстыру/монтаждау) іздерін мына пункттер бойынша мұқият тексеріңіз:\n"
        "1. Шаш сызықтары мен түйісетін жерлері: шаштың маңдаймен немесе фондағы аумақпен жалғасқан жерлерінде бұлыңғырлық, біркелкі еместік немесе ЖИ-ге тән қателіктер бар ма?\n"
        "2. Бет-әлпет, мимика, тері құрылымы және көздің жарық шағылуы: шынайы камера фотосы/видеосы ма, әлде біреудің бетін басқа біреуге жапсырған ба (face-swap)?\n"
        "3. ЖИ генерациясы немесе өңдеу белгілерінің пайызын (0-100% аралығында) анықтаңыз.\n\n"
        "МІНДЕТТІ ФОРМАТ:\n"
        "SCORE: [0-100 аралығындағы пайыз, мұнда жоғары пайыздар — ЖИ/монтаж екенін білдіреді]\n"
        "VERDICT: [Жасанды интеллект/Deepfake арқылы өзгертілген немесе жасалған / Шынайы камера материалы]\n"
        "REASON: [Қылмыстық немесе шантаж мақсатындағы өзгертулерді дәлелдейтін терең криминалистикалық қорытынды]"
    )
    
    sys_msg = "Сіз цифрлық криминалист-сарапшысыз."
    res_text = call_gemini_chat(sys_msg, [], prompt, pil_img=pil_img, video_file=video_file)
    
    score = 15.0
    verdict = "Шынайы камера материалы"
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

st.markdown("""
<div class="header-banner">
    <h1 class="header-title">⚖️ CyberShield.kz</h1>
    <p class="header-subtitle">Қазақстан Республикасы цифрлық сараптама және киберқұқықтық порталы</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🖼️ / 🎥 Терең цифрлық сараптама", "📝 Мәтін сараптамасы", "💬 Онлайн ҚР кибер-заңгері"])

with tab1:
    st.markdown("### 🔍 Медиа файлды терең бөлшектеп зерттеу (Deepfake / Шантажқа қарсы)")
    media_type = st.radio("Файл түрін таңдаңыз:", ["Фотосурет (Кез келген формат)", "Видеофайл"], horizontal=True)
    
    if media_type == "Фотосурет (Кез келген формат)":
        uploaded_file = st.file_uploader("Тексеретін суретті жүктеңіз (Кез келген формат)", type=None)
        if uploaded_file:
            try:
                pil_img = Image.open(uploaded_file)
                st.image(pil_img, caption="Жүктелген сурет", width=300)

                if st.button("🔍 ЖИ / Deepfake пен шантаж іздерін терең сараптау"):
                    with st.spinner("Шаш сызықтары, бет пішіні және пиксельдер ЖИ мен монтажға тексерілуде..."):
                        score, verdict, reason = analyze_media_deeply(pil_img=pil_img)
                        st.session_state["media_data"] = {"pct": score, "verdict": verdict, "reason": reason, "img": pil_img, "is_video": False}
                        st.session_state["media_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Терең сараптама актісі:**\n\n{reason}\n\nҚосымша сұрақтарыңызды төменде қоя аласыз:"}]
            except Exception as e:
                st.error(f"Суретті оқу кезінде қате шықты: {e}")

    else:
        uploaded_video = st.file_uploader("Тексеретін видеоны жүктеңіз (Кез келген формат)", type=None)
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("🔍 Видеоны ЖИ / Deepfake пен монтажға тексеру"):
                with st.spinner("Видео кадрлары мен көз/шаш ауыстыру (face-swap) іздері талдануда..."):
                    score, verdict, reason = analyze_media_deeply(video_file=uploaded_video)
                    st.session_state["media_data"] = {"pct": score, "verdict": verdict, "reason": reason, "vid": uploaded_video, "is_video": True}
                    st.session_state["media_chat_history"] = [{"role": "assistant", "content": f"⚖️ **Видеоны терең сараптау қорытындысы:**\n\n{reason}\n\nҚосымша сұрақтарыңызды төменде қоя аласыз:"}]

    if "media_data" in st.session_state:
        m_data = st.session_state["media_data"]
        pct = m_data["pct"]
        verdict = m_data["verdict"]

        if pct >= 50.0 or "ЖАСАНДЫ" in verdict.upper() or "DEEPFAKE" in verdict.upper() or "МОНТАЖ" in verdict.upper():
            st.markdown(f'<div class="verdict-ai">⚠️ САРАПТАМА АКТІСІ (Қауіпті): {verdict} (ЖИ немесе өзгерту көрсеткіші: {pct}%)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-real">✅ САРАПТАМА АКТІСІ: {verdict} (Шынайылық көрсеткіші: {100-pct}%)</div>', unsafe_allow_html=True)

        st.info(f"🔍 **Сараптамалық қорытынды және дәлелдер:**\n\n{m_data['reason']}")
        st.markdown("---")
        st.markdown("### 💬 Кибер-заңгермен чат және құқықтық кеңес")

        for msg in st.session_state.get("media_chat_history", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_q := st.chat_input("Сұрағыңызды жазыңыз...", key="media_input"):
            st.session_state["media_chat_history"].append({"role": "user", "content": user_q})
            with st.chat_message("user"): st.markdown(user_q)
            with st.chat_message("assistant"):
                with st.spinner("Заңгер жауабы дайындалуда..."):
                    sys_p = f"Сіз ҚР кибер-заңгерісіз. Шантаж бен ЖИ арқылы жасалған фейктермен күрес бойынша көмектесіңіз. Сараптама: {m_data['reason']}."
                    p_img = m_data.get("img") if not m_data.get("is_video") else None
                    v_file = m_data.get("vid") if m_data.get("is_video") else None
                    ans = call_gemini_chat(sys_p, st.session_state["media_chat_history"][:-1], user_q, pil_img=p_img, video_file=v_file)
                    st.markdown(ans)
                    st.session_state["media_chat_history"].append({"role": "assistant", "content": ans})

with tab2:
    st.markdown("### 📝 Мәтінді терең тексеру (Қорқыту, шантаж немесе фейк мәтіндер)")
    text_input = st.text_area("Тексеретін мәтінді енгізіңіз:", height=150)
    if st.button("🔍 Мәтінді сараптау"):
        if text_input.strip():
            with st.spinner("Талдануда..."):
                ans = call_gemini_chat("Сіз заңгер-редакторсыз.", [], f"Мәтінді терең талдап бер: {text_input}")
                st.info(ans)

with tab3:
    st.markdown("### 💬 Онлайн ҚР кибер-заңгері")
    if "gen_chat_history" not in st.session_state:
        st.session_state["gen_chat_history"] = [{"role": "assistant", "content": "Сәлеметсіз бе! Мен ҚР Цифрлық және кибер-құқық заңгерімін. Шантаж, кибербуллинг немесе ЖИ арқылы жасалған жалған материалдарға қарсы құқықтық көмек көрсетемін."}]

    for msg in st.session_state["gen_chat_history"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if user_q := st.chat_input("Сұрағыңызды жазыңыз...", key="gen_chat_input"):
        st.session_state["gen_chat_history"].append({"role": "user", "content": user_q})
        with st.chat_message("user"): st.markdown(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Жауап дайындалуда..."):
                ans = call_gemini_chat("Сіз ҚР кибер-заңгерісіз.", st.session_state["gen_chat_history"][:-1], user_q)
                st.markdown(ans)
                st.session_state["gen_chat_history"].append({"role": "assistant", "content": ans})
