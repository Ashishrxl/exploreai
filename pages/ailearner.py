import streamlit as st
import google.generativeai as genai
import requests
import json
from streamlit.components.v1 import html

# ================= HIDE STREAMLIT UI =================
html("""
<script>
try {
  const sel = window.top.document.querySelectorAll(
    '[href*="streamlit.io"], [href*="streamlit.app"]'
  );
  sel.forEach(e => e.style.display='none');
} catch(e) {}
</script>
""", height=0)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI Learning Path Generator",
    page_icon="🎓",
    layout="centered"
)

# ================= API KEYS =================
def safe_get_secret(key_name, label):
    try:
        return st.secrets[key_name]
    except Exception:
        st.warning(f"⚠️ {label} is missing. Some features may not work.")
        return None

api_keys = {
    "Key 1": safe_get_secret("KEY_1", "Gemini API Key 1"),
    "Key 2": safe_get_secret("KEY_2", "Gemini API Key 2"),
    "Key 3": safe_get_secret("KEY_3", "Gemini API Key 3"),
    "Key 4": safe_get_secret("KEY_4", "Gemini API Key 4"),
    "Key 5": safe_get_secret("KEY_5", "Gemini API Key 5"),
    "Key 6": safe_get_secret("KEY_6", "Gemini API Key 6"),
    "Key 7": safe_get_secret("KEY_7", "Gemini API Key 7"),
    "Key 8": safe_get_secret("KEY_8", "Gemini API Key 8"),
    "Key 9": safe_get_secret("KEY_9", "Gemini API Key 9"),
    "Key 10": safe_get_secret("KEY_10", "Gemini API Key 10"),
    "Key 11": safe_get_secret("KEY_11", "Gemini API Key 11"),
}

api_keys = {k: v for k, v in api_keys.items() if v}

selected_key_name = st.selectbox(
    "Select Key",
    list(api_keys.keys()) if api_keys else ["No API Keys Available"]
)

GOOGLE_API_KEY = api_keys.get(selected_key_name)
YOUTUBE_API_KEY = safe_get_secret("youtube", "YouTube API Key")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)

if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
    except Exception:
        model = None
        st.info("🤖 AI model is temporarily unavailable.")
else:
    model = None

# ================= SESSION STATE =================
st.session_state.setdefault("learning_plan", "")
st.session_state.setdefault("history", [])
st.session_state.setdefault("resource_decision", {})

# ================= API HELPERS =================
def search_youtube(query, max_results=20):
    if not YOUTUBE_API_KEY:
        st.info("📺 YouTube recommendations are unavailable.")
        return []

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results,
            "type": "video",
            "relevanceLanguage": "en"
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return [
            (i["snippet"]["title"], f"https://www.youtube.com/watch?v={i['id']['videoId']}")
            for i in r.json().get("items", [])
        ]
    except Exception:
        st.info("📺 Unable to load YouTube videos right now.")
        return []

def search_github(query, max_results=15):
    try:
        url = "https://api.github.com/search/repositories"
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results
        }

        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        return [
            {
                "name": item.get("full_name", "Unknown"),
                "url": item.get("html_url"),
                "description": item.get("description") or "No description available"
            }
            for item in data.get("items", [])
            if isinstance(item, dict)
        ]
    except Exception:
        st.info("💻 GitHub resources could not be loaded.")
        return []

# ================= AI LOGIC =================
def decide_resources(goal, style):
    if not model:
        return {
            "use_github": True,
            "use_case_studies": True,
            "use_practice": True,
            "use_reading_guides": True
        }

    try:
        prompt = f"""
Decide required resources for learning.

Goal: {goal}
Learning style: {', '.join(style)}

Return valid JSON only.
"""
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception:
        return {
            "use_github": "Hands-on Projects" in style,
            "use_case_studies": True,
            "use_practice": True,
            "use_reading_guides": True
        }

def generate_learning_plan(context):
    if not model:
        return "⚠️ AI learning plan generation is currently unavailable."

    try:
        prompt = f"""
Create a personalized learning plan with:
- Weekly roadmap
- Daily tasks (30–90 minutes)
- Topics to search on YouTube
- Practice or projects if relevant

Context:
{context}
"""
        return model.generate_content(prompt).text
    except Exception:
        return "⚠️ Unable to generate learning plan right now."

def simple_llm(prompt):
    if not model:
        return "ℹ️ AI content is temporarily unavailable."
    try:
        return model.generate_content(prompt).text
    except Exception:
        return "ℹ️ Content could not be generated at this time."

# ================= UI =================
st.title("🎓 AI-Personalized Learning Path Generator")
st.caption("Gemini • YouTube • Adaptive Resources")
st.divider()

# ================= FORM =================
with st.form("onboarding"):
    goal = st.text_input("🎯 Learning Goal", placeholder="Become a backend developer")
    level = st.selectbox("📊 Current Level", ["Beginner", "Intermediate", "Advanced"])
    time_per_day = st.slider("⏱️ Daily Time (minutes)", 30, 180, 60)
    duration = st.selectbox("📆 Target Duration", ["1 Month", "3 Months", "6 Months"])
    style = st.multiselect(
        "🎧 Preferred Learning Style",
        ["Videos", "Articles", "Hands-on Projects"],
        default=["Videos"]
    )

    submitted = st.form_submit_button("🚀 Generate Learning Plan")

# ================= GENERATION =================
if submitted and goal:
    context = f"""
Goal: {goal}
Level: {level}
Time per day: {time_per_day} minutes
Duration: {duration}
Learning style: {', '.join(style)}
"""
    with st.spinner("🧠 Generating learning plan..."):
        st.session_state.learning_plan = generate_learning_plan(context)
        st.session_state.resource_decision = decide_resources(goal, style)
        st.session_state.history.append(st.session_state.learning_plan)

# ================= DISPLAY =================
if st.session_state.learning_plan:
    st.subheader("📘 Your Learning Plan")
    st.markdown(st.session_state.learning_plan)
    st.divider()

    st.subheader("📺 Recommended YouTube Videos")
    for title, link in search_youtube(goal):
        st.markdown(f"- [{title}]({link})")

    if st.session_state.resource_decision.get("use_github"):
        st.subheader("💻 Recommended GitHub Projects")
        for repo in search_github(goal):
            st.markdown(f"- **[{repo['name']}]({repo['url']})**  \n_{repo['description']}_")

    if st.session_state.resource_decision.get("use_case_studies"):
        st.subheader("📚 Case Studies")
        st.markdown(simple_llm(f"Provide 3 short case studies for learning {goal}."))

    if st.session_state.resource_decision.get("use_practice"):
        st.subheader("🧪 Practice Exercises")
        st.markdown(simple_llm(f"Create 5 practice exercises for {goal}."))

    if st.session_state.resource_decision.get("use_reading_guides"):
        st.subheader("📖 Reading Guide")
        st.markdown(simple_llm(f"Create a structured reading guide for {goal}."))

    st.divider()

# ================= HISTORY =================
with st.expander("🗂️ Learning Plan History"):
    for i, version in enumerate(st.session_state.history):
        st.markdown(f"### Version {i+1}")
        st.markdown(version)
        st.divider()