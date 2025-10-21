# suggester.py

import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

model = genai.GenerativeModel("gemini-pro")

def get_suggestion(text):
    prompt = f"""
    You are a smart meeting assistant. Based on the following transcript snippet, suggest:
    - If it's a question, what could be a good answer?
    - If it's a decision or action item, summarize it.
    - If it's unclear, suggest clarification.

    Transcript: "{text}"
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating suggestion: {e}"