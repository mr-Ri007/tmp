import datetime as dt
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fine import Fine
from app.models.return_record import ReturnRecord


class FineService:
    @staticmethod
    def assess_damaged_fine(
        db: Session,
        *,
        return_record_id: int,
        amount: Decimal,
        reason: str,
        assessed_by: str
    ) -> Fine:
        """Nghiệp vụ Đánh giá sách hỏng (Damaged):
        
        Quy tắc nghiệp vụ:
          - Sách trả bị hỏng KHÔNG tự động tính tiền phạt bởi Trigger.
          - Nhân viên kiểm tra tình trạng sách thực tế và tự quyết định mức phạt.
          - Chỉ tạo khoản phạt sau khi nhân viên nhập và xác nhận số tiền.
          - Lưu thông tin nhân viên thực hiện đánh giá (assessed_by).
          - Mỗi phiếu trả sách chỉ có tối đa 1 khoản phạt (chặn trùng lặp).
        """
        # 1. Kiểm tra phiếu trả sách
        ret_record = db.scalar(
            select(ReturnRecord).where(ReturnRecord.id == return_record_id).with_for_update()
        )
        if not ret_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy phiếu trả sách có ID = {return_record_id}"
            )

        if ret_record.return_condition != "Hong":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phiếu trả này có tình trạng là '{ret_record.return_condition}', không phải tình trạng 'Hong' để đánh giá hư hại."
            )

        # 2. Kiểm tra xem đã có khoản phạt nào chưa
        existing_fine = db.scalar(select(Fine).where(Fine.return_record_id == return_record_id))
        if existing_fine:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phiếu trả sách này đã tồn tại khoản phạt (Loại: {existing_fine.fine_type}, Số tiền: {existing_fine.amount:,.0f} VNĐ)."
            )

        # 3. Tạo khoản phạt Damaged
        fine = Fine(
            return_record_id=return_record_id,
            fine_type="Damaged",
            amount=amount,
            reason=reason,
            late_amount=Decimal("0.00"),
            damaged_amount=amount,
            assessed_by=assessed_by,
            created_at=dt.datetime.now()
        )
        db.add(fine)
        db.commit()
        db.refresh(fine)
        return fine

    @staticmethod
    def pay_fine(
        db: Session,
        *,
        fine_id: int,
        paid_at: Optional[dt.datetime] = None
    ) -> Fine:
        """Ghi nhận độc giả đã nộp tiền phạt."""
        fine = db.scalar(select(Fine).where(Fine.id == fine_id).with_for_update())
        if not fine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy khoản phạt có ID = {fine_id}"
            )

        if fine.paid_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Khoản phạt này đã được thanh toán vào ngày {fine.paid_at}."
            )

        fine.paid_at = paid_at or dt.datetime.now()
        db.commit()
        db.refresh(fine)
        return fine


fine_service = FineService()
