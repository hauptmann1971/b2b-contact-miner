from models.database import PipelineState, SessionLocal
from loguru import logger
from datetime import datetime, timezone
import uuid


class StateManager:
    def __init__(self):
        self.run_id = str(uuid.uuid4())[:8]
    
    def create_run(self) -> str:
        """Create new pipeline run"""
        db = SessionLocal()
        try:
            state = PipelineState(
                run_id=self.run_id,
                status="started",
                started_at=datetime.now(timezone.utc)
            )
            db.add(state)
            db.commit()
            logger.info(f"Created new pipeline run: {self.run_id}")
            return self.run_id
        finally:
            db.close()
    
    def update_progress(self, keyword_id: int, websites_processed: int, 
                       contacts_found: int, total_websites: int):
        """Update pipeline progress checkpoint"""
        db = SessionLocal()
        try:
            progress = int((websites_processed / total_websites) * 100) if total_websites > 0 else 0
            
            state = db.query(PipelineState).filter(
                PipelineState.run_id == self.run_id,
                PipelineState.keyword_id == keyword_id
            ).first()
            
            if not state:
                state = PipelineState(
                    run_id=self.run_id,
                    keyword_id=keyword_id,
                    status="processing",
                    websites_processed=websites_processed,
                    contacts_found=contacts_found,
                    progress_percent=progress
                )
                db.add(state)
            else:
                state.websites_processed = websites_processed
                state.contacts_found = contacts_found
                state.progress_percent = progress
                state.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            logger.info(f"Progress: {progress}% | Websites: {websites_processed} | Contacts: {contacts_found}")
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
        finally:
            db.close()
    
    def mark_keyword_completed(self, keyword_id: int, contacts_found: int):
        """Mark keyword as completed"""
        db = SessionLocal()
        try:
            state = db.query(PipelineState).filter(
                PipelineState.run_id == self.run_id,
                PipelineState.keyword_id == keyword_id
            ).first()
            
            if state:
                state.status = "completed"
                state.contacts_found = contacts_found
                state.progress_percent = 100
                state.updated_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()
    
    def mark_failed(self, keyword_id: int, error: str):
        """Mark keyword as failed"""
        db = SessionLocal()
        try:
            state = db.query(PipelineState).filter(
                PipelineState.run_id == self.run_id,
                PipelineState.keyword_id == keyword_id
            ).first()
            
            if state:
                state.status = "failed"
                state.error_message = error
                state.updated_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()
    
    def get_last_run_status(self) -> dict:
        """Get status of last pipeline run"""
        db = SessionLocal()
        try:
            states = db.query(PipelineState).filter(
                PipelineState.run_id == self.run_id
            ).all()
            
            if not states:
                return {"status": "no_runs"}
            
            total = len(states)
            completed = sum(1 for s in states if s.status == "completed")
            failed = sum(1 for s in states if s.status == "failed")
            processing = sum(1 for s in states if s.status == "processing")
            
            total_contacts = sum(s.contacts_found for s in states)
            total_websites = sum(s.websites_processed for s in states)
            
            return {
                "run_id": self.run_id,
                "total_keywords": total,
                "completed": completed,
                "failed": failed,
                "processing": processing,
                "total_contacts": total_contacts,
                "total_websites": total_websites,
                "overall_progress": int((completed / total) * 100) if total > 0 else 0
            }
        finally:
            db.close()
