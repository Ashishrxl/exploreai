import streamlit as st
import google.generativeai as genai
import requests
import json
from streamlit.components.v1 import html


html(
  """
  <script>
  try {
    const sel = window.top.document.querySelectorAll('[href*="streamlit.io"], [href*="streamlit.app"]');
    sel.forEach(e => e.style.display='none');
  } catch(e) { console.warn('parent DOM not reachable', e); }
  </script>
  """,
  height=0
)

disable_footer_click = """
    <style>
    footer {pointer-events: none;}
    </style>
"""
st.markdown(disable_footer_click, unsafe_allow_html=True)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stToolbar"] {display: none;}
header a[href*="github"] {display:none;}
a[href^="https://streamlit.io"] {display: none !important;}
header > div:nth-child(2) { display: none; }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
        st.warning(f"⚠️ {label} missing")
        return None

api_keys = {
    f"Key {i}": safe_get_secret(f"KEY_{i}", f"Gemini API Key {i}")
    for i in range(1, 12)
}

api_keys = {k: v for k, v in api_keys.items() if v}

selected_key_name = st.selectbox(
    "Select Key",
    list(api_keys.keys()) if api_keys else ["No API Keys Available"]
)

YOUTUBE_API_KEY = safe_get_secret("youtube", "YouTube API Key")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")

# ================= KEY ROTATION =================
def get_key_rotation_list():
    keys = list(api_keys.values())
    if not keys:
        return []

    selected_value = api_keys.get(selected_key_name)
    if selected_value in keys:
        idx = keys.index(selected_value)
        return keys[idx:] + keys[:idx]

    return keys

def generate_with_key_rotation(prompt):
    keys = get_key_rotation_list()

    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash-lite")

            if i > 0:
                st.info("🔄 Switched to backup API key")

            return model.generate_content(prompt).text

        except Exception:
            continue

    return "⚠️ All API keys failed or quota exceeded."

def decide_with_key_rotation(prompt):
    keys = get_key_rotation_list()

    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash-lite")

            if i > 0:
                st.info("🔄 Switched to backup API key")

            return json.loads(model.generate_content(prompt).text)

        except Exception:
            continue

    return None

# ================= SESSION =================
st.session_state.setdefault("learning_plan", "")
st.session_state.setdefault("history", [])
st.session_state.setdefault("resource_decision", {})

# ================= YOUTUBE =================
def search_youtube(query, max_results=20):
    if not YOUTUBE_API_KEY:
        return []

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results,
            "type": "video"
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        return [
            (i["snippet"]["title"],
             f"https://www.youtube.com/watch?v={i['id']['videoId']}")
            for i in r.json().get("items", [])
        ]
    except Exception:
        return []

# ================= GITHUB =================
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

        return [
            {
                "name": item["full_name"],
                "url": item["html_url"],
                "description": item["description"] or "No description"
            }
            for item in r.json().get("items", [])
        ]

    except Exception:
        return []

# ================= AI LOGIC =================
def decide_resources(goal, style):

    prompt = f"""
Decide required resources for learning.

Goal: {goal}
Learning style: {', '.join(style)}

Return JSON with:
use_github, use_case_studies, use_practice, use_reading_guides
"""

    result = decide_with_key_rotation(prompt)

    if not isinstance(result, dict):
        result = {}

    return {
        "use_github": result.get("use_github", True),
        "use_case_studies": result.get("use_case_studies", True),
        "use_practice": result.get("use_practice", True),
        "use_reading_guides": result.get("use_reading_guides", True),
    }

def generate_learning_plan(context):
    prompt = f"""
Create a personalized learning plan with:
- Weekly roadmap
- Daily tasks
- Topics to search on YouTube
- Practice projects

Context:
{context}
"""
    return generate_with_key_rotation(prompt)

def simple_llm(prompt):
    return generate_with_key_rotation(prompt)

# ================= UI =================
st.title("🎓 AI-Personalized Learning Path Generator")
st.caption("Gemini • YouTube • Adaptive Resources")
st.divider()

# ================= FORM =================
with st.form("onboarding"):
    goal = st.text_input("🎯 Learning Goal")
    level = st.selectbox("📊 Current Level",
                         ["Beginner", "Intermediate", "Advanced"])
    time_per_day = st.slider("⏱️ Daily Time", 30, 180, 60)
    duration = st.selectbox("📆 Duration",
                            ["1 Month", "3 Months", "6 Months"])
    style = st.multiselect(
        "🎧 Style",
        ["Videos", "Articles", "Hands-on Projects"],
        default=["Videos"]
    )

    submitted = st.form_submit_button("🚀 Generate")

# ================= GENERATION =================
if submitted and goal:
    context = f"""
Goal: {goal}
Level: {level}
Time: {time_per_day}
Duration: {duration}
Style: {', '.join(style)}
"""

    with st.spinner("🧠 Generating..."):
        st.session_state.learning_plan = generate_learning_plan(context)
        st.session_state.resource_decision = decide_resources(goal, style)
        st.session_state.history.append(st.session_state.learning_plan)

# ================= DISPLAY =================
if st.session_state.learning_plan:
    st.subheader("📘 Your Learning Plan")
    st.markdown(st.session_state.learning_plan)
    st.divider()

    # YouTube
    st.subheader("📺 Recommended Videos")
    for title, link in search_youtube(goal):
        st.markdown(f"- [{title}]({link})")

    # GitHub (Guaranteed Show)
    if st.session_state.resource_decision.get("use_github", True):
        st.subheader("💻 GitHub Projects")
        repos = search_github(goal)

        if repos:
            for repo in repos:
                st.markdown(
                    f"- **[{repo['name']}]({repo['url']})**  \n_{repo['description']}_"
                )
        else:
            st.info("No GitHub repositories found.")

    # Case Studies
    if st.session_state.resource_decision.get("use_case_studies", True):
        st.subheader("📚 Case Studies")
        st.markdown(simple_llm(f"Give 3 case studies about {goal}"))

    # Practice
    if st.session_state.resource_decision.get("use_practice", True):
        st.subheader("🧪 Practice")
        st.markdown(simple_llm(f"Create 5 exercises for {goal}"))

    # Reading
    if st.session_state.resource_decision.get("use_reading_guides", True):
        st.subheader("📖 Reading Guide")
        st.markdown(simple_llm(f"Create reading guide for {goal}"))

    st.divider()

# ================= HISTORY =================
with st.expander("🗂️ History"):
    for i, h in enumerate(st.session_state.history):
        st.markdown(f"### Version {i+1}")
        st.markdown(h)
        st.divider()