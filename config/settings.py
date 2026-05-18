from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database (MySQL by default, PostgreSQL also supported)
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/contact_miner"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # SERP API (choose one provider)
    SERP_API_PROVIDER: str = "serpapi"  # duckduckgo | serpapi | yandex
    SERPAPI_KEY: str = ""
    YANDEX_SEARCH_API_URL: str = "https://searchapi.api.cloud.yandex.net/v2/web/search"
    YANDEX_SEARCH_TIMEOUT: int = 30
    BRIGHTDATA_API_KEY: str = ""
    SCRAPERAPI_KEY: str = ""
    
    # LLM Configuration
    OPENAI_API_KEY: str = ""
    USE_OPENAI: bool = False
    
    DEEPSEEK_API_KEY: str = ""
    USE_DEEPSEEK: bool = False
    
    YANDEX_IAM_TOKEN: str = ""
    YANDEX_OAUTH_TOKEN: str = ""
    YANDEX_FOLDER_ID: str = ""
    USE_YANDEXGPT: bool = True
    AUTO_REFRESH_YANDEX_IAM_BEFORE_RUN: bool = False
    PERSIST_REFRESHED_YANDEX_IAM_TO_ENV: bool = False
    ENFORCE_LLM_READY: bool = False
    LLM_HEALTHCHECK_BEFORE_RUN: bool = True
    LLM_HEALTHCHECK_TIMEOUT_SECONDS: int = 10
    
    USE_LLM_EXTRACTION: bool = True
    USE_LLM_DOMAIN_CLASSIFICATION: bool = False  # Extra LLM call per domain for tags only
    SAVE_EMPTY_DOMAIN_CONTACTS: bool = False  # Skip DB row when no contacts found

    # SERP filtering (provider-agnostic; works with duckduckgo, serpapi, etc.)
    SERP_BLOCKED_HOST_SUFFIXES: List[str] = [
        "wikipedia.org", "reddit.com", "youtube.com", "facebook.com", "instagram.com",
        "twitter.com", "x.com", "linkedin.com", "google.com", "chatgpt.com",
        "gemini.google.com", "grokipedia.com", "quora.com",
        "investopedia.com", "britannica.com", "medium.com", "forbes.com",
        "crunchbase.com", "bloomberg.com", "techcrunch.com",
        "netguru.com", "munich-startup.de", "blockchain.com",
        "learn.bybit.com",
    ]
    SERP_SNIPPET_SKIP_CRAWL: bool = True  # Skip Playwright when snippet has email/Telegram
    SERP_DENYLIST_LOOKBACK_DAYS: int = 7
    SERP_DENYLIST_MIN_ZERO_CRAWLS: int = 3

    # HTTP-first crawl (before Playwright)
    HTTP_FETCH_ENABLED: bool = True
    HTTP_FETCH_VERIFY_SSL: bool = True  # Set false only for sites with broken TLS certs
    HTTP_FETCH_TIMEOUT: float = 8.0
    HTTP_FETCH_MIN_TEXT_CHARS: int = 200

    # Crawler Settings
    MAX_PAGES_PER_DOMAIN: int = 3  # Reduced for speed
    PRIMARY_CONTACT_PATHS: List[str] = [
        "/contact", "/contacts", "/contact-us", "/impressum", "/kontakt",
    ]
    CRAWL_WAIT_UNTIL: str = "domcontentloaded"  # Faster than networkidle
    REQUEST_TIMEOUT: int = 12  # Per navigation (ms for Playwright)
    REQUEST_TIMEOUT_FALLBACK: int = 18  # load-state fallback if primary fails
    CRAWL_PAYLOAD_MAX_PAGES: int = 3
    CRAWL_PAYLOAD_MAX_TEXT_CHARS: int = 15000
    CRAWL_PAYLOAD_MAX_HTML_CHARS: int = 50000
    DOMAIN_CRAWL_TIMEOUT: int = 50  # Wall-clock cap for whole-domain crawl (see crawler wait_for)
    CONCURRENT_BROWSERS: int = 3  # Reduced from 5
    HEADLESS_BROWSER: bool = True
    BLOCK_HEAVY_RESOURCES: bool = True
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
    MAX_CONCURRENT_DOMAINS: int = 12  # Lower than 20 — less Playwright contention on VPS
    BATCH_SIZE: int = 50
    
    # Pipeline Settings
    SEARCH_RESULTS_PER_KEYWORD: int = 5  # Filtered by SERP_BLOCKED_HOST_SUFFIXES before crawl
    MAX_KEYWORDS_PER_RUN: int = 50  # Максимальное количество ключевых слов за один запуск
    
    # Task Queue Retry Settings
    SEARCH_MAX_RETRIES: int = 3      # SERP API может fail
    CRAWL_MAX_RETRIES: int = 2       # Сайт может быть down
    EXTRACT_MAX_RETRIES: int = 1     # LLM может timeout
    SAVE_MAX_RETRIES: int = 3        # DB lock issues
    TASK_LOCK_TIMEOUT: int = 300     # seconds before lock expires (5 minutes)
    ZERO_PAGE_CRAWLS_ALERT_THRESHOLD: int = 5
    TIMEOUT_RATE_ALERT_THRESHOLD_PCT: float = 35.0
    CONTACTS_RATE_ALERT_THRESHOLD_PCT: float = 20.0
    AVG_CONTACTS_PER_DOMAIN_ALERT_THRESHOLD: float = 0.5
    NIGHTLY_FAIL_ON_QUALITY_GATE: bool = False
    
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
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
