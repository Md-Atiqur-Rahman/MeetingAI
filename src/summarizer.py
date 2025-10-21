import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")  # Updated model

def generate_summary(transcript_list):
    """
    Generate a comprehensive meeting summary using Gemini AI
    
    Args:
        transcript_list: List of transcript segments
    
    Returns:
        str: Formatted meeting summary
    """
    if not transcript_list or len(transcript_list) == 0:
        return "No transcript available to summarize."
    
    # Combine all transcript segments
    full_text = " ".join(transcript_list)
    
    # If transcript is very short, return it as is
    if len(full_text) < 100:
        return full_text
    
    # Use Gemini to create a structured summary
    prompt = f"""
    You are an expert meeting assistant. Please analyze the following meeting transcript and provide:

    1. **Key Discussion Points**: Main topics discussed
    2. **Action Items**: Tasks or decisions that need follow-up
    3. **Important Questions**: Any unanswered questions or concerns raised
    4. **Summary**: A brief 2-3 sentence overview

    Meeting Transcript:
    {full_text}

    Please format your response clearly with headers and bullet points.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Summary generation error: {e}")
        # Fallback: simple truncation
        return f"**Meeting Transcript:**\n\n{full_text[:1000]}..." if len(full_text) > 1000 else full_text