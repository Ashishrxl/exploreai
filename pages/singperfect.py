import streamlit as st
import tempfile
import random
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import matplotlib.pyplot as plt
from google import genai
from google.genai import types
from streamlit.components.v1 import html
import wave
import base64
import os
from contextlib import contextmanager
import io

# ==============================
# Hide Streamlit elements
# ==============================
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

st.markdown("""
<style>
footer {pointer-events:none;}
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stStatusWidget"], [data-testid="stToolbar"] {display:none;}
.main {padding:2rem;}
.stButton>button {
    width:100%;
    background:#4CAF50;
    color:white;
    padding:0.75rem;
    font-size:1.1rem;
}
.lyrics-box {
    background-color:#f9f9f9;
    padding:1rem;
    border-radius:10px;
    white-space:pre-wrap;
    font-size:1.05rem;
    line-height:1.6;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="🎙️ AI Vocal Coach", layout="wide")

sttmodel = "gemini-2.5-flash-lite"
ttsmodel = "gemini-2.5-flash-preview-tts"

# ==============================
# API Keys Collection
# ==============================
api_keys = []
for i in range(1, 12):
    key_name = f"KEY_{i}"
    if key_name in st.secrets:
        api_keys.append(st.secrets[key_name])

random.shuffle(api_keys)

if not api_keys:
    st.warning("🔑 AI service is not configured.")
    st.stop()

def generate_with_key_rotation(model, contents, config=None):
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            if response:
                return response
        except:
            continue

    st.error("⚠️ AI service unavailable. Try again.")
    return None


# ==============================
# Audio Utilities
# ==============================
def safe_read_audio(path):
    try:
        y, sr = sf.read(path, always_2d=False)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        return y.astype(float), sr
    except:
        return np.array([]), 0


@st.cache_data(show_spinner=False)
def load_audio_energy(path):
    y, sr = safe_read_audio(path)
    if len(y) == 0:
        return np.array([])
    frame_len = int(0.05 * sr)
    hop = int(0.025 * sr)
    energies = []
    for i in range(0, len(y) - frame_len, hop):
        energies.append(np.mean(np.abs(y[i:i + frame_len])))
    energies = np.array(energies)
    if len(energies) and np.max(energies) > 0:
        energies /= np.max(energies)
    return energies


# ==============================
# Step 1
# ==============================
st.header("⚙️ Step 1: Choose Feedback Options")

feedback_lang = st.selectbox("🗣️ Feedback language", ["English", "Hindi"])
enable_audio_feedback = st.checkbox("🔊 Generate Audio Feedback", value=False)
voice_choice = st.selectbox("🎤 Choose AI voice", ["Kore", "Ava", "Wave"])

def map_language_code(lang):
    return "en-US" if lang == "English" else "hi-IN"

# ==============================
# Step 2 Upload
# ==============================
st.header("🎧 Step 2: Upload Reference Song")
ref_file = st.file_uploader("Upload song", type=["mp3", "wav"])

if "lyrics_text" not in st.session_state:
    st.session_state.lyrics_text = ""
if "ref_tmp_path" not in st.session_state:
    st.session_state.ref_tmp_path = None

if ref_file and not st.session_state.lyrics_text:
    with st.spinner("🎵 Extracting lyrics..."):
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        with open(tmp_path, "wb") as f:
            f.write(ref_file.read())
        st.session_state.ref_tmp_path = tmp_path

        response = generate_with_key_rotation(
            sttmodel,
            [{
                "role": "user",
                "parts": [
                    {"text": "Extract complete lyrics only."},
                    {"inline_data": {"mime_type": "audio/wav", "data": open(tmp_path, "rb").read()}}
                ]
            }]
        )

        if response:
            st.session_state.lyrics_text = response.candidates[0].content.parts[0].text.strip()

if st.session_state.lyrics_text:
    st.subheader("📜 Extracted Lyrics")
    st.markdown(
        f'<div class="lyrics-box">{st.session_state.lyrics_text}</div>',
        unsafe_allow_html=True
    )

# ==============================
# Step 3 Record
# ==============================
st.header("🎤 Step 3: Record Your Singing")
recorded_audio_native = st.audio_input("🎙️ Record voice")

recorded_file_path = None
if recorded_audio_native:
    recorded_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    with open(recorded_file_path, "wb") as f:
        f.write(recorded_audio_native.getvalue())
    st.success("✅ Recording captured!")

# ==============================
# Step 4 Evaluation
# ==============================
if st.session_state.ref_tmp_path and recorded_file_path:

    st.subheader("💬 AI Vocal Feedback")

    # Energy check for silence detection
    user_energy = load_audio_energy(recorded_file_path)

    if len(user_energy) == 0 or np.mean(user_energy) < 0.02:
        st.error("⚠️ No clear singing detected. Please sing louder and try again.")
    else:
        strict_prompt = """
You are a strict and professional vocal coach.

Analyze BOTH the reference song and the user's recording carefully.

Evaluate:
- Pitch accuracy
- Rhythm/timing
- Vocal energy
- Expression
- Breath control

IMPORTANT RULES:
- If the user barely sings, sings off-key, is silent, or performs poorly, clearly say it needs improvement.
- DO NOT automatically praise.
- Only praise if performance genuinely matches reference.
- Be honest but constructive.
- Give a score from 1 to 10.
- Provide 3 specific improvement tips.
"""

        response = generate_with_key_rotation(
            sttmodel,
            [{
                "role": "user",
                "parts": [
                    {"text": strict_prompt},
                    {"inline_data": {"mime_type": "audio/wav", "data": open(st.session_state.ref_tmp_path, "rb").read()}},
                    {"inline_data": {"mime_type": "audio/wav", "data": open(recorded_file_path, "rb").read()}}
                ]
            }]
        )

        if response:
            feedback_text = response.candidates[0].content.parts[0].text
        else:
            feedback_text = "Could not evaluate performance."

        st.write(feedback_text)

else:
    st.info("Upload song and record to get feedback.")