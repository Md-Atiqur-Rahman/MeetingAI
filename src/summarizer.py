import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if not GENAI_API_KEY:
    print("⚠️ WARNING: GENAI_API_KEY not found in .env file")

genai.configure(api_key=GENAI_API_KEY)

# Try multiple model names (in order of preference)
model = None
model_names = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest", 
    "gemini-pro"
]

for model_name in model_names:
    try:
        model = genai.GenerativeModel(model_name)
        print(f"✅ Using Gemini model: {model_name}")
        break
    except Exception as e:
        print(f"⚠️ Model {model_name} not available: {e}")
        continue

if model is None:
    print("❌ No Gemini model available. Summary will be basic text only.")

def generate_summary(transcript_list):
    """
    Generate a meeting summary (without AI for now)
    
    Args:
        transcript_list: List of transcript segments
    
    Returns:
        str: Formatted meeting summary
    """
    if not transcript_list or len(transcript_list) == 0:
        return "No transcript available to summarize."
    
    # Combine all transcript segments
    full_text = " ".join(transcript_list)
    
    # Generate basic statistics
    word_count = len(full_text.split())
    char_count = len(full_text)
    segment_count = len(transcript_list)
    
    # Create a simple but informative summary
    summary = f"""## 📊 Meeting Summary

**Statistics:**
- Total Segments: {segment_count}
- Total Words: {word_count}
- Total Characters: {char_count}
- Duration: ~{segment_count * 3} seconds of speech

---

## 📝 Full Transcript:

"""
    
    # Add all segments with numbers
    for i, text in enumerate(transcript_list, 1):
        summary += f"\n**{i}.** {text}\n"
    
    summary += "\n---\n\n*AI-powered summary is currently disabled. Enable Gemini API for intelligent summaries.*"
    
    return summary