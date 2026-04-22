import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import json
import random

# --- CONFIGURARE ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
if not api_key:
    st.error("❌ EROARE: Lipsește GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=api_key)
MODEL_NAME = 'gemini-2.5-flash'

# --- GAME CONFIG ---
LEVELS = [
    {"name": "🧹 Rookie Crew",       "min_xp": 0,    "color": "#7f8c8d"},
    {"name": "⚓ Junior Staff",       "min_xp": 50,   "color": "#3498db"},
    {"name": "🍽️ Trained Steward",   "min_xp": 150,  "color": "#2ecc71"},
    {"name": "🎖️ Senior Officer",    "min_xp": 350,  "color": "#f39c12"},
    {"name": "👑 Captain's Elite",   "min_xp": 700,  "color": "#e74c3c"},
]

BADGES = {
    "first_message":    {"icon": "🎤", "name": "First Words",        "desc": "Primul mesaj trimis"},
    "no_mistakes":      {"icon": "⭐", "name": "Flawless Round",     "desc": "Un răspuns fără greșeli"},
    "5_turns":          {"icon": "🔥", "name": "On Fire",            "desc": "5 ture consecutive"},
    "10_turns":         {"icon": "🚀", "name": "Cruise Veteran",     "desc": "10 ture completate"},
    "audio_used":       {"icon": "🎙️", "name": "Voice Activated",   "desc": "Ai folosit vocea"},
    "report_done":      {"icon": "📊", "name": "Self-Aware",         "desc": "Ai generat un raport"},
    "all_scenarios":    {"icon": "🌊", "name": "Full Crew",          "desc": "Ai încercat toate scenariile"},
}

XP_REWARDS = {
    "message_sent":   10,
    "no_mistake":     25,
    "audio_bonus":    15,
    "streak_3":       20,
    "streak_5":       40,
}

SCENARIOS = {
    "🛍️ Shop – Duty Free": {
        "icon": "🛍️",
        "char": "James",
        "char_emoji": "🧑‍💼",
        "difficulty": "⭐⭐",
        "prompt": """
        You are James, senior shop assistant at the Duty Free boutique on a luxury cruise ship.
        Shop sells: perfumes, cosmetics, jewelry, spirits, chocolates, souvenirs, luxury watches.
        Train Anamaria (new Eastern European crew) as shop assistant.
        
        TEACHING RULES (MANDATORY every turn):
        1. ALWAYS start with **🔍 Feedback:** block.
        2. Identify grammar errors, wrong vocabulary, unnatural phrases.
        3. Give corrected version + brief explanation.
        4. Score the turn: award 0-3 stars based on English quality.
        
        EXACT FORMAT:
        **🔍 Feedback:**
        - ❌ She said: *"[quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [explanation]
        - 🌟 Stars: [★★★ or ★★☆ or ★☆☆ based on quality]
        
        **🛍️ James:** [continue roleplay]
        
        OPENING: "Welcome aboard, Anamaria! I'm James, Deck 5 Boutique supervisor. First test — a passenger wants 'something nice for his wife.' What do you say?"
        """,
        "vocab": ["May I help you find something?", "This is one of our best sellers.", "Would you like to try a sample?", "I can gift-wrap that for you.", "Duty-free allowance", "We have a special offer on..."]
    },
    "🍽️ Waiter – Dining Room": {
        "icon": "🍽️",
        "char": "Marco",
        "char_emoji": "👨‍🍳",
        "difficulty": "⭐⭐⭐",
        "prompt": """
        You are Marco, Head Waiter in the Main Dining Room on a 5-star cruise ship.
        Formal dinners, 4-course menu, smart casual to formal dress code.
        Train Anamaria, new waitress from Romania.
        
        TEACHING RULES (MANDATORY every turn):
        1. ALWAYS start with **🔍 Feedback:** block.
        2. Check grammar, pronunciation (phonetics if needed), wrong word choice, missing articles.
        3. Focus on formal restaurant vocabulary and speech registers.
        4. Score the turn: award stars.
        
        EXACT FORMAT:
        **🔍 Feedback:**
        - ❌ She said: *"[quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [explanation]
        - 🌟 Stars: [★★★ or ★★☆ or ★☆☆]
        
        **🍽️ Marco:** [continue roleplay]
        
        OPENING: "Buonasera, Anamaria! I'm Marco. Tonight you shadow me. A couple just arrived at their table — greet them properly. Go!"
        """,
        "vocab": ["May I take your order?", "Would you care for...?", "The chef recommends...", "I do apologize for the inconvenience.", "Rare / medium / well-done", "Allergens / dietary requirements"]
    },
    "🍹 Bartender – Pool Bar": {
        "icon": "🍹",
        "char": "Jake",
        "char_emoji": "🧑‍🍳",
        "difficulty": "⭐",
        "prompt": """
        You are Jake, Head Bartender at the Lido Pool Bar. Relaxed, fun, international atmosphere.
        Train Anamaria in casual conversational English for bar work.
        
        TEACHING RULES (MANDATORY every turn):
        1. ALWAYS start with **🔍 Feedback:** block.
        2. Focus on casual speech, filler phrases, drink names pronunciation.
        3. Score the turn: award stars.
        
        EXACT FORMAT:
        **🔍 Feedback:**
        - ❌ She said: *"[quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [explanation]
        - 🌟 Stars: [★★★ or ★★☆ or ★☆☆]
        
        **🍹 Jake:** [continue roleplay]
        
        OPENING: "Hey! Best office on the ship — the pool bar! I'm Jake. First customer incoming — you serve. Go!"
        """,
        "vocab": ["Coming right up!", "What can I get for you?", "On the rocks / straight up / neat", "Would you like to start a tab?", "Our special today is...", "Cheers! / Enjoy!"]
    },
    "🛎️ Guest Services": {
        "icon": "🛎️",
        "char": "Patricia",
        "char_emoji": "👩‍💼",
        "difficulty": "⭐⭐⭐",
        "prompt": """
        You are Patricia, Senior Guest Services Officer at the Information Desk.
        Handle: ports, excursions, complaints, lost & found, emergencies, room issues.
        Train Anamaria — formal, professional English + empathy required.
        
        TEACHING RULES (MANDATORY every turn):
        1. ALWAYS start with **🔍 Feedback:** block.
        2. Focus on professional tone, empathy language, formal register.
        3. Score the turn: award stars.
        
        EXACT FORMAT:
        **🔍 Feedback:**
        - ❌ She said: *"[quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [explanation]
        - 🌟 Stars: [★★★ or ★★☆ or ★☆☆]
        
        **🛎️ Patricia:** [continue roleplay]
        
        OPENING: "Good morning, Anamaria. Welcome to Guest Services. An upset passenger is approaching — greet her."
        """,
        "vocab": ["I completely understand your concern.", "Allow me to look into that for you.", "I sincerely apologize for the inconvenience.", "I'm afraid...", "Shore excursion / tender port", "Embarkation / disembarkation"]
    },
    "🎯 HR Interview": {
        "icon": "🎯",
        "char": "Richard",
        "char_emoji": "👔",
        "difficulty": "⭐⭐⭐⭐",
        "prompt": """
        You are Richard, Recruitment Officer at a major cruise line (Royal Caribbean / MSC level).
        Final interview for Anamaria for a hospitality position.
        
        TEACHING RULES (MANDATORY every turn):
        1. ALWAYS start with **🔍 Feedback:** block.
        2. Focus on interview language, confident phrasing, STAR method.
        3. Rate: Language score + Answer quality score out of 5.
        
        EXACT FORMAT:
        **🔍 Feedback:**
        - ❌ She said: *"[quote]"*
        - ✅ Better: *"[correction]"*
        - 📖 Why: [explanation]
        - 🌟 Stars: [★★★ or ★★☆ or ★☆☆]
        - 📈 Language [X/5] | Answer [X/5]
        
        **👔 Richard:** [next question]
        
        OPENING: "Good morning, Anamaria! I'm Richard. Could you tell me about yourself and why you'd like to work on a cruise ship?"
        """,
        "vocab": ["I believe my strengths are...", "In my previous experience...", "I thrive under pressure.", "I'm a quick learner.", "Customer satisfaction is my priority.", "I'm eager to grow with the company."]
    },
}

# --- FUNCȚII GAME ---
def get_level(xp):
    current = LEVELS[0]
    for lvl in LEVELS:
        if xp >= lvl["min_xp"]:
            current = lvl
    return current

def get_next_level(xp):
    for i, lvl in enumerate(LEVELS):
        if xp < lvl["min_xp"]:
            return lvl, LEVELS[i-1]["min_xp"] if i > 0 else 0
    return None, LEVELS[-1]["min_xp"]

def xp_to_next(xp):
    next_lvl, prev_min = get_next_level(xp)
    if not next_lvl:
        return 100, 100
    total = next_lvl["min_xp"] - prev_min
    progress = xp - prev_min
    return progress, total

def award_xp(amount, reason=""):
    st.session_state.xp += amount
    st.session_state.xp_log.append(f"+{amount} XP — {reason}")
    if len(st.session_state.xp_log) > 5:
        st.session_state.xp_log.pop(0)

def award_badge(badge_key):
    if badge_key not in st.session_state.badges:
        st.session_state.badges.append(badge_key)
        st.session_state.new_badge = badge_key

def count_stars_in_response(text):
    if "★★★" in text:
        return 3
    elif "★★☆" in text:
        return 2
    elif "★☆☆" in text:
        return 1
    return 1

def count_turns():
    return len([m for m in st.session_state.messages if m["role"] == "user"])

def get_transcript():
    lines = [f"# 🚢 Cruise English Training — Anamaria\n**Scenariu:** {st.session_state.last_scenario}\n\n---\n\n"]
    for msg in st.session_state.messages:
        role = "🤖 Trainer" if msg["role"] == "assistant" else "👩 Anamaria"
        lines.append(f"### {role}:\n{msg['content']}\n\n")
    return "".join(lines)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cruise Trainer 🚢", page_icon="🚢", layout="wide")

# --- MEGA CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&display=swap');

:root {
    --bg-deep:    #050a18;
    --bg-card:    #0a1428;
    --bg-panel:   #0d1e35;
    --cyan:       #00f5ff;
    --gold:       #ffd700;
    --green:      #00ff88;
    --red:        #ff4757;
    --purple:     #a855f7;
    --border:     #1a3a5c;
    --text:       #c8d8f0;
    --text-dim:   #4a6a8a;
}

* { font-family: 'Exo 2', sans-serif !important; }

[data-testid="stAppViewContainer"] {
    background: var(--bg-deep) !important;
    background-image: 
        radial-gradient(ellipse at 20% 20%, rgba(0,245,255,0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(168,85,247,0.04) 0%, transparent 50%),
        repeating-linear-gradient(0deg, transparent, transparent 80px, rgba(26,58,92,0.15) 80px, rgba(26,58,92,0.15) 81px),
        repeating-linear-gradient(90deg, transparent, transparent 80px, rgba(26,58,92,0.15) 80px, rgba(26,58,92,0.15) 81px) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background: #060d1a !important;
    border-right: 1px solid var(--border) !important;
}

/* ===== HEADER ===== */
.game-header {
    background: linear-gradient(135deg, #060d1a 0%, #0a1628 40%, #06152a 100%);
    border: 1px solid var(--border);
    border-top: 2px solid var(--cyan);
    border-radius: 0 0 20px 20px;
    padding: 20px 28px 16px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.game-header::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), var(--purple), var(--cyan), transparent);
    animation: scanline 3s linear infinite;
}
@keyframes scanline {
    0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; }
}
.game-title {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.6rem !important;
    font-weight: 900 !important;
    color: #fff !important;
    letter-spacing: 2px !important;
    text-shadow: 0 0 20px rgba(0,245,255,0.5) !important;
    margin: 0 0 4px !important;
}
.game-subtitle { color: var(--text-dim); font-size: 0.85rem; }
.game-subtitle strong { color: var(--cyan); }

/* ===== XP BAR ===== */
.xp-container {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
}
.xp-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.level-name {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    color: var(--gold) !important;
    text-shadow: 0 0 10px rgba(255,215,0,0.4);
}
.xp-count { font-size: 0.75rem; color: var(--cyan); font-weight: 600; }
.xp-bar-bg {
    background: #0a1628;
    border-radius: 6px;
    height: 10px;
    border: 1px solid var(--border);
    overflow: hidden;
}
.xp-bar-fill {
    height: 10px;
    border-radius: 6px;
    background: linear-gradient(90deg, #00b4d8, #00f5ff, #7fffce);
    box-shadow: 0 0 12px rgba(0,245,255,0.6);
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
}
.xp-bar-fill::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 20px; height: 100%;
    background: rgba(255,255,255,0.4);
    border-radius: 6px;
    animation: shimmer 1.5s ease infinite;
}
@keyframes shimmer { 0%,100% { opacity: 0; } 50% { opacity: 1; } }

/* ===== STATS ROW ===== */
.stats-row {
    display: flex;
    gap: 8px;
    margin: 10px 0;
}
.stat-box {
    flex: 1;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 8px;
    text-align: center;
}
.stat-value {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    color: var(--cyan) !important;
    display: block;
    line-height: 1;
}
.stat-label { font-size: 0.65rem; color: var(--text-dim); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px; }

/* ===== STREAK FIRE ===== */
.streak-box {
    background: linear-gradient(135deg, #1a0a00, #2a1200);
    border: 1px solid #ff6b35;
    border-radius: 10px;
    padding: 10px 8px;
    text-align: center;
}
.streak-value {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    color: #ff9f43 !important;
    display: block;
    text-shadow: 0 0 10px rgba(255,159,67,0.5);
}

/* ===== BADGES ===== */
.badges-section { margin: 10px 0; }
.badges-title {
    font-size: 0.72rem;
    color: var(--gold);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.badges-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.badge-item {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 0.78em;
    color: var(--text);
    cursor: default;
}
.badge-item.earned {
    background: linear-gradient(135deg, #1a1400, #2a2200);
    border-color: var(--gold);
    color: var(--gold);
    box-shadow: 0 0 8px rgba(255,215,0,0.2);
}
.badge-item.locked { opacity: 0.3; filter: grayscale(1); }

/* ===== NEW BADGE POPUP ===== */
.badge-popup {
    background: linear-gradient(135deg, #1a1200, #2d1f00);
    border: 2px solid var(--gold);
    border-radius: 14px;
    padding: 16px 20px;
    text-align: center;
    animation: popIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 0 30px rgba(255,215,0,0.3);
}
@keyframes popIn {
    from { transform: scale(0.5); opacity: 0; }
    to   { transform: scale(1);   opacity: 1; }
}

/* ===== XP POPUP ===== */
.xp-popup {
    background: linear-gradient(135deg, #001a1a, #002a2a);
    border: 1px solid var(--cyan);
    border-radius: 10px;
    padding: 10px 16px;
    margin: 6px 0;
    font-size: 0.85em;
    color: var(--cyan);
    animation: slideIn 0.3s ease;
}
@keyframes slideIn { from { transform: translateX(-10px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* ===== SCENARIO CARDS ===== */
.scenario-active {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #001a2a, #002a3a);
    border: 1px solid var(--cyan);
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.82em;
    font-weight: 700;
    color: var(--cyan);
    letter-spacing: 0.5px;
    box-shadow: 0 0 15px rgba(0,245,255,0.15);
    margin-bottom: 12px;
}

/* ===== VOCAB CHIPS ===== */
.vocab-section-title { font-size: 0.72rem; color: var(--purple); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin: 10px 0 6px; }
.vocab-chip {
    background: linear-gradient(135deg, #100a28, #1a1040);
    border: 1px solid #3a2a6a;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 0;
    font-size: 0.82em;
    color: #c8b4f0;
}

/* ===== CHAT MESSAGES ===== */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
    margin-bottom: 10px !important;
    padding: 4px !important;
}

/* ===== FEEDBACK & ROLEPLAY ===== */
.feedback-box {
    background: linear-gradient(135deg, #1a0608, #2a0810);
    border-left: 4px solid var(--red);
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    margin: 6px 0 10px;
    font-size: 0.9em;
    box-shadow: inset 0 0 20px rgba(255,71,87,0.05);
}
.roleplay-box {
    background: linear-gradient(135deg, #001a0e, #002a16);
    border-left: 4px solid var(--green);
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    margin: 4px 0;
    font-size: 1.05em;
    font-weight: 500;
    box-shadow: inset 0 0 20px rgba(0,255,136,0.03);
}

/* ===== STARS DISPLAY ===== */
.stars-earned {
    display: inline-block;
    background: linear-gradient(135deg, #1a1400, #2a2000);
    border: 1px solid var(--gold);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 1.1em;
    color: var(--gold);
    box-shadow: 0 0 10px rgba(255,215,0,0.2);
    margin-top: 8px;
}

/* ===== BUTTONS ===== */
.stButton button {
    background: linear-gradient(135deg, #0a2040, #0d2a55) !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}
.stButton button:hover {
    background: linear-gradient(135deg, #00f5ff22, #00f5ff33) !important;
    box-shadow: 0 0 15px rgba(0,245,255,0.3) !important;
}

/* ===== SELECTBOX ===== */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}

/* ===== CHAT INPUT ===== */
[data-testid="stChatInput"] textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 1px var(--cyan) !important;
}

hr { border-color: var(--border) !important; }

/* ===== DIFFICULTY DOTS ===== */
.diff-label { font-size: 0.72rem; color: var(--text-dim); margin-bottom: 2px; }

/* ===== DOWNLOAD BUTTON ===== */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #0a2000, #0d2800) !important;
    color: var(--green) !important;
    border-color: var(--green) !important;
}

/* ===== MISSION BAR ===== */
.mission-bar {
    background: var(--bg-panel);
    border: 1px solid #2a1a4a;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 0.8em;
}
.mission-title { color: var(--purple); font-weight: 700; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.mission-text { color: var(--text); }

</style>
""", unsafe_allow_html=True)

# --- STATE INIT ---
if "messages"              not in st.session_state: st.session_state.messages = []
if "last_processed_audio"  not in st.session_state: st.session_state.last_processed_audio = None
if "last_scenario"         not in st.session_state: st.session_state.last_scenario = list(SCENARIOS.keys())[0]
if "chat_session"          not in st.session_state: st.session_state.chat_session = None
if "xp"                    not in st.session_state: st.session_state.xp = 0
if "xp_log"                not in st.session_state: st.session_state.xp_log = []
if "badges"                not in st.session_state: st.session_state.badges = []
if "new_badge"             not in st.session_state: st.session_state.new_badge = None
if "streak"                not in st.session_state: st.session_state.streak = 0
if "total_stars"           not in st.session_state: st.session_state.total_stars = 0
if "scenarios_tried"       not in st.session_state: st.session_state.scenarios_tried = set()

# --- HEADER ---
st.markdown("""
<div class="game-header">
    <div class="game-title">🚢 CRUISE ENGLISH TRAINER</div>
    <div class="game-subtitle">Training pentru <strong>Anamaria</strong> — misiunea ta pe vas începe aici</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    selected_scenario_name = st.selectbox(
        "🎮 Alege misiunea:",
        list(SCENARIOS.keys()),
        key="selected_scenario",
        index=list(SCENARIOS.keys()).index(st.session_state.last_scenario) if st.session_state.last_scenario in SCENARIOS else 0
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 RESET", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_session = None
            st.session_state.last_processed_audio = None
            st.rerun()
    with col2:
        if st.button("📊 RAPORT", use_container_width=True):
            if len(st.session_state.messages) > 2:
                with st.spinner("Se procesează raportul..."):
                    try:
                        rp = """[STOP ROLEPLAY] Analyze conversation. Output Markdown:
                        ## 📊 Performance Report
                        ### 🏆 Overall Score: [X/10]
                        ### 💪 Strengths: [3-5 points]
                        ### 🚨 Top Mistakes: [5 with corrections]
                        ### 📚 Vocabulary to Practice: [8-10 phrases]
                        ### 🎯 Next Session Goals: [3 exercises]
                        ### 🚢 Cruise-Specific Tips: [2-3 tips]"""
                        resp = st.session_state.chat_session.send_message(rp)
                        st.session_state.messages.append({"role": "assistant", "content": f"📊 **RAPORT:**\n\n{resp.text}"})
                        award_badge("report_done")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Eroare: {e}")
            else:
                st.warning("Mai practică înainte de raport!")

    st.divider()

    # XP & Level
    current_level = get_level(st.session_state.xp)
    xp_prog, xp_total = xp_to_next(st.session_state.xp)
    pct = int(xp_prog / xp_total * 100) if xp_total > 0 else 100

    st.markdown(f"""
    <div class="xp-container">
        <div class="xp-label">
            <span class="level-name">{current_level['name']}</span>
            <span class="xp-count">⚡ {st.session_state.xp} XP</span>
        </div>
        <div class="xp-bar-bg">
            <div class="xp-bar-fill" style="width:{pct}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    turns = count_turns()
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-box">
            <span class="stat-value">{'⭐' * min(st.session_state.total_stars, 5) if st.session_state.total_stars > 0 else '—'}</span>
            <div class="stat-label">Stars</div>
        </div>
        <div class="stat-box">
            <span class="stat-value">{turns}</span>
            <div class="stat-label">Ture</div>
        </div>
        <div class="streak-box">
            <span class="streak-value">🔥 {st.session_state.streak}</span>
            <div class="stat-label">Streak</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # XP log
    if st.session_state.xp_log:
        for log in reversed(st.session_state.xp_log[-3:]):
            st.markdown(f'<div class="xp-popup">{log}</div>', unsafe_allow_html=True)

    st.divider()

    # Badges
    st.markdown('<div class="badges-title">🏅 Achievements</div>', unsafe_allow_html=True)
    badge_html = '<div class="badges-grid">'
    for key, badge in BADGES.items():
        earned = key in st.session_state.badges
        cls = "badge-item earned" if earned else "badge-item locked"
        desc = badge["desc"]
        icon = badge["icon"]
        name = badge["name"]
        badge_html += f'<div class="{cls}" title="{desc}">{icon} {name}</div>'
    badge_html += '</div>'
    st.markdown(badge_html, unsafe_allow_html=True)

    st.divider()

    # Vocab
    sc_data = SCENARIOS.get(selected_scenario_name, {})
    if sc_data.get("vocab"):
        st.markdown('<div class="vocab-section-title">💬 Fraze Cheie</div>', unsafe_allow_html=True)
        for phrase in sc_data["vocab"]:
            st.markdown(f'<div class="vocab-chip">{phrase}</div>', unsafe_allow_html=True)

    st.divider()

    st.download_button(
        "💾 Descarcă Sesiunea",
        data=get_transcript(),
        file_name="cruise_training.md",
        mime="text/markdown",
        use_container_width=True
    )

    st.markdown("""
    <div style="text-align:center;margin-top:16px;font-size:0.7em;color:#1a3a5c;line-height:1.8">
        🚢 Cruise Trainer v3.0<br>Made with ❤️ for Anamaria
    </div>
    """, unsafe_allow_html=True)

# --- SCENARIO CHANGE LOGIC ---
if st.session_state.last_scenario != selected_scenario_name:
    st.session_state.messages = []
    st.session_state.chat_session = None
    st.session_state.last_processed_audio = None
    st.session_state.streak = 0
    st.session_state.last_scenario = selected_scenario_name
    st.session_state.scenarios_tried.add(selected_scenario_name)
    if len(st.session_state.scenarios_tried) >= len(SCENARIOS):
        award_badge("all_scenarios")
    st.rerun()

st.session_state.scenarios_tried.add(selected_scenario_name)

# --- INIT CHAT ---
if st.session_state.chat_session is None:
    sc = SCENARIOS[selected_scenario_name]
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=sc["prompt"])
    st.session_state.chat_session = model.start_chat(history=[])
    try:
        initial = st.session_state.chat_session.send_message("Start the roleplay with your opening line. Be engaging and fun.")
        st.session_state.messages.append({"role": "assistant", "content": initial.text})
    except Exception as e:
        st.session_state.chat_session = None
        if "429" in str(e) or "quota" in str(e).lower():
            st.warning("⏳ Ai atins limita de trafic a API-ului Google (Rate Limit / Quota). Te rog așteaptă câteva momente și apasă butonul RESET.")
        else:
            st.error(f"Eroare la inițializarea sesiunii: {e}")
        st.stop()

# --- NEW BADGE POPUP ---
if st.session_state.new_badge:
    badge = BADGES[st.session_state.new_badge]
    st.markdown(f"""
    <div class="badge-popup">
        <div style="font-size:2rem">{badge['icon']}</div>
        <div style="font-family:'Orbitron',monospace;color:#ffd700;font-size:0.9rem;font-weight:700;margin:4px 0">ACHIEVEMENT UNLOCKED!</div>
        <div style="color:#fff;font-weight:600">{badge['name']}</div>
        <div style="color:#a0a0a0;font-size:0.8em">{badge['desc']}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.new_badge = None

# --- SCENARIO BADGE ---
sc_info = SCENARIOS[selected_scenario_name]
st.markdown(f"""
<div class="scenario-active">
    {sc_info['icon']} {selected_scenario_name}
    &nbsp;·&nbsp; Difficulty: {sc_info['difficulty']}
</div>
""", unsafe_allow_html=True)

# --- MESSAGES ---
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            has_feedback = "**🔍 Feedback:**" in content

            if has_feedback:
                char_map = {
                    "🛍️ Shop – Duty Free":      f"**🛍️ James:**",
                    "🍽️ Waiter – Dining Room":  f"**🍽️ Marco:**",
                    "🍹 Bartender – Pool Bar":   f"**🍹 Jake:**",
                    "🛎️ Guest Services":         f"**🛎️ Patricia:**",
                    "🎯 HR Interview":           f"**👔 Richard:**",
                }
                marker = char_map.get(selected_scenario_name, "")
                split_point = content.find(marker) if marker else -1

                # Extract stars for display
                stars_display = ""
                if "★★★" in content:
                    stars_display = '<div class="stars-earned">★★★ Perfect!</div>'
                elif "★★☆" in content:
                    stars_display = '<div class="stars-earned">★★☆ Good job!</div>'
                elif "★☆☆" in content:
                    stars_display = '<div class="stars-earned">★☆☆ Keep going!</div>'

                if split_point > 0:
                    feedback_part = content[:split_point].strip()
                    roleplay_part = content[split_point:].strip()
                    st.markdown(f'<div class="feedback-box">{feedback_part}{stars_display}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="roleplay-box">{roleplay_part}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(content)
            else:
                st.markdown(content)

# --- INPUT ---
footer = st.container()
with footer:
    audio_val = st.audio_input("🎤 Vorbește")
    text_val = st.chat_input("Scrie în Engleză...")

    user_message = None
    is_audio = False
    should_process = False

    if audio_val and st.session_state.last_processed_audio != audio_val.file_id:
        user_message = audio_val
        is_audio = True
        should_process = True
        st.session_state.last_processed_audio = audio_val.file_id
    elif text_val:
        user_message = text_val
        should_process = True

    if should_process and user_message:
        with chat_container:
            with st.chat_message("user"):
                if is_audio: st.audio(user_message)
                else: st.markdown(user_message)

        content_to_save = "🎤 *Audio Message*" if is_audio else user_message
        st.session_state.messages.append({"role": "user", "content": content_to_save})

        # Badges
        if not "first_message" in st.session_state.badges:
            award_badge("first_message")
        if is_audio and "audio_used" not in st.session_state.badges:
            award_badge("audio_used")
        turns_now = count_turns()
        if turns_now >= 5  and "5_turns"  not in st.session_state.badges: award_badge("5_turns")
        if turns_now >= 10 and "10_turns" not in st.session_state.badges: award_badge("10_turns")

        char_map2 = {
            "🛍️ Shop – Duty Free":     "**🛍️ James:**",
            "🍽️ Waiter – Dining Room": "**🍽️ Marco:**",
            "🍹 Bartender – Pool Bar":  "**🍹 Jake:**",
            "🛎️ Guest Services":        "**🛎️ Patricia:**",
            "🎯 HR Interview":          "**👔 Richard:**",
        }
        char_tag = char_map2.get(selected_scenario_name, "**[Character]:**")
        reminder = f" (ALWAYS start with **🔍 Feedback:** block with stars rating ★★★/★★☆/★☆☆, then {char_tag} for roleplay)"

        try:
            with st.spinner("⚡ Procesează..."):
                if is_audio:
                    blob = {"mime_type": user_message.type, "data": user_message.getvalue()}
                    response = st.session_state.chat_session.send_message(["Analyze English quality of this audio.", blob, reminder])
                else:
                    response = st.session_state.chat_session.send_message(user_message + reminder)

            resp_text = response.text
            st.session_state.messages.append({"role": "assistant", "content": resp_text})

            # XP & streak logic
            stars = count_stars_in_response(resp_text)
            st.session_state.total_stars += stars

            xp_earned = XP_REWARDS["message_sent"]
            reason = "mesaj trimis"

            if stars == 3:
                xp_earned += XP_REWARDS["no_mistake"]
                reason = "răspuns perfect ★★★"
                st.session_state.streak += 1
                if st.session_state.streak == 3:
                    xp_earned += XP_REWARDS["streak_3"]
                    reason += " + streak x3!"
                    award_badge("no_mistakes")
                if st.session_state.streak == 5:
                    xp_earned += XP_REWARDS["streak_5"]
                    reason += " + streak x5! 🔥"
            else:
                st.session_state.streak = 0

            if is_audio:
                xp_earned += XP_REWARDS["audio_bonus"]
                reason += " + bonus audio 🎤"

            award_xp(xp_earned, reason)
            st.rerun()

        except Exception as e:
            # Revert UI messages
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
                
            # Revert Gemini session history to avoid "400 Please ensure that the dialogue role alternates"
            try:
                if st.session_state.chat_session.history and getattr(st.session_state.chat_session.history[-1], "role", "") == "user":
                    st.session_state.chat_session.history.pop()
            except Exception:
                pass
                
            # Revert audio processing state
            if is_audio:
                st.session_state.last_processed_audio = None

            if "429" in str(e) or "quota" in str(e).lower():
                st.warning("⏳ Ai atins limita de mesaje (prea multe solicitări simultane). Te rog așteaptă câteva momente și trimite mesajul din nou!")
            else:
                st.error(f"Eroare la procesare: {e}")