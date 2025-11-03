# check_audio.py
"""
Audio device checker and tester
Run this to verify microphone and speaker setup
"""

import sounddevice as sd
import numpy as np
import pygame
from gtts import gTTS
import tempfile
import os

print("\n" + "=" * 70)
print("🔊 AUDIO DEVICE CHECKER")
print("=" * 70)

# 1. List all audio devices
print("\n📋 Available Audio Devices:")
print("-" * 70)
devices = sd.query_devices()
for i, device in enumerate(devices):
    device_type = []
    if device['max_input_channels'] > 0:
        device_type.append("INPUT")
    if device['max_output_channels'] > 0:
        device_type.append("OUTPUT")
    
    marker = "✅" if device == sd.query_devices(kind='input') or device == sd.query_devices(kind='output') else "  "
    
    print(f"{marker} [{i}] {device['name']}")
    print(f"     Type: {'/'.join(device_type)}")
    print(f"     Input channels: {device['max_input_channels']}")
    print(f"     Output channels: {device['max_output_channels']}")
    print(f"     Sample rate: {device['default_samplerate']} Hz")
    print()

# 2. Check default devices
print("=" * 70)
print("\n🎤 Default Input Device (Microphone):")
print("-" * 70)
try:
    default_input = sd.query_devices(kind='input')
    print(f"✅ Name: {default_input['name']}")
    print(f"   Channels: {default_input['max_input_channels']}")
    print(f"   Sample rate: {default_input['default_samplerate']} Hz")
except Exception as e:
    print(f"❌ No input device found: {e}")

print("\n🔊 Default Output Device (Speaker):")
print("-" * 70)
try:
    default_output = sd.query_devices(kind='output')
    print(f"✅ Name: {default_output['name']}")
    print(f"   Channels: {default_output['max_output_channels']}")
    print(f"   Sample rate: {default_output['default_samplerate']} Hz")
except Exception as e:
    print(f"❌ No output device found: {e}")

# 3. Test microphone recording
print("\n" + "=" * 70)
print("🎤 MICROPHONE TEST")
print("=" * 70)
print("Recording 3 seconds... Please speak into your microphone/earbuds!")
print("Speak NOW:")

try:
    duration = 3  # seconds
    samplerate = 16000
    
    # Record audio
    print("🔴 Recording...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()  # Wait for recording to complete
    print("✅ Recording complete!")
    
    # Analyze audio
    max_amplitude = np.max(np.abs(audio))
    avg_amplitude = np.mean(np.abs(audio))
    
    print(f"\n📊 Recording Analysis:")
    print(f"   Max amplitude: {max_amplitude:.4f}")
    print(f"   Avg amplitude: {avg_amplitude:.4f}")
    
    if max_amplitude < 0.001:
        print("⚠️  WARNING: Very low amplitude! Microphone might not be working.")
        print("   Check:")
        print("   - Microphone is plugged in correctly")
        print("   - Microphone is not muted")
        print("   - Volume is turned up")
    elif max_amplitude < 0.01:
        print("⚠️  WARNING: Low amplitude. Speak louder or increase microphone volume.")
    else:
        print("✅ Good audio level detected!")
    
except Exception as e:
    print(f"❌ Microphone test failed: {e}")

# 4. Test speaker output
print("\n" + "=" * 70)
print("🔊 SPEAKER TEST")
print("=" * 70)
print("Playing test audio... You should hear a voice saying 'Hello'")

try:
    # Initialize pygame
    pygame.mixer.init()
    
    # Generate test audio
    test_text = "Hello! This is a speaker test. Can you hear me?"
    print(f"🔊 Generating audio: '{test_text}'")
    
    tts = gTTS(text=test_text, lang='en', slow=False)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_filename = temp_file.name
    temp_file.close()  # Close file before saving
    
    tts.save(temp_filename)
    print(f"💾 Saved to: {temp_filename}")
    
    # Play audio
    print("🔊 Playing NOW... Listen!")
    pygame.mixer.music.load(temp_filename)
    pygame.mixer.music.play()
    
    # Wait for audio to finish
    import time
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    print("✅ Speaker test complete!")
    
    # Cleanup
    pygame.mixer.music.unload()  # Unload before deleting
    time.sleep(0.2)
    try:
        os.remove(temp_filename)
    except:
        pass
    
    print("\n❓ Did you hear the audio?")
    print("   If YES: ✅ Speakers working!")
    print("   If NO:  ❌ Check speaker connection/volume")
    
except Exception as e:
    print(f"❌ Speaker test failed: {e}")
    import traceback
    traceback.print_exc()

# 5. Summary and recommendations
print("\n" + "=" * 70)
print("📋 SUMMARY & RECOMMENDATIONS")
print("=" * 70)

print("""
For your earbuds/headset:

1. **Connection:**
   ✅ Plug in before starting the app
   ✅ Check Windows Sound Settings
   ✅ Set as default input/output device

2. **Microphone (Input):**
   ✅ Should show in "Default Input Device" above
   ✅ Test showed audio level > 0.01
   ✅ Speak clearly, 10-20cm from mic

3. **Speaker (Output):**
   ✅ Should show in "Default Output Device" above
   ✅ Test audio played successfully
   ✅ Volume not muted

4. **If earbuds not detected:**
   - Unplug and replug
   - Restart app after reconnecting
   - Check Windows Sound Settings (Right-click speaker icon)
   - Set your earbuds as "Default Device"

5. **App Settings:**
   - No special settings needed in the app
   - Uses system default devices automatically
   - Audio capture is shared with meeting transcription
""")

print("=" * 70)
print("✅ Audio check complete!")
print("=" * 70)
print("\nIf everything looks good, you can now run: python app_gradio.py")
print("=" * 70 + "\n")