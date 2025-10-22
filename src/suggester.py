# suggester.py

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if not GENAI_API_KEY:
    print("⚠️ WARNING: GENAI_API_KEY not found in .env file")
    
genai.configure(api_key=GENAI_API_KEY)

# Use gemini-1.5-flash-latest or gemini-1.5-pro
try:
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except:
    # Fallback to older stable model
    model = genai.GenerativeModel("gemini-pro")

def get_suggestion(text):
    """
    Generate AI suggestions for meeting transcript
    """
    # TEMPORARILY DISABLED - Focus on transcription first
    # You can enable this later once transcription is working perfectly
    return ""
    
    # Uncomment below when ready to use Gemini:
    """
    if not text or len(text.strip()) < 3:
        return ""
    
    noise_words = ["you", "uh", "um", "hmm", "ah"]
    if text.strip().lower() in noise_words:
        return ""
    
    prompt = f'''
    You are a smart meeting assistant. Based on the following transcript snippet, provide a brief suggestion.

    Rules:
    - If it's a question, suggest a concise answer
    - If it's an action item or decision, summarize it
    - If it's unclear, say "Continue listening..."
    - Keep response under 50 words

    Transcript: "{text}"
    
    Your suggestion:
    '''
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Suggestion error: {str(e)[:100]}")
        return ""
    """