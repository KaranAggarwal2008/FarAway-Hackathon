import streamlit as st
from groq import Groq
from transformers import pipeline
import json

# Initialize
st.set_page_config(page_title="Mental Wellness Companion", page_icon="🌟")

# Crisis resources
CRISIS_RESOURCES = """
🚨 **If you're in crisis:**
- Call 988 (Suicide & Crisis Lifeline)
- Text HOME to 741741 (Crisis Text Line)
- Call 911 for emergencies
"""

# Initialize emotion analyzer
@st.cache_resource
def load_emotion_model():
    return pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

emotion_analyzer = load_emotion_model()

# Initialize Groq client
groq_api_key = st.secrets.get("GROQ_API_KEY", "")
if groq_api_key:
    groq_client = Groq(api_key=groq_api_key)
else:
    groq_client = None

# Crisis keywords
CRISIS_KEYWORDS = {
    "critical": ["suicide", "kill myself", "end my life", "want to die", "overdose"],
    "elevated": ["self harm", "hurt myself", "cutting", "worthless", "hopeless"]
}

def detect_crisis(text):
    text_lower = text.lower()
    for keyword in CRISIS_KEYWORDS["critical"]:
        if keyword in text_lower:
            return "CRITICAL"
    for keyword in CRISIS_KEYWORDS["elevated"]:
        if keyword in text_lower:
            return "ELEVATED"
    return "LOW"

def analyze_emotion(text):
    results = emotion_analyzer(text)[0]
    top_emotion = max(results, key=lambda x: x['score'])
    return top_emotion['label'], top_emotion['score']

def get_cbt_technique(emotion):
    techniques = {
        "sadness": "**Behavioral Activation**: Do one small enjoyable activity today.",
        "anger": "**Cognitive Restructuring**: What evidence challenges this thought?",
        "fear": "**Exposure**: Face your fear in small, manageable steps.",
        "anxiety": "**Worry Time**: Schedule 15 minutes to worry, then let it go."
    }
    return techniques.get(emotion.lower(), "**Mindfulness**: Take 5 deep breaths, focus on the present.")

def get_dbt_skill(emotion):
    skills = {
        "anger": "**TIPP**: Intense exercise for 20 minutes to reduce intensity.",
        "sadness": "**Self-Soothe**: Engage your 5 senses with something comforting.",
        "fear": "**Opposite Action**: Do the opposite of what fear tells you.",
        "anxiety": "**DEAR MAN**: Express your needs assertively."
    }
    return skills.get(emotion.lower(), "**Mindfulness**: Observe your thoughts without judgment.")

def generate_response(user_message, emotion, emotion_score, crisis_level):
    if not groq_client:
        return "⚠️ Please add your GROQ_API_KEY to Streamlit secrets."
    
    system_prompt = f"""You are a supportive mental wellness companion (NOT a licensed therapist).
    
Current user emotion: {emotion} (confidence: {emotion_score:.2f})
Crisis level: {crisis_level}

Provide empathetic, evidence-based support. Keep responses under 150 words.
If crisis level is CRITICAL/ELEVATED, emphasize professional help strongly.
DO NOT diagnose or replace professional treatment."""

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=300
    )
    
    return chat_completion.choices[0].message.content

# UI
st.title("🌟 Mental Wellness Companion")
st.caption("⚠️ This is NOT a replacement for professional therapy")

# Sidebar
with st.sidebar:
    st.markdown(CRISIS_RESOURCES)
    st.markdown("---")
    st.markdown("**Free Resources:**")
    st.markdown("- Groq API (LLM)")
    st.markdown("- Hugging Face (Emotion)")
    st.markdown("- Streamlit Cloud (Hosting)")

# Initialize chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("How are you feeling today?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Analyze
    emotion, emotion_score = analyze_emotion(prompt)
    crisis_level = detect_crisis(prompt)
    
    # Handle crisis
    if crisis_level in ["CRITICAL", "ELEVATED"]:
        crisis_message = f"""🚨 **I'm concerned about your safety.**

{CRISIS_RESOURCES}

I'm here to support you, but please reach out to a professional immediately."""
        st.session_state.messages.append({"role": "assistant", "content": crisis_message})
        with st.chat_message("assistant"):
            st.error(crisis_message)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt, emotion, emotion_score, crisis_level)
            
            # Add techniques
            full_response = f"""{response}

---
**Detected Emotion:** {emotion} ({emotion_score:.0%} confidence)

**CBT Technique:**
{get_cbt_technique(emotion)}

**DBT Skill:**
{get_dbt_skill(emotion)}"""
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
