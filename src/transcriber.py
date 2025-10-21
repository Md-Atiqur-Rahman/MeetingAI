# transcriber.py

import whisper
import numpy as np

model = whisper.load_model("base")

def transcribe(audio_chunk):
    audio_np = np.squeeze(audio_chunk)
    audio_np = whisper.pad_or_trim(audio_np)
    mel = whisper.log_mel_spectrogram(audio_np).to(model.device)
    result = model.decode(model.encode(mel))
    return result.text.strip()