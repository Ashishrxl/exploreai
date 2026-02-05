import streamlit as st
import base64
import tempfile
import io
import asyncio
import soundfile as sf
from google import genai
import requests
import wave
import numpy as np
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


# --- CSS: Hide all unwanted items but KEEP sidebar toggle ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stToolbar"] {display: none;}
a[href^="https://github.com"] {display: none !important;}
a[href^="https://streamlit.io"] {display: none !important;}

/* The following specifically targets and hides all child elements of the header's right side,
   while preserving the header itself and, by extension, the sidebar toggle button. */
header > div:nth-child(2) {
    display: none;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.set_page_config(page_title="Singify 🎶", layout="centered")
st.title("🎤 Singify")
st.caption("Record or upload a line → Transcribe → Sing 🎶")

sttmodel = "gemini-2.5-flash"

# --- API Key selection ---
api_keys = {
    "Key 1": st.secrets["KEY_1"],
    "Key 2": st.secrets["KEY_2"],
    "Key 3": st.secrets["KEY_3"],
    "Key 4": st.secrets["KEY_4"],
    "Key 5": st.secrets["KEY_5"],
    "Key 6": st.secrets["KEY_6"],
    "Key 7": st.secrets["KEY_7"],
    "Key 8": st.secrets["KEY_8"],
    "Key 9": st.secrets["KEY_9"],
    "Key 10": st.secrets["KEY_10"],
    "Key 11": st.secrets["KEY_11"],
}
selected_key_name = st.selectbox("Select Key", list(api_keys.keys()))
api_key = api_keys[selected_key_name]

# ---------------- Session State ----------------
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'vocal_path' not in st.session_state:
    st.session_state.vocal_path = None
if 'original_path' not in st.session_state:
    st.session_state.original_path = None
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'current_style' not in st.session_state:
    st.session_state.current_style = None
if 'current_voice' not in st.session_state:
    st.session_state.current_voice = None

# Sidebar
singing_style = st.selectbox("Singing Style", ["Pop", "Ballad", "Rap", "Soft"])
voice_option = st.selectbox("Voice", ["Kore", "Charon", "Fenrir", "Aoede"])

audio_bytes = None
tmp_path = None

# -------------------------
# Convert audio to WAV
# -------------------------
def convert_to_wav_bytes(file_bytes):
    try:
        with io.BytesIO(file_bytes) as f:
            data, samplerate = sf.read(f, always_2d=True)
        out_bytes = io.BytesIO()
        sf.write(out_bytes, data, samplerate, format='WAV')
        return out_bytes.getvalue()
    except Exception:
        st.warning("⚠️ We couldn’t process that audio format. Try another file or re-record.")
        return None

# -------------------------
# Audio Input
# -------------------------
st.subheader("📤 Choose Audio Input Method")
tab1, tab2 = st.tabs(["📁 Upload Audio File", "🎙️ Record Audio"])

with tab1:
    uploaded = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a", "ogg", "flac"]
    )

    if uploaded:
        file_bytes = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()

        if ext != "wav":
            with st.spinner("🔄 Converting audio…"):
                audio_bytes = convert_to_wav_bytes(file_bytes)
        else:
            audio_bytes = file_bytes

        if audio_bytes:
            tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp_file.name
            with open(tmp_path, "wb") as f:
                f.write(audio_bytes)

            st.session_state.original_path = tmp_path
            st.audio(tmp_path, format="audio/wav")

with tab2:
    recorded_audio_native = st.audio_input("🎙️ Record your voice")

    if recorded_audio_native:
        audio_bytes = recorded_audio_native.read()
        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp_file.name
        with open(tmp_path, "wb") as f:
            f.write(audio_bytes)
        st.session_state.original_path = tmp_path
        st.audio(tmp_path)

# -------------------------
# Friendly TTS
# -------------------------
async def synthesize_speech(text_prompt, voice_name="Kore"):
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

        data = {
            "contents": [{"parts": [{"text": text_prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name}
                    }
                }
            }
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: requests.post(url, headers=headers, json=data)
        )

        if response.status_code != 200:
            st.warning("⚠️ Voice generation is temporarily unavailable. Please try again shortly.")
            return None

        audio_base64 = response.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        return base64.b64decode(audio_base64)

    except Exception:
        st.warning("⚠️ Something went wrong while creating the singing voice.")
        return None

# -------------------------

# -------------------------
# PCM → WAV Converter
# -------------------------
def pcm_to_wav(pcm_bytes, sample_rate=24000, channels=1, sample_width=2):
    try:
        pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_array.tobytes())

        return wav_buffer.getvalue()

    except Exception:
        st.warning("⚠️ Failed to convert generated audio.")
        return None
# Transcribe & Sing
# -------------------------
async def transcribe_and_sing():
    if not st.session_state.original_path:
        st.warning("⚠️ Please upload or record audio first.")
        return

    client = genai.Client(api_key=api_key)
    audio_path = st.session_state.original_path

    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        resp = client.models.generate_content(
            model=sttmodel,
            contents=[{
                "role": "user",
                "parts": [
                    {"text": "Please transcribe this speech accurately."},
                    {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(audio_data).decode()}}
                ]
            }]
        )

        transcript = resp.text.strip()
        st.session_state.transcript = transcript

    except Exception:
        st.warning("⚠️ We couldn’t understand the audio clearly. Try speaking louder or slower.")
        return

    tts_prompt = f"Sing these words in a {singing_style.lower()} style: {transcript}"
    pcm = await synthesize_speech(tts_prompt, voice_option)

    if pcm is None:
        return

    wav_bytes = pcm_to_wav(pcm)
    if wav_bytes is None:
        return
    out_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with open(out_file.name, "wb") as f:
        f.write(wav_bytes)

    st.session_state.vocal_path = out_file.name
    st.session_state.generation_complete = True
    st.session_state.current_style = singing_style
    st.session_state.current_voice = voice_option

# -------------------------
# Main Button
# -------------------------
st.subheader("🚀 Generate Singing Voice")

if st.session_state.original_path:
    if st.button("🎶 Transcribe & Sing"):
        with st.spinner("🔊 Generating audio..."):
            asyncio.run(transcribe_and_sing())
else:
    st.info("ℹ️ Upload or record audio to get started.")

# -------------------------
# Results
# -------------------------
if st.session_state.transcript:
    st.subheader("📝 Transcription")
    st.write(st.session_state.transcript)

if st.session_state.vocal_path:
    st.subheader("🎶 Your Singing Voice")
    st.audio(st.session_state.vocal_path)