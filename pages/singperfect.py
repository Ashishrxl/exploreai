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
    max-height:250px;
    overflow-y:auto;
    border:1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="🎙️ AI Vocal Coach", layout="wide")

sttmodel = "gemini-2.5-flash-lite"
ttsmodel = "gemini-2.5-flash-preview-tts"

# ==============================
# API Keys
# ==============================
api_keys = []
for i in range(1, 12):
    key_name = f"KEY_{i}"
    if key_name in st.secrets:
        api_keys.append(st.secrets[key_name])

random.shuffle(api_keys)

if not api_keys:
    st.warning("🔑 AI service not configured.")
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
        except Exception:
            continue
    st.error("⚠️ AI service temporarily unavailable.")
    return None

# ==============================
# Utility Functions
# ==============================
def safe_read_audio(path):
    try:
        y, sr = sf.read(path, always_2d=False)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        return y.astype(float), sr
    except Exception:
        audio = AudioSegment.from_file(path)
        y = np.array(audio.get_array_of_samples()).astype(float)
        sr = audio.frame_rate
        return y, sr

def load_audio_energy(path):
    try:
        y, sr = safe_read_audio(path)
        frame_len = int(0.05 * sr)
        hop = int(0.025 * sr)
        energies = []
        for i in range(0, len(y) - frame_len, hop):
            energies.append(np.mean(np.abs(y[i:i + frame_len])))
        energies = np.array(energies)
        if np.max(energies) > 0:
            energies /= np.max(energies)
        return energies
    except Exception:
        return np.array([])

def save_tts_bytes(path, pcm_bytes):
    if isinstance(pcm_bytes, str):
        pcm_bytes = base64.b64decode(pcm_bytes)

    try:
        bio = io.BytesIO(pcm_bytes)
        seg = AudioSegment.from_file(bio)
        seg.export(path, format="wav")
    except Exception:
        with open(path, "wb") as f:
            f.write(pcm_bytes)

# ==============================
# Step 1
# ==============================
st.header("⚙️ Step 1: Choose Feedback Options")
col1, col2 = st.columns(2)
with col1:
    feedback_lang = st.selectbox("🗣️ Feedback language", ["English", "Hindi"])
with col2:
    enable_audio_feedback = st.checkbox("🔊 Generate Audio Feedback", value=True)

voice_choice = st.selectbox("🎤 Choose AI voice", ["Kore", "Ava", "Wave"])

def map_language_code(lang):
    return "en-US" if lang == "English" else "hi-IN"

# ==============================
# Step 2 Upload Song
# ==============================
st.header("🎧 Step 2: Upload Reference Song")
ref_file = st.file_uploader("Upload a song (mp3 or wav)", type=["mp3", "wav"])

if "lyrics_text" not in st.session_state:
    st.session_state.lyrics_text = ""
if "ref_tmp_path" not in st.session_state:
    st.session_state.ref_tmp_path = None

if ref_file and not st.session_state.lyrics_text:
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
    st.subheader("📜 Extracted Lyrics (Sing Along)")
    st.markdown(
        f'<div class="lyrics-box">{st.session_state.lyrics_text}</div>',
        unsafe_allow_html=True
    )

# ==============================
# Step 3 Record
# ==============================
st.header("🎤 Step 3: Record Your Singing")
recorded_audio_native = st.audio_input("🎙️ Record your voice")

recorded_file_path = None
if recorded_audio_native:
    recorded_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    with open(recorded_file_path, "wb") as f:
        f.write(recorded_audio_native.getvalue())
    st.success("✅ Recording captured!")

# ==============================
# Step 4 Compare + Feedback
# ==============================
if st.session_state.ref_tmp_path and recorded_file_path:

    st.subheader("🎶 Reference vs Your Singing")

    col_a, col_b = st.columns(2)
    with col_a:
        st.audio(st.session_state.ref_tmp_path)
        st.caption("🎧 Reference Song")
    with col_b:
        st.audio(recorded_file_path)
        st.caption("🎤 Your Recording")

    # Restore Energy Graph
    with st.spinner("🔍 Analyzing energy patterns..."):
        ref_energy = load_audio_energy(st.session_state.ref_tmp_path)
        user_energy = load_audio_energy(recorded_file_path)

    if len(ref_energy) and len(user_energy):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(ref_energy, label="Reference")
        ax.plot(user_energy, label="You")
        ax.legend()
        ax.set_title("Energy Contour Comparison")
        st.pyplot(fig)
    else:
        st.info("📊 Energy comparison limited.")

    if len(user_energy) == 0 or np.mean(user_energy) < 0.02:
        st.error("⚠️ No singing detected. Please sing clearly.")
        st.stop()

    st.subheader("💬 AI Vocal Feedback")

    evaluation_prompt = """
You are a strict professional vocal coach.

Analyze the singing carefully.

Be honest.
If bad, clearly explain weaknesses.
If good, clearly explain strengths.

Provide:
1. Overall Score (0-100)
2. Pitch Analysis
3. Rhythm Analysis
4. Energy Analysis
5. Final Verdict (Excellent / Good / Average / Poor)
"""

    response = generate_with_key_rotation(
        sttmodel,
        [{
            "role": "user",
            "parts": [
                {"text": evaluation_prompt},
                {"inline_data": {"mime_type": "audio/wav", "data": open(st.session_state.ref_tmp_path, "rb").read()}},
                {"inline_data": {"mime_type": "audio/wav", "data": open(recorded_file_path, "rb").read()}}
            ]
        }]
    )

    feedback_text = response.candidates[0].content.parts[0].text if response else "Evaluation unavailable."
    st.write(feedback_text)

    # ==============================
    # Improved Audio Feedback
    # ==============================
    if enable_audio_feedback and response:
        with st.spinner("🔊 Generating professional audio feedback..."):
            try:
                clean_tts_prompt = f"""
Speak the following vocal coaching feedback in a clear, confident, professional coach tone.
Use natural pauses.
Do not sound robotic.

Feedback:
{feedback_text}
"""

                config = types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        language_code=map_language_code(feedback_lang),
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_choice
                            )
                        )
                    )
                )

                tts_response = generate_with_key_rotation(
                    ttsmodel,
                    clean_tts_prompt,
                    config
                )

                if tts_response:
                    part = tts_response.candidates[0].content.parts[0]
                    pcm_data = part.inline_data.data
                    tts_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                    save_tts_bytes(tts_path, pcm_data)
                    st.audio(tts_path)
                    st.success("✅ Audio feedback ready!")

            except Exception:
                st.warning("🔊 Audio generation failed.")

else:
    st.info("🎵 Upload a song and record your voice to begin.")