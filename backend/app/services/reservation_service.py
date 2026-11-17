import datetime as dt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.hard_book import HardBook
from app.models.reader import Reader


class ReservationService:
    @staticmethod
    def reserve_book(
        db: Session,
        *,
        reader_id: int,
        hard_book_id: int,
        days: int = 3
    ) -> Reservation:
        """Thực hiện nghiệp vụ đặt trước bản sao sách vật lý.
        
        Quy tắc nghiệp vụ:
          1. Độc giả phải tồn tại.
          2. Khóa bản sao sách (SELECT FOR UPDATE).
          3. Bản sao sách PHẢI đang ở trạng thái 'SanSang'.
          4. Tạo lượt đặt trước với status='ChoNhan', pickup_deadline = now + days.
          5. Chuyển trạng thái bản sao sang 'DangCho'.
        """
        reader = db.get(Reader, reader_id)
        if not reader:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy độc giả có ID = {reader_id}"
            )

        # Khóa bản sao
        book = db.scalar(
            select(HardBook).where(HardBook.id == hard_book_id).with_for_update()
        )
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy bản sao sách có ID = {hard_book_id}"
            )

        if book.status != "SanSang":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bản sao sách hiện đang ở trạng thái '{book.status}', không sẵn sàng để đặt trước."
            )

        now = dt.datetime.now()
        deadline = now + dt.timedelta(days=days)

        reservation = Reservation(
            reader_id=reader_id,
            hard_book_id=hard_book_id,
            reserved_at=now,
            pickup_deadline=deadline,
            status="ChoNhan"
        )
        db.add(reservation)
        db.flush()

        # Chuyển sách sang DangCho
        book.status = "DangCho"

        db.commit()
        db.refresh(reservation)
        return reservation

    @staticmethod
    def cancel_reservation(db: Session, *, reservation_id: int) -> Reservation:
        """Hủy lượt đặt trước sách và trả bản sao về 'SanSang'."""
        res = db.scalar(
            select(Reservation).where(Reservation.id == reservation_id).with_for_update()
        )
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lượt đặt trước có ID = {reservation_id}"
            )

        if res.status != "ChoNhan":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lượt đặt trước này đang ở trạng thái '{res.status}', không thể hủy."
            )

        res.status = "Huy"

        # Trả sách về SanSang nếu đang DangCho
        book = db.scalar(select(HardBook).where(HardBook.id == res.hard_book_id).with_for_update())
        if book and book.status == "DangCho":
            book.status = "SanSang"

        db.commit()
        db.refresh(res)
        return res


reservation_service = ReservationService()
