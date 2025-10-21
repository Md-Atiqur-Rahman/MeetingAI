# transcriber.py

import whisper
import numpy as np

model = whisper.load_model("base")

def transcribe(audio_np):
    # Whisper expects a NumPy array of shape (samples,)
    audio_np = whisper.pad_or_trim(audio_np)
    mel = whisper.log_mel_spectrogram(audio_np).to(model.device)
    
    # Use the transcribe method instead of encode/decode
    result = model.transcribe(audio_np, language="en")
    return result["text"].strip()