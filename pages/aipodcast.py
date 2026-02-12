import streamlit as st

# --- Page Config MUST be first ---
st.set_page_config(page_title="VoiceVerse AI", layout="centered")

from google import genai
from google.genai import types
import wave
import random
import base64
from streamlit.components.v1 import html
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)

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


st.markdown("""
<style>
iframe[title="streamlitAppViewContainer"] + div {
    display:none !important;
}

div[data-testid="stDecoration"] {
    display:none !important;
}

div[data-testid="stToolbar"] {
    display:none !important;
}

button[title="View fullscreen"] {
    display:none !important;
}

footer {
    visibility:hidden;
}

header {
    visibility:hidden;
}
</style>
""", unsafe_allow_html=True)
# --- Models ---
ttsmodel = "gemini-2.5-flash-preview-tts"
textmodel = "gemini-2.5-flash-lite"

# --- Load API Keys ---
try:
    api_keys = [
        st.secrets["KEY_1"],
        st.secrets["KEY_2"],
        st.secrets["KEY_3"],
        st.secrets["KEY_4"],
        st.secrets["KEY_5"],
        st.secrets["KEY_6"],
        st.secrets["KEY_7"],
        st.secrets["KEY_8"],
        st.secrets["KEY_9"],
        st.secrets["KEY_10"],
        st.secrets["KEY_11"],
    ]
    random.shuffle(api_keys)

except Exception:
    st.error("⚠️ API keys not configured properly.")
    st.stop()

# --- Language Mapper ---
def map_language_code(language: str) -> str:
    lang = language.lower()
    if lang == "hindi":
        return "hi-IN"
    elif lang == "bhojpuri":
        return "bho-IN"
    return "en-US"

# --- WAV Save ---
def save_wave(filename: str, pcm_data: bytes, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

# --- Script Generator ---
def generate_script(topic: str) -> str:

    prompt = f"""
    Write a friendly and engaging podcast script about "{topic}".
    Include:
    - A short intro
    - 3 key talking points
    - A closing statement
    Keep it conversational and natural.
    """

    for key in api_keys:
        try:
            client = genai.Client(api_key=key)

            resp = client.models.generate_content(
                model=textmodel,
                contents=prompt
            )

            return resp.text or "Script generation failed."

        except Exception:
            continue

    return "❌ All API keys exhausted. Please try later."

# --- Audio Generator ---
def generate_audio(script_text: str, voice_name="Kore", language="English"):

    if language.lower() == "hindi":
        style_prompt = "Speak this in a warm and expressive Hindi accent."
    elif language.lower() == "bhojpuri":
        style_prompt = "Speak this in a friendly Bhojpuri tone."
    else:
        style_prompt = "Speak this in a natural and friendly tone."

    contents = f"{style_prompt}\n\n{script_text}"

    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            language_code=map_language_code(language),
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name
                )
            )
        )
    )

    for key in api_keys:
        try:
            client = genai.Client(api_key=key)

            response = client.models.generate_content(
                model=ttsmodel,
                contents=contents,
                config=config
            )

            pcm_data = response.candidates[0].content.parts[0].inline_data.data

            if isinstance(pcm_data, str):
                pcm_data = base64.b64decode(pcm_data)

            filename = "podcast.wav"
            save_wave(filename, pcm_data)
            return filename

        except Exception:
            continue

    return ""

# --- UI ---
st.title("🎙️ VoiceVerse AI Podcast Generator")

# --- Session State Init ---
if "script" not in st.session_state:
    st.session_state.script = ""

if "audio_file" not in st.session_state:
    st.session_state.audio_file = ""

topic = st.text_input("Enter your podcast topic:")
language = st.selectbox("Choose a language:", ["English", "Hindi", "Bhojpuri"])
gender = st.radio("Select voice gender:", ["Female", "Male"])

female_voices = ["Kore", "Aoede", "Callirhoe"]
male_voices = ["Puck", "Charon", "Fenrir"]

voice = st.selectbox("Choose a voice:", female_voices if gender == "Female" else male_voices)

# --- Generate Button ---
if st.button("Generate Podcast"):

    if not topic.strip():
        st.info("✍️ Please enter a topic.")
    else:

        with st.spinner("Creating podcast script..."):
            script = generate_script(topic)
            st.session_state.script = script
            st.session_state.audio_file = ""

        if "❌" not in script:
            with st.spinner("Converting to audio..."):
                audio_file = generate_audio(script, voice, language)
                st.session_state.audio_file = audio_file

# --- Persist Script ---
if st.session_state.script:
    st.text_area("Generated Script", st.session_state.script, height=300)

# --- Persist Audio ---
if st.session_state.audio_file:
    st.audio(st.session_state.audio_file)

    with open(st.session_state.audio_file, "rb") as f:
        st.download_button(
            "📥 Download Podcast",
            f,
            file_name="voiceverse_podcast.wav",
            mime="audio/wav"
        )

    st.success("🎉 Podcast ready!")


