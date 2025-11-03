    # test_gemini.py
"""
Test Gemini API with different prompts and safety settings
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
if not GENAI_API_KEY:
    print("❌ No API key found")
    exit(1)

genai.configure(api_key=GENAI_API_KEY)

print("=" * 60)
print("🧪 Testing Gemini Models")
print("=" * 60)

# Try different models
models_to_test = [
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",  
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
]

for model_name in models_to_test:
    print(f"\n📝 Testing: {model_name}")
    print("-" * 60)
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Test 1: Simple prompt (no safety issues)
        print("Test 1: Simple greeting")
        response = model.generate_content("Say hello in one sentence")
        print(f"✅ Response: {response.text}")
        
        # Test 2: Conversation prompt (might trigger safety)
        print("\nTest 2: Conversation response")
        prompt = """You are a teacher. User said: "I want to learn English"
        
Respond in 1 sentence:"""
        
        response = model.generate_content(
            prompt,
            safety_settings={
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
            }
        )
        
        if response.text:
            print(f"✅ Response: {response.text}")
        else:
            print(f"❌ Response blocked")
            print(f"   Finish reason: {response.candidates[0].finish_reason}")
            if response.candidates[0].safety_ratings:
                print("   Safety ratings:")
                for rating in response.candidates[0].safety_ratings:
                    print(f"   - {rating.category}: {rating.probability}")
        
        print(f"\n✅ {model_name} is working!")
        print("=" * 60)
        break  # Found working model
        
    except Exception as e:
        print(f"❌ {model_name} failed: {e}")
        continue

print("\n🔍 Recommendation:")
print("If all tests passed, the model is fine.")
print("If conversation test blocked, try using simple responses in code.")
print("=" * 60)