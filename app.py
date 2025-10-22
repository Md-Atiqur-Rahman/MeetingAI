import streamlit as st
from streamlit_autorefresh import st_autorefresh
import threading
import time
import numpy as np
import queue
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
last_transcription_time = [time.time()]
thread_instance = [None]

def save_transcripts(data):
    """Save transcript data to file"""
    with open(TRANSCRIPT_FILE, 'w') as f:
        json.dump(data, f)

def load_transcripts():
    """Load transcript data from file"""
    if os.path.exists(TRANSCRIPT_FILE):
        try:
            with open(TRANSCRIPT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"transcripts": [], "latest_text": "", "latest_suggestion": "", "timestamp": time.time()}
    return {"transcripts": [], "latest_text": "", "latest_suggestion": "", "timestamp": time.time()}

def meeting_loop():
    """Background thread for audio processing"""
    global audio_buffer
    
    print("🎙️ Meeting loop started")
    
    listener_thread = threading.Thread(target=start_listening(), daemon=True)
    listener_thread.start()
    
    while running_flag.is_set():
        try:
            if not combined_queue.empty():
                audio_chunk = combined_queue.get(timeout=1)
                audio_np = np.squeeze(audio_chunk).astype(np.float32)

                max_amp = np.max(np.abs(audio_np))
                
                if max_amp > 0.005:
                    audio_buffer.append(audio_np)
                    
                    current_time = time.time()
                    if current_time - last_transcription_time[0] >= 3.0 and len(audio_buffer) > 0:
                        print(f"🎤 Processing {len(audio_buffer)} audio chunks...")
                        
                        combined_audio = np.concatenate(audio_buffer)
                        audio_buffer = []
                        last_transcription_time[0] = current_time
                        
                        try:
                            text = transcribe(combined_audio)
                            
                            if text and len(text.strip()) > 2:
                                print(f"✅ Transcribed: {text}")
                                
                                data = load_transcripts()
                                data["transcripts"].append(text)
                                data["latest_text"] = text
                                data["timestamp"] = time.time()
                                
                                try:
                                    suggestion = get_suggestion(text)
                                    if suggestion:
                                        data["latest_suggestion"] = suggestion
                                except Exception as e:
                                    print(f"⚠️ Suggestion: {e}")
                                
                                save_transcripts(data)
                                print("💾 Saved")
                            else:
                                print("⏭️ No speech")
                                    
                        except Exception as e:
                            print(f"❌ Error: {e}")
            
            time.sleep(0.1)
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Loop error: {e}")
            time.sleep(0.5)
    
    print("🛑 Stopped")

# Initialize session state
if "running" not in st.session_state:
    st.session_state.running = False
if "last_timestamp" not in st.session_state:
    st.session_state.last_timestamp = 0
if "auto_refresh_count" not in st.session_state:
    st.session_state.auto_refresh_count = 0

# Streamlit UI
st.set_page_config(page_title="MeetingAI", layout="wide")

# Custom CSS for smoother updates
st.markdown("""
<style>
    .stButton button {
        height: 50px;
        font-size: 18px;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .live-indicator {
        animation: pulse 2s infinite;
        color: #4CAF50;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧑‍💼 MeetingAI - Real-time Meeting Assistant")

col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("▶️ Start Meeting", use_container_width=True)
with col2:
    stop_btn = st.button("⏹️ Stop Meeting", use_container_width=True)

caption_box = st.empty()
suggestion_box = st.empty()
summary_box = st.empty()

# Start meeting
if start_btn:
    if not st.session_state.running:
        st.session_state.running = True
        st.session_state.last_timestamp = 0
        st.session_state.auto_refresh_count = 0
        
        save_transcripts({"transcripts": [], "latest_text": "", "latest_suggestion": "", "timestamp": time.time()})
        
        if thread_instance[0] is None or not thread_instance[0].is_alive():
            running_flag.set()
            thread_instance[0] = threading.Thread(target=meeting_loop, daemon=True)
            thread_instance[0].start()
            
        st.success("✅ Started!")
        time.sleep(0.5)
        st.rerun()

# Stop meeting
if stop_btn:
    if st.session_state.running:
        st.session_state.running = False
        running_flag.clear()
        
        data = load_transcripts()
        transcripts = data.get("transcripts", [])
        
        if len(transcripts) > 0:
            summary = generate_summary(transcripts)
            summary_box.success(f"📝 **Summary:**\n\n{summary}")
        else:
            summary_box.info("No transcript")
        
        time.sleep(0.5)
        st.rerun()

# Main UI
if st.session_state.running:
    
    # Load data
    data = load_transcripts()
    current_text = data.get("latest_text", "")
    current_suggestion = data.get("latest_suggestion", "")
    all_transcripts = data.get("transcripts", [])
    transcript_count = len(all_transcripts)
    file_timestamp = data.get("timestamp", 0)
    
    # Check for updates
    new_content = False
    if file_timestamp > st.session_state.last_timestamp:
        st.session_state.last_timestamp = file_timestamp
        new_content = True
    
    # Status bar
    st.markdown(f'<p class="live-indicator">🔴 LIVE</p>', unsafe_allow_html=True)
    st.caption(f"📊 Segments: {transcript_count}")
    
    # Latest caption
    if current_text:
        caption_box.markdown(
            f"""
            <div style='background-color:#e3f2fd; padding:30px; border-radius:15px; 
                        border-left: 8px solid #2196F3; margin: 20px 0;
                        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                        transition: all 0.3s ease;'>
                <p style='font-size:16px; color:#1565C0; margin:0; font-weight:bold; 
                          text-transform: uppercase; letter-spacing: 2px;'>
                    💬 Latest Transcription
                </p>
                <p style='font-size:28px; color:#000; margin-top:20px; line-height:1.8; 
                          font-weight:500; font-family: -apple-system, system-ui;'>
                    "{current_text}"
                </p>
                <p style='font-size:13px; color:#666; margin-top:20px; font-style: italic;'>
                    Segment #{transcript_count} • Just now
                </p>
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
            <div style='background-color:#f3e5f5; padding:25px; border-radius:12px; 
                        border-left: 6px solid #9C27B0; margin: 20px 0;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
                <p style='font-size:16px; color:#6A1B9A; margin:0; font-weight:bold;
                          text-transform: uppercase; letter-spacing: 1px;'>
                    🤖 AI Suggestion
                </p>
                <p style='font-size:19px; color:#333; margin-top:15px; line-height:1.6;'>
                    {current_suggestion}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Sidebar transcript
    with st.sidebar:
        st.subheader("📜 Full Transcript")
        st.metric("Total", transcript_count)
        
        if transcript_count > 0:
            st.markdown("---")
            for i, text in enumerate(reversed(all_transcripts[-10:]), 0):
                idx = transcript_count - i
                with st.container():
                    st.markdown(f"**#{idx}**")
                    st.write(text)
                    st.markdown("---")
        else:
            st.info("No transcripts yet")
    
else:
    caption_box.info("👆 Click **'▶️ Start Meeting'**")
    st.info("""
    **Setup:**
    1. VB-Cable configured ✅
    2. Audio playing through CABLE Input ✅
    3. Click Start Meeting
    4. **Captions will appear automatically!**
    """)

st.markdown("---")
st.caption("🎙️ MeetingAI • Real-time transcription")

# Auto-refresh mechanism - place at the very end
if st.session_state.running:
    time.sleep(2)  # Wait 2 seconds
    st.rerun()  # Then refresh automatically