# transcriber.py - Using faster-whisper with auto device detection

from faster_whisper import WhisperModel
import numpy as np
import torch

print("📥 Loading faster-whisper model...")
print(f"🎮 CUDA available: {torch.cuda.is_available()}")

# Auto-detect best device
try:
    # Try GPU first
    if torch.cuda.is_available():
        print(f"🎮 Attempting GPU: {torch.cuda.get_device_name(0)}")
        model = WhisperModel(
            "tiny",  # CHANGED: tiny for ultra-low latency (was "base")
            device="cuda",
            compute_type="float16",
            device_index=0,
            num_workers=2  # Reduced for lower latency
        )
        print("✅ Faster-whisper TINY model loaded on GPU (ULTRA FAST MODE)")
    else:
        raise Exception("CUDA not available")
        
except Exception as e:
    print(f"⚠️ GPU load failed: {e}")
    print("📥 Loading TINY model on CPU...")
    
    # Fallback to CPU with tiny model
    model = WhisperModel(
        "tiny",  # Tiny model for speed
        device="cpu",
        compute_type="int8",
        cpu_threads=2,
        num_workers=2
    )
    print("✅ Faster-whisper TINY model loaded on CPU (FAST MODE)")

def transcribe(audio_np):
    """
    Fast transcription with automatic device selection
    
    Args:
        audio_np: NumPy array of audio samples (float32, 16kHz)
    
    Returns:
        str: Transcribed text
    """
    try:
        # Ensure audio is 1D array
        if len(audio_np.shape) > 1:
            audio_np = np.squeeze(audio_np)
        
        # Normalize audio
        if audio_np.max() > 1.0 or audio_np.min() < -1.0:
            audio_np = audio_np / np.abs(audio_np).max()
        
        # Fast transcription
        segments, info = model.transcribe(
            audio_np,
            language="en",
            beam_size=1,  # Fast mode
            best_of=1,  # Greedy decoding
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=100,
                threshold=0.5
            ),
            condition_on_previous_text=False,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            initial_prompt=None
        )
        
        # Collect segments
        transcription = ""
        for segment in segments:
            transcription += segment.text + " "
        
        text = transcription.strip()
        
        # Quick filters
        if len(text) < 2:
            return ""
        
        fillers = ["uh", "um", "hmm", "ah", "oh", "er"]
        if text.lower() in fillers:
            return ""
        
        return text
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""