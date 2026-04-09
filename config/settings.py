from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/contact_miner"
    
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
    
    GIGACHAT_CLIENT_ID: str = ""
    GIGACHAT_CLIENT_SECRET: str = ""
    USE_GIGACHAT: bool = False
    
    YANDEX_IAM_TOKEN: str = ""
    YANDEX_FOLDER_ID: str = ""
    USE_YANDEXGPT: bool = True
    
    USE_LLM_EXTRACTION: bool = True
    
    # Crawler Settings
    MAX_PAGES_PER_DOMAIN: int = 10
    REQUEST_TIMEOUT: int = 30
    CONCURRENT_BROWSERS: int = 5
    HEADLESS_BROWSER: bool = True
    MAX_CONCURRENT_DOMAINS_PER_SITE: int = 5
    
    # Rate Limiting
    DELAY_BETWEEN_REQUESTS: float = 1.0
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
    
    # Logging
    LOG_FORMAT: str = "text"  # "text" or "json"
    
    class Config:
        env_file = ".env"


settings = Settings()
