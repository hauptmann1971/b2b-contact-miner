from deep_translator import GoogleTranslator
from config.settings import settings
from loguru import logger
import time


class TranslationService:
    def __init__(self):
        self.cache = {}
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Google Translate"""
        cache_key = f"{text}_{source_lang}_{target_lang}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)
            
            self.cache[cache_key] = translated
            
            time.sleep(0.5)
            
            return translated
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise
