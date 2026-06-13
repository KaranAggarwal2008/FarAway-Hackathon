import streamlit as st
from groq import Groq
from textblob import TextBlob

# Initialize
st.set_page_config(page_title="Mental Wellness Companion", page_icon="🌟")

# Crisis resources
CRISIS_RESOURCES = """
🚨 **If you're in crisis:**
- Call 988 (Suicide & Crisis Lifeline)
- Text HOME to 741741 (Crisis Text Line)
- Call 911 for emergencies
"""

# Initialize Groq client
groq_api_key = st.secrets.get("GROQ_API_KEY", "")
if groq_api_key:
    groq_client = Groq(api_key=groq_api_key)
else:
    groq_client = None

# Crisis keywords
# Crisis keywords
CRISIS_KEYWORDS = {
    "critical": [
        "suicide", "kill myself", "end my life", "want to die", "overdose", 
        "not worth living", "better off dead", "no reason to live"
    ],
    "elevated": [
        "self harm", "hurt myself", "cutting", "worthless", "hopeless", 
        "can't go on", "want to disappear"
    ],
    "medical_emergency": [
        "heart attack", "chest pain", "can't breathe", "stroke", 
        "seizure", "overdosed", "poisoned", "heavy bleeding"
    ]
}

def detect_crisis(text):
    text_lower = text.lower()
    
    # Check medical emergencies first
    for keyword in CRISIS_KEYWORDS["medical_emergency"]:
        if keyword in text_lower:
            return "MEDICAL_EMERGENCY"
    
    for keyword in CRISIS_KEYWORDS["critical"]:
        if keyword in text_lower:
            return "CRITICAL"
    
    for keyword in CRISIS_KEYWORDS["elevated"]:
        if keyword in text_lower:
            return "ELEVATED"
    
    return "LOW"

def analyze_emotion(text):
    """Analyze emotion using TextBlob sentiment analysis"""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Map polarity to emotions
    if polarity < -0.3:
        emotion = "sadness"
    elif polarity > 0.3:
        emotion = "joy"
    elif subjectivity > 0.6 and polarity < 0:
        emotion = "anxiety"
    elif subjectivity > 0.6 and polarity > 0:
        emotion = "excitement"
    else:
        emotion = "neutral"
    
    confidence = abs(polarity)
    return emotion, confidence

def get_cbt_technique(emotion):
    techniques = {
        "sadness": "**Behavioral Activation**: Do one small enjoyable activity today (walk, music, call a friend).",
        "anger": "**Cognitive Restructuring**: What evidence challenges this thought? Is there another way to see this?",
        "anxiety": "**Worry Time**: Schedule 15 minutes to worry, then let it go. Use grounding: 5 things you see, 4 you touch, 3 you hear.",
        "joy": "**Savor the Moment**: Take a mental snapshot of this positive feeling to recall later.",
        "neutral": "**Mindfulness**: Take 5 deep breaths, focus on the present moment."
    }
    return techniques.get(emotion.lower(), techniques["neutral"])

def get_dbt_skill(emotion):
    skills = {
        "anger": "**TIPP**: Temperature (cold water on face), Intense exercise (20 min), Paced breathing (slow & deep), Paired muscle relaxation.",
        "sadness": "**Self-Soothe**: Engage your 5 senses - listen to calming music, smell lavender, wrap in a soft blanket.",
        "anxiety": "**DEAR MAN**: Describe situation, Express feelings, Assert needs, Reinforce positive, stay Mindful, Appear confident, Negotiate.",
        "joy": "**Build Positive Experiences**: Make a list of activities that bring joy and schedule them.",
        "neutral": "**Mindfulness of Current Emotion**: Observe your thoughts without judgment, like clouds passing."
    }
    return skills.get(emotion.lower(), skills["neutral"])

def generate_response(user_message, emotion, emotion_score, crisis_level):
    if not groq_client:
        return "⚠️ Please add your GROQ_API_KEY to Streamlit secrets."
    
    system_prompt = f"""You are a supportive mental wellness companion (NOT a licensed therapist).

Current user emotion: {emotion} (confidence: {emotion_score:.2f})
Crisis level: {crisis_level}

Guidelines:
- Provide empathetic, evidence-based support
- Keep responses under 150 words
- If crisis level is CRITICAL/ELEVATED, emphasize professional help strongly
- DO NOT diagnose or replace professional treatment
- Use warm, validating language
- Offer hope and actionable steps"""

    try:
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
    except Exception as e:
        return f"⚠️ Error connecting to AI: {str(e)}"

# UI
st.title("🌟 Mental Wellness Companion")
st.caption("⚠️ This is NOT a replacement for professional therapy")

# Sidebar
with st.sidebar:
    st.markdown(CRISIS_RESOURCES)
    st.markdown("---")
    st.markdown("**How It Works:**")
    st.markdown("1. Share your feelings")
    st.markdown("2. Get AI support & techniques")
    st.markdown("3. Practice CBT/DBT skills")
    st.markdown("---")
    st.markdown("**Free Tools Used:**")
    st.markdown("- Groq AI (LLM)")
    st.markdown("- TextBlob (Sentiment)")
    st.markdown("- Streamlit Cloud (Hosting)")

# Initialize chat
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm here to support your mental wellness. How are you feeling today? 💙"
    }]

# Display chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Share your thoughts or feelings..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Analyze
    emotion, emotion_score = analyze_emotion(prompt)
    crisis_level = detect_crisis(prompt)
    
# Handle crisis
    if crisis_level == "MEDICAL_EMERGENCY":
        medical_message = f"""🚨 **MEDICAL EMERGENCY - CALL 911 NOW!**

If you're having a heart attack, stroke, or other medical emergency:
- **CALL 911 IMMEDIATELY**
- Do NOT wait
- Do NOT drive yourself

This is a mental wellness app and CANNOT help with medical emergencies.

**CALL 911 RIGHT NOW! ☎️**"""
        
        st.session_state.messages.append({"role": "assistant", "content": medical_message})
        with st.chat_message("assistant"):
            st.error(medical_message)
        st.stop()
    
    if crisis_level in ["CRITICAL", "ELEVATED"]:
        crisis_message = f"""🚨 **I'm genuinely concerned about your safety.**

{CRISIS_RESOURCES}

Your life matters. Please reach out to a professional immediately. I'm here to support you, but trained crisis counselors can provide the help you need right now. 💙"""
        
        st.session_state.messages.append({"role": "assistant", "content": crisis_message})
        with st.chat_message("assistant"):
            st.error(crisis_message)
        st.stop()

---
**💭 Detected Emotion:** {emotion.capitalize()} ({emotion_score:.0%} confidence)

**🧠 CBT Technique:**
{get_cbt_technique(emotion)}

**🎯 DBT Skill:**
{get_dbt_skill(emotion)}

---
*Remember: These are evidence-based coping strategies. For persistent difficulties, please consult a mental health professional.*"""
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# Footer
st.markdown("---")
st.caption("💙 Built with care • Not a substitute for professional mental health care")
