import streamlit as st
import threading
import time
import numpy as np
import sounddevice as sd
import queue
from src.transcriber import transcribe
from src.suggester import get_suggestion
from src.summarizer import generate_summary

# Initialize session state
if "latest_text" not in st.session_state:
    st.session_state.latest_text = ""
if "latest_suggestion" not in st.session_state:
    st.session_state.latest_suggestion = ""
if "transcript_list" not in st.session_state:
    st.session_state.transcript_list = []

# Global state
running = False
audio_queue = queue.Queue()

# Streamlit UI
st.set_page_config(page_title="MeetingAI", layout="wide")
st.title("🧑‍💼 MeetingAI - Personal Meeting Assistant")

start_btn = st.button("▶️ Start Meeting")
stop_btn = st.button("⏹️ Stop Meeting")

caption_box = st.empty()
suggestion_box = st.empty()
summary_box = st.empty()

# Audio callback
def audio_callback(indata, frames, time_info, status):
    audio_queue.put(indata.copy())

# Background thread
def meeting_loop():
    global running

    LOOPBACK_DEVICE_ID = 20  # Stereo Mix (Realtek HD Audio Stereo input)

    try:
        with sd.InputStream(samplerate=16000, channels=2, device=LOOPBACK_DEVICE_ID, callback=audio_callback):
            while running:
                if not audio_queue.empty():
                    audio_chunk = audio_queue.get()
                    audio_np = np.mean(audio_chunk, axis=1)  # Convert stereo to mono

                    if audio_np is not None and len(audio_np) > 1000:
                        try:
                            text = transcribe(audio_np)
                            if text:
                                st.session_state.transcript_list.append(text)
                                st.session_state.latest_text = text
                                st.session_state.latest_suggestion = get_suggestion(text)
                        except Exception as e:
                            print("Transcription error:", e)
                    else:
                        print("Skipped empty or short audio chunk.")
                time.sleep(1)
    except Exception as e:
        st.error(f"❌ Failed to start loopback stream: {e}")

# Start meeting
if start_btn and not running:
    running = True
    threading.Thread(target=meeting_loop, daemon=True).start()
    st.success("Meeting started. Listening...")

# Stop meeting
if stop_btn and running:
    running = False
    st.warning("Meeting stopped.")
    summary = generate_summary(st.session_state.transcript_list)
    summary_box.success("📝 Summary:\n\n" + summary)

# UI polling
if running:
    caption_box.markdown(
        f"""
        <div style='background-color:#f0f0f0; padding:10px; border-radius:8px; font-size:24px; font-weight:bold; color:#333; text-align:center;'>
            {st.session_state.latest_text}
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.session_state.latest_suggestion:
        suggestion_box.markdown(f"**🤖 Gemini Suggestion:**\n\n{st.session_state.latest_suggestion}")
