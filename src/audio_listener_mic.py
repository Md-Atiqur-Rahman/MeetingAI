"""
Audio Listener - MICROPHONE VERSION
For testing with your voice instead of system audio
"""
import sounddevice as sd
import numpy as np
import queue
import time

combined_queue = queue.Queue(maxsize=100)

def start_listening(samplerate=16000, blocksize=1600):
    """Captures audio from MICROPHONE"""
    
    def record_loop():
        try:
            # List available microphones
            devices = sd.query_devices()
            print("\n🎤 Available Microphones:")
            
            mic_id = None
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    print(f"   [{i}] {dev['name']}")
                    # Try to find your Baseus headset mic
                    if "baseus" in dev['name'].lower() and "headset" in dev['name'].lower():
                        mic_id = i
            
            if mic_id is None:
                mic_id = sd.default.device[0]
                print(f"\n📢 Using default microphone: {devices[mic_id]['name']}")
            else:
                print(f"\n✅ Using Baseus headset microphone")
            
            def audio_callback(indata, frames, time_info, status):
                if status:
                    print(f"⚠️ Audio status: {status}")
                
                audio_data = indata.copy().astype(np.float32)
                
                # Auto amplification
                max_amplitude = np.max(np.abs(audio_data))
                if max_amplitude > 0.00001:
                    target_amplitude = 0.1
                    amplification_factor = target_amplitude / max_amplitude
                    amplification_factor = min(amplification_factor, 10.0)
                    audio_data = audio_data * amplification_factor
                    audio_data = np.clip(audio_data, -1.0, 1.0)
                
                if not combined_queue.full():
                    combined_queue.put(audio_data)
                else:
                    try:
                        combined_queue.get_nowait()
                    except queue.Empty:
                        pass
                    combined_queue.put(audio_data)
            
            print(f"🎙️ Starting MICROPHONE capture")
            print(f"🗣️  SPEAK INTO YOUR MICROPHONE NOW!")
            
            with sd.InputStream(
                samplerate=samplerate,
                channels=1,
                device=mic_id,
                callback=audio_callback,
                blocksize=blocksize,
                dtype='float32'
            ):
                print("✅ Microphone stream started")
                
                while True:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ Microphone error: {e}")
    
    return record_loop


def list_all_devices():
    """List all audio devices"""
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
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")