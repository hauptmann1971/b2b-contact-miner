import os
import enum
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from config.settings import settings

Base = declarative_base()


def _database_url() -> str:
    """Prefer live env (CI) over cached settings; avoid pymysql localhost socket."""
    url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    return url.replace("@localhost:", "@127.0.0.1:")

_COMMENT_ID = "Unique identifier"
_COMMENT_CREATED_AT = "Record creation timestamp"
_COMMENT_UPDATED_AT = "Last update timestamp"

# MySQL connection with pool settings
engine = create_engine(
    _database_url(),
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,  # MySQL closes idle connections after 8 hours
    pool_pre_ping=True,  # Verify connections before using them
    connect_args={
        "connect_timeout": 60,  # Connection timeout in seconds
        "read_timeout": 120,    # Read timeout in seconds
        "write_timeout": 120    # Write timeout in seconds
    },
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ContactType(enum.Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    LINKEDIN = "linkedin"
    PHONE = "phone"
    X = "x"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"


class Keyword(Base):
    """Search keywords to process (e.g., 'IT companies Moscow')"""
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True, comment="Owning tenant")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="User who added keyword")
    keyword = Column(String(500), nullable=False, comment="Search query text")
    language = Column(String(10), nullable=False, default="ru", comment="Language code (ru, en, etc.)")
    country = Column(String(5), nullable=False, default="RU", comment="Country code (RU, US, etc.)")
    is_processed = Column(Boolean, default=False, comment="True if keyword has been fully processed")
    last_crawled_at = Column(DateTime, nullable=True, comment="Timestamp of last crawl operation")
    created_at = Column(DateTime, default=datetime.utcnow, comment=_COMMENT_CREATED_AT)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment=_COMMENT_UPDATED_AT)
    
    searches = relationship("SearchResult", back_populates="keyword")

    __table_args__ = (
        Index("idx_keywords_tenant_keyword", "tenant_id", "keyword", "language", "country", unique=True),
    )


class SearchResult(Base):
    """SERP search results for a keyword"""
    __tablename__ = "search_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True, comment="Owning tenant")
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, comment="Foreign key to keywords table")
    url = Column(String(768), nullable=False, index=True, comment="Website URL from search results")  # Reduced for MySQL index limit (768 * 4 bytes = 3072)
    title = Column(String(1000), comment="Page title from SERP")
    snippet = Column(Text, comment="Text snippet/description from SERP")
    position = Column(Integer, comment="Position in search results (1, 2, 3, ...)")
    is_processed = Column(Boolean, default=False, comment="True if URL has been crawled")
    raw_search_query = Column(Text, comment="Raw query sent to SERP provider")
    raw_search_response = Column(JSON, comment="Raw JSON response from SERP provider")
    created_at = Column(DateTime, default=datetime.utcnow, comment=_COMMENT_CREATED_AT)
    
    keyword = relationship("Keyword", back_populates="searches")
    domain_contacts = relationship("DomainContact", back_populates="search_result")
    
    __table_args__ = (
        # mysql_length prefixes url for InnoDB index byte limit (utf8mb4).
        # Do not use text('url(255)') — MySQL DDL compiler requires Column.name.
        Index('idx_keyword_url', 'keyword_id', 'url', unique=True, mysql_length={'url': 255}),
    )


class DomainContact(Base):
    """Aggregated contact information for a domain"""
    __tablename__ = "domain_contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True, comment="Owning tenant")
    search_result_id = Column(Integer, ForeignKey("search_results.id"), nullable=False, comment="Foreign key to search_results table")
    domain = Column(String(500), nullable=False, index=True, comment="Domain name (e.g., example.com)")
    tags = Column(JSON, default=list, comment="Tags/categories extracted from website")
    site_metadata = Column("metadata", JSON, default=dict, comment="Website metadata (title, description, etc.)")  # Rename to avoid SQLAlchemy reserved word
    contacts_json = Column(JSON, default=dict, comment="Hybrid: JSON for fast read {emails, telegram, linkedin, phones}")
    extraction_method = Column(String(50), comment="Method used: llm, regex, html_parse")
    confidence_score = Column(Integer, default=0, comment="Confidence score 0-100")
    is_verified = Column(Boolean, default=False, comment="True if contacts have been verified")
    created_at = Column(DateTime, default=datetime.utcnow, comment=_COMMENT_CREATED_AT)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment=_COMMENT_UPDATED_AT)
    
    search_result = relationship("SearchResult", back_populates="domain_contacts")
    contacts = relationship("Contact", back_populates="domain_contact", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_domain', 'domain'),
    )


class Contact(Base):
    """Normalized individual contact records for efficient search"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True, comment="Owning tenant")
    domain_contact_id = Column(Integer, ForeignKey("domain_contacts.id"), nullable=False, comment="Foreign key to domain_contacts table")
    contact_type = Column(Enum(ContactType), nullable=False, comment="Type: email, telegram, linkedin, phone, x, facebook, instagram, youtube")
    value = Column(String(500), nullable=False, index=True, comment="Contact value (email address, phone number, etc.)")
    is_verified = Column(Boolean, default=False, comment="True if contact has been verified")
    verification_date = Column(DateTime, nullable=True, comment="Date of last verification")
    created_at = Column(DateTime, default=datetime.utcnow, comment=_COMMENT_CREATED_AT)
    
    domain_contact = relationship("DomainContact", back_populates="contacts")
    
    __table_args__ = (
        Index('idx_contact_value', 'value'),
        Index('idx_contact_type_value', 'contact_type', 'value'),
        Index('idx_domain_contact_type', 'domain_contact_id', 'contact_type'),
    )


class CrawlLog(Base):
    """Logs of website crawling operations"""
    __tablename__ = "crawl_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True, comment="Owning tenant")
    domain = Column(String(500), nullable=False, index=True, comment="Domain that was crawled")
    url = Column(String(2000), comment="Specific URL crawled")
    status_code = Column(Integer, comment="HTTP status code (200, 404, 500, etc.)")
    error_message = Column(Text, comment="Error message if crawl failed")
    pages_crawled = Column(Integer, default=0, comment="Number of pages crawled on this domain")
    duration_seconds = Column(Integer, comment="Crawl duration in seconds")
    llm_request = Column(Text, comment="Raw request sent to LLM")
    llm_response = Column(Text, comment="Raw response from LLM")
    llm_model = Column(String(100), comment="LLM model used (e.g., yandexgpt, deepseek, openai)")
    crawled_at = Column(DateTime, default=datetime.utcnow, comment="Crawl timestamp")


class PipelineState(Base):
    """Checkpoint for monitoring pipeline progress"""
    __tablename__ = "pipeline_state"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True, comment="Owning tenant")
    # Same run_id is shared across multiple rows (run header + per-keyword checkpoints); must not be UNIQUE.
    run_id = Column(String(100), nullable=False, index=True, comment="Pipeline run identifier (shared across checkpoints)")
    keyword_id = Column(Integer, ForeignKey("keywords.id"), comment="Current keyword being processed")
    status = Column(String(50), default="pending", comment="Status: pending, running, completed, failed")
    progress_percent = Column(Integer, default=0, comment="Progress percentage 0-100")
    websites_processed = Column(Integer, default=0, comment="Number of websites processed")
    contacts_found = Column(Integer, default=0, comment="Total contacts found in this run")
    started_at = Column(DateTime, default=datetime.utcnow, comment="Pipeline start timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment=_COMMENT_UPDATED_AT)
    error_message = Column(Text, comment="Error message if pipeline failed")
    
    keyword = relationship("Keyword")


def init_db():
    import models.tenant  # noqa: F401
    from services.tenant_bootstrap import bootstrap_default_tenant, ensure_multitenant_schema

    ensure_multitenant_schema()
    bootstrap_default_tenant()
