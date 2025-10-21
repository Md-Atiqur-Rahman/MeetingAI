import whisper
import numpy as np
import torch

# Load model once (globally)
print("📥 Loading Whisper model...")
model = whisper.load_model("base")  # Use "base" for speed, "medium" for accuracy
print("✅ Whisper model loaded")

def transcribe(audio_np):
    """
    Transcribe audio using Whisper
    
    Args:
        audio_np: NumPy array of audio samples (float32, 16kHz)
    
    Returns:
        str: Transcribed text
    """
    try:
        # Ensure audio is 1D array
        if len(audio_np.shape) > 1:
            audio_np = np.squeeze(audio_np)
        
        # Normalize audio to [-1, 1] range if needed
        if audio_np.max() > 1.0 or audio_np.min() < -1.0:
            audio_np = audio_np / np.abs(audio_np).max()
        
        # Pad or trim to 30 seconds (Whisper's expected length)
        audio_np = whisper.pad_or_trim(audio_np)
        
        # Convert to mel spectrogram
        mel = whisper.log_mel_spectrogram(audio_np).to(model.device)
        
        # Decode audio with better options
        options = whisper.DecodingOptions(
            language="en",  # Force English
            fp16=torch.cuda.is_available(),
            without_timestamps=True,
            # Suppress common noise tokens
            suppress_tokens="-1",
            # Only return if confidence is reasonable
            temperature=0.0  # More deterministic
        )
        result = whisper.decode(model, mel, options)
        
        text = result.text.strip()
        print(f"🔍 Raw transcription: '{text}'")  # DEBUG - see what Whisper actually returns
        
        # Filter out very short or repetitive transcriptions
        if len(text) < 2:  # Changed from 3 to 2
            return ""
        
        # Don't filter single words - they might be valid
        # Only filter if it's a known filler word
        common_fillers = ["uh", "um", "hmm", "ah", "oh"]
        if text.lower() in common_fillers:
            return ""
        
        # Return even short but valid transcriptions
        return text
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""