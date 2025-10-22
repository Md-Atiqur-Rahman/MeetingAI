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
    Generate AI suggestions - DISABLED for now
    Enable when Gemini API is properly configured
    """
    return ""  # Disabled - no suggestions