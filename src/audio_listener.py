# audio_listener.py

import soundcard as sc
import numpy as np
import queue

# Queues for audio chunks
mic_queue = queue.Queue()
speaker_queue = queue.Queue()
combined_queue = queue.Queue()

# Get default devices
mic = sc.default_microphone()
speaker = sc.default_speaker()

def start_listening(samplerate=16000, frames=1600):
    mic_rec = mic.recorder(samplerate=samplerate)
    speaker_rec = speaker.recorder(samplerate=samplerate)

    def record_loop():
        while True:
            mic_data = mic_rec.record(numframes=frames)
            speaker_data = speaker_rec.record(numframes=frames)

            mic_queue.put(mic_data)
            speaker_queue.put(speaker_data)

            # Combine both streams
            combined = mic_data + speaker_data
            combined_queue.put(combined)

    return record_loop