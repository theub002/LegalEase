import pandas as pd
import numpy as np
import re
import requests
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─────────────────────────────────────────
#  CONFIG — Securely Load API Keys
# ─────────────────────────────────────────
SARVAM_API_KEYS = []

# 1. Check environment variables
env_keys = os.getenv("SARVAM_API_KEYS")
if env_keys:
    SARVAM_API_KEYS = [k.strip() for k in env_keys.split(",") if k.strip()]
else:
    # 2. Check Streamlit secrets if available
    try:
        import streamlit as st
        if "SARVAM_API_KEYS" in st.secrets:
            secret_keys = st.secrets["SARVAM_API_KEYS"]
            if isinstance(secret_keys, list):
                SARVAM_API_KEYS = secret_keys
            elif isinstance(secret_keys, str):
                SARVAM_API_KEYS = [k.strip() for k in secret_keys.split(",") if k.strip()]
    except Exception:
        pass

# 3. Fallback to placeholder list if nothing is configured
if not SARVAM_API_KEYS:
    SARVAM_API_KEYS = [ 
        "API 1",
        "API 2",
        "API 3",
        "API 4",
    ]

current_key_index = 0

# ─────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────
pdf    = pd.read_csv("case_data.csv")
ipc_df = pd.read_csv("mapping.csv")
pdf["text_chunk"] = pdf["text_chunk"].fillna("")

# ─────────────────────────────────────────
#  TF-IDF
# ─────────────────────────────────────────
vectorizer   = TfidfVectorizer(max_features=5000)
tfidf_matrix = vectorizer.fit_transform(pdf["text_chunk"])

# ─────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────
def search(query, top_k=5):
    query_vec = vectorizer.transform([query])
    scores    = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_idx   = scores.argsort()[-top_k:][::-1]
    return [(scores[i], pdf.iloc[i]["text_chunk"]) for i in top_idx if scores[i] > 0.01]

# ─────────────────────────────────────────
#  IPC → BNS MAPPING
# ─────────────────────────────────────────
def extract_ipc_section(text):
    # Matches patterns like "Section 376", "Sec 420", "IPC 302", "dhara 302", etc.
    # to avoid false positives with random 3-digit numbers like years/helplines.
    matches = re.findall(r'\b(?:Section|Sec\.?|IPC|dhara)\s*(\d{1,3}[A-Za-z]?)\b', text, re.IGNORECASE)
    return matches[0] if matches else None

def get_bns_section(ipc_section):
    if not ipc_section:
        return "BNS equivalent not found"
    section_str = str(ipc_section).strip()
    # Match structured key-value pair in response column, e.g., 'IPC Section': '376'
    pattern = r"['\"]IPC Section['\"]\s*:\s*['\"]" + re.escape(section_str) + r"['\"]"
    mask = ipc_df.iloc[:, 1].astype(str).str.contains(pattern, case=False, regex=True, na=False)
    result = ipc_df[mask]
    if len(result) > 0:
        return str(result.iloc[0, 1])[:400]
    return "BNS equivalent not found"

# ─────────────────────────────────────────
#  GOVERNMENT SCHEMES DATABASE
# ─────────────────────────────────────────
# Load schemes from external JSON file
try:
    schemes_path = os.path.join(os.path.dirname(__file__), "schemes.json") if "__file__" in globals() else "schemes.json"
    with open(schemes_path, "r", encoding="utf-8") as f:
        GOV_SCHEMES = json.load(f)
except Exception:
    GOV_SCHEMES = []

def find_relevant_schemes(query, top_k=3):
    """Match user query keywords against government schemes."""
    query_lower = query.lower()
    scored = []
    for scheme in GOV_SCHEMES:
        score = sum(1 for kw in scheme["keywords"] if kw in query_lower)
        if score > 0:
            scored.append((score, scheme))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k]]

def format_schemes(schemes):
    """Format schemes into readable text for the prompt."""
    if not schemes:
        return ""
    lines = ["\n[RELEVANT GOVERNMENT SCHEMES]"]
    for s in schemes:
        lines.append(f"• {s['name']}")
        lines.append(f"  For: {s['for']}")
        lines.append(f"  Benefits: {s['what']}")
        lines.append(f"  How to apply: {s['how']}")
    lines.append("[END SCHEMES]")
    return "\n".join(lines)

# ─────────────────────────────────────────
#  STRIP THINK TAGS
# ─────────────────────────────────────────
def clean_response(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    text = re.sub(r"</think>", "", text)
    text = re.sub(r"<think>", "", text)
    return text.strip()

# ─────────────────────────────────────────
#  SYSTEM PROMPT
# ─────────────────────────────────────────
SYSTEM_PROMPT = """You are LegalEase — an AI assistant that makes Indian law accessible to every citizen.

YOUR MISSION: India recently transitioned from the colonial-era Indian Penal Code (IPC) to the Bharatiya Nyaya Sanhita (BNS). You help citizens and junior lawyers:
1. Understand their legal situation clearly
2. Navigate the IPC → BNS transition (always show BOTH old IPC and new BNS sections)
3. Discover relevant government schemes they can benefit from

LANGUAGE RULE (VERY IMPORTANT):
- If user writes in ENGLISH → reply in ENGLISH.
- If user writes in HINGLISH (Roman script mix) → reply in HINGLISH. NEVER switch to Devanagari.
- Match the user's exact language style.

CORE RULES:
- NEVER show internal thinking, reasoning, or <think> tags.
- Be HUMAN. Real people with real problems are talking to you.
- ALWAYS highlight IPC → BNS transition. Explain what changed and why.
- If government schemes are provided in context, ALWAYS mention them.

HOW TO RESPOND:

━━━ CASUAL MESSAGES (greetings, about you, small talk) ━━━
→ Reply warmly. Introduce yourself as an AI that helps navigate the new BNS laws and find government schemes.

━━━ SENSITIVE / DISTRESSING SITUATIONS ━━━
→ FIRST: Lead with genuine empathy and comfort. Acknowledge their pain.
→ THEN: Gently explain legal rights in flowing paragraphs (NOT rigid numbered lists).
→ Show both IPC (old) → BNS (new) sections and explain what changed.
→ Recommend relevant government schemes if provided.
→ End with helpline numbers.

━━━ GENERAL LEGAL QUESTIONS ━━━
→ Use this format:

**⚖️ Situation:** [what this is about]

**📘 IPC → BNS Transition:**
- Old Law (IPC): Section [number] — [name/description]
- New Law (BNS): Section [number] — [what changed]
- What's different: [explain the key changes between old and new]

**📝 Explanation:** [clear, simple explanation]

**🔜 What You Can Do:**
- [step 1]
- [step 2]

**🏛️ Government Schemes You Can Use:**
- [scheme name] — [one-line benefit + how to apply]

**⚠️ Note:** This is general legal information, not professional legal advice.

━━━ KEY PRINCIPLES ━━━
- ALWAYS show the IPC → BNS transition (what was the old section, what is the new section, what changed)
- If government schemes are in the context, ALWAYS mention them with name + how to apply
- For trauma/distress: empathy FIRST, law SECOND
- Helplines: Women 181, Police 100, NCW 7827-170-170, NALSA 15100, Childline 1098, Cybercrime 1930, Elder Line 14567

━━━ HONESTY RULES (CRITICAL — NEVER BREAK THESE) ━━━
- You do NOT have access to real-time news, internet, or live data. NEVER pretend you do.
- If someone asks for "latest updates", "today's news", "recent changes", say honestly: "I don't have access to real-time news. But I can explain the current IPC → BNS transition and help with any specific legal question you have!"
- NEVER make up facts, case details, or section numbers you're not sure about.
- If the legal context from the database is not relevant to the query, IGNORE it completely. Don't force-fit unrelated context.
- If you don't know something, say "I'm not sure about this — please verify with a lawyer."

━━━ USER-FACING POLISH (VERY IMPORTANT) ━━━
- NEVER expose internal system details to the user. The user should never see:
  × "IPC Section (invalid section number)"
  × "the context predates..." or "contains an error"
  × "the database references..." or "legal context provided"
  × any mention of "context", "database", "dataset", or how the system works internally
- If a retrieved section number looks wrong or the context is irrelevant, SILENTLY IGNORE it. Just don't mention it.
- Always respond as if you are a knowledgeable lawyer having a conversation — NOT a system reading from a database.
- Your responses should look like they come from a legal expert, not a search engine.
"""

def call_sarvam(messages):
    """Call Sarvam API with auto key rotation on rate limit."""
    global current_key_index
    attempts = len(SARVAM_API_KEYS)

    for _ in range(attempts):
        key = SARVAM_API_KEYS[current_key_index]
        try:
            response = requests.post(
                "https://api.sarvam.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sarvam-m",
                    "messages": messages,
                    "max_tokens": 1200,
                    "temperature": 0.3,
                },
                timeout=120
            )

            # Rate limit hit → rotate to next key
            if response.status_code == 429:
                current_key_index = (current_key_index + 1) % len(SARVAM_API_KEYS)
                continue

            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]
            cleaned = clean_response(raw)
            if not cleaned or len(cleaned.strip()) < 5:
                return "⚠️ Model returned an empty response. Please rephrase your question."
            return cleaned

        except requests.exceptions.Timeout:
            # Timeout → try next key
            current_key_index = (current_key_index + 1) % len(SARVAM_API_KEYS)
            continue
        except Exception as e:
            return f"⚠️ API error: {str(e)}"

    return "⚠️ All API keys have hit their limit. Please wait a while and try again."

# ─────────────────────────────────────────
#  SENSITIVE TOPIC DETECTION
# ─────────────────────────────────────────
SENSITIVE_KEYWORDS = [
    "rape", "बलात्कार", "assault", "sexual", "molest", "chedh", "छेड़",
    "shoshan", "शोषण", "maar", "मार", "kill", "murder", "हत्या",
    "suicide", "आत्महत्या", "abuse", "domestic violence", "marpit",
    "मारपीट", "threatened", "dhamki", "धमकी", "kidnap", "अपहरण",
    "dar", "डर", "attacked", "hamla", "हमला", "harassment", "torture",
    "beaten", "pita", "पीटा", "raped", "stalking", "blackmail",
    "trafficking", "death", "maut", "मौत", "zyadti", "ज़्यादती",
    "hatya", "dongathanam", "chori", "theft",
]

def is_sensitive(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SENSITIVE_KEYWORDS)

# ─────────────────────────────────────────
#  CLEAN HISTORY
# ─────────────────────────────────────────
def clean_history(chat_history):
    """Remove injected RAG context from past user messages."""
    cleaned = []
    for msg in chat_history:
        if msg["role"] == "user":
            content = msg["content"]
            if "[LEGAL CONTEXT FROM DATABASE]" in content:
                content = content.split("[LEGAL CONTEXT FROM DATABASE]")[0].strip()
            cleaned.append({"role": "user", "content": content})
        else:
            content = msg["content"][:600] if len(msg.get("content", "")) > 600 else msg.get("content", "")
            cleaned.append({"role": "assistant", "content": content})
    return cleaned[-6:]

# ─────────────────────────────────────────
#  MAIN CHATBOT FUNCTION
# ─────────────────────────────────────────
def legal_chatbot(query, chat_history=None):
    if chat_history is None:
        chat_history = []

    # 0. Detect news/update queries — skip RAG entirely (no context to hallucinate from)
    news_keywords = ["latest", "recent", "update", "news", "today", "yesterday",
                     "aaj", "kal", "khabar", "taaza", "naya", "current",
                     "last 24", "this week", "this month", "2025", "2026"]
    query_lower = query.lower()
    is_news_query = any(kw in query_lower for kw in news_keywords)

    if is_news_query:
        # No RAG, no context — let the model answer honestly from its honesty rules
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(clean_history(chat_history))
        messages.append({"role": "user", "content": f"""{query}

This is a question about recent news or updates. You do NOT have access to real-time data.
Be honest that you cannot provide real-time updates. Instead, briefly explain what the IPC → BNS transition is about and offer to help with specific legal questions."""})
        return call_sarvam(messages)

    # 1. RAG — retrieve legal context (only augment for legal queries)
    legal_keywords = ["section", "ipc", "bns", "law", "punishment", "crime",
                      "fir", "police", "court", "saza", "kanoon", "dhara",
                      "arrest", "bail", "murder", "theft", "rape", "assault",
                      "divorce", "property", "dowry", "violence", "chori",
                      "maar", "hatya", "case"]
    is_legal_query = any(kw in query_lower for kw in legal_keywords)

    if is_legal_query:
        augmented = query + " IPC BNS India law section"
    else:
        augmented = query
    context = search(augmented, top_k=5)

    if context:
        context_text = " ".join([c[1] for c in context[:3]])
        ipc = extract_ipc_section(context_text)
        bns = get_bns_section(ipc)
        ipc_text = f"IPC Section {ipc}" if ipc else "Not identified"

        rag_context = f"""
[LEGAL CONTEXT FROM DATABASE]
{context_text[:800]}

IPC Section Identified: {ipc_text}
BNS Equivalent: {bns}
[END CONTEXT]
"""
    else:
        rag_context = "[No specific legal context found in database]"

    # 2. Government schemes — match relevant ones
    schemes = find_relevant_schemes(query)
    scheme_text = format_schemes(schemes)

    # 3. Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(clean_history(chat_history))

    # 4. Instruction based on sensitivity
    if is_sensitive(query):
        instruction = """IMPORTANT: This person is sharing a traumatic/distressing experience.
You MUST start with genuine empathy and comfort FIRST.
THEN gently explain legal rights (show both IPC old section and BNS new section).
Mention any government schemes from context that can help them.
Include helpline numbers. Be human and caring."""
    else:
        instruction = """Show both IPC (old) and BNS (new) sections with what changed.
If government schemes are listed, mention them.
Do NOT show any thinking or reasoning."""

    user_message = f"""{query}

{rag_context}
{scheme_text}

{instruction}"""

    messages.append({"role": "user", "content": user_message})
    return call_sarvam(messages)


def legal_assistant(query):
    return legal_chatbot(query)
