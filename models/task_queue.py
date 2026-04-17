"""Task queue model for persistent task storage in database"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class TaskQueue(Base):
    """Persistent task queue stored in MySQL database"""
    __tablename__ = "task_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False, index=True)
    task_type = Column(String(100), nullable=False, index=True)  # 'search_keyword', 'crawl_domain', 'extract_contacts', 'save_results'
    payload = Column(Text, nullable=False)  # JSON serialized task data
    status = Column(String(50), default='pending', index=True)  # pending, running, completed, failed, retrying
    priority = Column(Integer, default=0, index=True)  # Higher number = higher priority
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)  # JSON serialized result
    keyword_id = Column(Integer, nullable=True, index=True)  # Link to keyword for tracking
    depends_on_task_id = Column(Integer, ForeignKey('task_queue.id'), nullable=True, index=True)  # Parent task dependency
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    scheduled_for = Column(DateTime, nullable=True, index=True)  # For delayed tasks
    locked_by = Column(String(100), nullable=True)  # Worker ID that locked this task
    locked_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<TaskQueue(id={self.id}, type={self.task_type}, status={self.status})>"
