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
            "duckduckgo": "",  # No API key needed
        }
        return keys.get(self.provider, "")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search(self, query: str, country: str = "RU", language: str = "ru", num_results: int = 10) -> tuple:
        """Perform search using configured SERP API
        Returns: (results_list, raw_response_dict)
        """
        if self.provider == "duckduckgo":
            return self._duckduckgo_search(query, country, language, num_results)
        elif self.provider == "serpapi":
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
    
    def _duckduckgo_search(self, query: str, country: str, language: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (free, no API key required)"""
        try:
            from ddgs import DDGS
            
            # Map country codes to DuckDuckGo regions
            region_map = {
                "RU": "ru-ru", "KZ": "kz-en", "UZ": "uz-en", "KG": "kg-en",
                "AZ": "az-en", "BY": "by-en", "UA": "ua-uk", "GE": "ge-en",
                "US": "us-en", "GB": "uk-en", "DE": "de-de", "FR": "fr-fr",
            }
            region = region_map.get(country, "ru-ru")
            
            results = []
            raw_response = None
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, region=region, max_results=num_results))
                
                # Store raw response
                raw_response = {
                    "provider": self.provider,
                    "query": query,
                    "region": region,
                    "max_results": num_results,
                    "results_count": len(ddg_results),
                    "raw_data": ddg_results  # Full raw data from DDGS
                }
                
                for idx, result in enumerate(ddg_results):
                    results.append({
                        "url": result.get("href", ""),
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "position": idx + 1
                    })
            
            logger.info(f"DuckDuckGo search returned {len(results)} results for '{query}'")
            return results, raw_response
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise
    
    def _brightdata_search(self, query: str, country: str, language: str, num_results: int) -> List[Dict]:
        """Search using BrightData SERP API"""
        raise NotImplementedError("BrightData integration pending")
    
    def save_results(self, db: Session, keyword_id: int, results: List[Dict], raw_query: str = None, raw_response: dict = None):
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
                    position=result.get("position"),
                    raw_search_query=raw_query,  # Save raw query sent to SERP provider
                    raw_search_response=raw_response  # Save raw response from SERP provider
                )
                db.add(search_result)
        
        db.commit()
        logger.info(f"Saved {len(results)} search results for keyword {keyword_id}")
