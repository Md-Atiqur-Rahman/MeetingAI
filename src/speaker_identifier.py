# speaker_identifier.py - Identify different speakers

import numpy as np
from collections import defaultdict
import hashlib

# Simple speaker identification based on audio characteristics
class SimpleSpeakerIdentifier:
    """
    Simple speaker identification using audio features
    (pitch, energy, spectral characteristics)
    """
    def __init__(self):
        self.speakers = {}  # Store speaker profiles
        self.speaker_names = ["Person-1", "Person-2", "Person-3", "Person-4", "Person-5"]
        self.current_speaker_id = None
        
    def extract_features(self, audio_np, samplerate=16000):
        """
        Extract simple audio features for speaker identification
        Returns: feature vector
        """
        try:
            # Energy (loudness)
            energy = np.mean(np.abs(audio_np))
            
            # Zero crossing rate (pitch proxy)
            zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_np)))) / len(audio_np)
            
            # Spectral centroid (voice characteristic)
            fft = np.fft.rfft(audio_np)
            magnitude = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio_np), 1/samplerate)
            spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude) if np.sum(magnitude) > 0 else 0
            
            # Pitch estimate (fundamental frequency)
            autocorr = np.correlate(audio_np, audio_np, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find first peak after zero
            peaks = []
            for i in range(1, min(400, len(autocorr)-1)):  # Search in reasonable pitch range
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    peaks.append((i, autocorr[i]))
            
            pitch = 0
            if peaks:
                max_peak = max(peaks, key=lambda x: x[1])
                pitch = samplerate / max_peak[0] if max_peak[0] > 0 else 0
            
            return np.array([energy, zero_crossings, spectral_centroid, pitch])
            
        except Exception as e:
            print(f"⚠️ Feature extraction error: {e}")
            return np.array([0, 0, 0, 0])
    
    def identify_speaker(self, audio_np, samplerate=16000):
        """
        Identify which speaker is talking
        Returns: speaker_id (Person-1, Person-2, etc.)
        """
        try:
            features = self.extract_features(audio_np, samplerate)
            
            # If no speakers registered yet, this is first speaker
            if len(self.speakers) == 0:
                speaker_id = 0
                self.speakers[speaker_id] = features
                self.current_speaker_id = speaker_id
                return self.speaker_names[speaker_id]
            
            # Compare with existing speakers
            min_distance = float('inf')
            best_match = None
            
            for speaker_id, speaker_features in self.speakers.items():
                # Calculate distance (similarity)
                distance = np.linalg.norm(features - speaker_features)
                if distance < min_distance:
                    min_distance = distance
                    best_match = speaker_id
            
            # Threshold for new speaker detection
            # If distance is too large, it's a new speaker
            THRESHOLD = 100  # Adjust based on testing
            
            if min_distance > THRESHOLD and len(self.speakers) < len(self.speaker_names):
                # New speaker detected
                speaker_id = len(self.speakers)
                self.speakers[speaker_id] = features
                self.current_speaker_id = speaker_id
                print(f"🆕 New speaker detected: {self.speaker_names[speaker_id]}")
                return self.speaker_names[speaker_id]
            else:
                # Existing speaker
                self.current_speaker_id = best_match
                return self.speaker_names[best_match]
                
        except Exception as e:
            print(f"⚠️ Speaker identification error: {e}")
            return "Unknown"
    
    def get_speaker_change(self, previous_speaker, current_speaker):
        """Check if speaker changed"""
        return previous_speaker != current_speaker
    
    def reset(self):
        """Reset speaker profiles"""
        self.speakers = {}
        self.current_speaker_id = None
        print("🔄 Speaker profiles reset")

# Global identifier instance
speaker_identifier = SimpleSpeakerIdentifier()

def identify_speaker(audio_np, samplerate=16000):
    """
    Identify speaker from audio
    Returns: speaker name (Person-1, Person-2, etc.)
    """
    return speaker_identifier.identify_speaker(audio_np, samplerate)

def reset_speakers():
    """Reset speaker identification"""
    speaker_identifier.reset()

def get_current_speaker():
    """Get current speaker name"""
    if speaker_identifier.current_speaker_id is not None:
        return speaker_identifier.speaker_names[speaker_identifier.current_speaker_id]
    return "Unknown"