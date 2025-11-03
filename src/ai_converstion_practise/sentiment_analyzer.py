# sentiment_analyzer.py

from textblob import TextBlob

class SentimentAnalyzer:
    def __init__(self):
        self.sentiment_history = []
    
    def analyze(self, text):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        sentiment = {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'label': self._get_label(polarity),
            'emoji': self._get_emoji(polarity),
            'confidence': abs(polarity)
        }
        
        self.sentiment_history.append(sentiment)
        return sentiment
    
    def _get_label(self, polarity):
        if polarity > 0.3:
            return "positive"
        elif polarity < -0.3:
            return "negative"
        else:
            return "neutral"
    
    def _get_emoji(self, polarity):
        if polarity > 0.5:
            return "😄"
        elif polarity > 0.3:
            return "😊"
        elif polarity > -0.3:
            return "😐"
        elif polarity > -0.5:
            return "😕"
        else:
            return "😔"
    
    def get_trend(self):
        """Get sentiment trend over last 5 messages"""
        if len(self.sentiment_history) < 2:
            return "stable"
        
        recent = self.sentiment_history[-5:]
        avg = sum(s['polarity'] for s in recent) / len(recent)
        
        if avg > 0.2:
            return "improving"
        elif avg < -0.2:
            return "declining"
        else:
            return "stable"