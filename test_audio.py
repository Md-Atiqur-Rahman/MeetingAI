"""
Audio Listener Test Script (Using sounddevice)
Run this to verify if audio is being captured correctly
"""

import threading
import time
import numpy as np
from src.audio_listener import start_listening, combined_queue, list_all_devices

def test_audio_capture(duration=10):
    """
    Test if audio is being captured from system
    
    Args:
        duration: How many seconds to test (default 10)
    """
    print("=" * 60)
    print("🧪 AUDIO LISTENER TEST")
    print("=" * 60)
    print(f"⏱️  Test Duration: {duration} seconds")
    print("🔊 Make sure Teams or YouTube is playing audio!")
    print("=" * 60)
    
    # Start audio listener in background thread
    listener_thread = threading.Thread(target=start_listening(), daemon=True)
    listener_thread.start()
    
    print("\n⏳ Starting audio capture...\n")
    
    # Give it a moment to initialize
    time.sleep(2)
    
    # Wait and check queue periodically
    start_time = time.time()
    check_interval = 2  # Check every 2 seconds
    last_check = 0
    audio_detected = False
    
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        
        # Print status every 2 seconds
        if elapsed > last_check and elapsed % check_interval == 0:
            queue_size = combined_queue.qsize()
            print(f"[{elapsed}s] Queue size: {queue_size} chunks")
            
            # Try to get one audio chunk and check it
            if not combined_queue.empty():
                audio_chunk = combined_queue.get()
                audio_np = np.squeeze(audio_chunk).astype(np.float32)
                
                print(f"    ✅ Audio chunk received!")
                print(f"    📊 Shape: {audio_np.shape}")
                print(f"    📈 Max amplitude: {audio_np.max():.4f}")
                print(f"    📉 Min amplitude: {audio_np.min():.4f}")
                
                # Check if audio has actual sound (not silence)
                max_amp = max(abs(audio_np.max()), abs(audio_np.min()))
                if max_amp > 0.01:
                    print(f"    ✅ AUDIO DETECTED! Amplitude: {max_amp:.4f}")
                    audio_detected = True
                else:
                    print(f"    ⚠️  Very quiet (silence?). Amplitude: {max_amp:.4f}")
                print()
            else:
                print("    ⚠️  Queue is empty - no audio captured")
                print()
            
            last_check = elapsed
        
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    final_queue_size = combined_queue.qsize()
    print(f"Final queue size: {final_queue_size} chunks")
    
    if audio_detected and final_queue_size > 0:
        print("\n✅ SUCCESS: Audio is being captured!")
        print("\n💡 Next steps:")
        print("   1. Your audio listener is working correctly")
        print("   2. Run: streamlit run app.py")
        print("   3. Start your Teams meeting")
        print("   4. The app will transcribe in real-time")
    elif final_queue_size > 0 and not audio_detected:
        print("\n⚠️ PARTIAL SUCCESS: Audio chunks received but very quiet")
        print("\n🔧 Try:")
        print("   1. Increase system volume")
        print("   2. Play louder audio (music/video)")
        print("   3. Speak into microphone if using mic input")
    else:
        print("\n❌ FAILED: No audio captured!")
        print("\n🔧 SOLUTION: Enable Stereo Mix")
        print("\nFollow these steps:")
        print("   1. Right-click speaker icon in taskbar")
        print("   2. Click 'Sounds' or 'Sound settings'")
        print("   3. Go to 'Recording' tab")
        print("   4. Right-click empty space → 'Show Disabled Devices'")
        print("   5. Find 'Stereo Mix', right-click → Enable")
        print("   6. Right-click 'Stereo Mix' → 'Set as Default Device'")
        print("   7. Click OK and run this test again")
        print("\n   Alternative: Use VB-Cable (Virtual Audio Cable)")
        print("   Download: https://vb-audio.com/Cable/")
    
    print("=" * 60)

if __name__ == "__main__":
    print("\n🚀 MeetingAI Audio Test\n")
    
    # First, list all available devices
    list_all_devices()
    
    # Give user time to check and start audio
    print("\n" + "="*60)
    print("⏰ Starting test in 3 seconds...")
    print("🔊 PLAY AUDIO NOW (YouTube, Teams, music, etc.)")
    print("="*60)
    
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Run the test
    test_audio_capture(duration=10)