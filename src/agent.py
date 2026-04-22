import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# --- CONFIGURARE ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        pass

if not api_key:
    st.error("❌ EROARE: Lipsește GOOGLE_API_KEY din fișierul .env sau din .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = 'gemini-2.0-flash'

# --- SCENARII CRUISE SHIP ---
SCENARIOS = {
    "🛍️ Shop Assistant – Duty Free": """
        You are James, a senior shop assistant at the Duty Free boutique on a luxury cruise ship.
        Your shop sells: perfumes, cosmetics, jewelry, spirits, chocolates, souvenirs, luxury watches.
        
        YOUR ROLE: Serve the user (Anamaria, a new Eastern European crew member) who is being trained as shop assistant.
        SIMULATE real passenger interactions: browsing, asking about products, prices, discounts, gift ideas.
        
        TEACHING RULES (MANDATORY every single turn):
        1. ALWAYS start your reply with a [FEEDBACK] block analyzing her English.
        2. In [FEEDBACK], identify: grammar errors, wrong vocabulary, unnatural phrases, missing words.
        3. Give the CORRECTED version and explain WHY briefly.
        4. Then continue the roleplay as James/a passenger.
        
        FEEDBACK FORMAT (use exactly this):
        **🔍 Feedback:**
        - ❌ She said: *"[exact quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [brief explanation]
        
        **🛍️ James:** [continue roleplay]
        
        OPENING LINE: "Welcome aboard, Anamaria! I'm James, your supervisor for Deck 5 Boutique. Before we open for passengers, let me show you around. First question — a passenger walks in and says they want 'something nice for their wife.' What do you say?"
        
        SCENARIOS TO SIMULATE:
        - Passenger asks for gift recommendations
        - Upselling perfumes / explaining notes (floral, woody, oriental)
        - Handling a complaint about a broken item
        - Explaining duty-free allowances
        - Processing a return
        - Passenger haggles for a discount
        - Describing a watch to an interested buyer
    """,

    "🍽️ Waiter – Main Dining Room": """
        You are Chef Marco, the Head Waiter of the Main Dining Room on a 5-star cruise ship.
        The restaurant serves formal dinners with a 4-course menu. Dress code is smart casual to formal.
        
        YOUR ROLE: Train Anamaria, a new waitress from Romania, through realistic passenger service scenarios.
        
        TEACHING RULES (MANDATORY every single turn):
        1. ALWAYS start your reply with a [FEEDBACK] block.
        2. Check: grammar, pronunciation notes (written phonetics if needed), wrong word choice, missing articles/prepositions.
        3. Pay special attention to restaurant-specific vocabulary and formal speech registers.
        4. Then continue roleplay as Marco or as a demanding passenger.
        
        FEEDBACK FORMAT (use exactly this):
        **🔍 Feedback:**
        - ❌ She said: *"[exact quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [brief explanation]
        
        **🍽️ Marco:** [continue roleplay]
        
        OPENING LINE: "Buonasera, Anamaria! I'm Marco, I run this dining room like a Swiss watch. Tonight you shadow me. First lesson — a couple arrives at their table. Go ahead, greet them properly. What do you say?"
        
        SCENARIOS TO SIMULATE:
        - Greeting guests and presenting menus
        - Taking orders (mains, allergies, wine pairings)
        - Explaining dishes: ingredients, preparation method, origin
        - Handling a complaint: wrong order, food too cold, long wait
        - Suggesting desserts and after-dinner drinks
        - Formal phrases: "May I take your order?", "Would you care for...?", "I do apologize..."
        - Dealing with a very rude/demanding guest
        - Clearing table between courses
    """,

    "🍹 Bartender – Pool Bar": """
        You are Jake, the Head Bartender at the Lido Pool Bar — the most social spot on the ship.
        The atmosphere is relaxed, fun, international. Guests are on holiday and in a good mood.
        
        YOUR ROLE: Train Anamaria, new bar crew, in real bar interactions and casual conversational English.
        This scenario focuses on CASUAL, FRIENDLY English — very different from the formal dining room.
        
        TEACHING RULES (MANDATORY every single turn):
        1. ALWAYS start your reply with a [FEEDBACK] block.
        2. Focus on: natural casual speech, filler phrases ("Sure thing!", "Coming right up!", "You bet!"),
           correct use of "Can I get you...?" vs "What would you like?", pronunciation of drink names.
        3. Then continue as Jake or simulate a fun/chatty passenger.
        
        FEEDBACK FORMAT (use exactly this):
        **🔍 Feedback:**
        - ❌ She said: *"[exact quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [brief explanation]
        
        **🍹 Jake:** [continue roleplay]
        
        OPENING LINE: "Hey! Welcome to the best office on the ship — the pool bar! I'm Jake. Sun's out, passengers are thirsty, and you're on shift with me. Ready? Here comes your first customer. I'll play them — you serve. Go!"
        
        SCENARIOS TO SIMULATE:
        - Taking drink orders at the bar
        - Explaining cocktail menu / making recommendations
        - Making small talk with passengers (where are you from, enjoying the cruise?)
        - Handling a passenger who's had too much to drink (diplomatically cut off)
        - Learning drink names and how to pronounce them
        - Upselling premium spirits
        - Explaining daily drink specials
        - Closing tabs and card payments
    """,

    "🚢 Guest Services – Information Desk": """
        You are Patricia, Senior Guest Services Officer at the Information Desk on a cruise ship.
        You handle: questions about ports, excursions, complaints, lost & found, emergencies, room issues.
        
        YOUR ROLE: Train Anamaria who just joined Guest Services. This role requires FORMAL, PROFESSIONAL English
        and EMPATHY — guests come here when they have problems.
        
        TEACHING RULES (MANDATORY every single turn):
        1. ALWAYS start your reply with a [FEEDBACK] block.
        2. Focus on: professional tone, empathy language ("I completely understand...", "I sincerely apologize..."),
           formal vs informal register, correct use of "I'm afraid...", "Unfortunately...", "Allow me to..."
        3. Note any pronunciation issues phonetically.
        4. Then continue as Patricia or as a stressed/upset passenger.
        
        FEEDBACK FORMAT (use exactly this):
        **🔍 Feedback:**
        - ❌ She said: *"[exact quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [brief explanation]
        
        **🛎️ Patricia:** [continue roleplay]
        
        OPENING LINE: "Good morning, Anamaria. Welcome to Guest Services — the heart of this ship. Our job is simple: every guest leaves this desk feeling heard and helped. Ready for your first interaction? A passenger is walking toward us. She looks upset. Go ahead — greet her."
        
        SCENARIOS TO SIMULATE:
        - Answering questions about port excursions and shore leave times
        - Handling lost luggage or lost items
        - Dealing with a billing dispute
        - Medical emergency — directing to medical center calmly
        - Room complaints (noise, AC, cleanliness)
        - Explaining ship safety procedures
        - Booking specialty restaurants
    """,

    "🎯 Mock Test – Job Interview (Cruise Line HR)": """
        You are Richard, Recruitment Officer at a major cruise line (think Royal Caribbean / MSC level).
        You are conducting a final interview for Anamaria for a hospitality position on board.
        
        YOUR ROLE: Ask real interview questions, evaluate her answers, correct her English in real-time.
        Be professional but warm. This is HIGH STAKES — she needs to perform well.
        
        TEACHING RULES (MANDATORY every single turn):
        1. ALWAYS start your reply with a [FEEDBACK] block.
        2. Focus on: interview-specific language ("I believe my strengths are...", "In my previous role..."),
           confident vs weak phrasing, hedging language, answer structure (STAR method hints).
        3. Rate her answer: star out of 5 for Language Quality + star out of 5 for Answer Quality.
        4. Then ask the next interview question.
        
        FEEDBACK FORMAT (use exactly this):
        **🔍 Feedback:**
        - ❌ She said: *"[exact quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [brief explanation]
        - 🌟 Score: Language [X/5] | Answer Quality [X/5]
        
        **👔 Richard:** [next question or comment]
        
        OPENING LINE: "Good morning, Anamaria! Thank you for joining us today. My name is Richard, and I'll be your interviewer. We have about 20 minutes together. I've reviewed your CV — lovely background. Let's start simply: Could you tell me a little about yourself and why you'd like to work on a cruise ship?"
        
        QUESTION BANK TO COVER:
        - Tell me about yourself
        - Why do you want to work on a cruise ship?
        - How do you handle difficult customers?
        - Describe a time you worked under pressure
        - How do you feel about being away from home for 6-8 months?
        - What languages do you speak?
        - Where do you see yourself in 2 years?
        - What would you do if a colleague was rude to a guest?
        - Are you comfortable with a strict uniform and grooming policy?
        - Do you have any questions for me?
    """
}

# --- VOCABULAR UTIL PER SCENARIU ---
VOCAB_TIPS = {
    "🛍️ Shop Assistant – Duty Free": [
        "**May I help you find something?**",
        "**We have a special offer on...**",
        "**This is one of our best sellers.**",
        "**Would you like to try a sample?**",
        "**I can gift-wrap that for you.**",
        "**Duty-free allowance**",
        "**Receipt / invoice**",
    ],
    "🍽️ Waiter – Main Dining Room": [
        "**May I take your order?**",
        "**Would you care for...?**",
        "**The chef recommends...**",
        "**I do apologize for the inconvenience.**",
        "**Your table is ready, sir/madam.**",
        "**Rare / medium / well-done**",
        "**Allergens / dietary requirements**",
    ],
    "🍹 Bartender – Pool Bar": [
        "**Coming right up!**",
        "**What can I get for you?**",
        "**On the rocks / straight up / neat**",
        "**Would you like to start a tab?**",
        "**That's your last one, buddy.**",
        "**Our special today is...**",
        "**Cheers! / Enjoy!**",
    ],
    "🚢 Guest Services – Information Desk": [
        "**I completely understand your concern.**",
        "**Allow me to look into that for you.**",
        "**I sincerely apologize for the inconvenience.**",
        "**I'm afraid...**",
        "**Let me connect you with the right department.**",
        "**Shore excursion / tender port**",
        "**Embarkation / disembarkation**",
    ],
    "🎯 Mock Test – Job Interview (Cruise Line HR)": [
        "**I believe my strengths are...**",
        "**In my previous experience...**",
        "**I'm comfortable working in a multicultural environment.**",
        "**I thrive under pressure.**",
        "**I'm a quick learner.**",
        "**Customer satisfaction is my priority.**",
        "**I'm eager to grow with the company.**",
    ],
}

# --- FUNCȚII AUXILIARE ---
def clean_html_for_markdown(text):
    text = text.replace('<div class="feedback-box">', '\n> **🔍 FEEDBACK:**\n> ')
    text = text.replace('</div>', '\n')
    text = text.replace('<div class="roleplay-box">', '\n')
    return text

def get_transcript():
    scenario = st.session_state.get("last_scenario", "Necunoscut")
    transcript = f"# 🚢 Cruise Ship English Training — Anamaria\n"
    transcript += f"**Scenariu:** {scenario}\n"
    transcript += f"**Model:** {MODEL_NAME}\n\n---\n\n"
    for msg in st.session_state.messages:
        role = "🤖 Trainer" if msg["role"] == "assistant" else "👩 Anamaria"
        content = clean_html_for_markdown(msg["content"])
        transcript += f"### {role}:\n{content}\n\n"
    return transcript

def count_turns():
    user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
    return len(user_msgs)

# --- INTERFAȚA GRAFICĂ ---
st.set_page_config(page_title="Cruise English Trainer", page_icon="🚢", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: #0a0f1e;
        color: #e8eaf0;
    }
    [data-testid="stSidebar"] {
        background: #0d1425;
        border-right: 1px solid #1e2d4a;
    }
    .cruise-header {
        background: linear-gradient(135deg, #0a1628 0%, #0d2347 50%, #0a1628 100%);
        border: 1px solid #1e3a5f;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .cruise-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: repeating-linear-gradient(
            45deg, transparent, transparent 40px,
            rgba(30,90,150,0.03) 40px, rgba(30,90,150,0.03) 80px
        );
    }
    .cruise-header h1 { font-size: 1.8rem; font-weight: 700; color: #ffffff; margin: 0 0 6px 0; }
    .cruise-header p { color: #7090b0; margin: 0; font-size: 0.9rem; }
    .feedback-box {
        background: linear-gradient(135deg, #0f1e35, #111d30);
        border-left: 4px solid #e85555;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 8px 0 12px 0;
        font-size: 0.92em;
    }
    .roleplay-box {
        background: linear-gradient(135deg, #0a1e10, #0d2216);
        border-left: 4px solid #2ecc71;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 4px 0;
        font-size: 1.05em;
        font-weight: 500;
    }
    .progress-container {
        background: #111d30;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        border: 1px solid #1e3a5f;
    }
    .progress-bar-bg { background: #1a2840; border-radius: 4px; height: 8px; margin-top: 6px; }
    .progress-bar-fill { background: linear-gradient(90deg, #2563eb, #3b82f6); height: 8px; border-radius: 4px; }
    .vocab-card {
        background: #111d30;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 10px 14px;
        margin: 5px 0;
        font-size: 0.85em;
        color: #a8c4e0;
    }
    .scenario-badge {
        display: inline-block;
        background: linear-gradient(135deg, #1a2840, #0d1929);
        border: 1px solid #2563eb;
        color: #60a5fa;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82em;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .tips-header {
        color: #60a5fa;
        font-size: 0.8em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 12px 0 6px 0;
    }
    [data-testid="stChatMessage"] {
        background: #0d1929 !important;
        border-radius: 12px !important;
        border: 1px solid #1a2e45 !important;
        margin-bottom: 8px !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #1a3a6e, #1e4a8a) !important;
        color: #ffffff !important;
        border: 1px solid #2563eb !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    hr { border-color: #1e3a5f !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="cruise-header">
    <h1>🚢 Cruise Ship English Trainer</h1>
    <p>Pregătire pentru <strong style="color:#60a5fa">Anamaria</strong> — practică reală pentru viața la bord</p>
</div>
""", unsafe_allow_html=True)

# --- INIȚIALIZARE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None
if "last_scenario" not in st.session_state:
    st.session_state.last_scenario = list(SCENARIOS.keys())[0]
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "total_corrections" not in st.session_state:
    st.session_state.total_corrections = 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Setări")
    
    selected_scenario_name = st.selectbox(
        "Alege poziția pe vas:",
        list(SCENARIOS.keys()),
        key="selected_scenario",
        index=list(SCENARIOS.keys()).index(st.session_state.last_scenario) if st.session_state.last_scenario in SCENARIOS else 0
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Sesiune Nouă", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_session = None
            st.session_state.last_processed_audio = None
            st.session_state.total_corrections = 0
            st.rerun()
    with col2:
        if st.button("📊 Raport", use_container_width=True):
            if len(st.session_state.messages) > 2:
                with st.spinner("Analizăm sesiunea..."):
                    try:
                        report_prompt = """
                        [SYSTEM OVERRIDE — STOP ROLEPLAY]
                        Analyze the entire conversation and create a detailed progress report in Markdown.
                        
                        Structure:
                        ## 📊 Cruise English Training Report
                        
                        ### 🏆 Overall Score: [X/10]
                        
                        ### 💪 What Anamaria did WELL:
                        [list 3-5 positive observations]
                        
                        ### 🚨 Top 5 Recurring Mistakes:
                        [list with corrections and examples from the conversation]
                        
                        ### 📚 Key Vocabulary to Practice:
                        [list 8-10 words/phrases she struggled with, with definitions]
                        
                        ### 🎯 Homework for Next Session:
                        [3 specific, actionable exercises]
                        
                        ### 🚢 Cruise-Specific Tips:
                        [2-3 tips specific to the role she was practicing]
                        """
                        response = st.session_state.chat_session.send_message(report_prompt)
                        st.session_state.messages.append({"role": "assistant", "content": f"📊 **RAPORT SESIUNE:**\n\n{response.text}"})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Eroare: {e}")
            else:
                st.warning("Mai practică puțin înainte de raport!")

    st.divider()
    
    turns = count_turns()
    goal = 10
    progress_pct = min(turns / goal * 100, 100)
    st.markdown(f"""
    <div class="progress-container">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="color:#60a5fa;font-size:0.82em;font-weight:700">PROGRES SESIUNE</span>
            <span style="color:#7090b0;font-size:0.78em">{turns}/{goal} ture</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:{progress_pct}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if turns >= goal:
        st.success("🎉 Sesiune completă! Apasă Raport.")
    
    st.divider()
    st.markdown('<div class="tips-header">💬 Fraze Cheie</div>', unsafe_allow_html=True)
    vocab_list = VOCAB_TIPS.get(selected_scenario_name, [])
    for phrase in vocab_list:
        st.markdown(f'<div class="vocab-card">{phrase}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown('<div class="tips-header">📁 Export</div>', unsafe_allow_html=True)
    transcript_txt = get_transcript()
    st.download_button(
        label="💾 Descarcă Sesiunea (.md)",
        data=transcript_txt,
        file_name=f"cruise_english_{selected_scenario_name[:15].replace(' ','_')}.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    st.divider()
    st.markdown("""
    <div style="font-size:0.72em;color:#3a5070;text-align:center;line-height:1.6">
        🚢 Antigravity Cruise Trainer v2.0<br>
        Made with ❤️ for Anamaria
    </div>
    """, unsafe_allow_html=True)

# --- LOGICA SCHIMBARE SCENARIU ---
if st.session_state.last_scenario != selected_scenario_name:
    st.session_state.messages = []
    st.session_state.chat_session = None
    st.session_state.last_processed_audio = None
    st.session_state.total_corrections = 0
    st.session_state.last_scenario = selected_scenario_name
    st.rerun()

# --- START CHAT ENGINE ---
if st.session_state.chat_session is None:
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SCENARIOS[selected_scenario_name])
    st.session_state.chat_session = model.start_chat(history=[])
    try:
        initial = st.session_state.chat_session.send_message("Start the roleplay now with your opening line. Be warm but professional.")
        st.session_state.messages.append({"role": "assistant", "content": initial.text})
    except Exception as e:
        st.error(f"Nu s-a putut inițializa sesiunea: {e}")

# --- SCENARIO BADGE ---
st.markdown(f'<span class="scenario-badge">{selected_scenario_name}</span>', unsafe_allow_html=True)
st.markdown("")

# --- AFIȘARE MESAJE ---
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            has_feedback = "**🔍 Feedback:**" in content
            
            if has_feedback:
                roleplay_markers = [
                    "**🛍️ James:**", "**🍽️ Marco:**", "**🍹 Jake:**",
                    "**🛎️ Patricia:**", "**👔 Richard:**"
                ]
                split_point = -1
                for marker in roleplay_markers:
                    if marker in content:
                        split_point = content.find(marker)
                        break
                
                if split_point > 0:
                    feedback_part = content[:split_point].strip()
                    roleplay_part = content[split_point:].strip()
                    st.markdown(f'<div class="feedback-box">{feedback_part}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="roleplay-box">{roleplay_part}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(content)
            else:
                st.markdown(content)

# --- INPUT ZONE ---
footer = st.container()
with footer:
    audio_val = st.audio_input("🎤 Sau vorbește direct")
    text_val = st.chat_input("Scrie răspunsul tău în Engleză...")
    
    user_message = None
    is_audio = False
    should_process = False
    
    has_new_audio = False
    if audio_val:
        if st.session_state.last_processed_audio != audio_val.file_id:
            has_new_audio = True
    
    if has_new_audio:
        user_message = audio_val
        is_audio = True
        should_process = True
        st.session_state.last_processed_audio = audio_val.file_id
    elif text_val:
        user_message = text_val
        is_audio = False
        should_process = True
    
    if should_process and user_message:
        with chat_container:
            with st.chat_message("user"):
                if is_audio:
                    st.audio(user_message)
                else:
                    st.markdown(user_message)
        
        if not is_audio:
            st.session_state.messages.append({"role": "user", "content": user_message})
        else:
            st.session_state.messages.append({"role": "user", "content": "🎤 *Mesaj audio*"})
        
        char_map = {
            "🛍️ Shop Assistant – Duty Free": "**🛍️ James:**",
            "🍽️ Waiter – Main Dining Room": "**🍽️ Marco:**",
            "🍹 Bartender – Pool Bar": "**🍹 Jake:**",
            "🚢 Guest Services – Information Desk": "**🛎️ Patricia:**",
            "🎯 Mock Test – Job Interview (Cruise Line HR)": "**👔 Richard:**",
        }
        char_tag = char_map.get(selected_scenario_name, "**[Character]:**")
        reminder = f" (IMPORTANT: Always start with **🔍 Feedback:** block analyzing my English, then use {char_tag} to continue the roleplay.)"
        
        try:
            with st.spinner("Se analizează..."):
                if is_audio:
                    blob = {"mime_type": user_message.type, "data": user_message.getvalue()}
                    response = st.session_state.chat_session.send_message(
                        ["Transcribe and analyze the English quality of this audio.", blob, reminder]
                    )
                else:
                    response = st.session_state.chat_session.send_message(user_message + reminder)
            
            content = response.text
            st.session_state.messages.append({"role": "assistant", "content": content})
            if "❌" in content:
                st.session_state.total_corrections += content.count("❌")
            st.rerun()
            
        except Exception as e:
            if "429" in str(e):
                st.warning("⏳ Prea multe mesaje. Așteaptă câteva secunde.")
            else:
                st.error(f"Eroare: {e}")