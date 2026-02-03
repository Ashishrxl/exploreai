import streamlit as st
import io
import re
import wave
import base64
import time
import threading
import os
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from streamlit.components.v1 import html


# ---------------- UI CLEANUP ----------------
try:
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
except Exception as e:
    print("HTML injection warning:", e)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stToolbar"] {display: none;}
a[href^="https://github.com"] {display: none !important;}
a[href^="https://streamlit.io"] {display: none !important;}
header > div:nth-child(2) { display: none; }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# ---------------- CONFIG ----------------
GEMMA_MODEL = "gemma-3-12b-it"
TTS_MODEL = "gemini-2.5-flash-preview-tts"

st.set_page_config(page_title="AI Roleplay Story", layout="wide")
st.title("AI Roleplay Story Generator")


# ---------------- API KEYS ----------------
try:
    api_keys = {
        f"Key {i}": st.secrets[f"KEY_{i}"]
        for i in range(1, 12)
        if f"KEY_{i}" in st.secrets
    }

    if not api_keys:
        st.info("⚠️ API keys are not configured yet.")
    else:
        selected_key_name = st.selectbox("Select Key", list(api_keys.keys()))
        client = genai.Client(api_key=api_keys[selected_key_name])

except Exception as e:
    st.info("⚠️ Unable to initialize API connection. Please try again later.")
    print("API init error:", e)
    client = None


# ---------------- INPUTS ----------------
genres = [
    "Fantasy", "High Fantasy", "Epic Fantasy", "Urban Fantasy",
    "Science Fiction", "Space Opera", "Time Travel",
    "Mystery", "Adventure", "Comedy",
    "Historical Fiction", "Inspirational Fiction"
]

genre = st.selectbox("Select story genre", genres)
characters = st.text_area("List characters (comma separated)", "Dog, cat, lion")
length = st.selectbox("Story length", ["Short", "Medium", "Long"])
language = st.selectbox("Select story language", ["English", "Hindi", "Bhojpuri"])

voice_options = {
    "English": ["English Male", "English Female"],
    "Hindi": ["Hindi Male", "Hindi Female"],
    "Bhojpuri": ["Bhojpuri Male", "Bhojpuri Female"]
}
voice_choice = st.selectbox("Select voice", voice_options[language])
add_audio = st.checkbox("Generate audio of full story")


# ---------------- HELPERS ----------------
def safe_run(fn, user_msg="Something went wrong. Please try again."):
    try:
        return fn()
    except Exception as e:
        st.warning(user_msg)
        print("Error:", e)
        return None


def pcm_to_wav_bytes(pcm_bytes, channels=1, rate=24000, sample_width=2):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)
    buf.seek(0)
    return buf.read()


def map_voice(v):
    return "Charon" if "Male" in v else "Kore"


def map_language_code(lang):
    return {"English": "en-US", "Hindi": "hi-IN", "Bhojpuri": "hi-IN"}.get(lang, "en-US")


# ---------------- PDF ----------------
def generate_pdf_reportlab(text, title="AI Roleplay Story"):
    def _gen():
        buf = io.BytesIO()

        pdfmetrics.registerFont(TTFont("Latin", "NotoSans-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("Deva", "NotoSansDevanagari-Regular.ttf"))

        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Latin", fontName="Latin", fontSize=12))
        styles.add(ParagraphStyle(name="Deva", fontName="Deva", fontSize=12))

        def is_deva(t): return bool(re.search(r'[\u0900-\u097F]', t))

        story = [Paragraph(title, styles["Latin"]), Spacer(1, 12)]
        for line in text.split("\n"):
            if line.strip():
                style = styles["Deva"] if is_deva(line) else styles["Latin"]
                story.append(Paragraph(line, style))
                story.append(Spacer(1, 6))

        doc.build(story)
        buf.seek(0)
        return buf

    return safe_run(_gen, "⚠️ PDF could not be generated.")


# ---------------- STORY GENERATION ----------------
if st.button("Generate Story"):
    if not client:
        st.info("⚠️ AI service is currently unavailable.")
    else:
        with st.spinner("✨ Creating your story..."):
            def _story():
                prompt = (
                    f"Write a {length} {genre} roleplay story in {language} ONLY. "
                    f"Introduce characters first ({characters})."
                )
                resp = client.models.generate_content(model=GEMMA_MODEL, contents=[prompt])
                return resp.text

            story = safe_run(_story, "⚠️ Story generation failed.")
            if story:
                st.session_state["story"] = story
                st.toast("📖 Story ready!", icon="✅")


# ---------------- DISPLAY STORY ----------------
if "story" in st.session_state:
    st.subheader("Story Script")
    st.write(st.session_state["story"])

    pdf = generate_pdf_reportlab(st.session_state["story"], "My AI Roleplay")
    if pdf:
        st.download_button("Download Story PDF", pdf, "story.pdf", "application/pdf")


# ---------------- AUDIO ----------------
if add_audio and "story" in st.session_state and client:
    with st.spinner("🔊 Generating audio..."):
        def _audio():
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    language_code=map_language_code(language),
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=map_voice(voice_choice)
                        )
                    )
                )
            )
            tts = client.models.generate_content(
                model=TTS_MODEL,
                contents=[st.session_state["story"]],
                config=config
            )
            data = tts.candidates[0].content.parts[0].inline_data.data
            return pcm_to_wav_bytes(base64.b64decode(data))

        audio = safe_run(_audio, "⚠️ Audio could not be generated.")
        if audio:
            st.audio(audio)
            st.download_button("Download Audio", audio, "story.wav", "audio/wav")


st.markdown("---")