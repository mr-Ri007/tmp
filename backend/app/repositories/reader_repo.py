from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.reader import Reader
from app.models.loan import Loan
from app.models.return_record import ReturnRecord
from app.schemas.reader import ReaderCreate, ReaderUpdate
from app.repositories.base import CRUDBase


class CRUDReader(CRUDBase[Reader, ReaderCreate, ReaderUpdate]):
    def get_by_email(self, db: Session, email: str) -> Optional[Reader]:
        stmt = select(Reader).where(Reader.email == email)
        return db.scalar(stmt)

    def get_by_national_id(self, db: Session, national_id: str) -> Optional[Reader]:
        stmt = select(Reader).where(Reader.national_id == national_id)
        return db.scalar(stmt)

    def count_active_loans(self, db: Session, reader_id: int) -> int:
        """Đếm số sách đang mượn (chưa có phiếu trả trong Return_records)."""
        stmt = (
            select(func.count(Loan.id))
            .outerjoin(ReturnRecord, ReturnRecord.loan_id == Loan.id)
            .where(Loan.reader_id == reader_id, ReturnRecord.id.is_(None))
        )
        return db.scalar(stmt) or 0


reader_repo = CRUDReader(Reader)
