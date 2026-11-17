import datetime as dt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.renewal import Renewal
from app.models.return_record import ReturnRecord


class RenewalService:
    @staticmethod
    def renew_book(
        db: Session,
        *,
        loan_id: int,
        extension_days: int = 7
    ) -> Renewal:
        """Thực hiện nghiệp vụ gia hạn sách.
        
        Quy tắc nghiệp vụ:
          1. Lượt mượn phải tồn tại và chưa có phiếu trả.
          2. old_due_at phải khớp với hạn trả hiện tại của lượt mượn.
          3. new_due_at > old_due_at.
          4. Cập nhật hạn trả mới vào bảng Loans.
        """
        # Khóa lượt mượn
        loan = db.scalar(select(Loan).where(Loan.id == loan_id).with_for_update())
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lượt mượn có ID = {loan_id}"
            )

        # Kiểm tra đã trả chưa
        if db.scalar(select(ReturnRecord).where(ReturnRecord.loan_id == loan_id)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lượt mượn này đã được trả sách, không thể gia hạn."
            )

        old_due = loan.due_at
        new_due = old_due + dt.timedelta(days=extension_days)

        renewal = Renewal(
            loan_id=loan_id,
            old_due_at=old_due,
            new_due_at=new_due
        )
        db.add(renewal)
        db.flush()

        # Cập nhật hạn mới vào Loans
        loan.due_at = new_due

        db.commit()
        db.refresh(renewal)
        return renewal


renewal_service = RenewalService()
