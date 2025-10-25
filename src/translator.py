# translator.py - English to Bangla translation

from deep_translator import GoogleTranslator
import time

# Initialize translator (English to Bengali)
translator = GoogleTranslator(source='en', target='bn')

print("✅ Translator initialized (English → Bangla)")

def translate_to_bangla(text):
    """
    Translate English text to Bangla using Google Translate
    
    Args:
        text: English text to translate
    
    Returns:
        str: Bangla translation
    """
    if not text or len(text.strip()) < 2:
        print("⚠️ Translation skipped - text too short")
        return ""
    
    try:
        print(f"🔄 Translating: '{text[:100]}'...")
        
        # Translate using Google Translate (free, no API key)
        bangla_text = translator.translate(text)
        
        print(f"✅ Translation result: '{bangla_text[:100]}'")
        
        return bangla_text
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        import traceback
        traceback.print_exc()
        return ""

def translate_batch(text_list):
    """
    Translate multiple texts (for efficiency)
    
    Args:
        text_list: List of English texts
    
    Returns:
        list: List of Bangla translations
    """
    results = []
    for text in text_list:
        if text:
            try:
                bangla = translator.translate(text)
                results.append(bangla)
            except Exception as e:
                print(f"⚠️ Translation error: {e}")
                results.append("")
        else:
            results.append("")
    
    return results