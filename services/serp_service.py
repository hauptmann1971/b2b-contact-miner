import requests
from typing import List, Dict, Optional, Tuple
from config.settings import settings
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from models.database import SearchResult
from sqlalchemy.orm import Session
from utils.yandex_search_mapping import yandex_l10n, yandex_search_type
from utils.yandex_search_xml import parse_api_response_body


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
            "duckduckgo": "",
            "yandex": settings.YANDEX_IAM_TOKEN,
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
        elif self.provider == "yandex":
            return self._yandex_search(query, country, language, num_results)
        elif self.provider == "brightdata":
            return self._brightdata_search(query, country, language, num_results)
        else:
            raise ValueError(f"Unsupported SERP provider: {self.provider}")

    def _yandex_search(
        self, query: str, country: str, language: str, num_results: int
    ) -> Tuple[List[Dict], dict]:
        """Yandex Cloud Search API v2 (CIS-friendly web search)."""
        if not settings.YANDEX_IAM_TOKEN or not settings.YANDEX_FOLDER_ID:
            raise ValueError("YANDEX_IAM_TOKEN and YANDEX_FOLDER_ID required for SERP provider yandex")

        url = settings.YANDEX_SEARCH_API_URL
        headers = {
            "Authorization": f"Bearer {settings.YANDEX_IAM_TOKEN}",
            "Content-Type": "application/json",
        }
        n = max(1, min(int(num_results), 20))
        payload = {
            "query": {
                "searchType": yandex_search_type(country),
                "queryText": query[:400],
                "familyMode": "FAMILY_MODE_MODERATE",
                "page": 0,
                "fixTypoMode": "FIX_TYPO_MODE_ON",
            },
            "folderId": settings.YANDEX_FOLDER_ID,
            "maxPassages": min(3, n),
            "l10n": yandex_l10n(language),
            "responseFormat": "FORMAT_XML",
            "groupSpec": {
                "groupMode": "GROUP_MODE_FLAT",
                "groupsOnPage": n,
                "docsInGroup": 1,
            },
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=settings.YANDEX_SEARCH_TIMEOUT,
        )
        if response.status_code == 403:
            raise PermissionError(
                "Yandex Search API 403: assign role search-api.webSearch.user on folder "
                f"{settings.YANDEX_FOLDER_ID} for your OAuth user. See doc/YANDEX_SEARCH_SETUP.md"
            )
        response.raise_for_status()
        data = response.json()
        results = parse_api_response_body(data, max_results=n)
        raw_response = {
            "provider": "yandex",
            "query": query,
            "country": country,
            "language": language,
            "search_type": payload["query"]["searchType"],
            "max_results": n,
            "results_count": len(results),
            "raw_data": data,
        }
        logger.info(f"Yandex Search returned {len(results)} results for '{query}' ({country})")
        return results, raw_response
    
    def _serpapi_search(self, query: str, country: str, language: str, num_results: int) -> tuple:
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
        
        raw_response = {
            "provider": self.provider,
            "query": query,
            "country": country,
            "language": language,
            "max_results": num_results,
            "results_count": len(results),
            "raw_data": data
        }
        logger.info(f"SerpAPI search returned {len(results)} results for '{query}'")
        return results, raw_response
    
    def _duckduckgo_search(self, query: str, country: str, language: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (free, no API key required)"""
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
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
