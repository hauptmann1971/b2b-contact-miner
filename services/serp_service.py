import requests
from typing import List, Dict, Optional
from config.settings import settings
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from models.database import SearchResult
from sqlalchemy.orm import Session


class SerpService:
    def __init__(self):
        self.provider = settings.SERP_API_PROVIDER
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> str:
        """Get API key based on provider"""
        keys = {
            "serpapi": settings.SERPAPI_KEY,
            "brightdata": settings.BRIGHTDATA_API_KEY,
            "scraperapi": settings.SCRAPERAPI_KEY,
        }
        return keys.get(self.provider, "")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search(self, query: str, country: str = "RU", language: str = "ru", num_results: int = 10) -> List[Dict]:
        """Perform search using configured SERP API"""
        if self.provider == "serpapi":
            return self._serpapi_search(query, country, language, num_results)
        elif self.provider == "brightdata":
            return self._brightdata_search(query, country, language, num_results)
        else:
            raise ValueError(f"Unsupported SERP provider: {self.provider}")
    
    def _serpapi_search(self, query: str, country: str, language: str, num_results: int) -> List[Dict]:
        """Search using SerpAPI"""
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "countryCode": country,
            "hl": language,
            "num": num_results,
            "api_key": self.api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        if "organic_results" in data:
            for idx, result in enumerate(data["organic_results"][:num_results]):
                results.append({
                    "url": result.get("link", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "position": idx + 1
                })
        
        logger.info(f"SerpAPI search returned {len(results)} results for '{query}'")
        return results
    
    def _brightdata_search(self, query: str, country: str, language: str, num_results: int) -> List[Dict]:
        """Search using BrightData SERP API"""
        raise NotImplementedError("BrightData integration pending")
    
    def save_results(self, db: Session, keyword_id: int, results: List[Dict]):
        """Save search results to database"""
        for result in results:
            existing = db.query(SearchResult).filter(
                SearchResult.keyword_id == keyword_id,
                SearchResult.url == result["url"]
            ).first()
            
            if not existing:
                search_result = SearchResult(
                    keyword_id=keyword_id,
                    url=result["url"],
                    title=result.get("title"),
                    snippet=result.get("snippet"),
                    position=result.get("position")
                )
                db.add(search_result)
        
        db.commit()
        logger.info(f"Saved {len(results)} search results for keyword {keyword_id}")
