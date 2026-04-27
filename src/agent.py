import os
import datetime
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
    {"name": "🧹 Rookie Crew",       "min_xp": 0,    "color": "#7f8c8d", "unlock_msg": "🚀 Bine ai venit la bord! Fiecare expert a început ca rookie."},
    {"name": "⚓ Junior Staff",       "min_xp": 50,   "color": "#3498db", "unlock_msg": "🌊 Eşti Junior Staff — începem să te cunoască pasagerii!"},
    {"name": "🍽️ Trained Steward",   "min_xp": 150,  "color": "#2ecc71", "unlock_msg": "🏖️ Eşti Trained Steward — pasagerii au încredere în tine!"},
    {"name": "🎖️ Senior Officer",    "min_xp": 350,  "color": "#f39c12", "unlock_msg": "🏆 Senior Officer! Engleza ta este impresionantă!"},
    {"name": "👑 Captain's Elite",   "min_xp": 700,  "color": "#e74c3c", "unlock_msg": "👑 Captain's Elite! Ai atins perfecțiunea pe vas!"},
]

BADGES = {
    "first_message":    {"icon": "🎤", "name": "First Words",        "desc": "Primul mesaj trimis"},
    "no_mistakes":      {"icon": "⭐", "name": "Flawless Round",     "desc": "Un răspuns fără greșeli"},
    "5_turns":          {"icon": "🔥", "name": "On Fire",            "desc": "5 ture consecutive"},
    "10_turns":         {"icon": "🚀", "name": "Cruise Veteran",     "desc": "10 ture completate"},
    "audio_used":       {"icon": "🎙️", "name": "Voice Activated",   "desc": "Ai folosit vocea"},
    "report_done":      {"icon": "📊", "name": "Self-Aware",         "desc": "Ai generat un raport"},
    "all_scenarios":    {"icon": "🌊", "name": "Full Crew",          "desc": "Ai încercat toate scenariile"},
    "vocab_master":     {"icon": "🏆", "name": "Vocab Master",       "desc": "Toate frazele stăpânite într-un scenariu"},
    # --- DAILY STREAK BADGE ---
    "streak_week":      {"icon": "📅", "name": "Full Week",          "desc": "7 zile consecutive de practică"},
}

XP_REWARDS = {
    "message_sent":   10,
    "no_mistake":     25,
    "audio_bonus":    15,
    "streak_3":       20,
    "streak_5":       40,
}

# Numărul maxim de vieți per sesiune (sistem Duolingo-style)
MAX_HEARTS = 5

# ===== QUICK PRACTICE EXERCISES =====
# Format per exercițiu: {"q": str, "options": [str x4], "correct": int (0-based index)}
QP_EXERCISES = {
    "🛍️ Shop – Duty Free": [
        {
            "q": "Un pasager întřeabă de un parfum cadou pentru soție. Ce spui?",
            "options": [
                "May I help you find something special for her?",
                "What you want for wife?",
                "We sell parfume here.",
                "I don't know, look yourself."
            ],
            "correct": 0
        },
        {
            "q": "Vrei să anunți că aveți o ofertă specială la ciocolată.",
            "options": [
                "Chocolate is cheap today!",
                "We have a special offer on our premium Belgian chocolates today.",
                "Buy chocolate, it good price.",
                "Chocolate discount, you want?"
            ],
            "correct": 1
        },
        {
            "q": "Un client vrea să încerce un eśantion de parfum. Cum răspunzi?",
            "options": [
                "No sample available, sorry.",
                "You can try but be careful.",
                "Would you like to try a sample? Let me spray it on a test strip for you.",
                "Sample is over there, go check."
            ],
            "correct": 2
        },
        {
            "q": "Clientul plăteşte şi vrei să oferi ambalaj cadou.",
            "options": [
                "Shall I gift-wrap that for you? It would make a lovely presentation.",
                "Want box for this?",
                "I put in bag, no problem.",
                "We have paper, you do yourself."
            ],
            "correct": 0
        },
        {
            "q": "Un pasager întreabă care e limita duty-free. Ce spui?",
            "options": [
                "I don't know the rules.",
                "Too much is not allowed, ask captain.",
                "Buy whatever you like, no problem.",
                "The duty-free allowance depends on your destination port — I can check that for you."
            ],
            "correct": 3
        },
    ],
    "🍽️ Waiter – Dining Room": [
        {
            "q": "Un cuplu tocmai a sosit la masă. Cum îtâmpini?",
            "options": [
                "Hey, sit down please.",
                "Good evening! Welcome to the Main Dining Room. May I show you to your table?",
                "Table is ready, go sit.",
                "You have reservation?"
            ],
            "correct": 1
        },
        {
            "q": "Vrei să iei comanda băuturii.",
            "options": [
                "You want drink?",
                "Can I get drinks for you?",
                "May I take your drinks order, or would you care to start with some still or sparkling water?",
                "Water or juice, which one?"
            ],
            "correct": 2
        },
        {
            "q": "Un oaspete cere friptura ‘medium’. Confirmi comanda.",
            "options": [
                "OK, medium, I write it.",
                "So that’s the sirloin cooked medium — a wonderful choice. I’ll have that right out.",
                "Medium is not too cooked, right?",
                "Medium means pink inside, you sure?"
            ],
            "correct": 1
        },
        {
            "q": "Un oaspete e nemulțumit de mâncare. Ce spui?",
            "options": [
                "I sincerely apologize. Allow me to inform the chef and arrange an alternative right away.",
                "Sorry, chef make mistake today.",
                "Is not my fault, talk to manager.",
                "You should have ordered something else."
            ],
            "correct": 0
        },
        {
            "q": "Vrei să întrebi despre alergeni înainte de comandă.",
            "options": [
                "You allergic to something?",
                "Before I take your order, do you have any dietary requirements or allergies I should be aware of?",
                "Our food has no allergens.",
                "Allergies are on the menu, check please."
            ],
            "correct": 1
        },
    ],
    "🍹 Bartender – Pool Bar": [
        {
            "q": "Un client vine la bar. Cum îl salută Jake?",
            "options": [
                "What do you need?",
                "Hey there! Welcome to the pool bar — what can I get for you today?",
                "Bar is open, order now.",
                "You want cocktail or beer?"
            ],
            "correct": 1
        },
        {
            "q": "Un client vrea whisky fără gheață. Cum confirmi?",
            "options": [
                "No ice whisky, coming!",
                "Whisky without cold things, ok.",
                "One whisky neat — coming right up!",
                "Sure, I remove the ice for you."
            ],
            "correct": 2
        },
        {
            "q": "Clientul vrea să deschidă un tab. Cum răspunzi?",
            "options": [
                "Sure! Can I take your cabin number to start a tab for you?",
                "Tab? What is tab?",
                "You pay now or later?",
                "Leave card here, I charge later."
            ],
            "correct": 0
        },
        {
            "q": "Vrei să prezinți cocktailul zilei.",
            "options": [
                "Today we have special drink, is good.",
                "Our special today is the Mango Sunset — it’s a blend of rum, fresh mango and lime. Want to try one?",
                "We make cocktail, you want?",
                "Cocktail today is tropical, order it."
            ],
            "correct": 1
        },
        {
            "q": "Un client termină băutura. Ce spui?",
            "options": [
                "Another one?",
                "Would you like another round, or can I get you anything else?",
                "You finish, want more?",
                "Same again or different?"
            ],
            "correct": 1
        },
    ],
    "🛎️ Guest Services": [
        {
            "q": "Un pasager nervos se apropie de birou. Cum îl întâmpini?",
            "options": [
                "What is the problem?",
                "Good morning, I can see you have a concern — I’m here to help. How may I assist you?",
                "Calm down please, what you want?",
                "Wait, I call my colleague."
            ],
            "correct": 1
        },
        {
            "q": "Pasagerul plânge că a pierdut un obiect. Ce spui?",
            "options": [
                "Lost & Found is in deck 2, go there.",
                "Oh no! I completely understand your concern. Let me check our Lost & Found log right away.",
                "Sorry, we can’t help with this.",
                "You should be more careful next time."
            ],
            "correct": 1
        },
        {
            "q": "Un client întreabă despre excursia de mâine la port.",
            "options": [
                "Excursion is at 8, take bus.",
                "The shore excursion departs from Deck 4 at 08:00. Shall I print your tickets?",
                "Ask tour operator, not me.",
                "Tomorrow morning, early, go to boat."
            ],
            "correct": 1
        },
        {
            "q": "Pasagerul reclamă că aerul condiționat din cabină nu funcționează.",
            "options": [
                "I’m afraid I’m unable to fix it myself, but I’ll dispatch our maintenance team to your cabin immediately.",
                "AC broken? Call reception.",
                "Open window, is better.",
                "Not my department, call housekeeping."
            ],
            "correct": 0
        },
        {
            "q": "Trebuie să transmiți o veste proastă cu empatie.",
            "options": [
                "Bad news: excursion cancelled.",
                "Unfortunately the excursion has been cancelled.",
                "I’m afraid I have some disappointing news — the excursion has been cancelled due to weather. I sincerely apologize for the inconvenience.",
                "Sorry, nothing I can do about weather."
            ],
            "correct": 2
        },
    ],
    "🎯 HR Interview": [
        {
            "q": "Richard te roagă să te prezinți. Ce răspunzi?",
            "options": [
                "I am Anamaria, I want to work on ship.",
                "My name is Anamaria. I have three years of hospitality experience and I’m passionate about delivering outstanding guest experiences.",
                "Hello, I come from Romania and I need this job.",
                "I am good worker, very hard working."
            ],
            "correct": 1
        },
        {
            "q": "Esti întrebată despre punctele tale forte.",
            "options": [
                "I am fast and I smile always.",
                "I believe my key strengths are adaptability, strong communication skills and the ability to remain calm under pressure.",
                "I have no weaknesses, only strengths.",
                "I work hard and learn quick."
            ],
            "correct": 1
        },
        {
            "q": "Cum răspunzi la “Tell me about a difficult customer situation”?",
            "options": [
                "Once a customer was very bad and I called my manager.",
                "In my previous role, a guest complained about a long wait. I acknowledged their frustration, offered a complimentary drink, and personally ensured their order was prioritized.",
                "I never had difficult customers, I am very good.",
                "Difficult customers are always wrong, I think."
            ],
            "correct": 1
        },
        {
            "q": "Richard întreabă de ce vrei să lucrezi pe vas.",
            "options": [
                "Because I want to travel and earn money.",
                "I am eager to grow with the company and believe the cruise environment will allow me to develop both professionally and personally while exceeding guest expectations.",
                "Ship is good for career I think.",
                "My friend works on ship and she say is good."
            ],
            "correct": 1
        },
        {
            "q": "Cum închei interviul profesionist?",
            "options": [
                "OK, bye, I wait your call.",
                "Thank you so much, I hope to hear back soon.",
                "Thank you for this opportunity, Mr. Richard. I’m genuinely excited about this role and confident I can make a valuable contribution to your team.",
                "I think interview go well, you should hire me."
            ],
            "correct": 2
        },
    ],
}

SCENARIOS = {
    "🛍️ Shop – Duty Free": {
        "icon": "🛍️",
        "char": "James",
        "char_emoji": "🧑‍💼",
        "avatar": "🧑‍💼",
        "role": "Senior Shop Assistant · Deck 5 Boutique",
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
        "vocab_cards": [
            {"phrase": "May I help you find something?",      "phonetic": "/meɪ aɪ help juː faɪnd ˈsʌmθɪŋ/",         "context": "La abordarea unui client",                       "example": "\"May I help you find something for your wife?\""},
            {"phrase": "This is one of our best sellers.",    "phonetic": "/ðɪs ɪz wʌn əv aʊər best ˈselərz/",          "context": "La recomandarea unui produs popular",            "example": "\"This perfume is one of our best sellers this season.\""},
            {"phrase": "Would you like to try a sample?",     "phonetic": "/wʊd juː laɪk tuː traɪ ə ˈsæmpəl/",           "context": "La oferirea unui eşantion",                         "example": "\"Would you like to try a sample of this cologne?\""},
            {"phrase": "I can gift-wrap that for you.",       "phonetic": "/aɪ kæn ˈɡɪft ræp ðæt fər juː/",            "context": "La finalizarea vânzării",                           "example": "\"Shall I gift-wrap that? It makes a lovely present.\""},
            {"phrase": "Duty-free allowance",                 "phonetic": "/ˈdjuːti friː əˈlaʊəns/",                   "context": "La explicarea regulilor vamale",                   "example": "\"The duty-free allowance for spirits is one litre.\""},
            {"phrase": "We have a special offer on...",       "phonetic": "/wiː hæv ə ˈspeʃəl ˈɔfər ɔn/",              "context": "La promovarea unei oferte",                         "example": "\"We have a special offer on Belgian chocolates today.\""},
        ],
        "vocab": ["May I help you find something?", "This is one of our best sellers.", "Would you like to try a sample?", "I can gift-wrap that for you.", "Duty-free allowance", "We have a special offer on..."]
    },
    "🍽️ Waiter – Dining Room": {
        "icon": "🍽️",
        "char": "Marco",
        "char_emoji": "👨‍🍳",
        "avatar": "👨‍🍳",
        "role": "Head Waiter · Main Dining Room",
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
        "vocab_cards": [
            {"phrase": "May I take your order?",              "phonetic": "/meɪ aɪ teɪk jʊər ˈɔːrdər/",              "context": "La preluarea comenzii",                             "example": "\"Good evening. May I take your order now?\""},
            {"phrase": "Would you care for...?",              "phonetic": "/wʊd juː keər fər/",                       "context": "La oferirea politicoasă a ceva",                    "example": "\"Would you care for some sparkling water to start?\""},
            {"phrase": "The chef recommends...",              "phonetic": "/ðə ʃef ˌrekəˈmendz/",                    "context": "La prezentarea specialității zilei",               "example": "\"The chef recommends the sea bass this evening.\""},
            {"phrase": "I do apologize for the inconvenience.","phonetic": "/aɪ duː əˈpɔlədʒaɪz fər ði ɪnˈkɔnvɪˈniːəns/","context": "La gestionarea unei plângeri",                       "example": "\"I do apologize for the inconvenience — allow me to replace that.\""},
            {"phrase": "Rare / medium / well-done",           "phonetic": "/reər ˈmiːdiəm wel dʌn/",                "context": "La preluarea comenzii de carne",                    "example": "\"How would you like your steak — rare, medium or well-done?\""},
            {"phrase": "Allergens / dietary requirements",    "phonetic": "/ˈælərdʒənz ˈdaɪətəri rɪˈkwaɪərmənts/",      "context": "La începerea servirii",                              "example": "\"Do you have any allergens or dietary requirements I should know of?\""},
        ],
        "vocab": ["May I take your order?", "Would you care for...?", "The chef recommends...", "I do apologize for the inconvenience.", "Rare / medium / well-done", "Allergens / dietary requirements"]
    },
    "🍹 Bartender – Pool Bar": {
        "icon": "🍹",
        "char": "Jake",
        "char_emoji": "🧑‍🍳",
        "avatar": "🍹",
        "role": "Head Bartender · Lido Pool Bar",
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
        "vocab_cards": [
            {"phrase": "Coming right up!",                    "phonetic": "/ˈkʌmɪŋ raɪt ʌp/",                      "context": "La confirmarea comenzii",                           "example": "\"One mojito — coming right up!\""},
            {"phrase": "What can I get for you?",             "phonetic": "/wɔt kæn aɪ ɡet fər juː/",               "context": "La întâmpinarea clientului",                        "example": "\"Hey there! What can I get for you today?\""},
            {"phrase": "On the rocks / straight up / neat",   "phonetic": "/ɔn ðə rɔks / streɪt ʌp / niːt/",        "context": "La preluarea comenzii de băutură spirtoase",       "example": "\"Would you like that on the rocks or neat?\""},
            {"phrase": "Would you like to start a tab?",      "phonetic": "/wʊd juː laɪk tuː stɑːrt ə tæb/",           "context": "La începerea evidenței băuturilor",                  "example": "\"Can I take your cabin number to start a tab?\""},
            {"phrase": "Our special today is...",             "phonetic": "/aʊər ˈspeʃəl təˈdeɪ ɪz/",                "context": "La prezentarea cocktailului zilei",                 "example": "\"Our special today is the Mango Sunset — rum, mango and lime.\""},
            {"phrase": "Cheers! / Enjoy!",                    "phonetic": "/tʃɪərz / ɪndʒɔɪ/",                      "context": "La servirea băuturii",                              "example": "\"Here you go — cheers! Enjoy!\""},
        ],
        "vocab": ["Coming right up!", "What can I get for you?", "On the rocks / straight up / neat", "Would you like to start a tab?", "Our special today is...", "Cheers! / Enjoy!"]
    },
    "🛎️ Guest Services": {
        "icon": "🛎️",
        "char": "Patricia",
        "char_emoji": "👩‍💼",
        "avatar": "👩‍💼",
        "role": "Senior Guest Services Officer · Information Desk",
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
        "vocab_cards": [
            {"phrase": "I completely understand your concern.","phonetic": "/aɪ kəmˈpliːtli ʌnˈdærstænd jʊər kənˈsɜːrn/","context": "La prima reacție la o plângere",                    "example": "\"I completely understand your concern — I will resolve this immediately.\""},
            {"phrase": "Allow me to look into that for you.", "phonetic": "/əˈlaʊ miː tuː lʊk ˈɪntuː ðæt fər juː/",  "context": "La investigarea unei solicitări",                   "example": "\"Please wait a moment — allow me to look into that for you.\""},
            {"phrase": "I sincerely apologize for the inconvenience.","phonetic": "/aɪ sɪnˈsɪərli əˈpɔlədʒaɪz/",          "context": "La recunoaşterea unei erori",                       "example": "\"I sincerely apologize for the inconvenience — we will make it right.\""},
            {"phrase": "I'm afraid...",                       "phonetic": "/aɪm əˈfreɪd/",                           "context": "La transmiterea unei veśti proaste diplomatic",     "example": "\"I'm afraid the excursion has been cancelled due to weather.\""},
            {"phrase": "Shore excursion / tender port",       "phonetic": "/ʃɔːr ɪkˈskɜːrʒən ˈtendər pɔːrt/",        "context": "La informarea pasagerilor despre port",              "example": "\"Your shore excursion departs from Deck 4 at 08:00.\""},
            {"phrase": "Embarkation / disembarkation",        "phonetic": "/ɮmbɑːrˈkeɪʃən dɪsɮmbɑːrˈkeɪʃən/",      "context": "La explicarea procesului de urcare/cobarâre",       "example": "\"Disembarkation begins at 07:00 on the last day of the cruise.\""},
        ],
        "vocab": ["I completely understand your concern.", "Allow me to look into that for you.", "I sincerely apologize for the inconvenience.", "I'm afraid...", "Shore excursion / tender port", "Embarkation / disembarkation"]
    },
    "🎯 HR Interview": {
        "icon": "🎯",
        "char": "Richard",
        "char_emoji": "👔",
        "avatar": "👔",
        "role": "Recruitment Officer · Cruise Line HR",
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
        "vocab_cards": [
            {"phrase": "I believe my strengths are...",       "phonetic": "/aɪ bɪˈliːv maɪ streŋks ɑːr/",            "context": "La răspunsul la 'What are your strengths?'",        "example": "\"I believe my strengths are adaptability, communication and attention to detail.\""},
            {"phrase": "In my previous experience...",        "phonetic": "/ɪn maɪ ˈpriːviəs ɪkˈspɪəriəns/",           "context": "La descrierea experienței anterioare",              "example": "\"In my previous experience at a hotel, I handled guest complaints daily.\""},
            {"phrase": "I thrive under pressure.",            "phonetic": "/aɪ ξraɪv ˈʌndər ˈpreʃər/",               "context": "La demonstrarea rezistenței la stres",               "example": "\"I thrive under pressure — in fact, I perform best when it's busy.\""},
            {"phrase": "I'm a quick learner.",                "phonetic": "/aɪm ə kwɪk ˈlɜːrnər/",                   "context": "La accentuarea capacității de adaptare",              "example": "\"I'm a quick learner — I pick up new procedures very fast.\""},
            {"phrase": "Customer satisfaction is my priority.","phonetic": "/ˈkʌstəmər sætɪsˈfækʃən ɪz maɪ praɪˈɔrɪti/","context": "La declararea valorilor profesionale",               "example": "\"Above all, customer satisfaction is my priority in every interaction.\""},
            {"phrase": "I'm eager to grow with the company.", "phonetic": "/aɪm ˈiːɡər tuː ɡrəʊ wɪð ðə ˈkʌmpəni/",    "context": "La încheierea interviului",                           "example": "\"I'm eager to grow with the company and contribute to your team's success.\""},
        ],
        "vocab": ["I believe my strengths are...", "In my previous experience...", "I thrive under pressure.", "I'm a quick learner.", "Customer satisfaction is my priority.", "I'm eager to grow with the company."]
    },
}

# --- STARTER PHRASES (empty state chips) ---
STARTER_PHRASES_MAP = {
    "🛍️ Shop – Duty Free":      ["I can help you with that!", "Let me show you our latest arrivals.", "This is one of our bestsellers."],
    "🍽️ Waiter – Dining Room":  ["Good evening!", "May I take your order?", "I’ll be right with you."],
    "🍹 Bartender – Pool Bar":         ["What can I get for you?", "Coming right up!", "Would you like to start a tab?"],
    "🛎️ Guest Services":              ["How may I assist you?", "I completely understand your concern.", "Allow me to look into that."],
    "🎯 HR Interview":                      ["I believe my strengths are…", "In my previous experience…", "I’m eager to grow with the company."],
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
    xp_before = st.session_state.xp
    st.session_state.xp += amount
    st.session_state.xp_log.append(f"+{amount} XP — {reason}")
    if len(st.session_state.xp_log) > 5:
        st.session_state.xp_log.pop(0)
    # Store last XP gain for floating popup
    st.session_state.xp_last_gain = amount
    # Detect level-up
    lvl_before = get_level(xp_before)
    lvl_after  = get_level(st.session_state.xp)
    if lvl_after["name"] != lvl_before["name"] and not st.session_state.get("level_up_shown"):
        st.session_state.level_up_pending = lvl_after

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

# --- FUNCȚIE DAILY STREAK ---
def update_daily_streak():
    """
    Apelată după fiecare turn reușit.
    - Numără turns din ziua curentă (today_turns).
    - Când today_turns atinge 3, marchează ziua ca activă
      și actualizează daily_streak.
    - Dacă userul a sărit o zi, resetează streak-ul.
    """
    today = datetime.date.today()
    today_iso = today.isoformat()

    # Incrementează contorul de turns al zilei de azi
    # (reset la 0 în STATE INIT; rămâne în memorie pe durata sesiunii)
    st.session_state.today_turns += 1

    # Nu facem nimic până la pragul de 3 turns—zi activă
    if st.session_state.today_turns < 3:
        return
    if st.session_state.today_turns > 3:
        # Deja marcată azi; nu recalculăm streakul din nou
        return

    # Azi e activă pentru prima oară în această sesiune
    last = st.session_state.last_active_date  # datetime.date | None

    if last is None:
        # Prima zi de practică
        st.session_state.daily_streak = 1
    elif today == last:
        # Același user a relansat pagina în aceeași zi — streak rămâne
        pass
    elif (today - last).days == 1:
        # Ziua următoare consecutivă → streak crește
        st.session_state.daily_streak += 1
    else:
        # A sărit cel puțin o zi → reset
        st.session_state.daily_streak = 1

    st.session_state.last_active_date = today

    # Adaugă ziua în lista de zile active (fără duplicate)
    if today_iso not in st.session_state.active_days:
        st.session_state.active_days.append(today_iso)
        # Păstrăm doar ultimele 30 de zile pentru a nu acumula prea mult
        st.session_state.active_days = st.session_state.active_days[-30:]

    # Badge streak 7 zile consecutive
    if st.session_state.daily_streak >= 7:
        award_badge("streak_week")


# --- AUDIO FEEDBACK (Web Audio API via st.components) ---
import streamlit.components.v1 as _st_components

def get_translation(msg_idx: int, text: str) -> str:
    """Calls Gemini to translate AI message to Romanian. Caches result."""
    if msg_idx in st.session_state.translations:
        return st.session_state.translations[msg_idx]
    try:
        _tm = genai.GenerativeModel(model_name=MODEL_NAME)
        _prompt = (
            "Translatează în română. Păstrează frazele în engleză între ghilimele. "
            "Returnează DOAR traducerea, fără introducere:\n\n" + text
        )
        _resp = _tm.generate_content(_prompt)
        _ro = _resp.text.strip()
        st.session_state.translations[msg_idx] = _ro
        return _ro
    except Exception as _e:
        return f"[Eroare traducere: {_e}]"

def _highlight_en_phrases(ro_text: str) -> str:
    """Wrap text in double quotes with cyan span for English phrases."""
    import html as _h
    t = _h.escape(ro_text)
    # Highlight content inside "..." or '...'
    t = re.sub(r'&quot;(.+?)&quot;', r'<span class="en-phrase">"\1"</span>', t)
    t = re.sub(r"&#x27;(.+?)&#x27;", r"<span class='en-phrase'>'\1'</span>", t)

    t = t.replace("\n", "<br>")
    return t


def play_sound(sound_type: str):
    """
    Injectează un oscilator Web Audio API prin st.components.v1.html().
    sound_type: 'ding' | 'buzz' | 'fanfare' | 'thud'
    Apelează doar dacă st.session_state.sound_on == True.
    """
    if not st.session_state.get("sound_on", True):
        return

    # Construiesc script-ul JS pentru fiecare tip de sunet
    if sound_type == "ding":
        # 880 Hz, 0.3s — sunet pozitiv ★★★
        js = """
        (function(){
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            gain.gain.setValueAtTime(0.35, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.3);
        })();
        """
    elif sound_type == "buzz":
        # 220 Hz, 0.2s — sunet negativ ★☆☆
        js = """
        (function(){
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(220, ctx.currentTime);
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.2);
        })();
        """
    elif sound_type == "fanfare":
        # 3 note ascendente: 523, 659, 784 Hz — badge nou
        js = """
        (function(){
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var notes = [523, 659, 784];
            notes.forEach(function(freq, i) {
                var osc  = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'triangle';
                var t = ctx.currentTime + i * 0.14;
                osc.frequency.setValueAtTime(freq, t);
                gain.gain.setValueAtTime(0.0, t);
                gain.gain.linearRampToValueAtTime(0.3, t + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.14);
                osc.start(t);
                osc.stop(t + 0.14);
            });
        })();
        """
    elif sound_type == "thud":
        # 100 Hz, 0.4s — pierdere ❤️
        js = """
        (function(){
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc  = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(150, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(60, ctx.currentTime + 0.4);
            gain.gain.setValueAtTime(0.5, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.4);
        })();
        """
    else:
        return

    _st_components.html(
        f"<script>{js}</script>",
        height=0,
        scrolling=False
    )


# --- QUICK PRACTICE RENDER FUNCTION ---
def render_quick_practice(scenario_name):
    """Afișează modul Quick Practice (multiple-choice) pentru scenariul activ."""
    exercises = QP_EXERCISES.get(scenario_name, [])
    total = len(exercises)
    if total == 0:
        st.warning("Nu există exerciții pentru acest scenariu.")
        return

    idx = st.session_state.qp_index

    # ── ECRAN FINAL ──────────────────────────────────────────────
    if idx >= total:
        pct_score = int(st.session_state.qp_correct / total * 100)
        emoji = "🎉" if pct_score >= 80 else ("👍" if pct_score >= 60 else "💪")
        st.markdown(f"""
        <div class="qp-score-card">
            <div class="qp-score-title">{emoji} ROUND COMPLET!</div>
            <div class="qp-score-big">{pct_score}%</div>
            <div class="qp-score-sub">
                {st.session_state.qp_correct} / {total} răspunsuri corecte
            </div>
            <div class="qp-xp-earned">⚡ +{st.session_state.qp_xp} XP câştigat</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("💬 Înapoi la Chat", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()
        if st.button("🔄 Repetă exercițiile", use_container_width=True):
            st.session_state.qp_index   = 0
            st.session_state.qp_answered = None
            st.session_state.qp_chosen  = None
            st.session_state.qp_xp      = 0
            st.session_state.qp_correct  = 0
            st.rerun()
        return

    # ── PROGRESS BAR ─────────────────────────────────────────────
    prog_pct = int(idx / total * 100)
    st.markdown(f"""
    <div class="qp-container">
        <div class="qp-progress-wrap">
            <div class="qp-progress-fill" style="width:{prog_pct}%"></div>
        </div>
        <div class="qp-progress-label">Exercițiu {idx + 1} / {total}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── EXERCISE DATA ─────────────────────────────────────────────
    ex = exercises[idx]
    # Support both formats:
    #   old: {"options": [...], "correct": int_index}
    #   new: {"correct": str, "wrong": [str, str, str]}
    if "options" in ex:
        options   = ex["options"]
        correct_i = ex["correct"]                # int index
        correct_txt = options[correct_i]
    else:
        import random as _rnd
        correct_txt = ex["correct"]
        all_opts    = [correct_txt] + list(ex.get("wrong", []))
        rng = _rnd.Random(idx * 42)
        rng.shuffle(all_opts)
        options   = all_opts
        correct_i = options.index(correct_txt)

    # Read state — use None = unanswered  (avoids falsy-False bug)
    answered = st.session_state.get("qp_answered", None)
    chosen   = st.session_state.get("qp_chosen",   None)  # int index

    # ── QUESTION CARD (HTML — visual only) ───────────────────────
    import html as _he
    opts_html = ""
    for i, opt in enumerate(options):
        if answered is None:
            cls = "qp-option"
        elif i == correct_i:
            cls = "qp-option correct"
        elif i == chosen:
            cls = "qp-option wrong"
        else:
            cls = "qp-option"
        opts_html += f'<div class="{cls}">{chr(65+i)}. {_he.escape(opt)}</div>'

    st.markdown(f"""
    <div class="qp-card">
        <div class="qp-question">🤔 {_he.escape(ex["q"])}</div>
        <div class="qp-options">{opts_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── ACTIVE ANSWER BUTTONS ─────────────────────────────────────
    if answered is None:
        # Full-width buttons with letter + answer text — clearly clickable
        for i, opt in enumerate(options):
            if st.button(
                f"{chr(65+i)}. {opt}",
                key=f"qp_ans_{idx}_{i}",
                use_container_width=True,
            ):
                st.session_state.qp_chosen   = i
                st.session_state.qp_answered = (i == correct_i)   # True/False
                if i == correct_i:
                    award_xp(15, "Quick Practice ★")
                    st.session_state.qp_xp      += 15
                    st.session_state.qp_correct  += 1
                    play_sound("ding")
                else:
                    play_sound("buzz")
                    if st.session_state.hearts > 0:
                        st.session_state.hearts    -= 1
                        st.session_state.heart_pulse = True
                        play_sound("thud")
                st.rerun()   # ← CRUCIAL

    # ── FEEDBACK + NEXT ──────────────────────────────────────────
    else:
        is_correct = (chosen == correct_i)
        if is_correct:
            fb_cls  = "ok"
            fb_text = "🎉 🎉 🎉 Excelent! Răspuns corect! +15 XP"
        else:
            fb_text = f"❌ Greşit! Răspunsul corect era: <em>{_he.escape(options[correct_i])}</em>"
            fb_cls  = "err"
        st.markdown(f'<div class="qp-feedback {fb_cls}">{fb_text}</div>',
                    unsafe_allow_html=True)

        if st.session_state.hearts <= 0:
            st.markdown("""
            <div class="game-over-overlay">
                <div class="game-over-modal">
                    <div class="game-over-icon">💔</div>
                    <div class="game-over-title">GAME OVER</div>
                    <div class="game-over-sub">Ai rămas fără vieți!<br>Apasă <strong>RESET</strong> în sidebar.</div>
                    <div style="font-size:2.5rem;letter-spacing:8px">🖤🖤🖤🖤🖤</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return

        if st.button("Următorul exercițiu ➜", use_container_width=True, key="qp_next"):
            st.session_state.qp_index   += 1
            st.session_state.qp_answered = None   # reset to None, not False
            st.session_state.qp_chosen   = None
            st.rerun()




# --- FLASHCARD RENDER FUNCTION ---
def render_flashcards(scenario_name):
    """Afișează modul Flashcards pentru scenariul activ.
    REGULĂ: st.button() NICIODATĂ în st.components.v1.html() — funcționează
    DOAR dacă e randat direct în Streamlit (în afara iframe-urilor).
    """
    cards = SCENARIOS.get(scenario_name, {}).get("vocab_cards", [])
    if not cards:
        st.warning("Nu există flashcard-uri pentru acest scenariu.")
        return

    total = len(cards)

    # RESET la schimbare scenariu
    if st.session_state.fc_scenario != scenario_name:
        st.session_state.fc_scenario = scenario_name
        st.session_state.fc_known    = []
        st.session_state.fc_queue    = list(range(total))
        st.session_state.fc_current  = 0
        st.session_state.fc_flipped  = False

    queue   = st.session_state.fc_queue
    known_n = len(st.session_state.fc_known)

    # VICTORY SCREEN
    if not queue:
        award_badge("vocab_master")
        play_sound("fanfare")
        st.markdown(f"""
        <div class="fc-done-card">
            <div style="font-size:3rem;margin-bottom:10px">\U0001f3c6</div>
            <div style="font-family:'Orbitron',monospace;font-size:1.3rem;
                        font-weight:900;color:var(--green);letter-spacing:2px;
                        margin-bottom:8px">VOCAB MASTER!</div>
            <div style="font-size:0.95rem;color:var(--text);margin-bottom:20px">
                Ai stapanit <strong>{total}/{total}</strong> fraze din <em>{scenario_name}</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("\U0001f504 Reia de la capat", use_container_width=True, key="fc_restart"):
            st.session_state.fc_known    = []
            st.session_state.fc_queue    = list(range(total))
            st.session_state.fc_current  = 0
            st.session_state.fc_flipped  = False
            st.rerun()
        if st.button("\U0001f4ac Inapoi la Chat", use_container_width=True, key="fc_back"):
            st.session_state.app_mode = "chat"
            st.rerun()
        return

    # PROGRESS BAR
    pct = int(known_n / total * 100) if total > 0 else 0
    st.markdown(f"""
    <div class="fc-wrapper">
        <div class="fc-progress-row">
            <div class="fc-progress-bar-wrap">
                <div class="fc-progress-bar-fill" style="width:{pct}%"></div>
            </div>
            <div class="fc-progress-label">\U0001f4da {known_n}/{total} fraze stapanite</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CARD CURENT
    import html as _he
    cur_pos  = min(st.session_state.fc_current, len(queue) - 1)
    card_idx = queue[cur_pos]
    card     = cards[card_idx]
    flipped  = st.session_state.fc_flipped

    ctx      = _he.escape(str(card.get("context",  "")))
    phrase   = _he.escape(str(card.get("phrase",   "")))
    phonetic = _he.escape(str(card.get("phonetic", "")))
    example  = _he.escape(str(card.get("example",  "")))

    # FATA CARD — st.markdown (nu components.html)
    if not flipped:
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#080f20,#0d1a30);
            border:2px solid #1a3a5c;border-radius:20px;
            padding:48px 32px;text-align:center;min-height:280px;
            display:flex;flex-direction:column;justify-content:center;
            box-sizing:border-box;margin-bottom:12px;">
    <div style="color:#4a6a8a;font-size:0.68rem;text-transform:uppercase;
                letter-spacing:2px;margin-bottom:14px">\U0001f1f7\U0001f1f4 Contextul</div>
    <div style="color:#00f5ff;font-size:1rem;font-style:italic;
                margin-bottom:20px;line-height:1.5">{ctx}</div>
    <div style="color:#2a4a6a;font-size:0.78rem">
        Apasa &bdquo;Rastoarna&rdquo; pentru a vedea raspunsul</div>
</div>
        """, unsafe_allow_html=True)

        if st.button("\U0001f504 RASTOARNA CARDUL", use_container_width=True, key="fc_flip"):
            st.session_state.fc_flipped = True
            st.rerun()

    # SPATELE CARD
    else:
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#040e1a,#081422);
            border:2px solid #00f5ff;border-radius:20px;
            padding:32px;text-align:center;min-height:280px;
            display:flex;flex-direction:column;justify-content:center;
            box-sizing:border-box;margin-bottom:12px;
            box-shadow:0 0 30px rgba(0,245,255,0.08);">
    <div style="color:#4a6a8a;font-size:0.68rem;text-transform:uppercase;
                letter-spacing:2px;margin-bottom:12px">\U0001f1ec\U0001f1e7 Fraza in Engleza</div>
    <div style="color:#fff;font-size:1.3rem;font-weight:700;
                line-height:1.4;margin-bottom:8px">{phrase}</div>
    <div style="color:#ffd700;font-size:0.9rem;font-family:serif;
                letter-spacing:0.5px;margin-bottom:16px">{phonetic}</div>
    <div style="border-left:2px solid #00f5ff;padding-left:12px;
                text-align:left;color:#8ab4d8;font-size:0.82rem;
                font-style:italic;line-height:1.5">&quot;{example}&quot;</div>
    <div style="color:#2a4a6a;font-size:0.72rem;margin-top:20px">Ai stiut-o?</div>
</div>
        """, unsafe_allow_html=True)

        # BUTOANE — OBLIGATORIU în afara HTML
        b1, b2 = st.columns(2)
        with b1:
            if st.button("\U0001f914 Nu stiam", use_container_width=True, key="fc_no"):
                play_sound("buzz")
                queue.append(queue.pop(cur_pos))
                st.session_state.fc_queue   = queue
                st.session_state.fc_current = cur_pos % len(queue)
                st.session_state.fc_flipped = False
                st.rerun()
        with b2:
            if st.button("\u2705 Stiam!", use_container_width=True, key="fc_yes"):
                play_sound("ding")
                st.session_state.fc_known.append(card_idx)
                queue.pop(cur_pos)
                st.session_state.fc_queue   = queue
                st.session_state.fc_current = cur_pos % max(len(queue), 1)
                st.session_state.fc_flipped = False
                award_xp(10, "flashcard stăpânit")
                st.rerun()



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

/* ===== HEARTS SYSTEM ===== */
.hearts-row {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 8px 0;
}
.hearts-label {
    font-size: 0.65rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-right: 4px;
}
.heart-active {
    font-size: 1.35rem;
    filter: drop-shadow(0 0 6px rgba(255,71,87,0.8));
    display: inline-block;
}
.heart-lost {
    font-size: 1.35rem;
    filter: grayscale(1) brightness(0.4);
    display: inline-block;
}
/* Pulse animation when a heart is lost */
@keyframes heartPulse {
    0%   { transform: scale(1); }
    25%  { transform: scale(1.5); filter: drop-shadow(0 0 12px rgba(255,71,87,1)); }
    50%  { transform: scale(0.85); }
    75%  { transform: scale(1.2); }
    100% { transform: scale(1); }
}
.heart-pulse {
    animation: heartPulse 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* ===== GAME OVER MODAL ===== */
.game-over-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(5, 10, 24, 0.92);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    backdrop-filter: blur(8px);
}
.game-over-modal {
    background: linear-gradient(135deg, #1a0608, #2a0010);
    border: 2px solid var(--red);
    border-radius: 20px;
    padding: 40px 48px;
    text-align: center;
    box-shadow: 0 0 60px rgba(255,71,87,0.4), inset 0 0 40px rgba(255,71,87,0.05);
    animation: popIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    max-width: 420px;
    width: 90%;
}
.game-over-icon  { font-size: 4rem; margin-bottom: 12px; }
.game-over-title {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.3rem !important;
    font-weight: 900 !important;
    color: var(--red) !important;
    text-shadow: 0 0 20px rgba(255,71,87,0.6) !important;
    letter-spacing: 2px !important;
    margin-bottom: 8px;
}
.game-over-sub {
    color: var(--text);
    font-size: 0.9rem;
    margin-bottom: 24px;
    line-height: 1.6;
}

/* ===== DAILY STREAK CALENDAR ===== */
.cal-section {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0;
}
.cal-title {
    font-size: 0.65rem;
    color: var(--gold);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.cal-row {
    display: flex;
    justify-content: space-between;
    gap: 2px;
    margin-bottom: 6px;
}
.cal-cell {
    flex: 1;
    text-align: center;
}
.cal-dot  { font-size: 1.05rem; line-height: 1; }
.cal-lbl  { font-size: 0.55rem; color: var(--text-dim); margin-top: 2px; }
.cal-streak {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-align: center;
    border-top: 1px solid var(--border);
    padding-top: 6px;
    margin-top: 4px;
}
.cal-streak strong { color: var(--cyan); }

/* ===== QUICK PRACTICE ===== */
.qp-container {
    max-width: 720px;
    margin: 0 auto;
    padding: 10px 0 40px;
}
.qp-progress-wrap {
    background: #0a1628;
    border: 1px solid var(--border);
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin-bottom: 6px;
}
.qp-progress-fill {
    height: 8px;
    border-radius: 8px;
    background: linear-gradient(90deg, var(--cyan), var(--purple));
    box-shadow: 0 0 10px rgba(0,245,255,0.5);
    transition: width 0.5s ease;
}
.qp-progress-label {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-align: right;
    margin-bottom: 18px;
    letter-spacing: 0.5px;
}
.qp-card {
    background: linear-gradient(135deg, #080f20, #0d1a30);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.qp-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--cyan), var(--purple));
}
.qp-question {
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 24px;
    line-height: 1.5;
}
.qp-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.qp-option {
    background: var(--bg-panel);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 0.92rem;
    color: var(--text);
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    font-family: 'Exo 2', sans-serif !important;
}
.qp-option:hover { border-color: var(--cyan); color: #fff; background: #0d2040; }
.qp-option.correct {
    background: linear-gradient(135deg, #001a0a, #002a14) !important;
    border-color: var(--green) !important;
    color: var(--green) !important;
    box-shadow: 0 0 16px rgba(0,255,136,0.2);
}
.qp-option.wrong {
    background: linear-gradient(135deg, #1a0005, #2a000a) !important;
    border-color: var(--red) !important;
    color: var(--red) !important;
    box-shadow: 0 0 16px rgba(255,71,87,0.2);
    animation: shakeCard 0.4s ease;
}
@keyframes shakeCard {
    0%,100% { transform: translateX(0); }
    20%      { transform: translateX(-8px); }
    40%      { transform: translateX(8px); }
    60%      { transform: translateX(-6px); }
    80%      { transform: translateX(6px); }
}
.qp-feedback {
    border-radius: 12px;
    padding: 14px 18px;
    margin-top: 16px;
    font-size: 0.95rem;
    font-weight: 600;
    text-align: center;
    animation: slideIn 0.3s ease;
}
.qp-feedback.ok  { background: linear-gradient(135deg,#001a0a,#002a14); border:1px solid var(--green); color:var(--green); }
.qp-feedback.err { background: linear-gradient(135deg,#1a0005,#2a000a); border:1px solid var(--red);   color:var(--red); }
.qp-score-card {
    background: linear-gradient(135deg, #060d1a, #0a1628);
    border: 2px solid var(--gold);
    border-radius: 20px;
    padding: 36px 40px;
    text-align: center;
    box-shadow: 0 0 40px rgba(255,215,0,0.15);
    animation: popIn 0.5s cubic-bezier(0.34,1.56,0.64,1);
}
.qp-score-title {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.4rem !important;
    font-weight: 900 !important;
    color: var(--gold) !important;
    letter-spacing: 2px !important;
    margin-bottom: 12px;
}
.qp-score-big {
    font-family: 'Orbitron', monospace !important;
    font-size: 3.5rem !important;
    font-weight: 900 !important;
    color: var(--cyan) !important;
    text-shadow: 0 0 30px rgba(0,245,255,0.5) !important;
    line-height: 1 !important;
    margin: 16px 0 !important;
}
.qp-score-sub  { font-size: 0.9rem; color: var(--text); margin-bottom: 24px; }
.qp-xp-earned  { font-size: 1.2rem; color: var(--green); font-weight: 700; margin-bottom: 8px; }
.mode-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #0a2040, #0d2a55);
    color: var(--cyan);
    border: 1px solid var(--cyan);
    border-radius: 8px;
    padding: 7px 18px;
    font-family: 'Exo 2', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    text-transform: uppercase;
    transition: all 0.2s;
    margin-top: 10px;
}
.mode-toggle-btn:hover {
    background: linear-gradient(135deg,#00f5ff22,#00f5ff33);
    box-shadow: 0 0 15px rgba(0,245,255,0.3);
}

/* ===== XP FLOAT POPUP ===== */
@keyframes fadeUpOut {
    0%   { opacity: 0; transform: translateY(0px) scale(0.8); }
    15%  { opacity: 1; transform: translateY(-8px) scale(1.1); }
    70%  { opacity: 1; transform: translateY(-28px) scale(1); }
    100% { opacity: 0; transform: translateY(-52px) scale(0.9); }
}
.xp-float {
    position: fixed;
    bottom: 120px;
    right: 30px;
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem;
    font-weight: 900;
    color: var(--green);
    text-shadow: 0 0 16px rgba(0,255,136,0.9);
    pointer-events: none;
    z-index: 9990;
    animation: fadeUpOut 1.6s ease forwards;
}

/* ===== LEVEL-UP MODAL ===== */
@keyframes confettiFall {
    0%   { transform: translateY(-20px) rotate(0deg); opacity: 1; }
    100% { transform: translateY(320px) rotate(720deg); opacity: 0; }
}
@keyframes levelGlow {
    0%,100% { text-shadow: 0 0 20px rgba(255,215,0,0.6); }
    50%      { text-shadow: 0 0 60px rgba(255,215,0,1), 0 0 120px rgba(255,215,0,0.5); }
}
.lvlup-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(2, 8, 20, 0.93);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9998;
}
.lvlup-modal {
    background: linear-gradient(135deg, #07111f, #0d1e38);
    border: 2px solid var(--gold);
    border-radius: 24px;
    padding: 48px 56px;
    text-align: center;
    box-shadow: 0 0 80px rgba(255,215,0,0.25), inset 0 0 60px rgba(255,215,0,0.04);
    animation: popIn 0.6s cubic-bezier(0.34,1.56,0.64,1);
    max-width: 460px;
    width: 90%;
    position: relative;
    overflow: hidden;
}
.lvlup-tag {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 3px;
    color: var(--gold);
    opacity: 0.7;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.lvlup-title {
    font-family: 'Orbitron', monospace !important;
    font-size: 2rem !important;
    font-weight: 900 !important;
    color: var(--gold) !important;
    animation: levelGlow 1.5s ease-in-out infinite;
    margin-bottom: 14px;
    line-height: 1.2;
}
.lvlup-msg {
    font-size: 1rem;
    color: var(--text);
    margin-bottom: 28px;
    line-height: 1.6;
}
/* confetti particles */
.confetti-wrap {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    overflow: hidden;
}
.confetti-p {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 2px;
    animation: confettiFall linear forwards;
}



/* ===== TRANSLATION PANEL ===== */
@keyframes transFadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}
.trans-panel {
    background: linear-gradient(135deg, #0a0a1a, #0d0d20);
    border-left: 3px solid #ffd700;
    border-radius: 0 0 12px 12px;
    padding: 10px 14px 12px;
    margin-top: -2px;
    animation: transFadeIn 0.3s ease;
}
.trans-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #ffd700;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    text-transform: uppercase;
}
.trans-text {
    color: #c8c8e8;
    font-size: 0.88em;
    font-style: italic;
    line-height: 1.6;
}
.trans-text .en-phrase {
    color: var(--cyan);
    font-style: normal;
    font-weight: 600;
}
.trans-toggle-btn {
    display: inline-block;
    background: transparent;
    border: 1px solid #2a2a4a;
    color: #4a6a8a;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 6px;
    cursor: pointer;
    margin-top: 6px;
    float: right;
    transition: all 0.2s;
}
.trans-toggle-btn:hover { color: #ffd700; border-color: #ffd700; }

/* ===== CHAT BUBBLES ===== */
.chat-area {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 4px 0 16px;
}
/* User bubble */
.bubble-user-wrap {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    margin-left: auto;
    max-width: 75%;
}
.bubble-user-label {
    font-size: 0.68rem;
    color: var(--cyan);
    opacity: 0.7;
    margin-bottom: 3px;
    padding-right: 4px;
    letter-spacing: 0.3px;
}
.bubble-user {
    background: linear-gradient(135deg, #0d2a4a, #0a2040);
    border: 1px solid #1a5080;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    color: var(--text);
    font-size: 0.92rem;
    line-height: 1.55;
    word-break: break-word;
}
/* AI opening bubble (no feedback) */
.bubble-opening {
    background: #001428;
    border-top: 2px solid var(--cyan);
    border-radius: 0 14px 14px 14px;
    padding: 14px 18px;
    color: var(--text);
    font-size: 0.92rem;
    line-height: 1.6;
    max-width: 88%;
    margin-right: auto;
}
/* Feedback sub-bubble */
.bubble-feedback-wrap {
    display: flex;
    flex-direction: column;
    max-width: 88%;
    margin-right: auto;
    gap: 6px;
}
.bubble-fb-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #ff4757;
    margin-bottom: 3px;
    letter-spacing: 0.5px;
}
.bubble-feedback {
    background: linear-gradient(135deg, #1a0608, #220810);
    border-left: 3px solid #ff4757;
    border-radius: 0 12px 12px 12px;
    padding: 12px 16px;
    color: var(--text);
    font-size: 0.88rem;
    line-height: 1.6;
}
/* Roleplay sub-bubble */
.bubble-rp-label {
    font-size: 0.7rem;
    color: var(--green);
    opacity: 0.8;
    margin-bottom: 3px;
    letter-spacing: 0.3px;
}
.bubble-roleplay {
    background: linear-gradient(135deg, #001a0e, #002216);
    border-left: 3px solid #00ff88;
    border-radius: 0 12px 12px 12px;
    padding: 12px 16px;
    color: var(--text);
    font-size: 0.92rem;
    line-height: 1.6;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}
.bubble-rp-avatar {
    font-size: 1.25rem;
    flex-shrink: 0;
    line-height: 1;
    margin-top: 2px;
}
.bubble-rp-text { flex: 1; min-width: 0; }
/* Stars pill */
.stars-pill {
    display: inline-block;
    font-size: 0.85rem;
    font-weight: 700;
    border-radius: 20px;
    padding: 3px 12px;
    margin-top: 4px;
    letter-spacing: 0.3px;
}
.stars-pill.s3 {
    background: rgba(255,215,0,0.08);
    border: 1px solid var(--gold);
    color: var(--gold);
    text-shadow: 0 0 10px rgba(255,215,0,0.6);
}
.stars-pill.s2 {
    background: rgba(180,180,180,0.07);
    border: 1px solid #aaa;
    color: #ccc;
}
.stars-pill.s1 {
    background: rgba(255,159,67,0.08);
    border: 1px solid #ff9f43;
    color: #ff9f43;
}

/* ===== FLASHCARDS ===== */
.fc-wrapper {
    max-width: 680px;
    margin: 0 auto;
    padding: 10px 0 40px;
}
.fc-progress-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}
.fc-progress-bar-wrap {
    flex: 1;
    background: #0a1628;
    border: 1px solid var(--border);
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin-right: 12px;
}
.fc-progress-bar-fill {
    height: 8px;
    border-radius: 8px;
    background: linear-gradient(90deg, var(--green), var(--cyan));
    box-shadow: 0 0 10px rgba(0,255,136,0.4);
    transition: width 0.5s ease;
}
.fc-progress-label {
    font-size: 0.72rem;
    color: var(--text-dim);
    white-space: nowrap;
}
/* ── 3D flip container ── */
.fc-scene {
    perspective: 1000px;
    width: 100%;
    height: 280px;
    margin-bottom: 20px;
}
.fc-card {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}
.fc-card.flipped {
    transform: rotateY(180deg);
}
.fc-face {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 28px 32px;
    box-sizing: border-box;
}
.fc-front {
    background: linear-gradient(135deg, #080f20, #0d1a30);
    border: 1px solid var(--border);
}
.fc-front::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 18px 18px 0 0;
    background: linear-gradient(90deg, var(--cyan), var(--purple));
}
.fc-back {
    background: linear-gradient(135deg, #040e1a, #081422);
    border: 1px solid var(--cyan);
    transform: rotateY(180deg);
    box-shadow: 0 0 30px rgba(0,245,255,0.08);
}
.fc-back::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 18px 18px 0 0;
    background: linear-gradient(90deg, var(--green), var(--cyan));
}
.fc-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-dim);
    margin-bottom: 12px;
}
.fc-context {
    font-size: 0.85rem;
    color: var(--cyan);
    margin-bottom: 14px;
    font-style: italic;
}
.fc-phrase {
    font-size: 1.25rem;
    font-weight: 700;
    color: #fff;
    text-align: center;
    line-height: 1.4;
}
.fc-tap-hint {
    position: absolute;
    bottom: 18px;
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.5px;
}
.fc-phonetic {
    font-size: 0.9rem;
    color: var(--gold);
    margin: 10px 0 14px;
    font-family: serif !important;
    letter-spacing: 0.5px;
}
.fc-example {
    font-size: 0.82rem;
    color: var(--text);
    text-align: center;
    font-style: italic;
    line-height: 1.5;
    border-left: 2px solid var(--cyan);
    padding-left: 12px;
    margin-top: 8px;
}
.fc-btn-row {
    display: flex;
    gap: 12px;
    margin-top: 8px;
}
.fc-done-card {
    background: linear-gradient(135deg, #060d1a, #0a1628);
    border: 2px solid var(--green);
    border-radius: 20px;
    padding: 36px 40px;
    text-align: center;
    box-shadow: 0 0 40px rgba(0,255,136,0.12);
    animation: popIn 0.5s cubic-bezier(0.34,1.56,0.64,1);
}

.xp-next-hint {
    font-size: 0.67rem;
    color: var(--text-dim);
    text-align: right;
    margin-top: 5px;
    letter-spacing: 0.3px;
}



/* ===== MODE TAB PILLS ===== */
.tab-pill-container {
    display: flex;
    gap: 0;
    background: #060d1a;
    border: 1px solid #1a3a5c;
    border-radius: 12px;
    padding: 4px;
    margin: 6px 0 10px;
    width: 100%;
    box-sizing: border-box;
}
.tab-pill {
    flex: 1;
    padding: 8px 20px;
    font-family: 'Exo 2', sans-serif;
    font-weight: 700;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-radius: 8px;
    text-align: center;
    color: #4a6a8a;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
    white-space: nowrap;
}
.tab-pill:hover:not(.tab-pill-active) {
    color: #8ab4d8;
}
.tab-pill-active {
    background: linear-gradient(135deg, #0a2040, #0d3060);
    color: var(--cyan) !important;
    border: 1px solid #00f5ff;
    box-shadow: 0 0 12px rgba(0,245,255,0.2);
    cursor: default;
    pointer-events: none;
}

/* override Streamlit button styling inside pill tabs */
div[data-testid="column"].tab-col > div > div > div > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    width: 100% !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: #4a6a8a !important;
    transition: color 0.2s ease !important;
}
div[data-testid="column"].tab-col > div > div > div > button:hover {
    color: #8ab4d8 !important;
}

/* ===== EMPTY STATE ===== */
@keyframes floatAvatar {
    0%,100% { transform: translateY(0px);   }
    50%      { transform: translateY(-10px); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px 36px;
    text-align: center;
    animation: fadeInUp 0.5s ease;
    gap: 10px;
}
.es-avatar-wrap {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: radial-gradient(circle at 40% 35%, #0e2d50, #040e1a);
    border: 2px solid var(--cyan);
    box-shadow: 0 0 24px rgba(0,245,255,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.4rem;
    animation: floatAvatar 3s ease-in-out infinite;
    margin-bottom: 6px;
}
.es-char-name {
    font-family: 'Orbitron', monospace !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: var(--cyan) !important;
}
.es-message {
    font-size: 0.92rem;
    color: var(--text);
    margin: 2px 0 6px;
    font-family: 'Exo 2', sans-serif;
}
.es-hint {
    font-size: 0.75rem;
    color: var(--text-dim);
    letter-spacing: 0.3px;
    margin-bottom: 14px;
    font-family: 'Exo 2', sans-serif;
}
.es-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    max-width: 480px;
}
.es-chip {
    background: rgba(0,245,255,0.05);
    border: 1px solid var(--cyan);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: var(--cyan);
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'Exo 2', sans-serif;
}
.es-chip:hover {
    background: rgba(0,245,255,0.12);
    box-shadow: 0 0 12px rgba(0,245,255,0.2);
    transform: translateY(-1px);
}

/* ===== INPUT AREA WRAPPER ===== */
.input-area-wrapper {
    position: relative;
    margin-top: 12px;
    padding: 10px 14px 6px;
    background: rgba(6,13,26,0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-top: 1px solid #1a3a5c;
}
.input-area-wrapper::before {
    content: '';
    position: absolute;
    top: -1px; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #1a3a5c 20%, var(--cyan) 50%, #1a3a5c 80%, transparent);
}
.input-area-label {
    font-size: 0.68rem;
    color: var(--cyan);
    opacity: 0.65;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}
@keyframes recDot {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.15; }
}
.rec-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #ff4757;
    animation: recDot 1s ease-in-out infinite;
    display: inline-block;
    box-shadow: 0 0 6px rgba(255,71,87,0.8);
}

/* ===== CHARACTER CARD ===== */
@keyframes moodFadeIn {
    from { opacity: 0; transform: translateX(-6px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes onlinePulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(0,255,136,0.7); }
    50%      { box-shadow: 0 0 0 5px rgba(0,255,136,0); }
}
.char-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 20px;
    background: linear-gradient(90deg, #050e1f 0%, #080f20 60%, #060c1c 100%);
    border-bottom: 1px solid var(--cyan);
    border-radius: 0;
    max-height: 90px;
    box-sizing: border-box;
    margin-bottom: 12px;
}
.char-avatar-wrap {
    position: relative;
    flex-shrink: 0;
    width: 58px;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at 40% 35%, #0d2a4a, #040e1a);
    border: 1.5px solid var(--cyan);
    border-radius: 50%;
    box-shadow: 0 0 18px rgba(0,245,255,0.25), inset 0 0 12px rgba(0,245,255,0.05);
    font-size: 1.85rem;
    line-height: 1;
}
.char-online-dot {
    position: absolute;
    bottom: 2px;
    right: 2px;
    width: 10px;
    height: 10px;
    background: var(--green);
    border-radius: 50%;
    border: 2px solid #050e1f;
    animation: onlinePulse 1.8s ease-in-out infinite;
}
.char-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
}
.char-name {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #fff !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.char-role {
    font-size: 0.68rem;
    color: var(--text-dim);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    letter-spacing: 0.3px;
}
.char-mood {
    font-size: 0.78rem;
    color: var(--cyan);
    animation: moodFadeIn 0.4s ease;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ===== RESPONSIVE DESIGN ===== */
@media (max-width: 768px) {
    .game-header { padding: 16px 20px 12px; margin-bottom: 12px; }
    .game-title { font-size: 1.3rem !important; }
    .game-subtitle { font-size: 0.75rem; }
    .stats-row { flex-wrap: wrap; }
    .stat-box, .streak-box { flex: 1 1 45%; padding: 8px 4px; }
    .feedback-box, .roleplay-box { padding: 10px 12px; font-size: 0.85em; }
    .roleplay-box { font-size: 0.95em; }
    .xp-container { padding: 10px 12px; }
    .badge-item { font-size: 0.7em; padding: 4px 8px; }
    .scenario-active { padding: 4px 12px; font-size: 0.75em; }
    [data-testid="stSidebar"] { padding: 1rem 0.5rem; }
    [data-testid="stChatMessage"] { padding: 2px !important; }
    .badges-title { font-size: 0.9rem; }
}

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
# --- HEARTS SYSTEM STATE ---
if "hearts"                not in st.session_state: st.session_state.hearts = 5      # Vieți rămase (max 5)
if "heart_streak"          not in st.session_state: st.session_state.heart_streak = 0 # Streak ★★★ consecutive pentru recuperare
if "heart_pulse"           not in st.session_state: st.session_state.heart_pulse = False # Trigger animație pierdere inimă
# --- DAILY STREAK STATE ---
# last_active_date : datetime.date | None  — ultima zi cu minim 3 turns
# daily_streak     : int                  — zile consecutive
# active_days      : list[str]            — zile ISO cu activitate (pentru calendar)
# today_turns      : int                  — turns în ziua curentă (pentru pragul de 3)
if "last_active_date"  not in st.session_state: st.session_state.last_active_date = None
if "daily_streak"      not in st.session_state: st.session_state.daily_streak = 0
if "active_days"       not in st.session_state: st.session_state.active_days = []
if "today_turns"       not in st.session_state: st.session_state.today_turns = 0
# --- QUICK PRACTICE STATE ---
if "app_mode"          not in st.session_state: st.session_state.app_mode = "chat"   # "chat" | "qp"
if "qp_index"          not in st.session_state: st.session_state.qp_index = 0        # index exercițiu curent
if "qp_answered"       not in st.session_state: st.session_state.qp_answered = None   # None=unanswered True/False=result
if "qp_chosen"         not in st.session_state: st.session_state.qp_chosen  = None   # int index of chosen option
if "qp_xp"             not in st.session_state: st.session_state.qp_xp = 0           # XP acumulat în sesiunea QP
if "qp_correct"        not in st.session_state: st.session_state.qp_correct = 0      # număr răspunsuri corecte
# --- XP VISUAL STATE ---
if "xp_last_gain"      not in st.session_state: st.session_state.xp_last_gain = 0       # ultimul căştig XP
if "level_up_pending"  not in st.session_state: st.session_state.level_up_pending = None # nivel nou de afişat
if "level_up_shown"    not in st.session_state: st.session_state.level_up_shown = False  # a fost afişat?
# --- SOUND STATE ---
if "sound_on"          not in st.session_state: st.session_state.sound_on = True      # toggle audio feedback
# --- FLASHCARD STATE ---
if "fc_known"          not in st.session_state: st.session_state.fc_known = set()    # indici fraze stăpânite
if "fc_queue"          not in st.session_state: st.session_state.fc_queue = []       # indici rămaşi de revăzut
if "fc_current"        not in st.session_state: st.session_state.fc_current = 0      # index în fc_queue
if "fc_flipped"        not in st.session_state: st.session_state.fc_flipped = False  # card răsturnat?
if "fc_scenario"       not in st.session_state: st.session_state.fc_scenario = None  # scenariu activ în FC
# --- CHARACTER MOOD STATE ---
if "char_mood"         not in st.session_state: st.session_state.char_mood = "😊 Ready to train you!"
# --- TRANSLATION STATE ---
if "translations"      not in st.session_state: st.session_state.translations = {}     # {msg_idx: ro_text}
if "show_translation"  not in st.session_state: st.session_state.show_translation = {} # {msg_idx: bool}
if "auto_translate"    not in st.session_state: st.session_state.auto_translate = False

# --- XP FLOAT POPUP (inject after each turn) ---
if st.session_state.get("xp_last_gain", 0) > 0:
    _gain = st.session_state.xp_last_gain
    _st_components.html(
        f'''<style>
        @keyframes fadeUpOut {{
            0%   {{ opacity:0; transform:translateY(0) scale(0.8); }}
            15%  {{ opacity:1; transform:translateY(-8px) scale(1.1); }}
            70%  {{ opacity:1; transform:translateY(-28px) scale(1); }}
            100% {{ opacity:0; transform:translateY(-52px) scale(0.9); }}
        }}
        .xp-float-el {{
            position:fixed; bottom:110px; right:28px;
            font-family:Orbitron,monospace; font-size:1.1rem; font-weight:900;
            color:#00ff88; text-shadow:0 0 16px rgba(0,255,136,0.9);
            pointer-events:none; z-index:9990;
            animation:fadeUpOut 1.6s ease forwards;
        }}
        </style><div class="xp-float-el">+{_gain} XP ⚡</div>''',
        height=0, scrolling=False
    )
    st.session_state.xp_last_gain = 0

# --- LEVEL-UP MODAL ---
if st.session_state.get("level_up_pending") and not st.session_state.get("level_up_shown"):
    _lvl = st.session_state.level_up_pending
    _msg = _lvl.get("unlock_msg", "")
    _col = _lvl.get("color", "#ffd700")
    # Generate 30 confetti particles
    _particles = ""
    import random as _rnd
    _colors = ["#ffd700","#00f5ff","#ff4757","#00ff88","#a855f7","#ff9f43","#fff"]
    for _i in range(30):
        _x    = _rnd.randint(0, 100)
        _delay= round(_rnd.uniform(0, 0.8), 2)
        _dur  = round(_rnd.uniform(1.2, 2.2), 2)
        _c    = _rnd.choice(_colors)
        _sz   = _rnd.randint(6, 12)
        _particles += (
            f'<div class="confetti-p" style="left:{_x}%;width:{_sz}px;height:{_sz}px;'
            f'background:{_c};animation-duration:{_dur}s;animation-delay:{_delay}s"></div>'
        )
    st.markdown(f"""
    <div class="lvlup-overlay">
        <div class="lvlup-modal">
            <div class="confetti-wrap">{_particles}</div>
            <div class="lvlup-tag">⚡ LEVEL UP!</div>
            <div class="lvlup-title">{_lvl['name']}</div>
            <div class="lvlup-msg">{_msg}</div>
            <div style="font-size:2rem;margin-bottom:16px">🎉🏆🎉</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("CONTINUĂ 🚀", use_container_width=True):
        st.session_state.level_up_shown  = True
        st.session_state.level_up_pending = None
        st.rerun()
    st.stop()

# --- HEADER ---
st.markdown("""
<div class="game-header">
    <div class="game-title">🚢 CRUISE ENGLISH TRAINER</div>
    <div class="game-subtitle">Training pentru <strong>Anamaria</strong> — misiunea ta pe vas începe aici</div>
</div>
""", unsafe_allow_html=True)

# --- MODE TAB PILLS ---
_mode = st.session_state.app_mode

def _pill_cls(m):
    return "tab-pill tab-pill-active" if _mode == m else "tab-pill"

# Render a pure-HTML display pill row (visual only — active tab no click)
# Plus hidden Streamlit buttons for inactive tabs (wired to rerun)
st.markdown(f"""
<div class="tab-pill-container">
    <div class="{_pill_cls('chat')}">💬 CHAT</div>
    <div class="{_pill_cls('qp')}">⚡ QUICK</div>
    <div class="{_pill_cls('fc')}">🃏 CARDS</div>
</div>
""", unsafe_allow_html=True)

# Invisible-but-functional Streamlit buttons below the visual pills
_tc1, _tc2, _tc3 = st.columns(3)
with _tc1:
    if _mode != "chat" and st.button("💬 CHAT", key="tab_chat", use_container_width=True):
        st.session_state.app_mode = "chat"
        st.rerun()
with _tc2:
    if _mode != "qp" and st.button("⚡ QUICK", key="tab_qp", use_container_width=True):
        st.session_state.app_mode = "qp"
        st.session_state.qp_index   = 0
        st.session_state.qp_answered = False
        st.session_state.qp_chosen  = None
        st.session_state.qp_xp     = 0
        st.session_state.qp_correct = 0
        st.rerun()
with _tc3:
    if _mode != "fc" and st.button("🃏 CARDS", key="tab_fc", use_container_width=True):
        st.session_state.app_mode = "fc"
        st.rerun()

# Hide the functional buttons with CSS (they fire on click, but are invisible)
st.markdown("""<style>
button[kind="secondary"][data-testid="baseButton-secondary"]:is(
    [aria-label="💬 CHAT"], [aria-label="⚡ QUICK"], [aria-label="🃏 CARDS"]
) { display: none !important; }
div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) {
    margin-top: -70px;
    opacity: 0;
    pointer-events: auto;
    height: 44px;
    overflow: hidden;
}
</style>""", unsafe_allow_html=True)

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
            # --- HEARTS: resetare la 5 vieți pentru noua sesiune ---
            st.session_state.hearts = 5
            st.session_state.heart_streak = 0
            st.session_state.heart_pulse = False
            st.session_state.level_up_shown = False
            st.session_state.level_up_pending = None
            st.session_state.xp_last_gain = 0
            st.session_state.char_mood = "😊 Ready to train you!"
            st.session_state.translations = {}
            st.session_state.show_translation = {}
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

    # --- SOUND TOGGLE ---
    sound_label = "🔊 Sunet ON" if st.session_state.sound_on else "🔇 Sunet OFF"
    if st.button(sound_label, use_container_width=True):
        st.session_state.sound_on = not st.session_state.sound_on
        st.rerun()

    # --- AUTO-TRANSLATE TOGGLE ---
    _auto_on = st.session_state.auto_translate
    auto_tr_label = "🇷🇴 AUTO-TRADUCERE ON" if _auto_on else "🇷🇴 AUTO-TRADUCERE OFF"
    if st.button(auto_tr_label, use_container_width=True):
        st.session_state.auto_translate = not _auto_on
        if _auto_on:
            # Turning OFF → hide all translation panels immediately
            st.session_state.show_translation = {}
        st.rerun()

    st.divider()

    # XP & Level
    current_level = get_level(st.session_state.xp)
    xp_prog, xp_total = xp_to_next(st.session_state.xp)
    pct = int(xp_prog / xp_total * 100) if xp_total > 0 else 100

    next_lvl, _ = get_next_level(st.session_state.xp)
    if next_lvl:
        xp_to_next_val = next_lvl["min_xp"] - st.session_state.xp
        next_hint = f'<div class="xp-next-hint">→ {xp_to_next_val} XP până la {next_lvl["name"]}</div>'
    else:
        next_hint = '<div class="xp-next-hint">👑 Nivel maxim atins!</div>'

    st.markdown(f"""
    <div class="xp-container">
        <div class="xp-label">
            <span class="level-name">{current_level['name']}</span>
            <span class="xp-count">⚡ {st.session_state.xp} XP</span>
        </div>
        <div class="xp-bar-bg">
            <div class="xp-bar-fill" style="width:{pct}%"></div>
        </div>
        {next_hint}
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

    # --- HEARTS ROW (lângă stats-row) ---
    hearts_html_parts = []
    for i in range(MAX_HEARTS):
        if i < st.session_state.hearts:
            # Ultima inimă activă primește clasa pulse dacă tocmai a pierdut
            is_last_active = (i == st.session_state.hearts - 1) and st.session_state.heart_pulse
            pulse_cls = " heart-pulse" if is_last_active else ""
            hearts_html_parts.append(f'<span class="heart-active{pulse_cls}">❤️</span>')
        else:
            hearts_html_parts.append('<span class="heart-lost">🖤</span>')
    hearts_inner = "".join(hearts_html_parts)
    st.markdown(
        f'<div class="hearts-row"><span class="hearts-label">VIEȚI</span>{hearts_inner}</div>',
        unsafe_allow_html=True
    )
    # Resetăm flag-ul de pulse după afișare
    st.session_state.heart_pulse = False

    # --- DAILY STREAK MINI-CALENDAR ---
    today = datetime.date.today()
    today_iso = today.isoformat()

    # Construim lista ultimelor 7 zile (cea mai veche prima)
    week_days = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]  # [d-6 .. azi]

    cal_parts = []
    for day in week_days:
        d_iso = day.isoformat()
        if day == today:
            dot = "🔵"  # Azi — indiferent de activitate
        elif d_iso in st.session_state.active_days:
            dot = "🟢"  # Zi cu activitate
        else:
            dot = "⬜"  # Zi fără activitate
        # Numele scurt al zilei în română (Lu Ma Mi Jo Vi Sâ Du)
        RO_DAYS = ["Lu", "Ma", "Mi", "Jo", "Vi", "Sâ", "Du"]
        day_lbl = RO_DAYS[day.weekday()]
        cal_parts.append(
            f'<div class="cal-cell"><div class="cal-dot">{dot}</div>'
            f'<div class="cal-lbl">{day_lbl}</div></div>'
        )

    cal_html = (
        '<div class="cal-section">'
        '<div class="cal-title">📅 Activitate — 7 zile</div>'
        f'<div class="cal-row">{" ".join(cal_parts)}</div>'
        f'<div class="cal-streak">🗓️ Streak zilnic: <strong>{st.session_state.daily_streak}</strong> zile</div>'
        '</div>'
    )
    st.markdown(cal_html, unsafe_allow_html=True)

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
    st.session_state.char_mood = "😊 Ready to train you!"
    st.session_state.translations = {}
    st.session_state.show_translation = {}
    # Resetare QP la schimbarea scenariului
    st.session_state.qp_index = 0
    st.session_state.qp_answered = False
    st.session_state.qp_chosen = None
    st.session_state.qp_xp = 0
    st.session_state.qp_correct = 0
    st.rerun()

st.session_state.scenarios_tried.add(selected_scenario_name)

# --- MAIN AREA ROUTING ---
if st.session_state.app_mode == "qp":
    # ── QUICK PRACTICE MODE ────────────────────────────────────
    render_quick_practice(selected_scenario_name)
elif st.session_state.app_mode == "fc":
    # ── FLASHCARD MODE ───────────────────────────────────────────
    render_flashcards(selected_scenario_name)
else:
    # -- CHAT MODE --------------------------------------------------

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
                st.warning("⏳ Ai atins limita de trafic a API-ului Google (Rate Limit / Quota). Te rog ăşteaptă câteva momente şi apasă butonul RESET.")
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

    # --- GAME OVER MODAL (0 vieți rămase) ---
    if st.session_state.hearts <= 0:
        st.markdown("""
        <div class="game-over-overlay">
            <div class="game-over-modal">
                <div class="game-over-icon">💔</div>
                <div class="game-over-title">GAME OVER</div>
                <div class="game-over-sub">
                    Ai rămas fără vieți!<br>
                    Apasă <strong>RESET</strong> în sidebar pentru a continua misiunea.
                </div>
                <div style="font-size:2.5rem;letter-spacing:8px">🖤🖤🖤🖤🖤</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()  # Blochează tot ce urmează

    def _md_to_safe(text):
        """Convertește Markdown basic în HTML safe pentru st.markdown.
        Guards against None/non-string input.
        """
        if not text or not isinstance(text, str):
            return ""
        import html as _html
        t = _html.escape(str(text))
        # Bold: **text**
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        # Italic: *text*  (after bold, so ** already consumed)
        t = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', t)
        # Quoted phrases "text" → highlight
        t = re.sub(r'&quot;([^&]+)&quot;', r'<strong>&quot;\1&quot;</strong>', t)
        # Inline code
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
        # Star ratings — coloured spans
        t = t.replace('★★★', '<span style="color:#ffd700;font-weight:700">★★★</span>')
        t = t.replace('★★☆', '<span style="color:#c0c0c0;font-weight:700">★★☆</span>')
        t = t.replace('★☆☆', '<span style="color:#cd7f32;font-weight:700">★☆☆</span>')
        # Newlines
        t = t.replace('\n', '<br>')
        return t

    # --- SCENARIO BADGE ---
    sc_info = SCENARIOS[selected_scenario_name]
    st.markdown(f"""
<div class="scenario-active">
    {sc_info['icon']} {selected_scenario_name}
    &nbsp;·&nbsp; Difficulty: {sc_info['difficulty']}
</div>
""", unsafe_allow_html=True)

    # --- CHARACTER CARD ---
    _avatar = sc_info.get("avatar", sc_info.get("char_emoji", "🧑"))
    _char   = sc_info.get("char", "Character")
    _role   = sc_info.get("role", "")
    _mood   = st.session_state.char_mood
    st.markdown(f"""
<div class="char-card">
    <div class="char-avatar-wrap">
        {_avatar}
        <div class="char-online-dot"></div>
    </div>
    <div class="char-info">
        <div class="char-name">{_char}</div>
        <div class="char-role">{_role}</div>
        <div class="char-mood">{_mood}</div>
    </div>
</div>
""", unsafe_allow_html=True)

    # --- MESSAGES ---
    _sc_avatar   = sc_info.get("avatar", sc_info.get("char_emoji", "🤖"))
    _sc_char     = sc_info.get("char", "Trainer")

    # Map scenariu → marker de split roleplay
    _char_marker_map = {
        "🛍️ Shop – Duty Free":      "**🛗️ James:**",
        "🍽️ Waiter – Dining Room":  "**🍽️ Marco:**",
        "🍹 Bartender – Pool Bar":         "**🍹 Jake:**",
        "🛎️ Guest Services":              "**🛝️ Patricia:**",
        "🎯 HR Interview":                      "**👔 Richard:**",
    }
    _rp_marker = _char_marker_map.get(selected_scenario_name, "")

    def _stars_pill(text):
        if "★★★" in text:
            return '<span class="stars-pill s3">★★★ Perfect!</span>'
        if "★★☆" in text:
            return '<span class="stars-pill s2">★★☆ Good job!</span>'
        if "★☆☆" in text:
            return '<span class="stars-pill s1">★☆☆ Keep going!</span>'
        return ""


    # Starter chips — populated via query param trick
    _starters = STARTER_PHRASES_MAP.get(selected_scenario_name, [])
    _qs = st.query_params
    _prefill = _qs.get("prefill", "")
    if _prefill:
        st.query_params.clear()
        # Inject as pending text — rerun will pick it up via text_val
        st.session_state._pending_prefill = _prefill

    chat_container = st.container()
    with chat_container:
        # ── EMPTY STATE ─────────────────────────────────────────────────────
        if not st.session_state.messages:
            _chips_html = "".join(
                f'<div class="es-chip" onclick="window.location.href='+ '?' + 'prefill=' + encodeURIComponent('{p}') + '">{p}</div>'
                for p in _starters
            )
            st.markdown(f"""
<div class="empty-state">
  <div class="es-avatar-wrap">{_sc_avatar}</div>
  <div class="es-char-name">{_sc_char}</div>
  <div class="es-message">Sunt gata să te antrenez, Anamaria.</div>
  <div class="es-hint">&rarr; Scrie primul mesaj sau apasă 🎤 pentru a vorbi</div>
  <div class="es-chips">{_chips_html}</div>
</div>""", unsafe_allow_html=True)

        st.markdown('<div class="chat-area">', unsafe_allow_html=True)
        is_first_ai = True  # primul mesaj AI = opening line

        for _mi, msg in enumerate(st.session_state.messages):
            role    = msg["role"]
            content = msg["content"]

            # ── USER BUBBLE ──────────────────────────────────────────────────
            if role == "user":
                is_first_ai = False  # reset flag (nu mai e primul AI)
                if content.startswith("🎤"):
                    inner = "🎤 <em>Audio message</em>"
                else:
                    inner = _md_to_safe(content)
                st.markdown(f"""
<div class="bubble-user-wrap">
  <div class="bubble-user-label">👩 Anamaria</div>
  <div class="bubble-user">{inner}</div>
</div>""", unsafe_allow_html=True)

            # ── AI BUBBLE ────────────────────────────────────────────────────
            else:
                has_feedback = "**🔍 Feedback:**" in content or "🔍 Feedback:" in content
                split_pt = content.find(_rp_marker) if _rp_marker else -1
                # Skip translation for short opening messages (< 50 chars)
                _is_opening = is_first_ai or not has_feedback or split_pt < 0
                _allow_trans = not (_is_opening and len(content) < 50)

                if _is_opening:
                    # Opening line sau mesaj simplu fără feedback
                    inner = _md_to_safe(content)
                    st.markdown(f"""
<div class="bubble-opening">{inner}</div>""", unsafe_allow_html=True)
                    is_first_ai = False
                else:
                    is_first_ai = False
                    fb_raw  = content[:split_pt].strip()
                    rp_raw  = content[split_pt:].strip()
                    pill    = _stars_pill(fb_raw)
                    fb_html = _md_to_safe(fb_raw)
                    rp_html = _md_to_safe(rp_raw)

                    st.markdown(f"""
<div class="bubble-feedback-wrap">
  <div class="bubble-fb-label">🔍 FEEDBACK</div>
  <div class="bubble-feedback">{fb_html}</div>
  {f'<div style="margin-top:2px">{pill}</div>' if pill else ""}
  <div class="bubble-rp-label" style="margin-top:4px">{_sc_avatar} {_sc_char.upper()}</div>
  <div class="bubble-roleplay">
    <div class="bubble-rp-avatar">{_sc_avatar}</div>
    <div class="bubble-rp-text">{rp_html}</div>
  </div>
</div>""", unsafe_allow_html=True)

                # ── TRANSLATION TOGGLE ────────────────────────────────────────
                if _allow_trans:
                    # Build translate text: Why lines + roleplay (skip ❌/✅ lines)
                    def _build_trans_text():
                        if has_feedback and split_pt > 0:
                            _fb_lines  = fb_raw.split("\n")
                            _why_lines = [l for l in _fb_lines if "📖" in l or "Why" in l]
                            return ("\n".join(_why_lines) + "\n\n" + rp_raw) if _why_lines else rp_raw
                        return content

                    # AUTO-TRANSLATE: generate eagerly for ALL assistant msgs
                    if st.session_state.auto_translate:
                        st.session_state.show_translation[_mi] = True
                        if _mi not in st.session_state.translations:
                            with st.spinner("🌐 Se traduce..."):
                                get_translation(_mi, _build_trans_text())

                    _showing = st.session_state.show_translation.get(_mi, False)
                    _btn_lbl = "🇬🇧 Ascunde" if _showing else "🇷🇴 Traducere"

                    # Manual toggle button (small, right-aligned)
                    _, _bcol = st.columns([8, 1])
                    with _bcol:
                        if st.button(_btn_lbl, key=f"tr_btn_{_mi}",
                                     help="Afișează/ascunde traducerea română"):
                            _new_showing = not _showing
                            st.session_state.show_translation[_mi] = _new_showing
                            if _new_showing and _mi not in st.session_state.translations:
                                with st.spinner("🌐 Se traduce..."):
                                    get_translation(_mi, _build_trans_text())
                            st.rerun()

                    if _showing and _mi in st.session_state.translations:
                        _ro_html = _highlight_en_phrases(st.session_state.translations[_mi])
                        st.markdown(f"""
<div class="trans-panel">
  <div class="trans-label">🇷🇴 Traducere</div>
  <div class="trans-text">{_ro_html}</div>
</div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # --- INPUT (blocat când hearts == 0) ---
    footer = st.container()
    with footer:
        st.markdown('''<div class="input-area-wrapper">
  <div class="input-area-label">
    <span class="rec-dot" id="rec-indicator" style="display:none"></span>
    🎙️ Răspunde în Engleză
  </div>
</div>''', unsafe_allow_html=True)
        audio_val = st.audio_input("🎤 Vorbeşte")
        text_val = st.chat_input("Scrie în Engleză...")
        # Handle chip prefill
        if st.session_state.get("_pending_prefill") and not text_val:
            text_val = st.session_state.pop("_pending_prefill")

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
                if is_audio:
                    st.markdown('<div class="bubble-user-wrap"><div class="bubble-user-label">👩 Anamaria</div><div class="bubble-user">🎤 <em>Audio message</em></div></div>', unsafe_allow_html=True)
                    st.audio(user_message)
                else:
                    import html as _html2
                    _safe = _html2.escape(user_message).replace("\n","<br>")
                    st.markdown(f'<div class="bubble-user-wrap"><div class="bubble-user-label">👩 Anamaria</div><div class="bubble-user">{_safe}</div></div>', unsafe_allow_html=True)

            content_to_save = "🎤 *Audio Message*" if is_audio else user_message
            st.session_state.messages.append({"role": "user", "content": content_to_save})

            if "first_message" not in st.session_state.badges:
                award_badge("first_message")
            if is_audio and "audio_used" not in st.session_state.badges:
                award_badge("audio_used")
            turns_now = count_turns()
            if turns_now >= 5  and "5_turns"  not in st.session_state.badges: award_badge("5_turns")
            if turns_now >= 10 and "10_turns" not in st.session_state.badges: award_badge("10_turns")

            char_map2 = {
                "🛍️ Shop – Duty Free":     "**🛗️ James:**",
                "🍽️ Waiter – Dining Room": "**🍽️ Marco:**",
                "🍹 Bartender – Pool Bar":        "**🍹 Jake:**",
                "🛎️ Guest Services":              "**🛝️ Patricia:**",
                "🎯 HR Interview":                      "**👔 Richard:**",
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

                stars = count_stars_in_response(resp_text)
                st.session_state.total_stars += stars
                xp_earned = XP_REWARDS["message_sent"]
                reason = "mesaj trimis"

                if stars == 3:
                    xp_earned += XP_REWARDS["no_mistake"]
                    reason = "răspuns perfect ★★★"
                    play_sound("ding")       # ★★★ — sunet pozitiv
                    st.session_state.char_mood = "🤩 Excellent work!"
                    st.session_state.streak += 1
                    st.session_state.heart_streak += 1
                    if st.session_state.heart_streak >= 3:
                        st.session_state.heart_streak = 0
                        if st.session_state.hearts < MAX_HEARTS:
                            st.session_state.hearts += 1
                            reason += " + ❤️ recuperată!"
                    if st.session_state.streak == 3:
                        xp_earned += XP_REWARDS["streak_3"]
                        reason += " + streak x3!"
                        award_badge("no_mistakes")
                    if st.session_state.streak == 5:
                        xp_earned += XP_REWARDS["streak_5"]
                        reason += " + streak x5! 🔥"
                elif stars == 2:
                    st.session_state.char_mood = "🙂 Getting there..."
                    st.session_state.streak = 0
                    st.session_state.heart_streak = 0
                elif stars == 1:
                    st.session_state.char_mood = "😬 Let's try that again..."
                    st.session_state.streak = 0
                    st.session_state.heart_streak = 0
                    if st.session_state.hearts > 0:
                        st.session_state.hearts -= 1
                        st.session_state.heart_pulse = True
                        play_sound("thud")   # pierdere ❤️
                    play_sound("buzz")       # ★☆☆ — sunet negativ
                else:
                    st.session_state.streak = 0
                    st.session_state.heart_streak = 0

                if is_audio:
                    xp_earned += XP_REWARDS["audio_bonus"]
                    reason += " + bonus audio 🎤"

                award_xp(xp_earned, reason)
                # Badge nou — fanfare după award_xp (new_badge a fost setat)
                if st.session_state.new_badge:
                    play_sound("fanfare")
                update_daily_streak()
                st.rerun()

            except Exception as e:
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
                try:
                    if st.session_state.chat_session.history and getattr(st.session_state.chat_session.history[-1], "role", "") == "user":
                        st.session_state.chat_session.history.pop()
                except Exception:
                    pass
                if is_audio:
                    st.session_state.last_processed_audio = None
                if "429" in str(e) or "quota" in str(e).lower():
                    st.warning("⏳ Ai atins limita de mesaje (prea multe solicitări simultane). Te rog aşteaptă câteva momente şi trimite mesajul din nou!")
                else:
                    st.error(f"Eroare la procesare: {e}")
