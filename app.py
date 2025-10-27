import streamlit as st
from streamlit.components.v1 import html

# --- Hide Streamlit Branding ---
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

st.set_page_config(
    page_title="Explore AI",
    page_icon="🌐",
    initial_sidebar_state="expanded",
    layout="wide"
)

# --- Hide Streamlit default UI ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stToolbar"] {display: none;}
a[href^="https://github.com"], a[href^="https://streamlit.io"] {display: none !important;}
header > div:nth-child(2) {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Modern Dashboard CSS ---
dashboard_css = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #1e3c72, #2a5298);
    color: #fff;
    font-family: 'Poppins', sans-serif;
}

/* Grid layout */
.tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    padding: 1rem 2rem;
    justify-items: center;
}

/* Tool Card */
.tool-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    backdrop-filter: blur(10px);
    padding: 1.2rem;
    width: 100%;
    max-width: 380px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    transition: all 0.3s ease-in-out;
}
.tool-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
}

/* Button inside each card */
a.tool-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.7rem;
    padding: 0.9rem;
    border-radius: 14px;
    color: white !important;
    font-size: 1.1rem;
    font-weight: 600;
    text-decoration: none !important;
    box-shadow: 0 6px 14px rgba(0,0,0,0.25);
    transition: all 0.3s ease-in-out;
}
a.tool-button:hover {
    transform: scale(1.04);
}

/* Gradients */
.audio-story { background: linear-gradient(135deg, #ff6a00, #ee0979); }
.text2audio  { background: linear-gradient(135deg, #36d1dc, #5b86e5); }
.singify     { background: linear-gradient(135deg, #11998e, #38ef7d); }
.aipodcast   { background: linear-gradient(135deg, #fc5c7d, #6a82fb); }
.csv         { background: linear-gradient(135deg, #ff9966, #ff5e62); }

/* SVG Icons */
a.tool-button svg {
    width: 26px;
    height: 26px;
    fill: white;
}

/* Description */
.tool-desc {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.85);
    margin-top: 0.6rem;
    line-height: 1.4;
}

/* Gradient Title */
h1 {
    text-align: center;
    font-size: 2.6rem !important;
    font-weight: 800 !important;
    margin-top: 0.5rem;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Responsive tweak for small screens */
@media (max-width: 600px) {
    .tools-grid {
        grid-template-columns: 1fr;
        padding: 1rem;
    }
}
</style>
"""
st.markdown(dashboard_css, unsafe_allow_html=True)

# ---- Page Title ----
st.title("🌐 Explore AI")

# ---- Tool Data ----
tools = [
    {
        "name": "🎧 AUDIO STORY",
        "desc": "Generate immersive, AI-narrated stories with dynamic voices and emotions.",
        "link": "https://exploreai.streamlit.app/audiostory",
        "class": "audio-story",
        "icon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 3v10.55a4 4 0 0 0 2 3.45V21a9 9 0 0 1-9-9h2a7 7 0 0 0 7 7v-3.55a4 4 0 0 0 0-7.9V3z"/></svg>"""
    },
    {
        "name": "🗣️ TEXT 2 AUDIO",
        "desc": "Convert written text into natural-sounding speech in seconds.",
        "link": "https://exploreai.streamlit.app/text2audio",
        "class": "text2audio",
        "icon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 10v4a1 1 0 0 0 1 1h3l3 3V6L7 9H4a1 1 0 0 0-1 1zM16 12a4 4 0 0 0-4-4v8a4 4 0 0 0 4-4zm3 0a7 7 0 0 0-7-7v2a5 5 0 0 1 5 5 5 5 0 0 1-5 5v2a7 7 0 0 0 7-7z"/></svg>"""
    },
    {
        "name": "🎵 SINGIFY",
        "desc": "Turn any text or lyrics into melodic AI-generated singing voices.",
        "link": "https://exploreai.streamlit.app/singify",
        "class": "singify",
        "icon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M9 3v12.563A4 4 0 1 0 11 19V8h8v7.563A4 4 0 1 0 21 19V3H9z"/></svg>"""
    },
    {
        "name": "🎙️ AI PODCAST",
        "desc": "Create podcast-style conversations between realistic AI voices.",
        "link": "https://exploreai.streamlit.app/aipodcast",
        "class": "aipodcast",
        "icon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3zM5 10v1a7 7 0 0 0 14 0v-1h-2v1a5 5 0 0 1-10 0v-1H5zM12 22a10 10 0 0 0 10-10h-2a8 8 0 0 1-16 0H2a10 10 0 0 0 10 10z"/></svg>"""
    },
    {
        "name": "📊 CSV ANALYSIS",
        "desc": "Upload and visualize CSV files with intelligent insights and charts.",
        "link": "https://csvvisualisation.streamlit.app",
        "class": "csv",
        "icon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 3h18v18H3V3zm4 4v10h2V7H7zm4 4v6h2v-6h-2zm4-2v8h2V9h-2z"/></svg>"""
    },
]

# ---- Render the grid ----
html_content = '<div class="tools-grid">'
for tool in tools:
    html_content += f"""
        <div class="tool-card">
            <a href="{tool['link']}" class="tool-button {tool['class']}" target="_blank">
                {tool['icon']}<span>{tool['name']}</span>
            </a>
            <div class="tool-desc">{tool['desc']}</div>
        </div>
    """
html_content += "</div>"

st.markdown(html_content, unsafe_allow_html=True)