# 🎙️ AI Conversation Practice - Feature Design Document

## Overview

An interactive AI conversation partner that provides real-time feedback on speaking skills, including sentiment analysis, pronunciation checking, grammar correction, and intelligent topic suggestions.

---

## 🎯 Feature Requirements

### Core Capabilities

1. **Real-time Conversation**
   - User speaks → AI listens and responds
   - Natural conversation flow
   - Context-aware responses

2. **Sentiment Analysis**
   - Detect user's emotion (happy, frustrated, confused)
   - Adjust AI tone accordingly
   - Track sentiment over time

3. **Question & Answer**
   - User asks questions → AI answers
   - AI asks follow-up questions
   - Progressive difficulty levels

4. **Next Topic Suggestion**
   - Based on conversation context
   - Suggest related topics
   - Keep conversation flowing

5. **Mistake Correction**
   - Detect grammar errors
   - Pronunciation issues
   - Suggest correct version
   - Practice until correct

6. **Pronunciation Checking**
   - Compare user audio to correct pronunciation
   - Phonetic analysis
   - Score accuracy (0-100%)

7. **Practice Loop**
   - Repeat incorrect sentences
   - Real-time feedback
   - Progress tracking

---

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  SIDEBAR: AI CONVERSATION                │
│  [Start Practice] [Stop] [Sentiment: 😊] [Score: 85%]   │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌─────────┐ ┌──────────┐ ┌───────────────┐
│ Audio   │ │ AI Brain │ │   Feedback    │
│         │ │          │ │               │
│ Whisper │ │ Gemini   │ │ • Sentiment   │
│ (STT)   │ │ (Chat)   │ │ • Grammar     │
│         │ │          │ │ • Pronunciation│
└─────────┘ └──────────┘ └───────────────┘
     │           │              │
     └───────────┼──────────────┘
                 ▼
     ┌────────────────────────┐
     │   Conversation State   │
     │   • History            │
     │   • Current topic      │
     │   • Mistakes           │
     │   • Progress           │
     └────────────────────────┘
```

---

## 🛠️ Technology Stack

### 1. Speech Recognition (STT)
**Tool:** Whisper (existing)
- Already implemented
- Real-time transcription
- Good accuracy

### 2. AI Conversation Engine
**Tool:** Google Gemini 2.5 Flash
- Free tier available
- Multi-turn conversation support
- Context memory (1M tokens)
- Fast response time

### 3. Sentiment Analysis
**Tool:** TextBlob / VADER / Gemini built-in
- **Option A:** TextBlob (lightweight, fast)
  - Polarity: -1 (negative) to +1 (positive)
  - Subjectivity: 0 (objective) to 1 (subjective)
- **Option B:** Gemini built-in (more accurate)
  - Ask Gemini to analyze sentiment in response

### 4. Pronunciation Checking
**Tool:** phonemizer + DTW (Dynamic Time Warping)
- Convert speech to phonemes
- Compare with correct pronunciation
- Calculate similarity score

**Alternative:** Gemini Audio API (if available)

### 5. Grammar Checking
**Tool:** LanguageTool API (free) / Gemini
- Detect grammar errors
- Suggest corrections
- Explain mistakes

### 6. Text-to-Speech (TTS)
**Tool:** gTTS (Google Text-to-Speech) - Free
- AI speaks back to user
- Pronunciation reference
- Fast and clear

---

## 📊 Data Flow

### Conversation Flow

```
1. User speaks: "I want to learn about AI"
   ↓
2. Whisper transcribes: "I want to learn about AI"
   ↓
3. Sentiment Analysis: Positive (excited)
   ↓
4. Gemini processes:
   - Check grammar ✅
   - Understand intent
   - Generate response
   - Suggest next topics
   ↓
5. AI responds: "Great! Let's start with machine learning basics..."
   ↓
6. Display feedback:
   - Sentiment: 😊 Positive
   - Grammar: ✅ Correct
   - Pronunciation: 92% accurate
   - Next topics: [Deep Learning] [Neural Networks] [Data Science]
```

### Error Correction Flow

```
1. User says: "I goes to market yesterday"
   ↓
2. Grammar Check: ❌ Error detected
   ↓
3. AI responds:
   "I noticed a grammar mistake. You said 'I goes', 
    but it should be 'I went' (past tense).
    
    Correct sentence: 'I went to market yesterday'
    
    Please try saying it correctly."
   ↓
4. User repeats: "I went to market yesterday"
   ↓
5. Check: ✅ Correct!
   ↓
6. AI: "Perfect! Now let's practice another sentence..."
```

---

## 🎨 UI Design (Sidebar)

```
┌─────────────────────────────────┐
│   🗣️ AI Conversation Practice   │
├─────────────────────────────────┤
│                                 │
│  Status: 🟢 Active              │
│  Sentiment: 😊 Positive         │
│  Accuracy: 85%                  │
│                                 │
├─────────────────────────────────┤
│  💬 Chat History                │
│  ┌─────────────────────────┐   │
│  │ AI: Hello! Ready to     │   │
│  │     practice?           │   │
│  │                         │   │
│  │ You: Yes, I want to     │   │
│  │      learn English      │   │
│  │      ✅ (92% accurate)  │   │
│  │                         │   │
│  │ AI: Great! Let's start  │   │
│  │     with greetings...   │   │
│  │                         │   │
│  │ You: I goes to market   │   │
│  │      ❌ Grammar error   │   │
│  │                         │   │
│  │ AI: Try: "I went to     │   │
│  │     market"             │   │
│  │     🔄 Repeat please    │   │
│  └─────────────────────────┘   │
│                                 │
├─────────────────────────────────┤
│  📊 Session Stats               │
│  • Total sentences: 12          │
│  • Correct: 10 (83%)            │
│  • Mistakes corrected: 2        │
│  • Pronunciation avg: 88%       │
│                                 │
├─────────────────────────────────┤
│  💡 Next Topic Suggestions      │
│  • Business vocabulary          │
│  • Past tense practice          │
│  • Job interview questions      │
│                                 │
├─────────────────────────────────┤
│  [Start Practice] [Stop]        │
│  [Change Topic] [Settings]      │
└─────────────────────────────────┘
```

---

## 🔧 Implementation Plan

### Phase 1: Basic Conversation (Week 1)
**Files to create:**
- `ai_conversation.py` - Main conversation engine
- `conversation_ui.py` - Gradio sidebar component

**Features:**
- [x] Basic Gemini chat integration
- [x] User speech input
- [x] AI text response
- [x] Conversation history

**Code structure:**
```python
class ConversationEngine:
    def __init__(self):
        self.history = []
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def process_user_input(self, text):
        # Add to history
        # Get AI response
        # Return response
        pass
```

### Phase 2: Sentiment Analysis (Week 2)
**Files:**
- `sentiment_analyzer.py` - Sentiment detection

**Features:**
- [x] Real-time sentiment detection
- [x] Emoji indicators (😊 😐 😔)
- [x] Sentiment-aware AI responses

**Library:**
```python
from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1
    
    if polarity > 0.3:
        return "positive", "😊"
    elif polarity < -0.3:
        return "negative", "😔"
    else:
        return "neutral", "😐"
```

### Phase 3: Grammar Checking (Week 3)
**Files:**
- `grammar_checker.py` - Grammar validation

**Features:**
- [x] Detect grammar mistakes
- [x] Suggest corrections
- [x] Explain errors

**Implementation options:**

**Option A: LanguageTool (Free API)**
```python
import language_tool_python

tool = language_tool_python.LanguageTool('en-US')

def check_grammar(text):
    matches = tool.check(text)
    errors = []
    for match in matches:
        errors.append({
            'error': match.ruleId,
            'message': match.message,
            'suggestion': match.replacements[0] if match.replacements else None
        })
    return errors
```

**Option B: Gemini (Integrated)**
```python
def check_grammar_gemini(text):
    prompt = f"""Check this sentence for grammar errors:
    "{text}"
    
    If there are errors, respond in JSON:
    {{
        "has_error": true,
        "errors": ["error description"],
        "correct": "corrected sentence"
    }}
    
    If correct, respond:
    {{
        "has_error": false
    }}
    """
    
    response = model.generate_content(prompt)
    return json.loads(response.text)
```

### Phase 4: Pronunciation Checking (Week 4)
**Files:**
- `pronunciation_checker.py` - Phonetic analysis

**Features:**
- [x] Phoneme extraction
- [x] Pronunciation scoring
- [x] Visual feedback

**Implementation:**
```python
from phonemizer import phonemize
import numpy as np
from scipy.spatial.distance import cosine

def check_pronunciation(user_audio, reference_text):
    # 1. Transcribe user audio
    user_text = transcribe(user_audio)
    
    # 2. Convert both to phonemes
    user_phonemes = phonemize(user_text)
    reference_phonemes = phonemize(reference_text)
    
    # 3. Compare similarity
    similarity = calculate_phoneme_similarity(user_phonemes, reference_phonemes)
    
    # 4. Return score (0-100%)
    score = int(similarity * 100)
    
    return {
        'score': score,
        'user_phonemes': user_phonemes,
        'reference_phonemes': reference_phonemes,
        'feedback': get_feedback(score)
    }

def get_feedback(score):
    if score >= 90:
        return "Excellent! 🎉"
    elif score >= 75:
        return "Good! Keep practicing. 👍"
    elif score >= 60:
        return "Needs improvement. Try again. 🔄"
    else:
        return "Let's practice this more. Listen carefully. 👂"
```

### Phase 5: Practice Loop (Week 5)
**Files:**
- `practice_manager.py` - Practice session management

**Features:**
- [x] Repeat until correct
- [x] Progress tracking
- [x] Difficulty adjustment

**State machine:**
```python
class PracticeSession:
    def __init__(self):
        self.state = "idle"  # idle, speaking, correcting, completed
        self.current_sentence = None
        self.attempts = 0
        self.max_attempts = 3
    
    def start_practice(self, sentence):
        self.current_sentence = sentence
        self.state = "speaking"
        self.attempts = 0
        return f"Please say: '{sentence}'"
    
    def check_attempt(self, user_audio):
        user_text = transcribe(user_audio)
        is_correct = self.validate(user_text)
        
        if is_correct:
            self.state = "completed"
            return "Perfect! ✅ Moving to next..."
        else:
            self.attempts += 1
            if self.attempts >= self.max_attempts:
                self.state = "skipped"
                return "Let's move on. We'll come back to this."
            else:
                self.state = "correcting"
                return f"Try again ({self.attempts}/{self.max_attempts}). Listen: [TTS plays]"
```

---

## 📝 Conversation Prompts

### System Prompt (for Gemini)

```python
SYSTEM_PROMPT = """You are a helpful English conversation practice partner. 

Your role:
1. Have natural conversations with the user
2. Gently correct grammar and pronunciation mistakes
3. Suggest related topics to keep conversation flowing
4. Adjust difficulty based on user's level
5. Be encouraging and supportive

Guidelines:
- Keep responses concise (2-3 sentences)
- Use simple language for beginners
- Provide corrections in a friendly way: "Good try! A better way to say that is..."
- Ask follow-up questions to encourage speaking
- Detect user's sentiment and respond appropriately

Current user sentiment: {sentiment}
User's English level: {level}
Current topic: {topic}
"""
```

### Example Conversations

**Scenario 1: Beginner asking question**
```
User: "What is AI?"
Sentiment: Curious 🤔
Level: Beginner

AI: "AI is like teaching computers to think. It helps us do 
     tasks faster. For example, Siri and Alexa use AI.
     
     Would you like to know how AI learns?"
     
Next topics: [Machine Learning] [AI Examples] [How it works]
```

**Scenario 2: Grammar mistake**
```
User: "Yesterday I go to market"
Grammar: ❌ Tense error

AI: "I noticed you said 'I go'. Since this happened yesterday,
     we use past tense: 'I went'.
     
     Correct sentence: 'Yesterday I went to market'
     
     Please try saying it again. 🔄"
     
[Wait for user to repeat]

User: "Yesterday I went to market"
Grammar: ✅ Correct

AI: "Perfect! Well done! 🎉
     
     Now tell me, what did you buy at the market?"
```

**Scenario 3: Pronunciation issue**
```
User: [Says "think" but pronounces as "tink"]
Transcription: "I tink it's good"
Pronunciation: 72% (th-sound issue)

AI: "Good sentence! But let's work on 'think'.
     
     The 'th' sound is important. Put your tongue 
     between your teeth: 'thhh-ink'
     
     Try again: 'I think it's good' 🗣️"
     
[Play TTS pronunciation reference]

User: [Tries again]
Pronunciation: 85% (improved)

AI: "Much better! Keep practicing that 'th' sound. 👍"
```

---

## 🎯 Feature Modules

### Module 1: Sentiment Analyzer
```python
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
```

### Module 2: Grammar Checker
```python
# grammar_checker.py

import google.generativeai as genai

class GrammarChecker:
    def __init__(self, model):
        self.model = model
    
    def check(self, text):
        prompt = f"""Analyze this sentence for grammar errors:
        
        Sentence: "{text}"
        
        Respond in JSON format:
        {{
            "is_correct": true/false,
            "errors": [
                {{
                    "type": "verb tense/subject-verb agreement/etc",
                    "incorrect": "the wrong part",
                    "correct": "the correct version",
                    "explanation": "simple explanation"
                }}
            ],
            "corrected_sentence": "fully corrected sentence",
            "suggestion": "friendly tip for improvement"
        }}
        """
        
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)
    
    def _parse_response(self, response_text):
        try:
            # Extract JSON from response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"is_correct": True, "errors": []}
        except:
            return {"is_correct": True, "errors": []}
```

### Module 3: Pronunciation Checker
```python
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
```

### Module 4: Conversation Engine
```python
# ai_conversation.py

import google.generativeai as genai
from sentiment_analyzer import SentimentAnalyzer
from grammar_checker import GrammarChecker
from pronunciation_checker import PronunciationChecker

class ConversationEngine:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        self.sentiment_analyzer = SentimentAnalyzer()
        self.grammar_checker = GrammarChecker(self.model)
        self.pronunciation_checker = PronunciationChecker()
        
        self.conversation_history = []
        self.user_level = "beginner"  # beginner, intermediate, advanced
        self.current_topic = "general"
        self.stats = {
            'total_messages': 0,
            'grammar_errors': 0,
            'corrections_made': 0,
            'avg_pronunciation': 0
        }
    
    def process_user_message(self, user_text, user_audio=None):
        """Main processing function"""
        
        # 1. Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze(user_text)
        
        # 2. Check grammar
        grammar_result = self.grammar_checker.check(user_text)
        
        # 3. Check pronunciation (if audio provided)
        pronunciation_result = None
        if user_audio:
            pronunciation_result = self.pronunciation_checker.check(
                user_text, 
                user_text  # Reference is the correct version
            )
        
        # 4. Update stats
        self._update_stats(grammar_result, pronunciation_result)
        
        # 5. Generate AI response
        ai_response = self._generate_response(
            user_text, 
            sentiment, 
            grammar_result,
            pronunciation_result
        )
        
        # 6. Get next topic suggestions
        topic_suggestions = self._suggest_topics(user_text)
        
        # 7. Add to history
        self.conversation_history.append({
            'user': user_text,
            'ai': ai_response,
            'sentiment': sentiment,
            'grammar': grammar_result,
            'pronunciation': pronunciation_result,
            'timestamp': time.time()
        })
        
        return {
            'ai_response': ai_response,
            'sentiment': sentiment,
            'grammar': grammar_result,
            'pronunciation': pronunciation_result,
            'topic_suggestions': topic_suggestions,
            'stats': self.stats
        }
    
    def _generate_response(self, user_text, sentiment, grammar, pronunciation):
        """Generate contextual AI response"""
        
        # Build context-aware prompt
        prompt = f"""Continue this conversation naturally.

User said: "{user_text}"
User sentiment: {sentiment['label']} {sentiment['emoji']}
Grammar: {"Correct ✅" if grammar['is_correct'] else "Has errors ❌"}

Your response should:
1. If grammar errors exist, gently correct them first
2. If pronunciation issues (if any), provide tips
3. Then respond to their message
4. Ask a follow-up question
5. Keep it friendly and encouraging

Response (2-3 sentences):"""

        response = self.model.generate_content(prompt)
        return response.text
    
    def _suggest_topics(self, user_text):
        """Suggest next conversation topics"""
        
        prompt = f"""Based on this user message: "{user_text}"
        
        Suggest 3 related conversation topics they might want to discuss next.
        
        Respond as JSON array: ["Topic 1", "Topic 2", "Topic 3"]"""
        
        response = self.model.generate_content(prompt)
        
        try:
            import json
            return json.loads(response.text)
        except:
            return ["Continue this topic", "Ask a question", "New topic"]
    
    def _update_stats(self, grammar, pronunciation):
        self.stats['total_messages'] += 1
        
        if not grammar['is_correct']:
            self.stats['grammar_errors'] += 1
            self.stats['corrections_made'] += len(grammar['errors'])
        
        if pronunciation:
            # Running average
            n = self.stats['total_messages']
            old_avg = self.stats['avg_pronunciation']
            new_score = pronunciation['score']
            self.stats['avg_pronunciation'] = ((old_avg * (n-1)) + new_score) / n
```

---

## 🚀 Integration with app_gradio.py

```python
# Add to app_gradio.py

with gr.Blocks() as demo:
    # ... existing meeting transcription UI ...
    
    # NEW: AI Conversation Sidebar
    with gr.Column(scale=1):
        gr.Markdown("## 🗣️ AI Conversation Practice")
        
        with gr.Row():
            conv_start_btn = gr.Button("Start Practice", variant="primary")
            conv_stop_btn = gr.Button("Stop", variant="stop")
        
        conv_status = gr.Textbox(label="Status", value="Ready", interactive=False)
        conv_sentiment = gr.Textbox(label="Sentiment", value="😐 Neutral", interactive=False)
        
        conv_chat = gr.Chatbot(label="Conversation", height=400)
        
        conv_stats = gr.Markdown("""
        **Session Stats:**
        - Total messages: 0
        - Grammar errors: 0
        - Avg pronunciation: 0%
        """)
        
        conv_topics = gr.CheckboxGroup(
            label="Next Topics",
            choices=["Continue", "Ask question", "New topic"]
        )
    
    # Event handlers
    def start_conversation():
        # Initialize conversation engine
        pass
    
    def process_conversation_audio(audio):
        # Process user speech
        # Return AI response + feedback
        pass
    
    conv_start_btn.click(start_conversation, outputs=[conv_status])
```

---

## 📦 Dependencies

```txt
# Add to requirements.txt

# Existing
openai-whisper
gradio
google-generativeai
python-dotenv
numpy

# NEW for AI Conversation
textblob==0.17.1              # Sentiment analysis
phonemizer==3.2.1             # Pronunciation checking
language-tool-python==2.7.1   # Grammar checking (optional)
gTTS==2.3.2                   # Text-to-speech
scipy==1.11.4                 # Similarity calculations
```

---

## ✅ Success Criteria

### Functional
- [ ] User can have natural conversation with AI
- [ ] Sentiment is detected correctly (>80% accuracy)
- [ ] Grammar errors are caught and corrected
- [ ] Pronunciation is scored accurately
- [ ] User is prompted to practice until correct
- [ ] Topic suggestions are relevant

### Performance
- [ ] Response time < 2s
- [ ] Real-time audio processing
- [ ] Smooth UI updates
- [ ] No lag or freezing

### UX
- [ ] Clear feedback indicators
- [ ] Encouraging tone (not discouraging)
- [ ] Progress visible
- [ ] Easy to use

---

## 🎯 Next Steps

1. **Review this design** - Approve or suggest changes
2. **Start with Phase 1** - Basic conversation (1 week)
3. **Iterate phases** - Add features incrementally
4. **Test with users** - Get feedback
5. **Polish UI** - Make it beautiful

---

**Ready to start implementation?** 🚀

Which phase should we begin with?