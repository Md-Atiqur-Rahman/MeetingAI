# ai_summarizer.py
"""
AI-powered meeting summary using Google Gemini (100% FREE)
No OpenAI, no paid API - completely free!
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

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
        "models/gemini-2.5-flash",       # Latest, fastest
        "models/gemini-2.0-flash",       # Stable
        "models/gemini-flash-latest",    # Auto-updated
        "models/gemini-pro-latest",      # High quality
    ]
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            # Quick test
            test_response = model.generate_content("Hi")
            print(f"✅ AI Summarizer using: {model_name}")
            break
        except Exception as e:
            print(f"⚠️ {model_name} failed, trying next...")
            continue
    
    if not model:
        print("❌ No Gemini model available")


def generate_ai_summary(transcripts_list):
    """
    Generate AI-powered meeting summary using Gemini
    
    Args:
        transcripts_list: List of transcript dicts with 'speaker', 'en', 'bn', 'time'
    
    Returns:
        str: Markdown formatted AI summary
    """
    
    if not transcripts_list or len(transcripts_list) == 0:
        return "📭 No transcripts available for AI summary."
    
    if not model:
        return """❌ Gemini AI Not Configured

**Setup Instructions:**

1. Get FREE API key from: https://makersuite.google.com/app/apikey
2. Add to `.env` file:
   ```
   GENAI_API_KEY=AIzaSyxxxxxxxxxxxxx
   ```
3. Restart the app

**Free Tier:**
- 60 requests per minute
- 1 million token context
- No credit card required!

**Fallback:** Use 'Show Summary' for basic transcript view.
"""
    
    try:
        # Prepare transcript text
        transcript_text = ""
        for i, t in enumerate(transcripts_list, 1):
            speaker = t.get('speaker', 'Unknown')
            text = t.get('en', '')
            timestamp = t.get('time', '')
            transcript_text += f"[{timestamp}] {speaker}: {text}\n"
        
        # AI prompt for intelligent summary
        prompt = f"""You are an expert meeting analyzer. Analyze this meeting transcript and provide a comprehensive summary.

Meeting Transcript (Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}):
{transcript_text}

Please provide:

1. **Executive Summary** (2-3 sentences overview of the entire meeting)

2. **Key Discussion Points** (Main topics discussed - use bullet points)

3. **Action Items** (Any tasks, decisions, or follow-ups mentioned)

4. **Important Decisions** (Key conclusions or agreements reached)

5. **Next Steps** (What should happen after this meeting)

6. **Suggestions** (Recommendations for improvement or follow-up)

Format your response in clean markdown. Be specific and professional."""

        # Generate with Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2000,
            ),
            safety_settings={
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
            }
        )
        
        # Check if response was blocked
        if not response.text:
            # Try to get the reason
            finish_reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
            safety_ratings = response.candidates[0].safety_ratings if response.candidates else []
            
            error_details = f"""**Finish Reason:** {finish_reason}

**Possible Causes:**
- Content was flagged by safety filters
- Empty or duplicate transcript
- API rate limit hit

**Safety Ratings:**
"""
            for rating in safety_ratings:
                error_details += f"- {rating.category}: {rating.probability}\n"
            
            return f"""⚠️ AI Summary Blocked

{error_details}

**Solutions:**
1. Wait 30 seconds and try again
2. Ensure transcript has meaningful content
3. Check if same meeting was summarized recently

**Statistics:**
- Segments: {total_segments}
- Words: {total_words}

**Fallback:** Use 'Show Summary' button for basic transcript view.
"""
        
        ai_summary = response.text
        
        # Calculate statistics
        total_segments = len(transcripts_list)
        total_words = sum(len(t.get('en', '').split()) for t in transcripts_list)
        unique_speakers = len(set(t.get('speaker', 'Unknown') for t in transcripts_list))
        
        # Build final summary
        full_summary = f"""# 🤖 AI-Powered Meeting Analysis
*Generated using Google Gemini 2.5 (FREE)*

{ai_summary}

---

## 📊 Meeting Statistics

| Metric | Value |
|--------|-------|
| Total Segments | {total_segments} |
| Total Words | {total_words} |
| Unique Speakers | {unique_speakers} |
| Estimated Duration | ~{total_segments * 5} seconds |

---

## 📝 Full Transcript

"""
        
        # Add condensed transcript
        for i, t in enumerate(transcripts_list, 1):
            speaker = t.get('speaker', 'Unknown')
            text = t.get('en', '')
            timestamp = t.get('time', '')
            full_summary += f"**{i}. [{timestamp}] {speaker}:**  \n{text}\n\n"
        
        full_summary += f"\n---\n\n*AI Summary generated on {time.strftime('%Y-%m-%d %H:%M:%S')}*\n"
        full_summary += "*Powered by Google Gemini 2.5 Flash (100% Free)*"
        
        return full_summary
            
    except Exception as e:
        error_msg = str(e)
        
        return f"""❌ AI Summary Generation Failed

**Error:** {error_msg}

**Troubleshooting:**

1. **Check API Key:**
   - Verify GENAI_API_KEY in .env file
   - Get new key: https://makersuite.google.com/app/apikey

2. **Check Internet Connection:**
   - Ensure stable internet access

3. **Check API Quota:**
   - Free tier: 60 requests/minute
   - Check usage: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com

4. **Try Again:**
   - Temporary API issues may resolve automatically

**Statistics:**
- Segments: {len(transcripts_list)}
- Words: {sum(len(t.get('en', '').split()) for t in transcripts_list)}

**Fallback:** Use 'Show Summary' button for basic transcript view.
"""


def test_ai_summarizer():
    """Test function to verify AI summarizer works"""
    
    print("\n" + "="*60)
    print("🧪 Testing AI Summarizer")
    print("="*60)
    
    # Sample transcript
    sample_transcripts = [
        {
            "speaker": "Person-1",
            "en": "Good morning everyone. Let's start the quarterly review meeting.",
            "bn": "সবাইকে সুপ্রভাত। চলুন ত্রৈমাসিক পর্যালোচনা মিটিং শুরু করি।",
            "time": "09:00:00"
        },
        {
            "speaker": "Person-2",
            "en": "Thank you. I'll present the Q3 financial results. Revenue is up 15% compared to last quarter.",
            "bn": "ধন্যবাদ। আমি Q3 আর্থিক ফলাফল উপস্থাপন করব। গত ত্রৈমাসিকের তুলনায় রাজস্ব 15% বৃদ্ধি পেয়েছে।",
            "time": "09:01:30"
        },
        {
            "speaker": "Person-1",
            "en": "That's excellent news. What are the main factors driving this growth?",
            "bn": "এটা দুর্দান্ত খবর। এই বৃদ্ধির মূল কারণগুলো কী?",
            "time": "09:03:00"
        },
        {
            "speaker": "Person-2",
            "en": "New product launches and expanded market reach. We should continue this strategy.",
            "bn": "নতুন পণ্য লঞ্চ এবং সম্প্রসারিত বাজার পৌঁছানো। আমাদের এই কৌশল চালিয়ে যাওয়া উচিত।",
            "time": "09:04:15"
        }
    ]
    
    print("\n📝 Sample Transcript:")
    for t in sample_transcripts:
        print(f"  [{t['time']}] {t['speaker']}: {t['en'][:50]}...")
    
    print("\n🤖 Generating AI Summary...\n")
    
    summary = generate_ai_summary(sample_transcripts)
    print(summary)
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)


if __name__ == "__main__":
    # Run test when executed directly
    test_ai_summarizer()