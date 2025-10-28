# speaker_identifier.py - Improved speaker identification using clustering

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from collections import deque
import warnings
warnings.filterwarnings('ignore')

class ImprovedSpeakerIdentifier:
    """
    Improved speaker identification using audio embeddings and clustering
    """
    def __init__(self, max_speakers=5):
        self.max_speakers = max_speakers
        self.speaker_embeddings = []  # Store embeddings for each segment
        self.speaker_labels = []  # Store assigned labels
        self.embedding_history = deque(maxlen=50)  # Keep last 50 embeddings
        self.label_history = deque(maxlen=50)
        
        # Speaker name mapping
        self.speaker_names = {
            0: "Person-1 👨",
            1: "Person-2 👩", 
            2: "Person-3 👨",
            3: "Person-4 👩",
            4: "Person-5 👨"
        }
        
    def extract_robust_features(self, audio_np, samplerate=16000):
        """
        Extract robust audio features that are consistent for same speaker
        """
        try:
            # Normalize first
            audio_np = audio_np / (np.max(np.abs(audio_np)) + 1e-8)
            
            # 1. MFCC-like features (spectral characteristics)
            # Energy in different frequency bands
            fft = np.fft.rfft(audio_np)
            magnitude = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio_np), 1/samplerate)
            
            # Divide into frequency bands (like MFCC)
            bands = [
                (0, 300),      # Very low (bass)
                (300, 1000),   # Low
                (1000, 3000),  # Mid (important for voice)
                (3000, 6000),  # High
                (6000, 8000)   # Very high
            ]
            
            band_energies = []
            for low, high in bands:
                mask = (freqs >= low) & (freqs < high)
                energy = np.sum(magnitude[mask])
                band_energies.append(energy)
            
            # Normalize band energies
            total_energy = sum(band_energies) + 1e-8
            band_energies = [e / total_energy for e in band_energies]
            
            # 2. Pitch (fundamental frequency) - very important for speaker identity
            # Use autocorrelation
            autocorr = np.correlate(audio_np, audio_np, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peaks
            pitch_candidates = []
            for lag in range(50, 400):  # Typical pitch range
                if lag < len(autocorr) - 1:
                    if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
                        pitch_candidates.append((lag, autocorr[lag]))
            
            if pitch_candidates:
                best_lag = max(pitch_candidates, key=lambda x: x[1])[0]
                pitch = samplerate / best_lag
            else:
                pitch = 0
            
            # 3. Speaking rate (zero crossing rate)
            zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_np)))) / (2 * len(audio_np))
            
            # 4. Voice quality (spectral centroid and spread)
            spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-8)
            spectral_spread = np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-8))
            
            # Combine all features
            features = np.array(band_energies + [
                pitch / 1000,  # Normalize pitch
                zero_crossings,
                spectral_centroid / 1000,  # Normalize
                spectral_spread / 1000
            ])
            
            return features
            
        except Exception as e:
            print(f"⚠️ Feature extraction error: {e}")
            return np.zeros(9)  # 5 bands + 4 other features
    
    def identify_speaker(self, audio_np, samplerate=16000):
        """
        Identify speaker using clustering of audio features
        """
        try:
            # Extract features
            features = self.extract_robust_features(audio_np, samplerate)
            
            # Add to history
            self.embedding_history.append(features)
            
            # Need at least 3 samples to cluster
            if len(self.embedding_history) < 3:
                label = 0  # First speaker
                self.label_history.append(label)
                return self.speaker_names[label]
            
            # Perform clustering on recent history
            embeddings_array = np.array(list(self.embedding_history))
            
            # Use Agglomerative Clustering (better for speaker diarization)
            n_clusters = min(2, len(embeddings_array))  # Start with 2 speakers
            
            # Try to find optimal number of clusters (up to max_speakers)
            best_n_clusters = n_clusters
            if len(embeddings_array) >= 5:
                # Simple heuristic: check variance
                for n in range(2, min(self.max_speakers + 1, len(embeddings_array))):
                    clustering = AgglomerativeClustering(
                        n_clusters=n,
                        linkage='ward'
                    ).fit(embeddings_array)
                    
                    # Check if last few samples have different labels
                    recent_labels = clustering.labels_[-5:]
                    if len(np.unique(recent_labels)) > 1:
                        best_n_clusters = n
                        break
            
            # Final clustering
            clustering = AgglomerativeClustering(
                n_clusters=best_n_clusters,
                linkage='ward'
            ).fit(embeddings_array)
            
            # Get label for current (last) segment
            current_label = clustering.labels_[-1]
            
            # Smooth labels (avoid rapid switching)
            if len(self.label_history) > 0:
                # If last 2 segments have same label, stick with it
                if len(self.label_history) >= 2:
                    if self.label_history[-1] == self.label_history[-2]:
                        prev_label = self.label_history[-1]
                        # Only switch if very confident
                        if current_label == prev_label:
                            label = current_label
                        else:
                            # Stick with previous unless feature distance is large
                            prev_features = self.embedding_history[-2]
                            distance = np.linalg.norm(features - prev_features)
                            if distance > 0.5:  # Threshold for speaker change
                                label = current_label
                                print(f"🔄 Speaker changed: {self.speaker_names.get(prev_label, 'Unknown')} → {self.speaker_names.get(label, 'Unknown')}")
                            else:
                                label = prev_label
                    else:
                        label = current_label
                else:
                    label = current_label
            else:
                label = current_label
            
            self.label_history.append(label)
            
            return self.speaker_names.get(label, f"Person-{label+1}")
            
        except Exception as e:
            print(f"⚠️ Speaker identification error: {e}")
            import traceback
            traceback.print_exc()
            return "Person-1 👨"
    
    def reset(self):
        """Reset all speaker data"""
        self.embedding_history.clear()
        self.label_history.clear()
        self.speaker_embeddings = []
        self.speaker_labels = []
        print("🔄 Speaker profiles reset")

# Global identifier instance
speaker_identifier = ImprovedSpeakerIdentifier(max_speakers=5)

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
    if len(speaker_identifier.label_history) > 0:
        label = speaker_identifier.label_history[-1]
        return speaker_identifier.speaker_names.get(label, "Unknown")
    return "Unknown"