from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class KeywordInput(BaseModel):
    keyword: str = Field(..., min_length=2, max_length=500)
    language: str = Field(default="ru", max_length=10)
    country: str = Field(default="RU", max_length=5)


class KeywordResponse(BaseModel):
    id: int
    keyword: str
    language: str
    country: str
    is_processed: bool
    last_crawled_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContactInfo(BaseModel):
    emails: List[str] = Field(default_factory=list)
    telegram_links: List[str] = Field(default_factory=list)
    linkedin_links: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    social_links: Dict[str, List[str]] = Field(default_factory=dict)


class DomainContactResponse(BaseModel):
    id: int
    domain: str
    emails: List[str]
    telegram_links: List[str]
    linkedin_links: List[str]
    tags: List[str]
    confidence_score: int
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class CrawlStats(BaseModel):
    total_keywords: int
    processed_keywords: int
    total_domains: int
    contacts_found: int
    last_run: Optional[datetime]
