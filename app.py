# app.py

import streamlit as st
import threading
import time
from src.audio_listener import start_listening, combined_queue
from src.transcriber import transcribe
from src.suggester import get_suggestion
from src.summarizer import generate_summary

# App state
transcript_list = []
running = False

# Streamlit UI
st.set_page_config(page_title="MeetingAI", layout="wide")
st.title("🧑‍💼 MeetingAI - Personal Meeting Assistant")

start_btn = st.button("▶️ Start Meeting")
stop_btn = st.button("⏹️ Stop Meeting")

transcript_box = st.empty()
suggestion_box = st.empty()
summary_box = st.empty()

def meeting_loop():
    record_loop = start_listening()
    threading.Thread(target=record_loop).start()
    global running
    with start_listening():
        while running:
            if not audio_queue.empty():
                audio_chunk = audio_queue.get()
                text = transcribe(audio_chunk)
                if text:
                    transcript_list.append(text)
                    transcript_box.markdown(f"**Live Transcript:** {text}")
                    suggestion = get_suggestion(text)
                    if suggestion:
                        suggestion_box.markdown(f"**🤖 Gemini Suggestion:**\n\n{suggestion}")
            time.sleep(1)

if start_btn:
    if not running:
        running = True
        threading.Thread(target=meeting_loop).start()
        st.success("Meeting started. Listening...")

if stop_btn:
    if running:
        running = False
        st.warning("Meeting stopped.")
