# utils/translation.py
from config import settings
from utils import log

def translate_text_sync(text: str, target_lang: str) -> str:
    """
    Translate text to target language using deep-translator
    
    Args:
        text: Text to translate
        target_lang: Target language code (en, hi, mr)
    
    Returns:
        Translated text or original if translation fails
    """
    
    # If no text or empty, return as-is
    if not text or not text.strip():
        return text
    
    # If target is English, no translation needed
    if target_lang == "en":
        log.info(f"🌐 Target is English, skipping translation")
        return text
    
    try:
        from deep_translator import GoogleTranslator
        
        # Language code mapping
        lang_map = {
            "hi": "hi",  # Hindi
            "mr": "mr",  # Marathi
            "en": "en"   # English
        }
        
        target = lang_map.get(target_lang, "hi")
        
        log.info(f"🔄 Translating to {target}: '{text[:50]}...'")
        
        # Create translator (auto-detect source language)
        translator = GoogleTranslator(source='auto', target=target)
        
        # Translate
        translated = translator.translate(text)
        
        if translated and translated != text:
            log.info(f"✅ Translation successful: '{translated[:50]}...'")
            return translated
        else:
            log.warning(f"⚠️ Translation returned same text")
            return text
            
    except ImportError as ie:
        log.error(f"❌ deep-translator not installed: {ie}")
        log.warning("Install with: pip install deep-translator")
        return text
        
    except Exception as e:
        log.error(f"❌ Translation error: {e}")
        
        # Try Sarvam API as fallback if configured
        if hasattr(settings, 'SARVAM_API_KEY') and settings.SARVAM_API_KEY:
            try:
                log.info("🔄 Trying Sarvam API as fallback...")
                return translate_with_sarvam(text, target_lang)
            except Exception as sarvam_error:
                log.error(f"❌ Sarvam also failed: {sarvam_error}")
        
        # Return original text if all fail
        log.warning("⚠️ All translation methods failed, returning original text")
        return text


def translate_with_sarvam(text: str, target_lang: str) -> str:
    """
    Translate using Sarvam AI API (fallback)
    
    Args:
        text: Text to translate
        target_lang: Target language (hi, mr, en)
    
    Returns:
        Translated text or original if fails
    """
    import requests
    
    try:
        if not hasattr(settings, 'SARVAM_API_KEY') or not settings.SARVAM_API_KEY:
            log.warning("⚠️ SARVAM_API_KEY not configured")
            return text
        
        # Sarvam API endpoint
        url = "https://api.sarvam.ai/translate"
        
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Language mapping for Sarvam
        lang_codes = {
            "hi": "hi-IN",
            "mr": "mr-IN",
            "en": "en-IN"
        }
        
        payload = {
            "input": text,
            "source_language_code": "auto",
            "target_language_code": lang_codes.get(target_lang, "hi-IN"),
            "speaker_gender": "Male",
            "mode": "formal"
        }
        
        log.info(f"📤 Calling Sarvam API for {target_lang} translation...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            translated = result.get("translated_text", text)
            
            if translated and translated != text:
                log.info(f"✅ Sarvam translation success")
                return translated
            else:
                log.warning("⚠️ Sarvam returned same text")
                return text
        else:
            log.error(f"❌ Sarvam API error: {response.status_code}")
            return text
            
    except Exception as e:
        log.error(f"❌ Sarvam translation failed: {e}")
        return text


# Async wrapper for compatibility
async def translate_text_async(text: str, target_lang: str) -> str:
    """
    Async wrapper for translate_text_sync
    
    Args:
        text: Text to translate
        target_lang: Target language code
    
    Returns:
        Translated text
    """
    import asyncio
    
    # Run sync function in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, translate_text_sync, text, target_lang)
    return result
