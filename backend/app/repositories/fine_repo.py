from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.fine import Fine
from app.models.return_record import ReturnRecord
from app.models.loan import Loan


class CRUDFine:
    def get_count(
        self,
        db: Session,
        *,
        reader_id: Optional[int] = None,
        unpaid_only: bool = False,
        fine_type: Optional[str] = None,
    ) -> int:
        stmt = (
            select(func.count(Fine.id))
            .join(ReturnRecord, ReturnRecord.id == Fine.return_record_id)
            .join(Loan, Loan.id == ReturnRecord.loan_id)
        )
        if reader_id is not None:
            stmt = stmt.where(Loan.reader_id == reader_id)
        if unpaid_only:
            stmt = stmt.where(Fine.paid_at.is_(None))
        if fine_type:
            stmt = stmt.where(Fine.fine_type == fine_type)
        return int(db.scalar(stmt) or 0)

    def get(self, db: Session, fine_id: int) -> Optional[Fine]:
        return db.get(Fine, fine_id)

    def get_by_return_record(self, db: Session, return_record_id: int) -> Optional[Fine]:
        stmt = select(Fine).where(Fine.return_record_id == return_record_id)
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        reader_id: Optional[int] = None,
        unpaid_only: bool = False,
        fine_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Fine]:
        stmt = select(Fine).join(ReturnRecord, ReturnRecord.id == Fine.return_record_id).join(Loan, Loan.id == ReturnRecord.loan_id)
        if reader_id:
            stmt = stmt.where(Loan.reader_id == reader_id)
        if unpaid_only:
            stmt = stmt.where(Fine.paid_at.is_(None))
        if fine_type:
            stmt = stmt.where(Fine.fine_type == fine_type)
        stmt = stmt.order_by(Fine.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_unpaid_sum_by_reader(self, db: Session, reader_id: int) -> Decimal:
        """Tổng tiền phạt chưa thanh toán của độc giả (để kiểm tra giới hạn 100.000đ)."""
        stmt = (
            select(func.coalesce(func.sum(Fine.amount), Decimal("0.00")))
            .join(ReturnRecord, ReturnRecord.id == Fine.return_record_id)
            .join(Loan, Loan.id == ReturnRecord.loan_id)
            .where(Loan.reader_id == reader_id, Fine.paid_at.is_(None))
        )
        return Decimal(str(db.scalar(stmt) or 0))


fine_repo = CRUDFine()
