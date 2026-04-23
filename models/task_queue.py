"""Task queue model for persistent task storage in database"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class TaskQueue(Base):
    """Persistent task queue stored in MySQL database for reliable async processing"""
    __tablename__ = "task_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Unique task identifier")
    task_name = Column(String(255), nullable=False, index=True, comment="Human-readable task name")
    task_type = Column(String(100), nullable=False, index=True, comment="Task type: search_keyword, crawl_domain, extract_contacts, save_results")  # 'search_keyword', 'crawl_domain', 'extract_contacts', 'save_results'
    payload = Column(Text, nullable=False, comment="JSON serialized task data/parameters")  # JSON serialized task data
    status = Column(String(50), default='pending', index=True, comment="Status: pending, running, completed, failed, retrying")  # pending, running, completed, failed, retrying
    priority = Column(Integer, default=0, index=True, comment="Priority level (higher number = higher priority)")  # Higher number = higher priority
    retry_count = Column(Integer, default=0, comment="Current retry attempt count")
    max_retries = Column(Integer, default=3, comment="Maximum retry attempts allowed")
    error_message = Column(Text, nullable=True, comment="Error message if task failed")
    result = Column(Text, nullable=True, comment="JSON serialized task result/output")  # JSON serialized result
    keyword_id = Column(Integer, nullable=True, index=True, comment="Associated keyword ID for tracking")  # Link to keyword for tracking
    depends_on_task_id = Column(Integer, ForeignKey('task_queue.id'), nullable=True, index=True, comment="Parent task ID - this task waits for parent completion")  # Parent task dependency
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, comment="Task creation timestamp")
    started_at = Column(DateTime, nullable=True, comment="Task execution start timestamp")
    completed_at = Column(DateTime, nullable=True, comment="Task completion timestamp")
    scheduled_for = Column(DateTime, nullable=True, index=True, comment="Scheduled execution time for delayed tasks")  # For delayed tasks
    locked_by = Column(String(100), nullable=True, comment="Worker ID that locked this task for execution")  # Worker ID that locked this task
    locked_at = Column(DateTime, nullable=True, comment="Task lock timestamp")
    
    def __repr__(self):
        return f"<TaskQueue(id={self.id}, type={self.task_type}, status={self.status})>"
