import streamlit as st
from google import genai
import requests
import json
import random
from streamlit.components.v1 import html
import logging
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(levelname)s - %(message)s",
force=True
)

html(
"""
<script>
try {
const sel = window.top.document.querySelectorAll('[href*="streamlit.io"], [href*="streamlit.app"]');
sel.forEach(e => e.style.display='none');
} catch(e) {}
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
page_title="AI Learner",
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

api_keys = dict(random.sample(list(api_keys.items()), len(api_keys)))

YOUTUBE_API_KEY = safe_get_secret("youtube", "YouTube API Key")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")

# ================= KEY ROTATION =================
def get_key_rotation_list():
    return list(api_keys.values())

def gemini_generate(key, prompt):

    client = genai.Client(api_key=key)

    response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt
    )

    return response.text


def generate_with_key_rotation(prompt):

    keys = get_key_rotation_list()

    for key in keys:
        try:
            return gemini_generate(key, prompt)
        except Exception:
            continue

    return "⚠️ All API keys failed or quota exceeded."


def decide_with_key_rotation(prompt):

    keys = get_key_rotation_list()

    for key in keys:
        try:
            text = gemini_generate(key, prompt)
            return json.loads(text)
        except Exception:
            continue

    return None

# ================= SESSION =================
st.session_state.setdefault("learning_plan","")
st.session_state.setdefault("history",[])
st.session_state.setdefault("resource_decision",{})
st.session_state.setdefault("videos",[])
st.session_state.setdefault("repos",[])
st.session_state.setdefault("case_studies","")
st.session_state.setdefault("practice","")
st.session_state.setdefault("reading","")

# ================= YOUTUBE =================
def search_youtube(query,max_results=20):

    if not YOUTUBE_API_KEY:
        return []

    try:

        url="https://www.googleapis.com/youtube/v3/search"

        params={
        "part":"snippet",
        "q":query,
        "key":YOUTUBE_API_KEY,
        "maxResults":max_results,
        "type":"video"
        }

        r=requests.get(url,params=params,timeout=10)
        r.raise_for_status()

        return [
        (i["snippet"]["title"],
        f"https://www.youtube.com/watch?v={i['id']['videoId']}")
        for i in r.json().get("items",[])
        ]

    except Exception:
        return []

# ================= GITHUB =================
def search_github(query,max_results=15):

    try:

        url="https://api.github.com/search/repositories"

        headers={"Accept":"application/vnd.github+json"}

        if GITHUB_TOKEN:
            headers["Authorization"]=f"token {GITHUB_TOKEN}"

        params={
        "q":query,
        "sort":"stars",
        "order":"desc",
        "per_page":max_results
        }

        r=requests.get(url,headers=headers,params=params,timeout=10)
        r.raise_for_status()

        return [
        {
        "name":item["full_name"],
        "url":item["html_url"],
        "description":item["description"] or "No description"
        }
        for item in r.json().get("items",[])
        ]

    except Exception:
        return []

# ================= AI LOGIC =================
def decide_resources(goal,style):

    prompt=f"""
Decide required resources for learning.

Goal: {goal}
Learning style: {', '.join(style)}

Return JSON with:
use_github, use_case_studies, use_practice, use_reading_guides
"""

    result=decide_with_key_rotation(prompt)

    if not isinstance(result,dict):
        result={}

    return{
    "use_github":result.get("use_github",True),
    "use_case_studies":result.get("use_case_studies",True),
    "use_practice":result.get("use_practice",True),
    "use_reading_guides":result.get("use_reading_guides",True),
    }

def generate_learning_plan(context):

    prompt=f"""
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

# ================= PDF =================
def create_pdf():

    buffer=BytesIO()

    doc=SimpleDocTemplate(buffer,pagesize=letter)
    styles=getSampleStyleSheet()

    story=[]

    story.append(Paragraph("AI Learner Report",styles["Title"]))
    story.append(Spacer(1,20))

    story.append(Paragraph("Learning Plan",styles["Heading2"]))

    for line in st.session_state.learning_plan.split("\n"):
        story.append(Paragraph(line,styles["Normal"]))
        story.append(Spacer(1,5))

    story.append(Spacer(1,20))
    story.append(Paragraph("Recommended Videos",styles["Heading2"]))

    for title,link in st.session_state.videos:
        story.append(
        Paragraph(
        f'<link href="{link}">{title}</link>',
        styles["Normal"]
        )
        )

    story.append(Spacer(1,20))
    story.append(Paragraph("GitHub Projects",styles["Heading2"]))

    for repo in st.session_state.repos:

        story.append(
        Paragraph(
        f'<link href="{repo["url"]}">{repo["name"]}</link>',
        styles["Normal"]
        )
        )

        story.append(Paragraph(repo["description"],styles["Normal"]))
        story.append(Spacer(1,10))

    if st.session_state.case_studies:

        story.append(Paragraph("Case Studies",styles["Heading2"]))

        for line in st.session_state.case_studies.split("\n"):
            story.append(Paragraph(line,styles["Normal"]))

    if st.session_state.practice:

        story.append(Paragraph("Practice Exercises",styles["Heading2"]))

        for line in st.session_state.practice.split("\n"):
            story.append(Paragraph(line,styles["Normal"]))

    if st.session_state.reading:

        story.append(Paragraph("Reading Guide",styles["Heading2"]))

        for line in st.session_state.reading.split("\n"):
            story.append(Paragraph(line,styles["Normal"]))

    doc.build(story)

    buffer.seek(0)

    return buffer

# ================= UI =================
st.title("🎓 AI Learner")
st.caption("Gemini • YouTube • Adaptive Resources")
st.divider()

with st.form("onboarding"):

    goal=st.text_input("🎯 Learning Goal")

    level=st.selectbox(
    "📊 Current Level",
    ["Beginner","Intermediate","Advanced"]
    )

    time_per_day=st.slider("⏱️ Daily Time",30,180,60)

    duration=st.selectbox(
    "📆 Duration",
    ["1 Month","3 Months","6 Months"]
    )

    style=st.multiselect(
    "🎧 Style",
    ["Videos","Articles","Hands-on Projects"],
    default=["Videos"]
    )

    submitted=st.form_submit_button("🚀 Generate")

# ================= GENERATION =================
if submitted and goal:

    context=f"""
Goal: {goal}
Level: {level}
Time: {time_per_day}
Duration: {duration}
Style: {', '.join(style)}
"""

    with st.spinner("🧠 Generating..."):

        st.session_state.learning_plan=generate_learning_plan(context)

        st.session_state.resource_decision=decide_resources(goal,style)

        st.session_state.history.append(st.session_state.learning_plan)

        st.session_state.videos=search_youtube(goal)

        st.session_state.repos=search_github(goal)

        st.session_state.case_studies=simple_llm(f"Give 3 case studies about {goal}")

        st.session_state.practice=simple_llm(f"Create 5 exercises for {goal}")

        st.session_state.reading=simple_llm(f"Create reading guide for {goal}")

# ================= DISPLAY =================
if st.session_state.learning_plan:

    st.subheader("📘 Your Learning Plan")
    st.markdown(st.session_state.learning_plan)
    st.divider()

    st.subheader("📺 Recommended Videos")

    for title,link in st.session_state.videos:
        st.markdown(f"- [{title}]({link})")

    if st.session_state.resource_decision.get("use_github",True):

        st.subheader("💻 GitHub Projects")

        if st.session_state.repos:

            for repo in st.session_state.repos:

                st.markdown(
                f"- **[{repo['name']}]({repo['url']})**  \n_{repo['description']}_"
                )

        else:
            st.info("No GitHub repositories found.")

    if st.session_state.resource_decision.get("use_case_studies",True):

        st.subheader("📚 Case Studies")
        st.markdown(st.session_state.case_studies)

    if st.session_state.resource_decision.get("use_practice",True):

        st.subheader("🧪 Practice")
        st.markdown(st.session_state.practice)

    if st.session_state.resource_decision.get("use_reading_guides",True):

        st.subheader("📖 Reading Guide")
        st.markdown(st.session_state.reading)

    st.divider()

# ================= DOWNLOAD PDF =================
if st.session_state.learning_plan:

    st.download_button(
    label="📥 Download Full Learning Report PDF",
    data=create_pdf(),
    file_name="AI_Learner_Report.pdf",
    mime="application/pdf"
    )

# ================= HISTORY =================
with st.expander("🗂️ History"):

    for i,h in enumerate(st.session_state.history):

        st.markdown(f"### Version {i+1}")
        st.markdown(h)
        st.divider()