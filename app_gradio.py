import gradio as gr
import threading
import time
import numpy as np
import queue
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from transcriber import transcribe
    from translator import translate_to_bangla
    from summarizer import generate_summary
    from audio_listener import start_listening, combined_queue
    from speaker_identifier import identify_speaker, reset_speakers
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️ Running without speaker identification")
    
    # Fallback: no speaker identification
    def identify_speaker(audio, samplerate=16000):
        return "Person-1"
    
    def reset_speakers():
        pass

# Global state
running_flag = threading.Event()
audio_buffer = []
thread_instance = [None]

# Shared state for real-time updates
latest_english = ["Waiting for speech..."]
latest_bangla = ["বক্তৃতার জন্য অপেক্ষা করছি..."]
all_transcripts = []
transcript_counter = [0]
current_segment = {"speaker": None, "text": "", "text_bn": ""}  # Accumulating current segment

def split_into_sentences(text):
    """Split text into sentences"""
    import re
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
    return result if result else [text]

def meeting_loop():
    """Background thread for real-time transcription"""
    global audio_buffer
    
    print("🎙️ Meeting loop started (GRADIO REAL-TIME)")
    
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
                                # Identify speaker (fast, cached)
                                speaker = identify_speaker(audio, samplerate=16000)
                                
                                # Transcribe (GPU accelerated)
                                text = transcribe(audio)
                                
                                if text and len(text.strip()) > 2:
                                    print(f"⚡ [{speaker}] {text}")
                                    
                                    # Check if same speaker or new speaker
                                    if current_segment["speaker"] is None:
                                        current_segment["speaker"] = speaker
                                        current_segment["text"] = text
                                        current_segment["text_bn"] = ""
                                        
                                    elif current_segment["speaker"] == speaker:
                                        # Same speaker - keep appending
                                        current_segment["text"] += " " + text
                                        
                                    else:
                                        # Different speaker - save & start new
                                        if current_segment["text"]:
                                            # Translate in background (non-blocking)
                                            prev_text = current_segment["text"]
                                            prev_speaker = current_segment["speaker"]
                                            
                                            def translate_and_save():
                                                try:
                                                    text_bn = translate_to_bangla(prev_text)
                                                    all_transcripts.append({
                                                        "speaker": prev_speaker,
                                                        "en": prev_text,
                                                        "bn": text_bn if text_bn else "",
                                                        "time": time.strftime("%H:%M:%S")
                                                    })
                                                    transcript_counter[0] += 1
                                                except Exception as e:
                                                    print(f"⚠️ Translation error: {e}")
                                            
                                            # Run translation async (don't wait)
                                            threading.Thread(target=translate_and_save, daemon=True).start()
                                        
                                        # Immediately start new segment (no blocking)
                                        current_segment["speaker"] = speaker
                                        current_segment["text"] = text
                                        current_segment["text_bn"] = ""
                                    
                            except Exception as e:
                                print(f"❌ {e}")
                        
                        threading.Thread(target=process_audio, args=(combined_audio,), daemon=True).start()
            
            time.sleep(0.01)
        except:
            time.sleep(0.01)
    
    print("🛑 Stopped")

def start_meeting():
    """Start the meeting transcription"""
    global all_transcripts, current_segment
    all_transcripts = []
    transcript_counter[0] = 0
    latest_english[0] = "🎧 Listening..."
    latest_bangla[0] = "🎧 শুনছি..."
    current_segment = {"speaker": None, "text": "", "text_bn": ""}
    
    # Reset speaker identification
    reset_speakers()
    
    if thread_instance[0] is None or not thread_instance[0].is_alive():
        running_flag.set()
        thread_instance[0] = threading.Thread(target=meeting_loop, daemon=True)
        thread_instance[0].start()
        
        return (
            "✅ Meeting started! Streaming word-by-word transcription active...",
            "🎧 Listening... Waiting for speech...",
            "🎧 শুনছি... বক্তৃতার জন্য অপেক্ষা করছি...",
            "🟢 LIVE | Segments: 0"
        )
    return "⚠️ Already running", "", "", ""

def stop_meeting():
    """Stop the meeting and generate summary"""
    running_flag.clear()
    time.sleep(0.5)  # Give time to stop
    
    if len(all_transcripts) > 0:
        transcripts_en = [t["en"] for t in all_transcripts]
        summary = generate_summary(transcripts_en)
        
        # Return summary + stop status
        return (
            summary,
            "⏹️ Meeting stopped",
            "⚪ STOPPED | Meeting ended"
        )
    
    return (
        "No transcripts to summarize",
        "⏹️ Meeting stopped (no transcripts)",
        "⚪ STOPPED"
    )

def get_current_captions():
    """Get current live captions with streaming text"""
    count = transcript_counter[0]
    status = f"🟢 LIVE | Segments: {count}" if running_flag.is_set() else "⚪ Stopped"
    
    # Get last 10 completed transcripts
    recent = all_transcripts[-10:] if len(all_transcripts) > 0 else []
    
    # Build English output
    en_text = ""
    
    # Show completed transcripts
    if len(recent) > 0:
        for i, t in enumerate(recent):
            speaker = t.get('speaker', 'Unknown')
            text_content = t.get('en', '')
            
            # Extract speaker number safely
            try:
                speaker_str = speaker.split()[0]
                if 'Person-' in speaker_str:
                    speaker_num = int(speaker_str.split('-')[1])
                else:
                    speaker_num = 0
            except:
                speaker_num = 0
            
            is_right_aligned = (speaker_num % 2 == 0)
            indent = "                              " if is_right_aligned else ""
            
            en_text += f"{indent}{speaker}: {text_content}\n\n"
    
    # Add current incomplete segment (streaming)
    if current_segment["text"]:
        speaker = current_segment["speaker"]
        text_content = current_segment["text"]
        
        try:
            speaker_str = speaker.split()[0] if speaker else "Unknown"
            if 'Person-' in speaker_str:
                speaker_num = int(speaker_str.split('-')[1])
            else:
                speaker_num = 0
        except:
            speaker_num = 0
        
        is_right_aligned = (speaker_num % 2 == 0)
        indent = "                              " if is_right_aligned else ""
        
        # Highlight as LIVE (incomplete) with streaming indicator
        en_text += f"{indent}🔴 {speaker}: {text_content}\n\n"
    
    if not en_text:
        en_text = "🎧 Listening... Waiting for speech..."
    
    # Build Bangla output (same logic)
    bn_text = ""
    
    if len(recent) > 0:
        for i, t in enumerate(recent):
            speaker = t.get('speaker', 'Unknown')
            bn = t.get('bn', '') if t.get('bn', '') else "[অনুবাদ মুলতুবি...]"
            
            try:
                speaker_str = speaker.split()[0]
                if 'Person-' in speaker_str:
                    speaker_num = int(speaker_str.split('-')[1])
                else:
                    speaker_num = 0
            except:
                speaker_num = 0
            
            is_right_aligned = (speaker_num % 2 == 0)
            indent = "                              " if is_right_aligned else ""
            
            bn_text += f"{indent}{speaker}: {bn}\n\n"
    
    # Add current incomplete segment (NO TRANSLATION for live - faster!)
    if current_segment["text"]:
        speaker = current_segment["speaker"]
        
        # Skip live translation to reduce latency
        bn = "[সরাসরি চলছে... অনুবাদ পরে]"
        bn = current_segment.get("text_bn", "") if current_segment.get("text_bn", "") else "[অনুবাদ হচ্ছে...]"
        
        try:
            speaker_str = speaker.split()[0] if speaker else "Unknown"
            if 'Person-' in speaker_str:
                speaker_num = int(speaker_str.split('-')[1])
            else:
                speaker_num = 0
        except:
            speaker_num = 0
        
        is_right_aligned = (speaker_num % 2 == 0)
        indent = "                              " if is_right_aligned else ""
        
        bn_text += f"{indent}🔴 {speaker}: {bn}\n\n"
    
    if not bn_text:
        bn_text = "🎧 শুনছি... বক্তৃতার জন্য অপেক্ষা করছি..."
    
    return en_text, bn_text, status

def get_transcript_history():
    """Get full transcript history with speaker labels"""
    if len(all_transcripts) == 0:
        return "📭 No transcripts yet. Start speaking!"
    
    history = f"## 📜 Full Transcript ({len(all_transcripts)} segments)\n\n"
    for i, t in enumerate(reversed(all_transcripts[-15:]), 1):
        idx = len(all_transcripts) - i + 1
        speaker = t.get('speaker', 'Unknown')
        history += f"### [{t['time']}] {speaker}\n\n"
        history += f"**🇬🇧 English:**  \n{t['en']}\n\n"
        if t['bn']:
            history += f"**🇧🇩 বাংলা:**  \n{t['bn']}\n\n"
        history += "---\n\n"
    
    return history

# Gradio Interface
with gr.Blocks(
    title="MeetingAI - Real-time Transcription", 
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange")
) as demo:
    
    gr.Markdown("""
    # 🧑‍💼 MeetingAI - Zero Latency Transcription ⚡
    **GPU Accelerated | English + বাংলা Translation**
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            start_btn = gr.Button("▶️ Start Meeting", variant="primary", size="lg")
        with gr.Column(scale=2):
            stop_btn = gr.Button("⏹️ Stop Meeting", variant="stop", size="lg")
        with gr.Column(scale=3):
            status_display = gr.Textbox(label="Status", interactive=False, value="⚪ Ready")
    
    status_text = gr.Textbox(label="System Message", interactive=False, visible=False)
    
    gr.Markdown("## 💬 Live Captions (Real-time)")
    
    with gr.Row():
        with gr.Column():
            english_output = gr.Textbox(
                label="🇬🇧 English (Last 10 Segments)", 
                lines=12,
                value="Click 'Start Meeting' to begin...",
                interactive=False,
                show_copy_button=True,
                autoscroll=True,  # Auto-scroll to bottom
                max_lines=15
            )
        
        with gr.Column():
            bangla_output = gr.Textbox(
                label="🇧🇩 বাংলা (শেষ ১০টি সেগমেন্ট)", 
                lines=12,
                value="'Start Meeting' ক্লিক করুন...",
                interactive=False,
                show_copy_button=True,
                autoscroll=True,  # Auto-scroll to bottom
                max_lines=15
            )
    
    with gr.Accordion("📜 Transcript History", open=False):
        transcript_display = gr.Markdown("Click 'Start Meeting' to begin")
    
    with gr.Accordion("📝 Meeting Summary", open=False):
        summary_output = gr.Markdown("Stop the meeting to generate summary")
    
    # Event handlers
    start_event = start_btn.click(
        fn=start_meeting,
        outputs=[status_text, english_output, bangla_output, status_display]
    )
    
    stop_event = stop_btn.click(
        fn=stop_meeting,
        outputs=[summary_output, status_text, status_display]
    )
    
    # Continuous polling for live updates
    demo.load(
        fn=get_current_captions,
        outputs=[english_output, bangla_output, status_display],
        show_progress=False
    )
    
    # Refresh captions every 200ms (EXTREME SPEED!)
    caption_refresh = gr.Timer(0.2)
    caption_refresh.tick(
        fn=get_current_captions,
        outputs=[english_output, bangla_output, status_display]
    )
    
    # Refresh transcript every 2 seconds
    transcript_refresh = gr.Timer(2)
    transcript_refresh.tick(
        fn=get_transcript_history,
        outputs=transcript_display
    )

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting MeetingAI with Gradio")
    print("="*60)
    print("📊 GPU accelerated transcription")
    print("🌐 Access at: http://localhost:7860")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )