def call_gemini_chat(system_prompt, chat_history, user_new_msg, pil_img=None):
    if not GEMINI_KEY:
        return "⚠️ Gemini API кілті (GEMINI_KEY) Streamlit Secrets бөлімінде көрсетілмеген!"

    # Қолданылатын модельдер тізімі (стандартты және тұрақты атаулар)
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.5-flash']
    prepared_img = compress_image(pil_img) if pil_img is not None else None

    last_error = ""
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            
            full_prompt = f"{system_prompt}\n\n--- ЧАТ ТАРИХЫ ---\n"
            for msg in chat_history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            
            full_prompt += f"\nПАЙДАЛАНУШЫ СҰРАҒЫ: {user_new_msg}\n"
            full_prompt += "\nЖАУАП ЕРЕЖЕСІ: Шаблон қолданбай, әрбір деталіне терең үңіліп, нақты, жан-жақты әрі кәсіби заңгерлік/сараптамалық жауап бер."

            contents = [full_prompt]
            if prepared_img is not None:
                contents.append(prepared_img)

            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return f"⚠️ API қатесі орын алды: {last_error}. Google AI Studio жүйесіндегі балансыңызды немесе кілтіңізді тексеріңіз."
