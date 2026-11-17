import datetime as dt
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.hard_book import HardBook
from app.models.reader import Reader
from app.models.reservation import Reservation
from app.models.return_record import ReturnRecord
from app.repositories.reader_repo import reader_repo
from app.repositories.fine_repo import fine_repo


class LoanService:
    @staticmethod
    def borrow_book(
        db: Session,
        *,
        reader_id: int,
        hard_book_id: int,
        days: Optional[int] = None
    ) -> Loan:
        """Thực hiện nghiệp vụ mượn sách vật lý.
        
        Quy tắc nghiệp vụ:
          1. Độc giả phải tồn tại trong hệ thống.
          2. Khóa bản sao sách (SELECT FOR UPDATE) để ngăn chặn race condition.
          3. Sách không được ở trạng thái DangMuon. Nếu DangCho, chỉ người đặt trước mới được mượn.
          4. Sinh viên mượn tối đa 5 cuốn đồng thời.
          5. Tiền phạt chưa thanh toán không được vượt quá 100.000 VNĐ.
          6. Tự động tính hạn trả: SV = 14 ngày, GV/NCS = 30 ngày (nếu không chỉ định).
        """
        # 1. Kiểm tra độc giả
        reader = db.get(Reader, reader_id)
        if not reader:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy độc giả có ID = {reader_id}"
            )

        # 2. Khóa bản sao sách bằng SELECT ... FOR UPDATE
        book_stmt = (
            select(HardBook)
            .where(HardBook.id == hard_book_id)
            .with_for_update()
        )
        book = db.scalar(book_stmt)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy bản sao sách có ID = {hard_book_id}"
            )

        # 3. Kiểm tra trạng thái sách
        if book.status == "DangMuon":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bản sao sách này hiện đang được mượn bởi người khác."
            )

        if book.status == "DangCho":
            # Kiểm tra xem có đúng độc giả này đã đặt trước và đang chờ nhận không
            res_stmt = select(Reservation).where(
                Reservation.hard_book_id == hard_book_id,
                Reservation.reader_id == reader_id,
                Reservation.status == "ChoNhan"
            )
            reservation = db.scalar(res_stmt)
            if not reservation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bản sao sách này đang được giữ chỗ cho độc giả khác đặt trước."
                )

        # 4. Kiểm tra giới hạn mượn của Sinh viên (tối đa 5 cuốn)
        if reader.reader_type == "Sinh vien":
            active_count = reader_repo.count_active_loans(db, reader_id)
            if active_count >= 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sinh viên không được mượn quá 5 cuốn sách cùng lúc."
                )

        # 5. Kiểm tra nợ phạt chưa thanh toán (> 100.000đ thì bị chặn)
        unpaid_fines = fine_repo.get_unpaid_sum_by_reader(db, reader_id)
        if unpaid_fines > 100000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Độc giả đang có khoản phạt chưa nộp là {unpaid_fines:,.0f} VNĐ (vượt quá hạn mức 100.000 VNĐ)."
            )

        # 6. Tính hạn trả
        now = dt.datetime.now()
        if days:
            due_at = now + dt.timedelta(days=days)
        else:
            default_days = 14 if reader.reader_type == "Sinh vien" else 30
            due_at = now + dt.timedelta(days=default_days)

        # 7. Tạo lượt mượn
        loan = Loan(
            reader_id=reader_id,
            hard_book_id=hard_book_id,
            borrowed_at=now,
            due_at=due_at
        )
        db.add(loan)

        # 8. Cập nhật trạng thái sách sang DangMuon
        book.status = "DangMuon"

        # 9. Nếu có đặt trước tương ứng, cập nhật sang DaNhan
        res_update_stmt = select(Reservation).where(
            Reservation.hard_book_id == hard_book_id,
            Reservation.reader_id == reader_id,
            Reservation.status == "ChoNhan"
        )
        active_res = db.scalar(res_update_stmt)
        if active_res:
            active_res.status = "DaNhan"

        db.commit()
        db.refresh(loan)
        return loan


loan_service = LoanService()
