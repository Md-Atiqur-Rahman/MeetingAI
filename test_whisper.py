"""
Direct Whisper Test - bypasses Streamlit
Tests if Whisper can transcribe the captured audio
"""

import time
import numpy as np
import threading
from src.audio_listener import start_listening, combined_queue
from src.transcriber import transcribe

print("="*60)
print("🧪 DIRECT WHISPER TEST")
print("="*60)
print("This will capture 5 seconds of audio and transcribe it")
print("🔊 PLAY YOUR YOUTUBE VIDEO NOW!")
print("="*60)

# Start audio capture
listener_thread = threading.Thread(target=start_listening(), daemon=True)
listener_thread.start()

print("\n⏳ Waiting 2 seconds for audio capture to start...")
time.sleep(2)

print("🎤 Capturing audio for 5 seconds...")
audio_buffer = []
start_time = time.time()

# Collect 5 seconds of audio
while time.time() - start_time < 5.0:
    if not combined_queue.empty():
        audio_chunk = combined_queue.get()
        audio_np = np.squeeze(audio_chunk).astype(np.float32)
        
        # Check amplitude
        max_amp = np.max(np.abs(audio_np))
        if max_amp > 0.005:
            audio_buffer.append(audio_np)
            print(f"  ✅ Captured chunk {len(audio_buffer)}, amplitude: {max_amp:.4f}")
    
    time.sleep(0.1)

print(f"\n📊 Total chunks captured: {len(audio_buffer)}")

if len(audio_buffer) == 0:
    print("❌ No audio captured!")
    print("\n🔧 Solutions:")
    print("1. Make sure YouTube is playing")
    print("2. Check system volume is not 0")
    print("3. Verify Stereo Mix is enabled and set as default")
else:
    # Combine all audio
    print("\n🔄 Combining audio chunks...")
    combined_audio = np.concatenate(audio_buffer)
    
    print(f"📏 Total audio length: {len(combined_audio)} samples")
    print(f"⏱️  Duration: {len(combined_audio) / 16000:.2f} seconds")
    print(f"📊 Max amplitude: {np.max(np.abs(combined_audio)):.4f}")
    
    print("\n🎤 Transcribing with Whisper...")
    print("⏳ This may take 10-30 seconds...\n")
    
    try:
        text = transcribe(combined_audio)
        
        print("="*60)
        print("📝 TRANSCRIPTION RESULT")
        print("="*60)
        
        if text and len(text) > 0:
            print(f"✅ SUCCESS!\n")
            print(f"Transcribed text:\n\"{text}\"\n")
            print(f"Length: {len(text)} characters")
        else:
            print("❌ No text transcribed (empty result)")
            print("\n🔧 Possible reasons:")
            print("1. Audio is music/instrumental (Whisper needs speech)")
            print("2. Audio quality is too low")
            print("3. Language detection issue")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")

print("\n✅ Test complete!")