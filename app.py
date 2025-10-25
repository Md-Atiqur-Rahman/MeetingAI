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
from src.translator import translate_to_bangla
from src.audio_listener import start_listening, combined_queue
import json
import os

# File-based communication
TRANSCRIPT_FILE = "temp_transcript.json"

# Global thread control
running_flag = threading.Event()
audio_buffer = []
thread_instance = [None]

def save_transcripts(data):
    """Save transcript data to file"""
    # Ensure all keys exist
    if "transcripts_bn" not in data:
        data["transcripts_bn"] = []
    if "latest_text_bn" not in data:
        data["latest_text_bn"] = ""
    
    with open(TRANSCRIPT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_transcripts():
    """Load transcript data from file"""
    if os.path.exists(TRANSCRIPT_FILE):
        try:
            with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "transcripts": [], 
                "transcripts_bn": [],  # Bangla translations
                "latest_text": "", 
                "latest_text_bn": "",  # Latest Bangla
                "latest_suggestion": "", 
                "timestamp": time.time()
            }
    return {
        "transcripts": [], 
        "transcripts_bn": [], 
        "latest_text": "", 
        "latest_text_bn": "",
        "latest_suggestion": "", 
        "timestamp": time.time()
    }

def split_into_sentences(text):
    """Split text into sentences at natural boundaries"""
    # Split on common sentence endings
    sentences = re.split(r'([.!?]+\s+|,\s+(?=[A-Z]))', text)
    
    result = []
    current = ""
    
    for part in sentences:
        current += part
        # If it ends with punctuation and space, it's a sentence boundary
        if re.search(r'[.!?]+\s*$', part):
            if current.strip():
                result.append(current.strip())
            current = ""
    
    # Add remaining text
    if current.strip():
        result.append(current.strip())
    
    # If no good splits, return as single sentence
    if not result:
        return [text]
    
    return result

def meeting_loop():
    """Background thread for REAL-TIME audio processing with GPU"""
    global audio_buffer
    
    print("🎙️ Meeting loop started (REAL-TIME GPU MODE)")
    
    listener_thread = threading.Thread(target=start_listening(), daemon=True)
    listener_thread.start()
    
    silence_counter = 0
    MIN_AUDIO_LENGTH = 8000    # 0.5 seconds minimum
    MAX_AUDIO_LENGTH = 32000   # 2 seconds max (faster response)
    SILENCE_THRESHOLD = 2      # 0.2 seconds silence (very responsive!)
    
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
                    
                    # AGGRESSIVE: Process quickly when pause detected
                    should_process = (
                        (total_samples >= MIN_AUDIO_LENGTH and silence_counter >= SILENCE_THRESHOLD) or
                        total_samples >= MAX_AUDIO_LENGTH
                    )
                    
                    if should_process:
                        combined_audio = np.concatenate(audio_buffer)
                        audio_buffer = []
                        silence_counter = 0
                        
                        # Process in separate thread to not block audio capture
                        def process_audio(audio):
                            try:
                                text = transcribe(audio)
                                
                                if text and len(text.strip()) > 2:
                                    duration = len(audio) / 16000
                                    print(f"\n{'='*60}")
                                    print(f"✅ [{duration:.1f}s] EN: {text}")
                                    
                                    # Translate to Bangla
                                    print("🔄 Translating to Bangla...")
                                    text_bn = translate_to_bangla(text)
                                    
                                    if text_bn:
                                        print(f"🇧🇩 [{duration:.1f}s] BN: {text_bn}")
                                    else:
                                        print("❌ Translation failed - empty result")
                                    
                                    print(f"{'='*60}\n")
                                    
                                    # Split into natural segments
                                    sentences = split_into_sentences(text)
                                    
                                    data = load_transcripts()
                                    
                                    # Ensure Bangla keys exist
                                    if "transcripts_bn" not in data:
                                        data["transcripts_bn"] = []
                                    if "latest_text_bn" not in data:
                                        data["latest_text_bn"] = ""
                                    
                                    for sentence in sentences:
                                        if sentence.strip():
                                            # Translate each sentence
                                            print(f"🔄 Translating sentence: {sentence[:50]}...")
                                            sentence_bn = translate_to_bangla(sentence)
                                            print(f"✅ Got translation: {sentence_bn[:50] if sentence_bn else 'EMPTY'}")
                                            
                                            data["transcripts"].append(sentence.strip())
                                            data["transcripts_bn"].append(sentence_bn if sentence_bn else "")
                                            data["latest_text"] = sentence.strip()
                                            data["latest_text_bn"] = sentence_bn if sentence_bn else ""
                                    
                                    data["timestamp"] = time.time()
                                    save_transcripts(data)
                                    print("💾 Data saved with translations")
                                    
                            except Exception as e:
                                print(f"❌ Error in process_audio: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Process async to maintain low latency
                        threading.Thread(target=process_audio, args=(combined_audio,), daemon=True).start()
            
            time.sleep(0.01)  # Ultra-fast polling (10ms)
            
        except queue.Empty:
            time.sleep(0.01)
        except Exception as e:
            print(f"❌ Loop error: {e}")
            time.sleep(0.1)
    
    print("🛑 Stopped")

# Initialize session state
if "running" not in st.session_state:
    st.session_state.running = False
if "last_timestamp" not in st.session_state:
    st.session_state.last_timestamp = 0

# Streamlit UI
st.set_page_config(page_title="MeetingAI", layout="wide")

# Custom CSS
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

st.title("🧑‍💼 MeetingAI - Real-time Meeting Assistant ⚡ GPU")

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
        
        # Initialize with all required keys
        save_transcripts({
            "transcripts": [], 
            "transcripts_bn": [],
            "latest_text": "", 
            "latest_text_bn": "",
            "latest_suggestion": "", 
            "timestamp": time.time()
        })
        
        if thread_instance[0] is None or not thread_instance[0].is_alive():
            running_flag.set()
            thread_instance[0] = threading.Thread(target=meeting_loop, daemon=True)
            thread_instance[0].start()
            
        st.success("✅ Meeting started! GPU-accelerated transcription active")
        time.sleep(0.5)
        st.rerun()

# Stop meeting
if stop_btn:
    if st.session_state.running:
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
        
        st.info("👆 Summary generated! You can now start a new meeting.")

# Main UI
if st.session_state.running:
    
    # AUTO-REFRESH: This runs every 2 seconds
    count = st_autorefresh(interval=2000, key="datarefresh")
    
    # Load data
    data = load_transcripts()
    current_text = data.get("latest_text", "")
    current_text_bn = data.get("latest_text_bn", "")  # Bangla translation
    current_suggestion = data.get("latest_suggestion", "")
    all_transcripts = data.get("transcripts", [])
    all_transcripts_bn = data.get("transcripts_bn", [])
    transcript_count = len(all_transcripts)
    
    # Status bar
    st.markdown(f'<p class="live-indicator">🔴 LIVE - GPU Mode (Updates: {count})</p>', unsafe_allow_html=True)
    st.caption(f"📊 Segments: {transcript_count}")
    
    # Latest caption - English + Bangla
    # print("🇬🇧 English-", current_text)
    # print("🇬🇧 English-", current_text)
    if current_text:
        caption_box.markdown(
            f"""
            <div style='background-color:#e3f2fd; padding:30px; border-radius:15px; 
                        border-left: 8px solid #2196F3; margin: 20px 0;
                        box-shadow: 0 6px 12px rgba(0,0,0,0.15);'>
                <p style='font-size:14px; color:#1565C0; margin:0; font-weight:bold; 
                          text-transform: uppercase; letter-spacing: 2px;'>
                    🇬🇧 English
                </p>
                <p style='font-size:26px; color:#000; margin-top:15px; line-height:1.8; 
                          font-weight:500; font-family: -apple-system, system-ui;'>
                    "{current_text}"
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Show Bangla translation if available
        if current_text_bn:
            caption_box.markdown(
                f"""
                <div style='background-color:#fff3e0; padding:30px; border-radius:15px; 
                            border-left: 8px solid #ff6f00; margin: 20px 0;
                            box-shadow: 0 6px 12px rgba(0,0,0,0.15);'>
                    <p style='font-size:14px; color:#e65100; margin:0; font-weight:bold; 
                              text-transform: uppercase; letter-spacing: 2px;'>
                        🇧🇩 বাংলা
                    </p>
                    <p style='font-size:26px; color:#000; margin-top:15px; line-height:1.8; 
                          font-weight:500; font-family: -apple-system, system-ui;'>
                    "{current_text}"
                    </p>
                    <p style='font-size:26px; color:#000; margin-top:15px; line-height:1.8; 
                              font-weight:500; font-family: "Noto Sans Bengali", system-ui;'>
                        "{current_text_bn}"
                    </p>
                    <p style='font-size:13px; color:#666; margin-top:15px; font-style: italic;'>
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
        
        # Show GPU info
        st.markdown("---")
        st.subheader("⚙️ System Info")
        try:
            import torch
            if torch.cuda.is_available():
                st.success(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
                st.caption(f"CUDA: {torch.version.cuda}")
            else:
                st.warning("💻 Running on CPU")
        except:
            pass
        
        st.markdown("---")
        
        if transcript_count > 0:
            st.markdown("**Recent Transcriptions (EN + BN):**")
            for i, (text, text_bn) in enumerate(zip(reversed(all_transcripts[-10:]), reversed(all_transcripts_bn[-10:])), 0):
                idx = transcript_count - i
                with st.container():
                    st.markdown(f"**#{idx}**")
                    st.write(f"🇬🇧 {text}")
                    if text_bn:
                        st.write(f"🇧🇩 {text_bn}")
                    st.markdown("---")
        else:
            st.info("No transcripts yet")
    
else:
    caption_box.info("👆 Click **'▶️ Start Meeting'**")
    
    with st.expander("ℹ️ How to Use", expanded=False):
        st.markdown("""
        **Setup:**
        1. ✅ VB-Cable configured
        2. ✅ Audio playing through CABLE Input
        3. ✅ GPU detected for faster-whisper
        4. ✅ Click Start Meeting
        5. ✅ Real-time captions appear automatically!
        
        **For Teams meetings:**
        - Set Teams audio output to CABLE Input
        - Keep this app open during the meeting
        - Click Stop Meeting when done for summary
        
        **Performance:**
        - GPU accelerated transcription (50-200ms latency)
        - Near-instant captions like YouTube
        """)

st.markdown("---")
st.caption("🎙️ MeetingAI • Real-time transcription with Whisper AI (GPU)")