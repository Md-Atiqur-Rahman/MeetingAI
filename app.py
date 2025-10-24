import streamlit as st
from streamlit_autorefresh import st_autorefresh
import threading
import time
import numpy as np
import queue
import re
from src.transcriber import transcribe
from src.suggester import get_suggestion
from src.summarizer import generate_summary
from src.audio_listener import start_listening, combined_queue
import json
import os

# File-based communication
TRANSCRIPT_FILE = "temp_transcript.json"

# Global thread control
running_flag = threading.Event()
audio_buffer = []
thread_instance = [None]
meeting_start_time = [0.0]  # store meeting start time

# ----------------------------
# Helper Functions
# ----------------------------
def save_transcripts(data):
    with open(TRANSCRIPT_FILE, 'w') as f:
        json.dump(data, f)

def load_transcripts():
    if os.path.exists(TRANSCRIPT_FILE):
        try:
            with open(TRANSCRIPT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"transcripts": [], "latest_text": "", "latest_suggestion": "", "timestamp": time.time()}
    return {"transcripts": [], "latest_text": "", "latest_suggestion": "", "timestamp": time.time()}

def split_into_sentences(text):
    sentences = re.split(r'([.!?]+\s+|,\s+(?=[A-Z]))', text)
    result = []
    current = ""
    for part in sentences:
        current += part
        if re.search(r'[.!?]+\s*$', part):
            if current.strip():
                result.append(current.strip())
            current = ""
    if current.strip():
        result.append(current.strip())
    if not result:
        return [text]
    return result

# ----------------------------
# Meeting loop (Background thread)
# ----------------------------
def meeting_loop():
    global audio_buffer
    print("🎙️ Meeting loop started (REAL-TIME GPU MODE)")
    
    listener_thread = threading.Thread(target=start_listening(), daemon=True)
    listener_thread.start()
    
    silence_counter = 0
    MIN_AUDIO_LENGTH = 8000
    MAX_AUDIO_LENGTH = 32000
    SILENCE_THRESHOLD = 2

    while running_flag.is_set():
        try:
            if not combined_queue.empty():
                audio_chunk = combined_queue.get_nowait()
                audio_np = np.squeeze(audio_chunk).astype(np.float32)
                max_amp = np.max(np.abs(audio_np))
                
                if max_amp > 0.005:
                    audio_buffer.append(audio_np)
                    silence_counter = 0
                else:
                    silence_counter += 1
                
                if len(audio_buffer) > 0:
                    total_samples = sum(len(chunk) for chunk in audio_buffer)
                    should_process = (
                        (total_samples >= MIN_AUDIO_LENGTH and silence_counter >= SILENCE_THRESHOLD) or
                        total_samples >= MAX_AUDIO_LENGTH
                    )
                    
                    if should_process:
                        combined_audio = np.concatenate(audio_buffer)
                        audio_buffer = []
                        silence_counter = 0
                        
                        def process_audio(audio):
                            try:
                                text = transcribe(audio)
                                if text and len(text.strip()) > 2:
                                    duration = len(audio) / 16000  # seconds of audio
                                    elapsed = time.time() - meeting_start_time[0]
                                    
                                    data = load_transcripts()
                                    sentences = split_into_sentences(text)
                                    
                                    for sentence in sentences:
                                        if sentence.strip():
                                            entry = f"✅ [{elapsed:.1f}s] {sentence.strip()}"
                                            data["transcripts"].append(entry)
                                            data["latest_text"] = entry
                                    
                                    save_transcripts(data)
                            except Exception as e:
                                print(f"❌ Error: {e}")
                        
                        threading.Thread(target=process_audio, args=(combined_audio,), daemon=True).start()
            
            time.sleep(0.01)
        except queue.Empty:
            time.sleep(0.01)
        except Exception as e:
            print(f"❌ Loop error: {e}")
            time.sleep(0.1)
    print("🛑 Meeting loop stopped")

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="MeetingAI", layout="wide")
st.title("🧑‍💼 MeetingAI - Real-time Meeting Assistant ⚡ GPU")

col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("▶️ Start Meeting", use_container_width=True)
with col2:
    stop_btn = st.button("⏹️ Stop Meeting", use_container_width=True)

caption_box = st.empty()
suggestion_box = st.empty()
summary_box = st.empty()

# Session state
if "running" not in st.session_state:
    st.session_state.running = False

# ----------------------------
# Start Meeting
# ----------------------------
if start_btn and not st.session_state.running:
    st.session_state.running = True
    meeting_start_time[0] = time.time()
    save_transcripts({"transcripts": [], "latest_text": "", "latest_suggestion": "", "timestamp": time.time()})
    
    if thread_instance[0] is None or not thread_instance[0].is_alive():
        running_flag.set()
        thread_instance[0] = threading.Thread(target=meeting_loop, daemon=True)
        thread_instance[0].start()
    st.success("✅ Meeting started! GPU-accelerated transcription active")
    time.sleep(0.5)
    st.rerun()

# ----------------------------
# Stop Meeting
# ----------------------------
if stop_btn and st.session_state.running:
    st.session_state.running = False
    running_flag.clear()
    st.warning("⏹️ Meeting stopped. Generating summary...")
    
    data = load_transcripts()
    transcripts = data.get("transcripts", [])
    if len(transcripts) > 0:
        summary = generate_summary(transcripts)
        summary_box.success(f"📝 **Meeting Summary:**\n\n{summary}")
    else:
        summary_box.info("No transcript available to summarize.")
    st.info("👆 Summary generated! You can start a new meeting.")

# ----------------------------
# Main UI (Live updates)
# ----------------------------
if st.session_state.running:
    # Auto-refresh every 1s
    st_autorefresh(interval=1000, key="live_refresh")
    
    data = load_transcripts()
    all_transcripts = data.get("transcripts", [])
    transcript_count = len(all_transcripts)
    current_suggestion = data.get("latest_suggestion", "")
    
    st.markdown(f'<p style="color:#4CAF50; font-weight:bold;">🔴 LIVE - GPU Mode</p>', unsafe_allow_html=True)
    st.caption(f"📊 Total Segments: {transcript_count}")
    
    # Live transcription box (last 30 entries)
    if transcript_count > 0:
        formatted_text = "<br>".join(all_transcripts[-10:])
        caption_box.markdown(
            f"""
            <div style='background-color:#e3f2fd; padding:20px; border-radius:12px;
                        border-left:6px solid #2196F3; max-height:500px; overflow-y:auto;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
                <p style='font-weight:bold; color:#1565C0; margin:0;'>💬 Live Transcription</p>
                <p style='font-size:18px; line-height:1.6; white-space: pre-wrap;'>{formatted_text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        caption_box.info("🎧 Listening... Waiting for speech...")
    
    # AI Suggestion
    if current_suggestion:
        suggestion_box.markdown(
            f"""
            <div style='background-color:#f3e5f5; padding:15px; border-radius:12px;
                        border-left:6px solid #9C27B0; box-shadow:0 4px 8px rgba(0,0,0,0.1);'>
                <p style='font-weight:bold; color:#6A1B9A; margin:0;'>🤖 AI Suggestion</p>
                <p style='font-size:16px; line-height:1.6;'>{current_suggestion}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    caption_box.info("👆 Click **▶️ Start Meeting** to begin real-time transcription.")

st.markdown("---")
st.caption("🎙️ MeetingAI • Real-time transcription with Whisper AI (GPU)")
