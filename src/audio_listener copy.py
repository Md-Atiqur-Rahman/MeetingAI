"""
Audio Listener with AUTO AMPLIFICATION
Captures system audio and automatically boosts quiet signals
"""
import sounddevice as sd
import numpy as np
import queue
import time

# Global queue for audio data
combined_queue = queue.Queue(maxsize=100)

def find_loopback_device():
    """Find the appropriate audio input device for system audio capture"""
    devices = sd.query_devices()
    
    search_terms = ["stereo mix", "loopback", "what u hear", "wave out mix"]
    
    print("\n🔍 Searching for audio capture device...")
    
    for term in search_terms:
        for i, device in enumerate(devices):
            if term in device['name'].lower() and device['max_input_channels'] > 0:
                print(f"✅ Found loopback device: {device['name']}")
                return i
    
    print("⚠️ No loopback device found. Using default input.")
    return None

def start_listening(samplerate=16000, blocksize=1600):
    """Captures system audio with automatic volume amplification"""
    
    def record_loop():
        """Main recording loop with auto-amplification"""
        
        try:
            device_id = find_loopback_device()
            
            if device_id is None:
                device_id = sd.default.device[0]
                devices = sd.query_devices()
                print(f"📢 Using default input: {devices[device_id]['name']}")
            
            def audio_callback(indata, frames, time_info, status):
                """Process each audio block with amplification"""
                if status:
                    print(f"⚠️ Audio status: {status}")
                
                # Copy and convert to float32
                audio_data = indata.copy().astype(np.float32)
                
                # Calculate current amplitude
                max_amplitude = np.max(np.abs(audio_data))
                
                # AUTO AMPLIFICATION
                if max_amplitude > 0.00001:  # Not complete silence
                    # Target amplitude: 0.1 (10% of max range)
                    target_amplitude = 0.1
                    amplification_factor = target_amplitude / max_amplitude
                    
                    # Limit amplification to prevent extreme noise
                    amplification_factor = min(amplification_factor, 100.0)
                    
                    # Apply amplification
                    audio_data = audio_data * amplification_factor
                    
                    # Clip to prevent distortion
                    audio_data = np.clip(audio_data, -1.0, 1.0)
                
                # Add to queue
                if not combined_queue.full():
                    combined_queue.put(audio_data)
                else:
                    try:
                        combined_queue.get_nowait()
                    except queue.Empty:
                        pass
                    combined_queue.put(audio_data)
            
            print(f"🎙️ Starting audio stream with AUTO-AMPLIFICATION")
            print(f"📊 Device ID: {device_id}")
            
            with sd.InputStream(
                samplerate=samplerate,
                channels=1,
                device=device_id,
                callback=audio_callback,
                blocksize=blocksize,
                dtype='float32'
            ):
                print("✅ Audio stream started - Auto-amplification ACTIVE")
                
                while True:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ Audio stream error: {e}")
            print("\n🔧 Solutions:")
            print("1. Enable 'Stereo Mix' in Windows Sound settings")
            print("2. Set Stereo Mix volume to 100%")
            print("3. Or install VB-Cable virtual audio device")
    
    return record_loop


def list_all_devices():
    """Helper function to list all audio devices"""
    try:
        devices = sd.query_devices()
        print("\n" + "="*60)
        print("🎤 ALL AUDIO DEVICES")
        print("="*60)
        
        print("\n📢 OUTPUT DEVICES (Speakers):")
        for i, dev in enumerate(devices):
            if dev['max_output_channels'] > 0:
                default = " [DEFAULT]" if i == sd.default.device[1] else ""
                print(f"   [{i}] {dev['name']}{default}")
        
        print("\n🎙️ INPUT DEVICES (Microphones):")
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                default = " [DEFAULT]" if i == sd.default.device[0] else ""
                print(f"   [{i}] {dev['name']}{default}")
        
        print("\n💡 To capture system audio, you need:")
        print("   - 'Stereo Mix' enabled in Windows, OR")
        print("   - Virtual Audio Cable software installed")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error listing devices: {e}")