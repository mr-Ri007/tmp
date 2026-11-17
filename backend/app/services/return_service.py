import datetime as dt
import uuid
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.return_record import ReturnRecord
from app.models.fine import Fine
from app.models.hard_book import HardBook


class ReturnService:
    @staticmethod
    def return_book(
        db: Session,
        *,
        loan_id: int,
        return_condition: str = "Tot",
        returned_at: Optional[dt.datetime] = None
    ) -> Tuple[ReturnRecord, Optional[Fine]]:
        """Thực hiện nghiệp vụ trả sách.
        
        Quy tắc nghiệp vụ:
          1. Lượt mượn phải tồn tại và chưa có phiếu trả.
          2. Ngày trả thực tế phải >= ngày mượn.
          3. Tình trạng sách phải thuộc: 'Tot', 'Hong', 'Mat'.
          4. Khi lưu phiếu trả:
             - Trigger MySQL `trg_returns_after` tự động chuyển sách về 'SanSang'.
             - Trigger tự động tính và tạo khoản phạt (Lost = 100% giá bìa; Late = 10% * giá bìa * số ngày trễ).
             - Backend tuyệt đối KHÔNG tự tính thêm tiền phạt để tránh trùng lặp.
          5. Trả về cả phiếu trả và khoản phạt tự động (nếu có).
        """
        if return_condition not in ("Tot", "Hong", "Mat"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tình trạng sách trả không hợp lệ (chỉ chấp nhận: 'Tot', 'Hong', 'Mat')."
            )

        # 1. Khóa lượt mượn với SELECT ... FOR UPDATE
        loan_stmt = select(Loan).where(Loan.id == loan_id).with_for_update()
        loan = db.scalar(loan_stmt)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lượt mượn có ID = {loan_id}"
            )

        # 2. Kiểm tra xem lượt mượn đã có phiếu trả chưa
        existing_ret = db.scalar(select(ReturnRecord).where(ReturnRecord.loan_id == loan_id))
        if existing_ret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lượt mượn này đã được trả với mã phiếu {existing_ret.return_code}."
            )

        actual_return_time = returned_at or dt.datetime.now()
        if actual_return_time < loan.borrowed_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thời điểm trả sách không thể trước thời điểm mượn sách."
            )

        # 3. Tạo mã phiếu trả độc nhất
        return_code = f"PT{uuid.uuid4().hex[:8].upper()}"

        return_record = ReturnRecord(
            loan_id=loan_id,
            return_code=return_code,
            returned_at=actual_return_time,
            return_condition=return_condition
        )
        db.add(return_record)

        # Cập nhật trạng thái sách (đồng bộ với trigger)
        book = db.get(HardBook, loan.hard_book_id)
        if book:
            book.status = "SanSang"

        db.commit()
        db.refresh(return_record)

        # 4. Kiểm tra khoản phạt được sinh ra từ MySQL Trigger (nếu có)
        fine = db.scalar(select(Fine).where(Fine.return_record_id == return_record.id))
        return return_record, fine


return_service = ReturnService()
