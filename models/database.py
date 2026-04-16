from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index, Enum, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import settings
import enum

Base = declarative_base()

# MySQL connection with pool settings
engine = create_engine(
    settings.DATABASE_URL,
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


class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(500), unique=True, nullable=False, index=True)
    language = Column(String(10), nullable=False, default="ru")
    country = Column(String(5), nullable=False, default="RU")
    is_processed = Column(Boolean, default=False)
    last_crawled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    searches = relationship("SearchResult", back_populates="keyword")


class SearchResult(Base):
    __tablename__ = "search_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    url = Column(String(768), nullable=False, index=True)  # Reduced for MySQL index limit (768 * 4 bytes = 3072)
    title = Column(String(1000))
    snippet = Column(Text)
    position = Column(Integer)
    is_processed = Column(Boolean, default=False)
    raw_search_query = Column(Text)  # Raw query sent to SERP provider
    created_at = Column(DateTime, default=datetime.utcnow)
    
    keyword = relationship("Keyword", back_populates="searches")
    domain_contacts = relationship("DomainContact", back_populates="search_result")
    
    __table_args__ = (
        Index('idx_keyword_url', 'keyword_id', text('url(255)'), unique=True, mysql_length={'url': 255}),
    )


class DomainContact(Base):
    __tablename__ = "domain_contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    search_result_id = Column(Integer, ForeignKey("search_results.id"), nullable=False)
    domain = Column(String(500), nullable=False, index=True)
    tags = Column(JSON, default=list)
    site_metadata = Column("metadata", JSON, default=dict)  # Rename to avoid SQLAlchemy reserved word
    contacts_json = Column(JSON, default=dict)  # Hybrid: JSON for fast read {emails, telegram, linkedin, phones}
    extraction_method = Column(String(50))
    confidence_score = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    search_result = relationship("SearchResult", back_populates="domain_contacts")
    contacts = relationship("Contact", back_populates="domain_contact", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_domain', 'domain'),
    )


class Contact(Base):
    """Normalized contact table for efficient search"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_contact_id = Column(Integer, ForeignKey("domain_contacts.id"), nullable=False)
    contact_type = Column(Enum(ContactType), nullable=False)
    value = Column(String(500), nullable=False, index=True)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    domain_contact = relationship("DomainContact", back_populates="contacts")
    
    __table_args__ = (
        Index('idx_contact_value', 'value'),
        Index('idx_contact_type_value', 'contact_type', 'value'),
        Index('idx_domain_contact_type', 'domain_contact_id', 'contact_type'),
    )


class CrawlLog(Base):
    __tablename__ = "crawl_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(500), nullable=False, index=True)
    url = Column(String(2000))
    status_code = Column(Integer)
    error_message = Column(Text)
    pages_crawled = Column(Integer, default=0)
    duration_seconds = Column(Integer)
    llm_request = Column(Text)  # Raw request sent to LLM
    llm_response = Column(Text)  # Raw response from LLM
    llm_model = Column(String(100))  # LLM model used (e.g., "yandexgpt", "gigachat")
    crawled_at = Column(DateTime, default=datetime.utcnow)


class PipelineState(Base):
    """Checkpoint for monitoring progress"""
    __tablename__ = "pipeline_state"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=False, index=True, unique=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    status = Column(String(50), default="pending")
    progress_percent = Column(Integer, default=0)
    websites_processed = Column(Integer, default=0)
    contacts_found = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text)
    
    keyword = relationship("Keyword")


def init_db():
    Base.metadata.create_all(bind=engine)
