import streamlit as st
import threading
import time
import numpy as np
import sounddevice as sd
import queue
from src.transcriber import transcribe
from src.suggester import get_suggestion
from src.summarizer import generate_summary

# Global state
transcript_list = []
latest_text = ""
latest_suggestion = ""
audio_queue = queue.Queue()
running_flag = False  # Thread-safe flag for background loop

# Initialize session state safely
if "running" not in st.session_state:
    st.session_state.running = False
if "latest_text" not in st.session_state:
    st.session_state.latest_text = ""
if "latest_suggestion" not in st.session_state:
    st.session_state.latest_suggestion = ""
if "transcript_list" not in st.session_state:
    st.session_state.transcript_list = []

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
    global running_flag, latest_text, latest_suggestion
    devices = sd.query_devices()
    mic_id = None
    for i, dev in enumerate(devices):
        if "baseus" in dev["name"].lower() and dev["max_input_channels"] > 0:
            mic_id = i
            break

    if mic_id is None:
        print("❌ Headset mic not found.")
        return

    try:
        with sd.InputStream(samplerate=16000, channels=1, device=mic_id, callback=audio_callback, blocksize=32000):
            while running_flag:
                if not audio_queue.empty():
                    audio_chunk = audio_queue.get()
                    audio_np = np.squeeze(audio_chunk).astype(np.float32)

                    if audio_np is not None and len(audio_np) > 1000:
                        try:
                            text = transcribe(audio_np)
                            if text:
                                transcript_list.append(text)
                                latest_text = text
                                print("main Block:", text)
                                latest_suggestion = get_suggestion(text)
                        except Exception as e:
                            print("Transcription error:", e)
                    else:
                        print("Skipped empty or short audio chunk.")
                time.sleep(0.5)
    except Exception as e:
        print(f"❌ Failed to start mic stream: {e}")

# Start meeting
if start_btn and not st.session_state.running:
    st.session_state.running = True
    running_flag = True
    threading.Thread(target=meeting_loop, daemon=True).start()
    st.success("Meeting started. Listening...")

# Stop meeting
if stop_btn and st.session_state.running:
    st.session_state.running = False
    running_flag = False
    st.warning("Meeting stopped.")
    st.session_state.transcript_list = transcript_list
    summary = generate_summary(st.session_state.transcript_list)
    summary_box.success("📝 Summary:\n\n" + summary)

# UI update block
if st.session_state.running:
    st.session_state.latest_text = latest_text
    st.session_state.latest_suggestion = latest_suggestion

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