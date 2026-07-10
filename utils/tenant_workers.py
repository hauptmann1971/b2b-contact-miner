"""Worker helpers for tenant propagation."""
from __future__ import annotations

from sqlalchemy.orm import Session

from models.database import Keyword


def tenant_id_for_keyword(db: Session, keyword_id: int | None) -> int | None:
    if not keyword_id:
        return None
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    return keyword.tenant_id if keyword else None
