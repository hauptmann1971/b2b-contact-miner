from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database (MySQL by default, PostgreSQL also supported)
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/contact_miner"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # SERP API (choose one provider)
    SERP_API_PROVIDER: str = "serpapi"
    SERPAPI_KEY: str = ""
    BRIGHTDATA_API_KEY: str = ""
    SCRAPERAPI_KEY: str = ""
    
    # LLM Configuration
    OPENAI_API_KEY: str = ""
    USE_OPENAI: bool = False
    
    DEEPSEEK_API_KEY: str = ""
    USE_DEEPSEEK: bool = False
    
    YANDEX_IAM_TOKEN: str = ""
    YANDEX_FOLDER_ID: str = ""
    USE_YANDEXGPT: bool = True
    
    USE_LLM_EXTRACTION: bool = True
    
    # Crawler Settings
    MAX_PAGES_PER_DOMAIN: int = 3  # Reduced for speed
    REQUEST_TIMEOUT: int = 15  # Reduced from 30s for faster crawling
    DOMAIN_CRAWL_TIMEOUT: int = 45  # Max seconds to crawl entire domain (prevents hanging)
    CONCURRENT_BROWSERS: int = 3  # Reduced from 5
    HEADLESS_BROWSER: bool = True
    MAX_CONCURRENT_DOMAINS_PER_SITE: int = 3  # Reduced from 5
    
    # Rate Limiting
    DELAY_BETWEEN_REQUESTS: float = 0.5  # Reduced for speed
    MAX_RETRIES: int = 3
    
    # Target Countries & Languages
    TARGET_COUNTRIES: List[str] = [
        "RU", "KZ", "UZ", "KG", "TJ", "TM",
        "AZ", "AM", "GE", "BY", "MD", "UA",
        "MN", "AF", "PK"
    ]
    
    LANGUAGES: List[str] = ["ru", "en", "kk", "uz", "ky", "tg", "az", "hy", "ka", "be", "ro"]
    
    # Email Filtering
    BLOCKED_EMAIL_PATTERNS: List[str] = [
        r"^noreply@",
        r"^no-reply@",
        r"^donotreply@",
        r"^support@",
        # r"^info@",  # info@ is often a valid business contact
        r"^admin@",
        r"^webmaster@",
        r"^postmaster@",
    ]
    
    # Contact Pages to Check
    CONTACT_PATHS: List[str] = [
        "/contact",
        "/contacts",
        "/about",
        "/about-us",
        "/team",
        "/our-team",
        "/leadership",
        "/contact-us",
        "/impressum",
        "/legal",
    ]
    
    # Parallel Processing
    MAX_CONCURRENT_DOMAINS: int = 20
    BATCH_SIZE: int = 50
    
    # Pipeline Settings
    SEARCH_RESULTS_PER_KEYWORD: int = 2  # Reduced for speed (was 5)
    MAX_KEYWORDS_PER_RUN: int = 50  # Максимальное количество ключевых слов за один запуск
    
    # Task Queue Retry Settings
    SEARCH_MAX_RETRIES: int = 3      # SERP API может fail
    CRAWL_MAX_RETRIES: int = 2       # Сайт может быть down
    EXTRACT_MAX_RETRIES: int = 1     # LLM может timeout
    SAVE_MAX_RETRIES: int = 3        # DB lock issues
    TASK_LOCK_TIMEOUT: int = 300     # seconds before lock expires (5 minutes)
    ZERO_PAGE_CRAWLS_ALERT_THRESHOLD: int = 5
    
    # Logging
    LOG_FORMAT: str = "text"  # "text" or "json"
    LOG_LEVEL: str = "INFO"  # "DEBUG", "INFO", "WARNING", "ERROR"
    
    # SonarCloud
    SONAR_TOKEN: Optional[str] = None  # For API access to SonarCloud reports
    LLM_DATA_API_TOKEN: str = ""
    API_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
