import soundcard as sc
import numpy as np
import queue
import pythoncom  # Make sure pywin32 is installed

combined_queue = queue.Queue()

def start_listening(samplerate=16000, frames=1600):
    def record_loop():
        pythoncom.CoInitialize()

        speaker = sc.default_speaker()

        while True:
            # Directly record from speaker (loopback)
            speaker_data = speaker.record(numframes=frames, samplerate=samplerate)
            combined_queue.put(speaker_data)

    return record_loop