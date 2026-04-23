from sqlalchemy.orm import Session
from models.database import Keyword, SearchResult
from models.schemas import KeywordInput
from services.translation_service import TranslationService
from config.settings import settings
from loguru import logger
from typing import List, Dict
from datetime import datetime, timezone


class KeywordService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.translator = TranslationService()
    
    def add_keyword(self, keyword_data: KeywordInput) -> Keyword:
        """Add a new keyword with automatic translation to target languages"""
        existing = self.db.query(Keyword).filter(
            Keyword.keyword == keyword_data.keyword,
            Keyword.language == keyword_data.language
        ).first()
        
        if existing:
            logger.warning(f"Keyword already exists: {keyword_data.keyword}")
            return existing
        
        keyword = Keyword(
            keyword=keyword_data.keyword,
            language=keyword_data.language,
            country=keyword_data.country
        )
        
        self.db.add(keyword)
        self.db.commit()
        self.db.refresh(keyword)
        
        logger.info(f"Added keyword: {keyword_data.keyword} ({keyword_data.language})")
        return keyword
    
    def generate_translations(self, keyword: str, source_lang: str = "ru") -> Dict[str, List[str]]:
        """Generate keyword variations for all target languages"""
        translations = {}
        
        for target_lang in settings.LANGUAGES:
            if target_lang == source_lang:
                translations[target_lang] = [keyword]
                continue
            
            try:
                translated = self.translator.translate(keyword, source_lang, target_lang)
                variations = self._generate_variations(translated)
                translations[target_lang] = variations
                logger.info(f"Translated '{keyword}' to {target_lang}: {variations}")
            except Exception as e:
                logger.error(f"Translation failed for {target_lang}: {e}")
                translations[target_lang] = [keyword]
        
        return translations
    
    def _generate_variations(self, keyword: str) -> List[str]:
        """Generate keyword variations (synonyms, related terms)"""
        variations = [keyword]
        
        business_terms = {
            "стартап": ["компания", "бизнес", "предприятие"],
            "startup": ["company", "business", "venture"],
            "финтех": ["financial technology", "fintech"],
        }
        
        for term, synonyms in business_terms.items():
            if term in keyword.lower():
                for synonym in synonyms:
                    variation = keyword.lower().replace(term, synonym)
                    if variation not in variations:
                        variations.append(variation)
        
        return variations
    
    def get_pending_keywords(self, limit: int = 100) -> List[Keyword]:
        """Get keywords that haven't been processed yet"""
        return self.db.query(Keyword).filter(
            Keyword.is_processed == False
        ).order_by(Keyword.created_at).limit(limit).all()
    
    def mark_as_processed(self, keyword_id: int):
        """Mark keyword as processed after crawling"""
        keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            keyword.is_processed = True
            keyword.last_crawled_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Marked keyword {keyword_id} as processed")
    
    def get_existing_keywords(self) -> List[Dict]:
        """Get list of already processed keywords (readonly view)"""
        keywords = self.db.query(Keyword).all()
        return [
            {
                "id": k.id,
                "keyword": k.keyword,
                "language": k.language,
                "country": k.country,
                "is_processed": k.is_processed,
                "last_crawled_at": k.last_crawled_at
            }
            for k in keywords
        ]
    
    def get_languages_summary(self) -> Dict[str, int]:
        """Get count of keywords per language"""
        from sqlalchemy import func
        result = self.db.query(
            Keyword.language,
            func.count(Keyword.id)
        ).group_by(Keyword.language).all()
        
        return {lang: count for lang, count in result}
