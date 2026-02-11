import streamlit as st
import io
import re
import struct
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import A4
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


# ---------------- LOAD API KEYS ----------------
clients = []

try:
    api_keys = [
        st.secrets[f"KEY_{i}"]
        for i in range(1, 12)
        if f"KEY_{i}" in st.secrets
    ]
    random.shuffle(api_keys)
    if not api_keys:
        st.error("⚠️ No API keys configured.")
    else:
        clients = [genai.Client(api_key=k) for k in api_keys]

except Exception as e:
    st.error("⚠️ Failed to initialize AI service.")
    print("API error:", e)


# ---------------- KEY ROTATION ----------------
def call_with_key_rotation(fn):
    last_error = None

    for idx, client in enumerate(clients):
        try:
            return fn(client)

        except Exception as e:
            last_error = e
            print(f"Key {idx+1} failed:", e)

    st.error("🚫 AI service is busy or unavailable. Please try again later.")
    print("All keys failed:", last_error)
    return None


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
def map_voice(v):
    return "Charon" if "Male" in v else "Kore"

def map_language_code(lang):
    return {"English": "en-US", "Hindi": "hi-IN", "Bhojpuri": "hi-IN"}.get(lang, "en-US")


# ---------------- PDF ----------------
def generate_pdf_reportlab(text, title="AI Roleplay Story"):

    buf = io.BytesIO()

    pdfmetrics.registerFont(TTFont("Latin", "NotoSans-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Deva", "NotoSansDevanagari-Regular.ttf"))

    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Latin", fontName="Latin", fontSize=12))
    styles.add(ParagraphStyle(name="Deva", fontName="Deva", fontSize=12))

    def is_deva(t):
        return bool(re.search(r'[\u0900-\u097F]', t))

    story = [Paragraph(title, styles["Latin"]), Spacer(1, 12)]

    for line in text.split("\n"):
        if line.strip():
            style = styles["Deva"] if is_deva(line) else styles["Latin"]
            story.append(Paragraph(line, style))
            story.append(Spacer(1, 6))

    doc.build(story)
    buf.seek(0)
    return buf


# ---------------- STORY GENERATION ----------------
if st.button("Generate Story"):
    if not clients:
        st.error("⚠️ AI service unavailable.")
    else:
        with st.spinner("✨ Creating your story..."):

            def generate_story(client):
                prompt = (
                    f"Write a {length} {genre} roleplay story in {language} ONLY. "
                    f"Introduce characters first ({characters})."
                )

                resp = client.models.generate_content(
                    model=GEMMA_MODEL,
                    contents=[prompt]
                )

                return resp.text

            story = call_with_key_rotation(generate_story)

            if story:
                st.session_state["story"] = story
                st.toast("📖 Story ready!", icon="✅")


# ---------------- DISPLAY STORY ----------------
if "story" in st.session_state:
    st.subheader("Story Script")
    st.write(st.session_state["story"])

    pdf = generate_pdf_reportlab(st.session_state["story"], "My AI Roleplay")

    st.download_button("Download Story PDF", pdf, "story.pdf", "application/pdf")


# ---------------- AUDIO HELPERS ----------------
def parse_audio_mime_type(mime_type: str):
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()

        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=")[1])
            except:
                pass

        if "audio/L" in param:
            try:
                bits_per_sample = int(param.split("L")[1])
            except:
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    params = parse_audio_mime_type(mime_type)

    bits_per_sample = params["bits_per_sample"]
    sample_rate = params["rate"]
    num_channels = 1

    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )

    return header + audio_data


# ---------------- AUDIO ----------------
if add_audio and "story" in st.session_state and clients:

    with st.spinner("🔊 Generating audio..."):

        def generate_audio(client):

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

            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=st.session_state["story"])]
                )
            ]

            audio_chunks = []
            mime_type = None

            for chunk in client.models.generate_content_stream(
                model=TTS_MODEL,
                contents=contents,
                config=config
            ):

                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                part = chunk.candidates[0].content.parts[0]

                if part.inline_data and part.inline_data.data:
                    mime_type = part.inline_data.mime_type
                    audio_chunks.append(part.inline_data.data)

            if not audio_chunks:
                return None

            combined_audio = b"".join(audio_chunks)

            if mime_type and "wav" not in mime_type.lower():
                combined_audio = convert_to_wav(combined_audio, mime_type)

            return combined_audio

        audio = call_with_key_rotation(generate_audio)

        if audio:
            st.audio(audio)
            st.download_button("Download Audio", audio, "story.wav", "audio/wav")


st.markdown("---")