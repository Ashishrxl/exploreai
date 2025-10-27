import streamlit as st
from streamlit.components.v1 import html

# ---- Page Config ----
st.set_page_config(
    page_title="Explore AI",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---- Hide Streamlit Branding ----
hide_ui = """
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"], [data-testid="stStatusWidget"] {display: none !important;}
</style>
"""
st.markdown(hide_ui, unsafe_allow_html=True)

# ---- CSS + HTML ----
page_css = """
<style>
html, body, .stApp {
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #1e3c72, #2a5298);
    font-family: 'Poppins', sans-serif;
    overflow-x: hidden;
}

/* Remove Streamlit padding */
section.main > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Wrapper fills screen height */
.wrapper {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center; /* centers vertically */
    align-items: center;
    box-sizing: border-box;
}

/* Title */
.title {
    text-align: center;
    font-size: 2.5rem;
    font-weight: 800;
    margin: 2rem 0 1.5rem 0;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Grid layout */
.tools {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
    gap: 1.6rem;
    padding: 1rem;
    justify-items: center;
}

/* Card */
.card {
    background: rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1.3rem 1rem;
    width: 100%;
    max-width: 360px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    backdrop-filter: blur(10px);
    transform: translateY(40px);
    opacity: 0;
    transition: all 0.8s ease;
}
.card.visible {
    transform: translateY(0);
    opacity: 1;
}
.card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 8px 25px rgba(0,0,0,0.35);
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.9rem;
    width: 90%;
    border-radius: 14px;
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
    text-decoration: none;
    gap: 0.6rem;
    box-shadow: 0 6px 14px rgba(0,0,0,0.25);
    transition: all 0.25s ease-in-out;
}
.btn:hover { transform: scale(1.05); }

/* Gradients */
.audio-story { background: linear-gradient(135deg, #ff6a00, #ee0979); }
.text2audio  { background: linear-gradient(135deg, #36d1dc, #5b86e5); }
.singify     { background: linear-gradient(135deg, #11998e, #38ef7d); }
.aipodcast   { background: linear-gradient(135deg, #fc5c7d, #6a82fb); }
.csv         { background: linear-gradient(135deg, #ff9966, #ff5e62); }

/* Description */
.desc {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.85);
    margin-top: 0.8rem;
    line-height: 1.4;
}

/* Force background fill */
body {
    min-height: 100vh;
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-size: cover;
    overscroll-behavior: none;
}

/* Mobile tweaks */
@media (max-width: 600px) {
    .title { font-size: 2rem; margin: 1.5rem 0 1rem 0; }
    .btn { font-size: 1rem; }
    .tools { padding-bottom: 1.5rem; }
}
</style>

<script>
document.addEventListener("DOMContentLoaded", function() {
  // Animate cards
  const cards = document.querySelectorAll('.card');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) entry.target.classList.add('visible');
    });
  }, { threshold: 0.1 });
  cards.forEach(card => observer.observe(card));

  // Resize Streamlit frame height dynamically
  const resizeObserver = new ResizeObserver(() => {
    const height = Math.max(document.body.scrollHeight, window.innerHeight);
    window.parent.postMessage({ streamlitResizeFrame: height }, "*");
  });
  resizeObserver.observe(document.body);
});
</script>
"""

page_html = """
<div class="wrapper">
  <div class="title">🌐 Explore AI</div>

  <div class="tools">

    <div class="card">
      <a href="https://exploreai.streamlit.app/audiostory" target="_blank" class="btn audio-story">
        🎧 <span>AUDIO STORY</span>
      </a>
      <div class="desc">Generate immersive, AI-narrated stories with dynamic voices and emotions.</div>
    </div>

    <div class="card">
      <a href="https://exploreai.streamlit.app/text2audio" target="_blank" class="btn text2audio">
        🗣️ <span>TEXT 2 AUDIO</span>
      </a>
      <div class="desc">Convert written text into natural-sounding speech in seconds.</div>
    </div>

    <div class="card">
      <a href="https://exploreai.streamlit.app/singify" target="_blank" class="btn singify">
        🎵 <span>SINGIFY</span>
      </a>
      <div class="desc">Turn any text or lyrics into melodic AI-generated singing voices.</div>
    </div>

    <div class="card">
      <a href="https://exploreai.streamlit.app/aipodcast" target="_blank" class="btn aipodcast">
        🎙️ <span>AI PODCAST</span>
      </a>
      <div class="desc">Create podcast-style conversations between realistic AI voices.</div>
    </div>

    <div class="card">
      <a href="https://csvvisualisation.streamlit.app" target="_blank" class="btn csv">
        📊 <span>CSV ANALYSIS</span>
      </a>
      <div class="desc">Upload and visualize CSV files with intelligent insights and charts.</div>
    </div>

  </div>
</div>
"""

# Dynamic full-height layout (no fixed height)
html(page_css + page_html, height=None, scrolling=False)