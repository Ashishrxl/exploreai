import streamlit as st
from google import genai
import random
from google.genai import types
import wave
from io import BytesIO
import time
import base64
from streamlit.components.v1 import html

# Hide Streamlit default elements
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

st.set_page_config(page_title="🎙️ Text 2 Audio", layout="wide")

# CSS to hide unwanted elements
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stToolbar"] {display: none;}
a[href^="https://github.com"] {display: none !important;}
a[href^="https://streamlit.io"] {display: none !important;}
header > div:nth-child(2) { display: none; }
.main { padding: 2rem; }
.stButton > button {
    width: 100%;
    background-color: #4CAF50;
    color: white;
    padding: 0.75rem;
    font-size: 1.1rem;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

textmodel = "gemini-2.5-flash-lite"
ttsmodel = "gemini-2.5-flash-preview-tts"

# Initialize session state
defaults = {
    "audio_generated": False,
    "audio_buffer": None,
    "summary_text": None,
    "original_word_count": 0,
    "final_word_count": 0,
    "was_summarized": False,
    "selected_voice_used": None,
    "text_confirmed": False,
    "input_text": "",
    "typed_text_temp": "",
    "current_typed_text": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# Helper: Save PCM as WAV
def save_wave_file(pcm_data, channels=1, rate=24000, sample_width=2):
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    buffer.seek(0)
    return buffer


# Extract text from uploaded file
def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_type == 'txt':
            return uploaded_file.read().decode('utf-8')
        elif file_type == 'pdf':
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
            return " ".join(page.extract_text() or "" for page in pdf_reader.pages)
        elif file_type in ['doc', 'docx']:
            import docx
            doc = docx.Document(BytesIO(uploaded_file.read()))
            return " ".join(p.text for p in doc.paragraphs)
        else:
            st.warning("⚠️ This file type isn’t supported yet.")
            return None
    except Exception:
        st.warning("😕 Could not read this file.")
        return None


# -------- GET ALL KEYS AUTOMATICALLY --------
def get_all_api_keys():
    keys = []
    for i in range(1, 12):
        k = st.secrets.get(f"KEY_{i}")
        if k:
            keys.append(k)
    return keys


# -------- SUMMARIZE WITH KEY ROTATION --------
def summarize_text(text, api_keys_list, max_words=3500):
    random.shuffle(api_keys_list)

    for key in api_keys_list:
        try:
            client = genai.Client(api_key=key)

            prompt = f"""
Please provide a comprehensive summary of the following text.
Keep it under {max_words} words.

TEXT:
{text}
SUMMARY:
"""

            response = client.models.generate_content(
                model=textmodel,
                contents=prompt
            )

            if response and response.text:
                return response.text

        except Exception:
            continue

    st.warning("🤖 All API keys failed while summarizing.")
    return None


# -------- TTS WITH KEY ROTATION --------
def generate_audio_tts(text, api_keys_list, voice_name='Kore', speaking_style=''):
    random.shuffle(api_keys_list)

    for key in api_keys_list:
        try:
            client = genai.Client(api_key=key)
            prompt = f"{speaking_style}: {text}" if speaking_style else text

            response = client.models.generate_content(
                model=ttsmodel,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        ),
                    )
                )
            )

            if (
                hasattr(response, "candidates")
                and response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                audio_part = response.candidates[0].content.parts[0]
                if hasattr(audio_part, "inline_data") and audio_part.inline_data.data:
                    b64_data = audio_part.inline_data.data

                    if isinstance(b64_data, bytes):
                        return b64_data
                    elif isinstance(b64_data, str):
                        b64_data += "=" * (-len(b64_data) % 4)
                        return base64.b64decode(b64_data)

        except Exception:
            continue

    st.warning("🎧 All API keys failed while generating audio.")
    return None


def main():
    st.title("🎙️ Text-to-Audio Converter")
    st.markdown("### Convert your text files to natural-sounding speech")
    st.markdown("---")

    MAX_WORDS_FOR_TTS = 4000
    api_keys = get_all_api_keys()

    st.subheader("🎵 Voice Options")

    voice_options = {
            'Kore': 'Firm and clear',
            'Puck': 'Upbeat and energetic',
            'Zephyr': 'Bright and friendly',
            'Charon': 'Informative and steady',
            'Fenrir': 'Excitable and dynamic',
            'Aoede': 'Breezy and light',
            'Leda': 'Youthful and vibrant',
            'Orus': 'Firm and authoritative',
            'Callirrhoe': 'Easy-going and relaxed',
            'Autonoe': 'Bright and articulate'
        }

    selected_voice = st.selectbox(
            "Select Voice",
            options=list(voice_options.keys()),
            format_func=lambda x: f"{x} – {voice_options[x]}"
        )

    speaking_style = st.text_input(
            "🎭 Optional speaking style",
            placeholder="e.g., calm, confident, conversational"
        )

    col1, col2 = st.columns(2)

    # ---------------- INPUT ----------------
    with col1:
        st.header("📝 Input Text")
        tab1, tab2 = st.tabs(["📁 Upload File", "✍️ Type Text"])

        with tab1:
            uploaded = st.file_uploader("Upload a file", type=["txt", "pdf", "docx", "doc"])
            if uploaded:
                extracted = extract_text_from_file(uploaded)
                if extracted:
                    st.session_state.input_text = extracted
                    st.session_state.text_confirmed = True

        with tab2:
            with st.form("text_form"):
                text_input = st.text_area("Paste or type text here", height=300)
                submitted = st.form_submit_button("Confirm text")
            if submitted and text_input.strip():
                st.session_state.input_text = text_input
                st.session_state.text_confirmed = True
                st.rerun()

        # ✅ SHOW TEXT TO USER (PERSISTENT)
        if st.session_state.text_confirmed and st.session_state.input_text:
            st.markdown("### 📖 Text Preview")
            st.text_area(
                "Preview",
                value=st.session_state.input_text,
                height=250,
                disabled=True
            )

    # ---------------- AUDIO ----------------
    with col2:
        st.header("🔊 Generate Audio")

        if api_keys and st.session_state.text_confirmed and st.session_state.input_text:

            txt = st.session_state.input_text
            wc = len(txt.split())
            needs_summary = wc > MAX_WORDS_FOR_TTS

            if st.button("🎵 Convert to Audio"):

                use_text = txt

                if needs_summary:
                    with st.spinner("Summarizing long text…"):
                        summary = summarize_text(txt, api_keys, MAX_WORDS_FOR_TTS)

                    if summary:
                        use_text = summary
                        st.session_state.summary_text = summary

                with st.spinner("Creating audio…"):
                    audio_data = generate_audio_tts(
                        use_text,
                        api_keys,
                        selected_voice,
                        speaking_style
                    )

                if audio_data:
                    st.session_state.audio_buffer = save_wave_file(audio_data)
                    st.session_state.audio_generated = True

        # ✅ PERSIST AUDIO PLAYER
        if st.session_state.audio_generated and st.session_state.audio_buffer:
            st.audio(st.session_state.audio_buffer, format="audio/wav")

            ts = time.strftime("%Y%m%d-%H%M%S")
            st.download_button(
                "⬇️ Download audio",
                data=st.session_state.audio_buffer,
                file_name=f"audio_{ts}.wav",
                mime="audio/wav"
            )

        else:
            st.info("👈 Please upload or type text first.")


if __name__ == "__main__":
    main()