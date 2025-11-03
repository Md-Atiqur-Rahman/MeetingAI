# pronunciation_checker.py

from phonemizer import phonemize
from difflib import SequenceMatcher

class PronunciationChecker:
    def __init__(self):
        self.phoneme_cache = {}
    
    def check(self, user_text, reference_text):
        # Convert to lowercase for comparison
        user_text = user_text.lower()
        reference_text = reference_text.lower()
        
        # Get phonemes
        user_phonemes = self._get_phonemes(user_text)
        reference_phonemes = self._get_phonemes(reference_text)
        
        # Calculate similarity
        similarity = SequenceMatcher(None, user_phonemes, reference_phonemes).ratio()
        score = int(similarity * 100)
        
        return {
            'score': score,
            'user_phonemes': user_phonemes,
            'reference_phonemes': reference_phonemes,
            'feedback': self._get_feedback(score),
            'pronunciation_grade': self._get_grade(score)
        }
    
    def _get_phonemes(self, text):
        if text in self.phoneme_cache:
            return self.phoneme_cache[text]
        
        phonemes = phonemize(text, language='en-us', backend='espeak')
        self.phoneme_cache[text] = phonemes
        return phonemes
    
    def _get_feedback(self, score):
        if score >= 95:
            return "Perfect pronunciation! 🌟"
        elif score >= 85:
            return "Excellent! Very clear. 🎉"
        elif score >= 75:
            return "Good! Minor improvements needed. 👍"
        elif score >= 60:
            return "Keep practicing. Listen again. 🔄"
        else:
            return "Let's work on this together. 💪"
    
    def _get_grade(self, score):
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"