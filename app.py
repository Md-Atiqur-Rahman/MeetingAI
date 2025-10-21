import streamlit as st
import threading
import time
import numpy as np
import queue
from streamlit_autorefresh import st_autorefresh
from src.transcriber import transcribe
from src.suggester import get_suggestion
import os
from src.summarizer import generate_summary
from src.audio_listener import start_listening, combined_queue

# Global state (thread-safe)
running_flag = threading.Event()  # Thread-safe flag
state_lock = threading.Lock()

# Shared data between thread and UI
shared_data = {
    "latest_text": "",
    "latest_suggestion": "",
    "transcript_list": []
}

# Initialize session state
if "running" not in st.session_state:
    st.session_state.running = False
if "latest_text" not in st.session_state:
    st.session_state.latest_text = ""
if "latest_suggestion" not in st.session_state:
    st.session_state.latest_suggestion = ""
if "transcript_list" not in st.session_state:
    st.session_state.transcript_list = []
if "thread_started" not in st.session_state:
    st.session_state.thread_started = False

# Streamlit UI
st.set_page_config(page_title="MeetingAI", layout="wide")
st.title("🧑‍💼 MeetingAI - Personal Meeting Assistant")

col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("▶️ Start Meeting", use_container_width=True)
with col2:
    stop_btn = st.button("⏹️ Stop Meeting", use_container_width=True)

caption_box = st.empty()
suggestion_box = st.empty()
summary_box = st.empty()

# Background thread for audio processing
audio_buffer = []
last_transcription_time = time.time()

def meeting_loop():
    """Background thread that processes audio from Teams"""
    global audio_buffer, last_transcription_time
    
    print("🎙️ Meeting loop started")
    
    # Start audio listener
    listener_thread = threading.Thread(target=start_listening(), daemon=True)
    listener_thread.start()
    
    while running_flag.is_set():
        try:
            if not combined_queue.empty():
                audio_chunk = combined_queue.get(timeout=1)
                audio_np = np.squeeze(audio_chunk).astype(np.float32)

                # Check if audio has sound
                max_amp = np.max(np.abs(audio_np))
                
                if max_amp > 0.005:  # Has sound
                    # Add to buffer
                    audio_buffer.append(audio_np)
                    
                    # Process every 3 seconds (accumulate audio)
                    current_time = time.time()
                    if current_time - last_transcription_time >= 3.0 and len(audio_buffer) > 0:
                        print(f"🎤 Processing {len(audio_buffer)} audio chunks...")
                        
                        # Concatenate buffered audio
                        combined_audio = np.concatenate(audio_buffer)
                        audio_buffer = []  # Clear buffer
                        last_transcription_time = current_time
                        
                        try:
                            # Transcribe the combined audio
                            text = transcribe(combined_audio)
                            
                            if text and len(text.strip()) > 2:
                                print(f"✅ Transcribed: {text}")
                                
                                # Thread-safe state update
                                with state_lock:
                                    shared_data["transcript_list"].append(text)
                                    shared_data["latest_text"] = text
                                    
                                    # Get AI suggestion
                                    try:
                                        suggestion = get_suggestion(text)
                                        if suggestion:
                                            shared_data["latest_suggestion"] = suggestion
                                            print(f"🤖 Suggestion: {suggestion[:100]}...")
                                    except Exception as e:
                                        print(f"⚠️ Suggestion error: {e}")
                                        shared_data["latest_suggestion"] = ""
                            else:
                                print("⏭️ No clear speech detected")
                                    
                        except Exception as e:
                            print(f"❌ Transcription error: {e}")
            
            time.sleep(0.1)
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Loop error: {e}")
            time.sleep(0.5)
    
    print("🛑 Meeting loop stopped")

# Start meeting
if start_btn:
    if not st.session_state.running:
        st.session_state.running = True
        st.session_state.latest_text = ""
        st.session_state.latest_suggestion = ""
        st.session_state.transcript_list = []
        
        # Reset shared data
        with state_lock:
            shared_data["latest_text"] = ""
            shared_data["latest_suggestion"] = ""
            shared_data["transcript_list"] = []
        
        # Start background thread
        running_flag.set()  # Set the flag to True
        
        if not st.session_state.thread_started:
            thread = threading.Thread(target=meeting_loop, daemon=True)
            thread.start()
            st.session_state.thread_started = True
            
        st.success("✅ Meeting started. Listening to Teams audio...")
        time.sleep(1)
        st.rerun()

# Stop meeting
if stop_btn:
    if st.session_state.running:
        st.session_state.running = False
        running_flag.clear()  # Set the flag to False
        
        st.warning("⏹️ Meeting stopped. Generating summary...")
        
        # Get final transcript from shared data
        with state_lock:
            final_transcript = shared_data["transcript_list"].copy()
        
        st.session_state.transcript_list = final_transcript
        
        # Generate summary
        if len(final_transcript) > 0:
            with st.spinner("Generating AI summary..."):
                summary = generate_summary(final_transcript)
                summary_box.success(f"📝 **Meeting Summary:**\n\n{summary}")
        else:
            summary_box.info("No transcript available to summarize.")
        
        time.sleep(1)
        st.rerun()

# Display real-time captions and suggestions
if st.session_state.running:
    # Auto-refresh every 2 seconds
    st_autorefresh(interval=2000, limit=None, key="meeting_refresh")
    
    # Get latest data from shared state
    with state_lock:
        current_text = shared_data["latest_text"]
        current_suggestion = shared_data["latest_suggestion"]
        transcript_count = len(shared_data["transcript_list"])
    
    # Update session state for display
    st.session_state.latest_text = current_text
    st.session_state.latest_suggestion = current_suggestion
    
    # Display latest caption
    if current_text:
        caption_box.markdown(
            f"""
            <div style='background-color:#e3f2fd; padding:15px; border-radius:10px; 
                        border-left: 5px solid #2196F3; margin-bottom: 10px;'>
                <p style='font-size:20px; color:#1565C0; margin:0;'>
                    <strong>💬 Live Caption:</strong>
                </p>
                <p style='font-size:18px; color:#333; margin-top:10px;'>
                    {current_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        caption_box.info("🎧 Listening... Waiting for speech...")
    
    # Display AI suggestion
    if current_suggestion:
        suggestion_box.markdown(
            f"""
            <div style='background-color:#f3e5f5; padding:15px; border-radius:10px; 
                        border-left: 5px solid #9C27B0;'>
                <p style='font-size:18px; color:#6A1B9A; margin:0;'>
                    <strong>🤖 AI Suggestion:</strong>
                </p>
                <p style='font-size:16px; color:#333; margin-top:10px;'>
                    {current_suggestion}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Show transcript history in sidebar
    with st.sidebar:
        st.subheader("📜 Transcript History")
        st.write(f"Total segments: {transcript_count}")
        
        if transcript_count > 0:
            with st.expander("View Recent Transcript"):
                with state_lock:
                    recent_transcripts = shared_data["transcript_list"][-10:]
                for i, text in enumerate(recent_transcripts, 1):
                    st.text(f"{i}. {text}")
else:
    caption_box.info("👆 Click 'Start Meeting' to begin live transcription")
    
# Footer
st.markdown("---")
st.caption("💡 Tip: Make sure Teams audio is playing through your speakers")
st.caption("🔊 Audio amplification is active - works with low volume too!")
# st.caption("Developed by OpenAI ChatGPT")
st.caption("© 2024 MeetingAI")