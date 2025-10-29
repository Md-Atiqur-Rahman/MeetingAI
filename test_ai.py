# test_ai.py - UPDATED
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 50)
print("🔍 API Key Check")
print("=" * 50)

gemini_key = os.getenv("GENAI_API_KEY")
print(f"Gemini Key: {'✅ Found' if gemini_key else '❌ Not found'}")

print("\n" + "=" * 50)
print("🧪 Testing Available Gemini Models")
print("=" * 50)

if gemini_key:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    
    # List all available models
    print("\n📋 Available Models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  ✅ {m.name}")
    except Exception as e:
        print(f"  ❌ Can't list models: {e}")
    
    # Test specific models
    test_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-pro",
        "models/gemini-pro",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro"
    ]
    
    print("\n🧪 Testing Models:")
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say hello")
            print(f"  ✅ {model_name} - Working!")
            print(f"     Response: {response.text[:50]}...")
            break  # Found working model
        except Exception as e:
            print(f"  ❌ {model_name} - {str(e)[:60]}")
else:
    print("⚠️ Gemini key not found")