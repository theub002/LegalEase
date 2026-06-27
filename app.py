import streamlit as st
from backend import legal_chatbot
import time

# ----------- PAGE CONFIG -----------
st.set_page_config(
    page_title="LegalEase | AI Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------- THEME TOGGLE (Must be before CSS) -----------
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚖️ LegalEase</div>', unsafe_allow_html=True)
    is_dark_mode = st.toggle("🌙 Dark Mode", value=False)
    st.markdown("---")

# ----------- DYNAMIC THEME VARIABLES -----------
if is_dark_mode:
    bg_color = "#0f172a"          
    text_color = "#f8fafc"        
    sidebar_box_bg = "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
    sidebar_box_border = "#334155"
    sidebar_box_text = "#93c5fd"
    card_bg = "#1e293b"
    card_border = "#334155"
    card_text = "#e2e8f0"
    card_hover_border = "#60a5fa"
    hero_grad_1 = "#60a5fa"
    hero_grad_2 = "#93c5fd"
    subtitle_color = "#94a3b8"
    input_border = "#475569"
    input_bg = "#1e293b"
    input_text = "#f8fafc"
    input_placeholder = "#94a3b8"
else:
    bg_color = "#f8fafc"          
    text_color = "#0f172a"        
    sidebar_box_bg = "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)"
    sidebar_box_border = "#bfdbfe"
    sidebar_box_text = "#1e40af"
    card_bg = "#ffffff"
    card_border = "#e2e8f0"
    card_text = "#1e3a8a"
    card_hover_border = "#3b82f6"
    hero_grad_1 = "#1e3a8a"
    hero_grad_2 = "#3b82f6"
    subtitle_color = "#64748b"
    input_border = "#cbd5e1"
    input_bg = "#ffffff"
    input_text = "#0f172a"
    input_placeholder = "#64748b"

# ----------- AGGRESSIVE PREMIUM CSS -----------
st.markdown(f"""
<style>
/* Import premium Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@600;700&display=swap');

/* 1. FORCE THE ENTIRE APP BACKGROUND */
html, body, .stApp, 
[data-testid="stAppViewContainer"], 
[data-testid="stHeader"], 
[data-testid="stBottom"], 
[data-testid="stBottom"] > div {{
    background-color: {bg_color} !important;
    font-family: 'Inter', sans-serif !important;
    transition: background-color 0.3s ease;
}}

/* Force the Sidebar background explicitly */
[data-testid="stSidebar"] > div:first-child {{
    background-color: {bg_color} !important;
}}

/* 2. FORCE TEXT COLORS globally */
.stMarkdown, p, li, h1, h2, h3, h4, h5, h6 {{
    color: {text_color} !important;
}}

/* Hero Section */
.hero-title {{
    font-family: 'Playfair Display', serif !important;
    font-size: 4rem;
    background: linear-gradient(135deg, {hero_grad_1} 0%, {hero_grad_2} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.5rem;
    padding-top: 3rem;
    animation: fadeInDown 0.8s ease-out;
}}
.hero-subtitle {{
    text-align: center;
    color: {subtitle_color} !important;
    font-size: 1.25rem;
    margin-bottom: 3.5rem;
    font-weight: 400;
    animation: fadeInUp 0.8s ease-out;
}}

/* Custom Button Styling */
div.stButton > button:first-child {{
    background-color: {card_bg} !important;
    border: 1px solid {card_border} !important;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    font-weight: 500;
    font-size: 1.05rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    text-align: left;
    display: flex;
    justify-content: flex-start;
}}
div.stButton > button:first-child p {{
    color: {card_text} !important; 
}}
div.stButton > button:first-child:hover {{
    border-color: {card_hover_border} !important;
    box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.2);
    transform: translateY(-3px);
}}

/* Sidebar Customization */
.sidebar-box {{
    background: {sidebar_box_bg} !important;
    padding: 1.5rem;
    border-radius: 16px;
    border: 1px solid {sidebar_box_border};
    margin-bottom: 2rem;
}}
.sidebar-title {{
    font-family: 'Playfair Display', serif !important;
    font-weight: 700;
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: {hero_grad_1} !important;
}}
.sidebar-box strong, .sidebar-list li {{
    color: {sidebar_box_text} !important;
}}
.sidebar-list {{
    margin-left: -1rem;
}}
.sidebar-list li {{
    margin-bottom: 0.5rem;
}}

/* --- CHAT INPUT (SEARCH BAR) STYLING --- */
/* Target all layers of the chat input box to ensure background applies */
[data-testid="stChatInput"], 
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {{
    background-color: {input_bg} !important;
    border-color: {input_border} !important;
    border-radius: 20px !important;
}}

/* Force typing text and cursor colors to match theme dynamically */
[data-testid="stChatInput"] textarea {{
    color: {input_text} !important;
    -webkit-text-fill-color: {input_text} !important;
    caret-color: {input_text} !important;
}}

/* Ensure placeholder text matches theme dynamically */
[data-testid="stChatInput"] textarea::placeholder {{
    color: {input_placeholder} !important;
    -webkit-text-fill-color: {input_placeholder} !important;
}}

/* Footer */
.footer {{
    text-align: center;
    color: {subtitle_color} !important;
    font-size: 0.85rem;
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid {card_border};
}}

/* Animations */
@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
</style>
""", unsafe_allow_html=True)

# ----------- SESSION STATE -----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------- SIDEBAR CONTENT -----------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-box">
        <strong>📌 What LegalEase Does</strong>
        <ul class="sidebar-list">
            <li>Navigate the <b>IPC → BNS</b> transition</li>
            <li>Shows old law vs new law + what changed</li>
            <li>Discover <b>government schemes</b> you qualify for</li>
            <li>Case-law powered RAG accuracy</li>
            <li>Hindi, Hinglish & English support</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    if st.button("🔄 Start New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ----------- MAIN CHAT INTERFACE -----------

if not st.session_state.messages:
    st.markdown('<div class="hero-title">LegalEase</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Your AI-Powered Legal Assistant for Indian Law (IPC & BNS)</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 8, 1]) 
    
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚨 What is the punishment for theft?"):
                st.session_state.example_query = "What is punishment for theft?"
                st.rerun()
            if st.button("💔 Domestic violence ke liye kya laws hain?"):
                st.session_state.example_query = "Domestic violence ke liye kya section hai?"
                st.rerun()
        with c2:
            if st.button("💍 Explain dowry laws in India"):
                st.session_state.example_query = "Explain dowry laws in India"
                st.rerun()
            if st.button("👮 Mujhe arrest kiya bina warrant, kya karoon?"):
                st.session_state.example_query = "Mujhe arrest kiya bina warrant, kya karoon?"
                st.rerun()

else:
    header_color = "#60a5fa" if is_dark_mode else "#1e3a8a"
    sub_color = "#94a3b8" if is_dark_mode else "#64748b"
    
    st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 15px; padding-bottom: 1.5rem; border-bottom: 1px solid {card_border}; margin-bottom: 2rem;'>
            <div style='background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 10px; border-radius: 12px; color: white; font-size: 1.5rem; line-height: 1;'>⚖️</div>
            <div>
                <h2 style='margin: 0; font-family: "Playfair Display", serif; color: {header_color} !important; font-size: 1.8rem;'>LegalEase Chat</h2>
                <span style='color: {sub_color} !important; font-size: 0.9rem;'>Powered by Sarvam-M</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ----------- DISPLAY CHAT HISTORY -----------
for msg in st.session_state.messages:
    avatar_icon = "🧑‍💼" if msg["role"] == "user" else "⚖️"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# ----------- LOGIC: HANDLE INPUT -----------
prompt = None

if "example_query" in st.session_state:
    prompt = st.session_state.pop("example_query")
elif chat_input := st.chat_input("Apna legal sawaal poochiye... (Ask your legal question)"):
    prompt = chat_input

# ----------- PROCESS THE PROMPT -----------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Analyzing legal context & generating response..."):
            history = st.session_state.messages[:-1]
            response = legal_chatbot(prompt, history)
            time.sleep(0.5) 
            
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# ----------- FOOTER -----------
st.markdown('<div class="footer">Built for Hackathon 🚀 | LegalEase © 2026 | RAG + Sarvam-M</div>', unsafe_allow_html=True)