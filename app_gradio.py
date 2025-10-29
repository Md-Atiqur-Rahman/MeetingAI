import gradio as gr
import threading
import time
import numpy as np
import queue
import json
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from transcriber import transcribe
    from translator import translate_to_bangla
    from summarizer import generate_summary
    from audio_listener import start_listening, combined_queue
    from speaker_identifier import identify_speaker, reset_speakers
    from ai_summarizer import generate_ai_summary  # NEW: Gemini-only AI summarizer
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️ Running with limited functionality")
    
    def identify_speaker(audio, samplerate=16000):
        return "Person-1"
    
    def reset_speakers():
        pass
    
    def generate_ai_summary(transcripts):
        return "❌ AI Summarizer module not found. Check ai_summarizer.py"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to configure AI models (OpenAI or Gemini)
AI_MODEL = None
AI_TYPE = None

# Try OpenAI first
try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        import openai
        openai.api_key = OPENAI_API_KEY
        AI_MODEL = "gpt-3.5-turbo"  # or "gpt-4" for better quality
        AI_TYPE = "openai"
        print(f"✅ Using OpenAI: {AI_MODEL}")
except Exception as e:
    print(f"⚠️ OpenAI not available: {e}")

# Fallback to Gemini if OpenAI not available
if not AI_MODEL:
    try:
        GENAI_API_KEY = os.getenv("GENAI_API_KEY")
        if GENAI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GENAI_API_KEY)
            
            # Latest Gemini models (2024-2025)
            model_names = [
                "models/gemini-2.5-flash",           # Latest, fastest
                "models/gemini-2.0-flash",           # Stable, fast
                "models/gemini-flash-latest",        # Auto-updated
                "models/gemini-pro-latest",          # High quality
                "models/gemini-2.5-pro",             # Most powerful
            ]
            
            for model_name in model_names:
                try:
                    AI_MODEL = genai.GenerativeModel(model_name)
                    # Quick test
                    test_response = AI_MODEL.generate_content("Hi")
                    AI_TYPE = "gemini"
                    print(f"✅ Using Gemini: {model_name}")
                    break
                except Exception as e:
                    print(f"⚠️ {model_name} not available: {str(e)[:50]}")
                    continue
    except Exception as e:
        print(f"⚠️ Gemini initialization failed: {e}")

if not AI_MODEL:
    print("⚠️ No AI model configured. Add OPENAI_API_KEY or GENAI_API_KEY to .env file")

# Global state
running_flag = threading.Event()
audio_buffer = []
thread_instance = [None]

# Shared state for real-time updates
latest_english = ["Waiting for speech..."]
latest_bangla = ["বক্তৃতার জন্য অপেক্ষা করছি..."]
all_transcripts = []
transcript_counter = [0]
current_segment = {
    "speaker": None, 
    "text": "", 
    "text_bn_temp": "",      # Phase 1: Word-by-word (temporary)
    "text_bn_final": "",     # Phase 2: Context-aware (saved)
    "is_translating": False  # Flag to show translation in progress
}

def word_by_word_translate(text):
    """
    Phase 1: Quick word-by-word translation (NOT SAVED)
    This is just for instant visual feedback
    """
    # Simple word mapping for common words (extend as needed)
    word_map = {
        "hello": "হ্যালো", "hi": "হাই", "good": "ভালো", "morning": "সকাল",
        "afternoon": "বিকাল", "evening": "সন্ধ্যা", "night": "রাত",
        "thank": "ধন্যবাদ", "you": "আপনি", "yes": "হ্যাঁ", "no": "না",
        "please": "দয়া করে", "can": "পারেন", "the": "", "is": "হয়",
        "are": "আছে", "what": "কি", "how": "কিভাবে", "when": "কখন",
        "where": "কোথায়", "who": "কে", "why": "কেন", "meeting": "মিটিং",
        "discussion": "আলোচনা", "project": "প্রকল্প", "team": "দল",
        "work": "কাজ", "today": "আজ", "tomorrow": "আগামীকাল",
        "report": "রিপোর্ট", "update": "আপডেট", "question": "প্রশ্ন",
        "answer": "উত্তর", "time": "সময়", "break": "বিরতি", "okay": "ঠিক আছে"
    }
    
    words = text.lower().split()
    translated_words = []
    
    for word in words:
        # Clean punctuation
        clean_word = word.strip('.,!?;:')
        translated = word_map.get(clean_word, word)  # Fallback to original if not found
        translated_words.append(translated)
    
    return " ".join(translated_words)

def context_aware_translate(text):
    """
    Phase 2: Full context-aware translation (SAVED)
    Uses the actual translator module
    """
    try:
        return translate_to_bangla(text)
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return ""

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
    
    print("🎙️ Meeting loop started (2-PHASE TRANSLATION)")
    
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
                                        
                                        # Phase 1: Instant word-by-word (NOT SAVED)
                                        current_segment["text_bn_temp"] = word_by_word_translate(text)
                                        current_segment["text_bn_final"] = ""
                                        current_segment["is_translating"] = True
                                        
                                        # Phase 2: Background context-aware translation
                                        def translate_contextual():
                                            final_bn = context_aware_translate(text)
                                            current_segment["text_bn_final"] = final_bn
                                            current_segment["is_translating"] = False
                                            print(f"✅ Translation complete: {final_bn[:50]}...")
                                        
                                        threading.Thread(target=translate_contextual, daemon=True).start()
                                        
                                    elif current_segment["speaker"] == speaker:
                                        # Same speaker - keep appending
                                        current_segment["text"] += " " + text
                                        
                                        # Update Phase 1 (instant word-by-word)
                                        current_segment["text_bn_temp"] = word_by_word_translate(current_segment["text"])
                                        current_segment["is_translating"] = True
                                        
                                        # Update Phase 2 (background context-aware)
                                        full_text = current_segment["text"]
                                        def update_translation():
                                            final_bn = context_aware_translate(full_text)
                                            current_segment["text_bn_final"] = final_bn
                                            current_segment["is_translating"] = False
                                        
                                        threading.Thread(target=update_translation, daemon=True).start()
                                        
                                    else:
                                        # Different speaker - save previous & start new
                                        if current_segment["text"]:
                                            prev_text = current_segment["text"]
                                            prev_speaker = current_segment["speaker"]
                                            prev_bn = current_segment["text_bn_final"]
                                            
                                            # Wait a bit for final translation if still processing
                                            if current_segment["is_translating"]:
                                                time.sleep(0.5)  # Short wait for translation to complete
                                                prev_bn = current_segment["text_bn_final"]
                                            
                                            # Save ONLY the final context-aware translation
                                            all_transcripts.append({
                                                "speaker": prev_speaker,
                                                "en": prev_text,
                                                "bn": prev_bn if prev_bn else "[Translation pending]",
                                                "time": time.strftime("%H:%M:%S")
                                            })
                                            transcript_counter[0] += 1
                                            print(f"💾 Saved segment {transcript_counter[0]}")
                                        
                                        # Start new segment
                                        current_segment["speaker"] = speaker
                                        current_segment["text"] = text
                                        current_segment["text_bn_temp"] = word_by_word_translate(text)
                                        current_segment["text_bn_final"] = ""
                                        current_segment["is_translating"] = True
                                        
                                        # Phase 2 for new segment
                                        def translate_new():
                                            final_bn = context_aware_translate(text)
                                            current_segment["text_bn_final"] = final_bn
                                            current_segment["is_translating"] = False
                                        
                                        threading.Thread(target=translate_new, daemon=True).start()
                                    
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
    current_segment = {
        "speaker": None, 
        "text": "", 
        "text_bn_temp": "",
        "text_bn_final": "",
        "is_translating": False
    }
    
    reset_speakers()
    
    if thread_instance[0] is None or not thread_instance[0].is_alive():
        running_flag.set()
        thread_instance[0] = threading.Thread(target=meeting_loop, daemon=True)
        thread_instance[0].start()
        
        return (
            "✅ Meeting started! 2-Phase translation active (Word-by-word → Context-aware)...",
            "🎧 Listening... Waiting for speech...",
            "🎧 শুনছি... বক্তৃতার জন্য অপেক্ষা করছি...",
            "🟢 LIVE | Segments: 0"
        )
    return "⚠️ Already running", "", "", ""

def stop_meeting():
    """Stop the meeting"""
    running_flag.clear()
    
    # Save current segment before stopping
    if current_segment["text"]:
        if current_segment["is_translating"]:
            time.sleep(1)  # Wait for translation
        
        all_transcripts.append({
            "speaker": current_segment["speaker"],
            "en": current_segment["text"],
            "bn": current_segment["text_bn_final"] if current_segment["text_bn_final"] else "[Translation pending]",
            "time": time.strftime("%H:%M:%S")
        })
    
    time.sleep(0.5)
    
    # Return message for status
    return "⏹️ Meeting stopped. Click 'Show Summary' to view transcript."

def show_basic_summary():
    """Generate basic summary without AI"""
    if len(all_transcripts) == 0:
        return "📭 No transcripts yet. Start the meeting first!"
    
    # Statistics
    total_segments = len(all_transcripts)
    total_words_en = sum(len(t["en"].split()) for t in all_transcripts)
    total_words_bn = sum(len(t["bn"].split()) for t in all_transcripts)
    
    # Build summary
    summary = f"""## 📊 Meeting Summary

**📈 Statistics:**
- Total Segments: {total_segments}
- Total Words (English): {total_words_en}
- Total Words (বাংলা): {total_words_bn}
- Estimated Duration: ~{total_segments * 5} seconds

---

## 📝 Full Transcript:

"""
    
    # Add all segments with speaker labels
    for i, t in enumerate(all_transcripts, 1):
        summary += f"### {i}. [{t['time']}] {t.get('speaker', 'Unknown')}\n\n"
        summary += f"**🇬🇧 EN:** {t['en']}\n\n"
        if t['bn']:
            summary += f"**🇧🇩 BN:** {t['bn']}\n\n"
        summary += "---\n\n"
    
    summary += "\n💡 **Click 'Generate AI Summary' for intelligent insights and suggestions!**"
    
    return summary

def generate_ai_summary_ui():
    """
    Generate AI-powered summary using separate ai_summarizer.py module
    Uses ONLY Gemini (100% FREE) - No OpenAI
    """
    if len(all_transcripts) == 0:
        return "📭 No transcripts available for AI summary."
    
    try:
        # Call the separate ai_summarizer module (Gemini only)
        summary = generate_ai_summary(all_transcripts)
        return summary
    except Exception as e:
        return f"""❌ AI Summary Error

**Error:** {str(e)}

**Troubleshooting:**

1. **Check ai_summarizer.py file:**
   - File must be in same directory as app_gradio.py
   - File name: `ai_summarizer.py`

2. **Check GENAI_API_KEY:**
   - Get free key: https://makersuite.google.com/app/apikey
   - Add to .env: `GENAI_API_KEY=AIzaSy...`

3. **Install Gemini library:**
   ```bash
   pip install google-generativeai
   ```

4. **Test ai_summarizer separately:**
   ```bash
   python ai_summarizer.py
   ```

**Fallback:** Use 'Show Summary' button for basic transcript view.
"""

def get_current_captions():
    """Get current live captions with 2-phase translation"""
    count = transcript_counter[0]
    status = f"🟢 LIVE | Segments: {count}" if running_flag.is_set() else "⚪ Stopped"
    
    # Get last 10 completed transcripts
    recent = all_transcripts[-10:] if len(all_transcripts) > 0 else []
    
    # Build English output
    en_text = ""
    
    if len(recent) > 0:
        for t in recent:
            speaker = t.get('speaker', 'Unknown')
            text_content = t.get('en', '')
            
            try:
                speaker_str = speaker.split()[0]
                speaker_num = int(speaker_str.split('-')[1]) if 'Person-' in speaker_str else 0
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
            speaker_num = int(speaker_str.split('-')[1]) if 'Person-' in speaker_str else 0
        except:
            speaker_num = 0
        
        is_right_aligned = (speaker_num % 2 == 0)
        indent = "                              " if is_right_aligned else ""
        
        en_text += f"{indent}🔴 {speaker}: {text_content}\n\n"
    
    if not en_text:
        en_text = "🎧 Listening... Waiting for speech..."
    
    # Build Bangla output with 2-PHASE TRANSLATION
    bn_text = ""
    
    # Show completed segments (with FINAL translation only)
    if len(recent) > 0:
        for t in recent:
            speaker = t.get('speaker', 'Unknown')
            bn = t.get('bn', '') if t.get('bn', '') else "[অনুবাদ মুলতুবি...]"
            
            try:
                speaker_str = speaker.split()[0]
                speaker_num = int(speaker_str.split('-')[1]) if 'Person-' in speaker_str else 0
            except:
                speaker_num = 0
            
            is_right_aligned = (speaker_num % 2 == 0)
            indent = "                              " if is_right_aligned else ""
            
            bn_text += f"{indent}{speaker}: {bn}\n\n"
    
    # Show current segment with PHASE 1 → PHASE 2 transition
    if current_segment["text"]:
        speaker = current_segment["speaker"]
        
        try:
            speaker_str = speaker.split()[0] if speaker else "Unknown"
            speaker_num = int(speaker_str.split('-')[1]) if 'Person-' in speaker_str else 0
        except:
            speaker_num = 0
        
        is_right_aligned = (speaker_num % 2 == 0)
        indent = "                              " if is_right_aligned else ""
        
        # SIMPLIFIED: Show ONLY icon + translation (Phase 2 replaces Phase 1)
        if current_segment["text_bn_final"]:
            # Phase 2 ready - show final translation with checkmark
            bn = current_segment["text_bn_final"]
            icon = "✅"
        else:
            # Phase 1 - show word-by-word with lightning
            bn = current_segment["text_bn_temp"] if current_segment["text_bn_temp"] else "[অনুবাদ হচ্ছে...]"
            icon = "⚡"
        
        bn_text += f"{indent}🔴 {speaker}: {icon}{bn}\n\n"
    
    if not bn_text:
        bn_text = "🎧 শুনছি... বক্তৃতার জন্য অপেক্ষা করছি..."
    
    return en_text, bn_text, status

def get_transcript_history():
    """Get full transcript history (ONLY FINAL translations)"""
    if len(all_transcripts) == 0:
        return "📭 No transcripts yet. Start speaking!"
    
    history = f"## 📜 Full Transcript ({len(all_transcripts)} segments)\n\n"
    for i, t in enumerate(reversed(all_transcripts[-15:]), 1):
        idx = len(all_transcripts) - i + 1
        speaker = t.get('speaker', 'Unknown')
        history += f"### [{t['time']}] {speaker}\n\n"
        history += f"**🇬🇧 English:**  \n{t['en']}\n\n"
        if t['bn']:
            history += f"**🇧🇩 বাংলা (Context-aware):**  \n{t['bn']}\n\n"
        history += "---\n\n"
    
    return history

# Gradio Interface
with gr.Blocks(
    title="MeetingAI - 2-Phase Translation", 
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange")
) as demo:
    
    gr.Markdown("""
    # 🧑‍💼 MeetingAI - 2-Phase Translation System ⚡
    **Phase 1:** Word-by-word (instant) → **Phase 2:** Context-aware (accurate)
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            start_btn = gr.Button("▶️ Start Meeting", variant="primary", size="lg")
        with gr.Column(scale=2):
            stop_btn = gr.Button("⏹️ Stop Meeting", variant="stop", size="lg")
        with gr.Column(scale=2):
            summary_btn = gr.Button("📊 Show Summary", variant="secondary", size="lg")
        with gr.Column(scale=2):
            ai_summary_btn = gr.Button("🤖 Generate AI Summary", variant="primary", size="lg")
        with gr.Column(scale=2):
            status_display = gr.Textbox(label="Status", interactive=False, value="⚪ Ready")
    
    status_text = gr.Textbox(label="System Message", interactive=False, visible=False)
    
    gr.Markdown("""
    ## 💬 Live Captions (2-Phase Translation)
    **⚡ Phase 1:** Word-by-word translation (instant feedback)  
    **✅ Phase 2:** Context-aware translation (replaces Phase 1 when ready)
    """)
    
    with gr.Row():
        with gr.Column():
            english_output = gr.Textbox(
                label="🇬🇧 English (Last 10 Segments)", 
                lines=12,
                value="Click 'Start Meeting' to begin...",
                interactive=False,
                show_copy_button=True,
                autoscroll=True,
                max_lines=15
            )
        
        with gr.Column():
            bangla_output = gr.Textbox(
                label="🇧🇩 বাংলা (2-Phase: Word→Context)", 
                lines=12,
                value="'Start Meeting' ক্লিক করুন...",
                interactive=False,
                show_copy_button=True,
                autoscroll=True,
                max_lines=15
            )
    
    with gr.Accordion("📜 Transcript History (Final Translations Only)", open=False):
        transcript_display = gr.Markdown("Click 'Start Meeting' to begin")
    
    with gr.Accordion("📝 Basic Summary (Transcript View)", open=False):
        summary_output = gr.Markdown("Click 'Show Summary' to view transcript")
    
    with gr.Accordion("🤖 AI Summary (Intelligent Analysis)", open=False):
        ai_summary_output = gr.Markdown("Click 'Generate AI Summary' for AI-powered insights")
    
    # Event handlers
    start_btn.click(
        fn=start_meeting,
        outputs=[status_text, english_output, bangla_output, status_display]
    )
    
    stop_btn.click(
        fn=stop_meeting,
        outputs=status_text
    )
    
    summary_btn.click(
        fn=show_basic_summary,
        outputs=summary_output
    )
    
    ai_summary_btn.click(
        fn=generate_ai_summary_ui,
        outputs=ai_summary_output
    )
    
    # Continuous polling for live updates
    demo.load(
        fn=get_current_captions,
        outputs=[english_output, bangla_output, status_display],
        show_progress=False
    )
    
    # Refresh captions every 200ms
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
    print("🚀 Starting MeetingAI with 2-Phase Translation")
    print("="*60)
    print("⚡ Phase 1: Word-by-word (instant)")
    print("✅ Phase 2: Context-aware (accurate + saved)")
    print("🌐 Access at: http://localhost:7860")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )