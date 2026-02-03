import streamlit as st
from google import genai
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
.success-box {
    padding: 1rem;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 0.25rem;
    color: #155724;
}
.warning-box {
    padding: 1rem;
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 0.25rem;
    color: #856404;
}
.info-box {
    padding: 1rem;
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    border-radius: 0.25rem;
    color: #0c5460;
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
            st.warning("⚠️ This file type isn’t supported yet. Please upload TXT, PDF, or DOCX.")
            return None
    except Exception:
        st.warning(
            "😕 We couldn’t read this file.\n\n"
            "• Make sure it’s not corrupted\n"
            "• Try exporting it again or uploading a different format"
        )
        return None

# Summarize text using Gemini
def summarize_text(text, api_key, max_words=3500):
    try:
        client = genai.Client(api_key=api_key)
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
        return response.text
    except Exception:
        st.warning(
            "🤖 We ran into an issue while summarizing your text.\n\n"
            "You can try again, shorten the text, or switch to another API key."
        )
        return None

# Generate audio using Gemini TTS
def generate_audio_tts(text, api_key, voice_name='Kore', speaking_style=''):
    try:
        client = genai.Client(api_key=api_key)
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

        st.warning(
            "🔇 The audio service didn’t return any sound.\n\n"
            "This can happen if the text is empty, too long, or the API key hit a limit."
        )
        return None

    except Exception:
        st.warning(
            "🎧 We couldn’t generate the audio this time.\n\n"
            "Please try again, switch voices, or use a different API key."
        )
        return None

def main():
    st.title("🎙️ Text-to-Audio Converter")
    st.markdown("### Convert your text files to natural-sounding speech")
    st.markdown("---")

    MAX_WORDS_FOR_TTS = 4000

    with st.expander("⚙️ Settings", expanded=False):
        st.header("Configuration")

        api_keys = {
            f"Key {i}": st.secrets.get(f"KEY_{i}")
            for i in range(1, 12)
        }
        selected_key_name = st.selectbox("Select Key", list(api_keys.keys()))
        api_key = api_keys[selected_key_name]

        st.markdown("---")
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

        st.info("💡 Supports TXT, PDF, DOCX\nLong texts are summarized automatically")

    col1, col2 = st.columns(2)

    with col1:
        st.header("📝 Input Text")
        tab1, tab2 = st.tabs(["📁 Upload File", "✍️ Type Text"])

        with tab1:
            uploaded = st.file_uploader("Upload a file", type=["txt", "pdf", "docx", "doc"])
            if uploaded:
                with st.spinner("Reading your file…"):
                    extracted = extract_text_from_file(uploaded)
                if extracted:
                    st.session_state.input_text = extracted
                    st.session_state.text_confirmed = True
                    wc = len(extracted.split())
                    st.text_area("Preview", extracted[:2000], height=300, disabled=True)
                    st.caption(f"📊 Word count: {wc}")
                    if wc > MAX_WORDS_FOR_TTS:
                        st.warning("⚠️ This text is long and will be summarized automatically.")

        with tab2:
            if st.session_state.text_confirmed and st.session_state.input_text and not uploaded:
                wc = len(st.session_state.input_text.split())
                st.success(f"✅ Text confirmed ({wc} words)")
                if st.button("✏️ Edit text"):
                    st.session_state.text_confirmed = False
                    st.session_state.input_text = ""
                    st.rerun()
            else:
                with st.form("text_form"):
                    text_input = st.text_area("Paste or type text here", height=300)
                    submitted = st.form_submit_button("Confirm text")
                if submitted:
                    if text_input.strip():
                        st.session_state.input_text = text_input
                        st.session_state.text_confirmed = True
                        st.success("Text confirmed! You can generate audio now ➡️")
                        st.rerun()
                    else:
                        st.warning("✋ Please enter some text before continuing.")

    with col2:
        st.header("🔊 Generate Audio")

        if api_key and st.session_state.text_confirmed and st.session_state.input_text:
            txt = st.session_state.input_text
            wc = len(txt.split())
            needs_summary = wc > MAX_WORDS_FOR_TTS

            if st.button("🎵 Convert to Audio"):
                use_text = txt

                if needs_summary:
                    with st.spinner("Summarizing long text…"):
                        summary = summarize_text(txt, api_key, MAX_WORDS_FOR_TTS)
                    if summary:
                        use_text = summary
                        st.success("Summary ready!")
                    else:
                        st.warning("⚠️ Using original text instead.")

                with st.spinner("Creating audio…"):
                    audio_data = generate_audio_tts(use_text, api_key, selected_voice, speaking_style)

                if audio_data:
                    audio_buf = save_wave_file(audio_data)
                    st.audio(audio_buf, format="audio/wav")
                    ts = time.strftime("%Y%m%d-%H%M%S")
                    st.download_button(
                        "⬇️ Download audio",
                        data=audio_buf,
                        file_name=f"audio_{ts}.wav",
                        mime="audio/wav"
                    )
        else:
            st.info("👈 Please upload or type text first, then confirm it.")

if __name__ == "__main__":
    main()