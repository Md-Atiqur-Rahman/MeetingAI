# ai_conversation.py
"""
AI Conversation Practice Engine
Week 1: Basic spoken conversation with voice input/output
FIXED VERSION - Temp file handling corrected
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from gtts import gTTS
import tempfile
import pygame
import threading

load_dotenv()

# Configure Gemini
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
if not GENAI_API_KEY:
    print("❌ ERROR: GENAI_API_KEY not found in .env file")
    print("Get your free key: https://makersuite.google.com/app/apikey")
    model = None
else:
    genai.configure(api_key=GENAI_API_KEY)
    
    # Try latest Gemini models
    model = None
    model_names = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-flash-latest",
    ]
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            # Quick test
            test_response = model.generate_content("Hi")
            print(f"✅ Conversation AI using: {model_name}")
            break
        except Exception as e:
            print(f"⚠️ {model_name} not available, trying next...")
            continue
    
    if not model:
        print("❌ No Gemini model available")

# Initialize pygame for audio playback
try:
    pygame.mixer.init()
    print("✅ Pygame mixer initialized")
except Exception as e:
    print(f"⚠️ Pygame init warning: {e}")


class ConversationEngine:
    """
    Manages AI conversation with voice input/output
    """
    
    def __init__(self):
        self.model = model
        self.conversation_history = []
        self.is_active = False
        self.user_level = "beginner"  # beginner, intermediate, advanced
        self.current_topic = "general conversation"
        
        # Stats
        self.stats = {
            'total_turns': 0,
            'session_start': None,
            'last_interaction': None
        }
        
        # System prompt for conversational AI
        self.system_prompt = """You are a helpful English teacher having a conversation.

Keep responses very short - just 1-2 sentences.
Ask simple follow-up questions.
Be friendly and encouraging.

User level: {level}
Current turns: {turns}
"""
    
    def start_session(self):
        """Start a new conversation session"""
        self.is_active = True
        self.stats['session_start'] = time.time()
        self.conversation_history = []
        
        # Initial greeting
        greeting = "Hello! I'm your AI conversation partner. Let's practice English together! What would you like to talk about?"
        
        self.conversation_history.append({
            'role': 'ai',
            'text': greeting,
            'timestamp': time.time()
        })
        
        print(f"🤖 AI: {greeting}")
        
        return greeting
    
    def stop_session(self):
        """Stop the conversation session"""
        self.is_active = False
        duration = time.time() - self.stats['session_start'] if self.stats['session_start'] else 0
        
        summary = f"""Session ended!

**Duration:** {int(duration/60)} minutes
**Total turns:** {self.stats['total_turns']}
**Topics discussed:** {self.current_topic}

Great practice session! Keep it up! 💪"""
        
        return summary
    
    def process_user_speech(self, user_text):
        """
        Process user's spoken input and generate AI response
        
        Args:
            user_text: Transcribed user speech
            
        Returns:
            dict: {
                'ai_response': str,
                'should_speak': bool,
                'stats': dict
            }
        """
        
        if not self.model:
            return {
                'ai_response': "AI model not available. Please check your API key.",
                'should_speak': False,
                'stats': self.stats
            }
        
        if not user_text or len(user_text.strip()) < 2:
            return {
                'ai_response': "I didn't catch that. Could you please repeat?",
                'should_speak': True,
                'stats': self.stats
            }
        
        try:
            # Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'text': user_text,
                'timestamp': time.time()
            })
            
            # Build conversation context
            context = self._build_context()
            
            # Try to generate AI response
            ai_response = None
            
            try:
                # Generate AI response with safety settings disabled
                prompt = f"""{self.system_prompt.format(
                    level=self.user_level,
                    turns=self.stats['total_turns']
                )}

Recent conversation:
{context}

User: "{user_text}"

Your response (1-2 sentences):"""
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.9,
                        max_output_tokens=100,
                    ),
                    safety_settings={
                        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                    }
                )
                
                # Try to get response text
                if response and response.text:
                    ai_response = response.text.strip()
                    ai_response = ai_response.strip('"').strip("'")
                    print("✅ AI response generated successfully")
                else:
                    print("⚠️ AI response blocked by safety filters")
                    ai_response = None
                    
            except Exception as gemini_error:
                print(f"⚠️ Gemini API error: {gemini_error}")
                ai_response = None
            
            # Fallback responses if AI blocked
            if not ai_response:
                fallback_responses = [
                    "That's interesting! Can you tell me more?",
                    "I see. What else would you like to talk about?",
                    "Sounds good! What do you think about it?",
                    "Nice! Tell me more about that.",
                    "Great! What's your favorite part?"
                ]
                
                import random
                ai_response = random.choice(fallback_responses)
                print(f"🔄 Using fallback response: {ai_response}")
            
            # Add AI response to history
            self.conversation_history.append({
                'role': 'ai',
                'text': ai_response,
                'timestamp': time.time()
            })
            
            # Update stats
            self.stats['total_turns'] += 1
            self.stats['last_interaction'] = time.time()
            
            print(f"👤 You: {user_text}")
            print(f"🤖 AI: {ai_response}")
            
            return {
                'ai_response': ai_response,
                'should_speak': True,
                'stats': self.stats,
                'conversation_history': self._format_history()
            }
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                'ai_response': "Sorry, I had a problem. Could you say that again?",
                'should_speak': True,
                'stats': self.stats
            }
    
    def _build_context(self):
        """Build recent conversation context (last 4 turns)"""
        recent = self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history
        
        context_lines = []
        for msg in recent:
            role = "You" if msg['role'] == 'user' else "AI"
            context_lines.append(f"{role}: {msg['text']}")
        
        return "\n".join(context_lines)
    
    def _format_history(self):
        """Format conversation history for display"""
        formatted = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            role_name = "You" if msg['role'] == 'user' else "AI"
            formatted.append(f"{role_icon} **{role_name}:** {msg['text']}")
        
        return "\n\n".join(formatted)
    
    def suggest_topics(self):
        """Suggest conversation topics based on level"""
        topics_by_level = {
            'beginner': [
                "Introduce yourself",
                "Talk about your hobbies",
                "Describe your day",
                "Your favorite food",
                "Your family"
            ],
            'intermediate': [
                "Your career goals",
                "Recent news or events",
                "Travel experiences",
                "Books or movies",
                "Technology and innovation"
            ],
            'advanced': [
                "Global issues",
                "Philosophy and ethics",
                "Business strategies",
                "Scientific discoveries",
                "Cultural differences"
            ]
        }
        
        return topics_by_level.get(self.user_level, topics_by_level['beginner'])
    
    def change_level(self, new_level):
        """Change user's English level"""
        if new_level in ['beginner', 'intermediate', 'advanced']:
            self.user_level = new_level
            return f"Level changed to: {new_level}"
        return "Invalid level"


class VoiceManager:
    """
    Manages text-to-speech for AI responses
    FIXED: Proper temp file handling
    """
    
    def __init__(self):
        self.temp_files = []
        self.is_speaking = False
    
    def speak(self, text, lang='en'):
        """
        Convert text to speech and play it
        FIXED VERSION with proper file handling
        
        Args:
            text: Text to speak
            lang: Language code (default: 'en')
        """
        
        if not text:
            print("⚠️ TTS: No text to speak")
            return
        
        temp_filename = None
        
        try:
            print(f"🔊 TTS: Preparing to speak: '{text[:50]}...'")
            self.is_speaking = True
            
            # Generate speech
            print("🔊 TTS: Generating audio with gTTS...")
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # FIXED: Create temp file and close it before saving
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_filename = temp_file.name
            temp_file.close()  # ✅ CRITICAL: Close file before saving
            
            print(f"🔊 TTS: Saving to temp file: {temp_filename}")
            tts.save(temp_filename)
            
            # Verify file exists
            if not os.path.exists(temp_filename):
                print(f"❌ TTS: File not created: {temp_filename}")
                self.is_speaking = False
                return
            
            file_size = os.path.getsize(temp_filename)
            print(f"✅ TTS: File saved successfully ({file_size} bytes)")
            self.temp_files.append(temp_filename)
            
            # Play audio
            print(f"🔊 TTS: Loading audio file...")
            pygame.mixer.music.load(temp_filename)
            print(f"🔊 TTS: Playing audio NOW... 🔊")
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print(f"✅ TTS: Finished speaking")
            self.is_speaking = False
            
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            import traceback
            traceback.print_exc()
            self.is_speaking = False
        
        finally:
            # Unload audio to free the file
            try:
                pygame.mixer.music.unload()
                time.sleep(0.1)  # Give it time to release the file
            except:
                pass
    
    def stop_speaking(self):
        """Stop current speech"""
        if self.is_speaking:
            pygame.mixer.music.stop()
            self.is_speaking = False
    
    def cleanup(self):
        """Clean up temporary audio files"""
        # Unload first
        try:
            pygame.mixer.music.unload()
            time.sleep(0.2)
        except:
            pass
        
        # Then delete
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ Cleaned up: {temp_file}")
            except Exception as e:
                print(f"⚠️ Could not delete {temp_file}: {e}")
        
        self.temp_files = []


# Global instances
conversation_engine = ConversationEngine()
voice_manager = VoiceManager()


def start_conversation():
    """Start a new conversation session"""
    greeting = conversation_engine.start_session()
    
    # Speak greeting in background thread
    threading.Thread(target=voice_manager.speak, args=(greeting,), daemon=True).start()
    
    return {
        'status': '🟢 Active',
        'message': greeting,
        'history': conversation_engine._format_history(),
        'stats': _format_stats()
    }


def stop_conversation():
    """Stop the conversation session"""
    voice_manager.stop_speaking()
    summary = conversation_engine.stop_session()
    voice_manager.cleanup()
    
    return {
        'status': '⚪ Stopped',
        'message': summary,
        'history': conversation_engine._format_history(),
        'stats': _format_stats()
    }


def process_speech(user_text):
    """
    Process user's speech and generate AI response
    
    Args:
        user_text: Transcribed user speech
    
    Returns:
        dict with AI response and stats
    """
    
    # Process with conversation engine
    result = conversation_engine.process_user_speech(user_text)
    
    # Speak AI response in background
    if result['should_speak']:
        threading.Thread(
            target=voice_manager.speak, 
            args=(result['ai_response'],), 
            daemon=True
        ).start()
    
    return {
        'ai_response': result['ai_response'],
        'history': result.get('conversation_history', ''),
        'stats': _format_stats()
    }


def _format_stats():
    """Format stats for display"""
    stats = conversation_engine.stats
    
    duration = 0
    if stats['session_start']:
        duration = int((time.time() - stats['session_start']) / 60)
    
    return f"""**Session Stats:**
- Duration: {duration} minutes
- Total turns: {stats['total_turns']}
- Level: {conversation_engine.user_level}
- Topic: {conversation_engine.current_topic}
"""


def get_topic_suggestions():
    """Get topic suggestions for current level"""
    return conversation_engine.suggest_topics()


def change_level(level):
    """Change conversation difficulty level"""
    return conversation_engine.change_level(level)


# Test function
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Testing AI Conversation Engine - FIXED VERSION")
    print("="*60)
    
    # Start conversation
    print("\n1️⃣ Starting conversation...")
    result = start_conversation()
    print(f"Status: {result['status']}")
    print(f"AI: {result['message']}")
    
    print("\n⏳ Waiting for AI to speak...")
    time.sleep(5)  # Wait for TTS to complete
    
    # Simulate user speech
    print("\n2️⃣ User speaks...")
    test_inputs = [
        "Hello! I want to practice English",
        "I like programming and technology",
        "What should I learn next?"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        result = process_speech(user_input)
        print(f"🤖 AI: {result['ai_response']}")
        print("\n⏳ Waiting for AI to speak...")
        time.sleep(5)  # Wait for TTS
    
    # Stop conversation
    print("\n3️⃣ Stopping conversation...")
    result = stop_conversation()
    print(f"Status: {result['status']}")
    print(f"\n{result['message']}")
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)