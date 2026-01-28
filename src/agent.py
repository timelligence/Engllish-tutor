import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# --- CONFIGURARE ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ EROARE: Lipsește GOOGLE_API_KEY din fișierul .env")
    st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = 'gemini-2.0-flash'

# --- DEFINIRE SCENARII ---
SCENARIOS = {
    "Client Insistent (Business)": """
        ROLE: Pushy Client.
        GOAL: Force the user to accept an impossible deadline.
        TONE: Urgent, slightly rude.
        IMPORTANT: Before replying, YOU MUST output a correction block if the user made ANY mistake.
        FORMAT:
        [FEEDBACK: "User said..." -> "Better: ..."]
        [ROLEPLAY RESPONSE: "Listen, I don't care about the details..."]
    """,
    "Interviu Senior Developer": """
        ROLE: Engineering Manager (Alex).
        GOAL: Assess technical depth.
        IMPORTANT: Correct technical terms and grammar explicitly.
        FORMAT:
        [FEEDBACK: "You said 'I make code' -> 'I write/deploy code'."]
        [ROLEPLAY RESPONSE: "Interesting approach. But how does it scale?"]
    """,
    "Recrutare UK (Horeca/Hospitality)": """
        ROLE: Sarah, HR Recruiter London.
        GOAL: Interview for Waiter/Housekeeping.
        TONE: British, fast, pragmatic.
        CRITICAL INSTRUCTION: Correct the user's English in every turn.
        STARTING LINE: "Right then, love. Thanks for popping in. I see you're looking for some shift work. Have you got experience in the UK?"
    """
}

# --- FUNCȚII AUXILIARE ---
def clean_html_for_markdown(text):
    text = text.replace('<div class="feedback-box">', '\n> **🔍 FEEDBACK:**\n> ')
    text = text.replace('</div>', '\n')
    text = text.replace('<div class="roleplay-box">', '\n')
    return text

def get_transcript():
    scenario = st.session_state.get("last_scenario", "Necunoscut")
    transcript = f"# Antigravity Tutor Session\n"
    transcript += f"**Scenariu:** {scenario}\n"
    transcript += f"**Model:** {MODEL_NAME}\n\n---\n\n"
    for msg in st.session_state.messages:
        role = "🤖 AI" if msg["role"] == "assistant" else "👤 TU"
        content = clean_html_for_markdown(msg["content"])
        transcript += f"### {role}:\n{content}\n\n"
    return transcript

# --- INTERFAȚA GRAFICĂ & INIȚIALIZARE ---
st.set_page_config(page_title="Antigravity Tutor", page_icon="🪐", layout="wide")
st.title("🪐 Antigravity English Tutor")

st.markdown("""
<style>
    .feedback-box {
        background-color: #262730;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .roleplay-box {
        font-size: 1.1em;
        font-weight: 500;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 1. INIȚIALIZARE VARIABILE (Safety First)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None
if "last_scenario" not in st.session_state:
    st.session_state.last_scenario = list(SCENARIOS.keys())[0]
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# 2. SIDEBAR
with st.sidebar:
    st.header("⚙️ Setări")
    
    selected_scenario_name = st.selectbox(
        "Alege Scenariul:", 
        list(SCENARIOS.keys()), 
        key="selected_scenario",
        index=list(SCENARIOS.keys()).index(st.session_state.last_scenario) if st.session_state.last_scenario in SCENARIOS else 0
    )
    
    if st.button("🔄 Sesiune Nouă"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.session_state.last_processed_audio = None
        st.rerun()
    
    st.divider()
    st.header("📊 Export & Raport")
    
    transcript_txt = get_transcript()
    st.download_button(
        label="💾 Descarcă Sesiunea (.md)",
        data=transcript_txt,
        file_name="english_session.md",
        mime="text/markdown"
    )

# 3. LOGICA SCHIMBARE SCENARIU
if st.session_state.last_scenario != selected_scenario_name:
    st.session_state.messages = []
    st.session_state.chat_session = None
    st.session_state.last_processed_audio = None
    st.session_state.last_scenario = selected_scenario_name
    st.rerun()

# 4. START CHAT ENGINE
if st.session_state.chat_session is None:
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SCENARIOS[selected_scenario_name])
    st.session_state.chat_session = model.start_chat(history=[])
    try:
        initial = st.session_state.chat_session.send_message("Start the roleplay now with your opening line.")
        st.session_state.messages.append({"role": "assistant", "content": initial.text})
    except:
        pass

# 5. AFIȘARE ISTORIC
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if "**🔍 Feedback:**" in content or "[FEEDBACK:" in content:
                parts = content.split("**🗣️ Sarah:**") 
                if len(parts) > 1:
                    st.markdown(f'<div class="feedback-box">{parts[0]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="roleplay-box">🗣️ Sarah: {parts[1]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(content)
            else:
                st.markdown(content)

# 6. ZONA DE INPUT (LOGICA FIXATĂ AICI)
footer_container = st.container()
with footer_container:
    # A. ZONA DE RAPORT
    if len(st.session_state.messages) > 2:
        if st.button("📝 Generează Raport Final"):
            with st.spinner("Analizăm..."):
                try:
                    report_prompt = """
                    [SYSTEM OVERRIDE]
                    STOP ROLEPLAY. Analyze conversation history.
                    Output Markdown report:
                    1. 🏆 Score (1-10) Grammar/Vocab.
                    2. 🚨 Top 3 Recurring Mistakes.
                    3. 💡 Actionable Tips.
                    """
                    response = st.session_state.chat_session.send_message(report_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": f"📊 **RAPORT:**\n\n{response.text}"})
                    st.rerun()
                except Exception as e:
                    st.error(f"Eroare: {e}")

    # B. INPUT WIDGETS
    audio_val = st.audio_input("🎤")
    text_val = st.chat_input("Scrie mesajul tău...")

    user_message = None
    is_audio = False
    should_process = False

    # --- LOGICA NOUĂ DE PRIORITIZARE ---
    # 1. Verificăm dacă avem AUDIO NOU (ne-procesat încă)
    has_new_audio = False
    if audio_val:
        if st.session_state.last_processed_audio != audio_val.file_id:
            has_new_audio = True

    if has_new_audio:
        # Avem audio nou -> Prioritate Audio
        user_message = audio_val
        is_audio = True
        should_process = True
        st.session_state.last_processed_audio = audio_val.file_id
    
    elif text_val:
        # NU avem audio nou -> Putem procesa textul
        # (Chiar dacă există un fișier audio vechi în widget, îl ignorăm)
        user_message = text_val
        is_audio = False
        should_process = True

    # --- PROCESARE ---
    if should_process and user_message:
        with chat_container:
            with st.chat_message("user"):
                if is_audio: st.audio(user_message)
                else: st.markdown(user_message)
        
        if not is_audio: st.session_state.messages.append({"role": "user", "content": user_message})
        else: st.session_state.messages.append({"role": "user", "content": "🎤 *Audio Message*" })

        try:
            reminder_prompt = " (IMPORTANT: Analyze my grammar first, start response with '**🔍 Feedback:**', then '**🗣️ Sarah:**' for roleplay.)"
            if is_audio:
                blob = {"mime_type": user_message.type, "data": user_message.getvalue()}
                response = st.session_state.chat_session.send_message(["Analyze audio english quality.", blob, reminder_prompt])
            else:
                response = st.session_state.chat_session.send_message(user_message + reminder_prompt)
            
            content = response.text
            st.session_state.messages.append({"role": "assistant", "content": content})
            st.rerun()

        except Exception as e:
             if "429" in str(e): st.warning("⏳ Prea multe mesaje.")
             else: st.error(f"Eroare: {e}")