from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.hard_book import HardBook
from app.schemas.hard_book import HardBookCreate, HardBookUpdate
from app.repositories.base import CRUDBase


class CRUDHardBook(CRUDBase[HardBook, HardBookCreate, HardBookUpdate]):
    def get_by_branch_and_status(
        self,
        db: Session,
        *,
        branch_id: Optional[int] = None,
        source_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[HardBook]:
        stmt = select(HardBook)
        if branch_id:
            stmt = stmt.where(HardBook.branch_id == branch_id)
        if source_id:
            stmt = stmt.where(HardBook.source_id == source_id)
        if status:
            stmt = stmt.where(HardBook.status == status)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())


hard_book_repo = CRUDHardBook(HardBook)
