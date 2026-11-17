from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.hard_book import HardBook
from app.schemas.hard_book import HardBookCreate, HardBookUpdate
from app.repositories.base import CRUDBase


class CRUDHardBook(CRUDBase[HardBook, HardBookCreate, HardBookUpdate]):
    def get_detail(self, db: Session, id: int) -> Optional[HardBook]:
        stmt = (
            select(HardBook)
            .options(
                selectinload(HardBook.source),
                selectinload(HardBook.branch),
            )
            .where(HardBook.id == id)
        )
        return db.scalars(stmt).first()

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
        stmt = select(HardBook).options(
            selectinload(HardBook.source),
            selectinload(HardBook.branch),
        )
        if branch_id is not None:
            stmt = stmt.where(HardBook.branch_id == branch_id)
        if source_id is not None:
            stmt = stmt.where(HardBook.source_id == source_id)
        if status:
            stmt = stmt.where(HardBook.status == status)
        stmt = stmt.order_by(HardBook.id).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def count_by_branch_and_status(
        self,
        db: Session,
        *,
        branch_id: Optional[int] = None,
        source_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> int:
        stmt = select(func.count()).select_from(HardBook)
        if branch_id is not None:
            stmt = stmt.where(HardBook.branch_id == branch_id)
        if source_id is not None:
            stmt = stmt.where(HardBook.source_id == source_id)
        if status:
            stmt = stmt.where(HardBook.status == status)
        return db.scalar(stmt) or 0


hard_book_repo = CRUDHardBook(HardBook)
