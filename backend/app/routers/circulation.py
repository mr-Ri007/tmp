from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.loan import (
    LoanCreate, LoanResponse,
    RenewalCreate, RenewalResponse,
    ReturnRecordCreate, ReturnRecordResponse
)
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.schemas.fine import FineResponse
from app.services.loan_service import loan_service
from app.services.return_service import return_service
from app.services.renewal_service import renewal_service
from app.services.reservation_service import reservation_service

router = APIRouter(prefix="/circulation", tags=["Circulation (Mượn - Trả - Gia hạn - Đặt trước)"])


@router.post("/borrow", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def borrow_book(payload: LoanCreate, db: Session = Depends(get_db)):
    """Thực hiện mượn sách vật lý.
    
    Quy tắc kiểm tra tự động:
      - Sách phải đang SanSang (hoặc DangCho đúng độc giả này).
      - Sinh viên tối đa 5 cuốn.
      - Nợ phạt chưa nộp <= 100.000 VNĐ.
    """
    return loan_service.borrow_book(
        db,
        reader_id=payload.reader_id,
        hard_book_id=payload.hard_book_id,
        days=payload.days
    )


@router.post("/return")
def return_book(payload: ReturnRecordCreate, db: Session = Depends(get_db)):
    """Thực hiện trả sách và ghi nhận phiếu trả.
    
    Trigger MySQL sẽ tự động tính phạt:
      - Lost: 100% giá bìa (không tính phí trễ hạn).
      - Late: 10% * giá bìa * số ngày quá hạn (nếu điều kiện Tot).
      - Hong: Không phạt tự động (chờ nhân viên đánh giá).
    """
    ret_record, fine = return_service.return_book(
        db,
        loan_id=payload.loan_id,
        return_condition=payload.return_condition,
        returned_at=payload.returned_at
    )
    return {
        "message": "Trả sách thành công.",
        "return_record": ReturnRecordResponse.model_validate(ret_record),
        "fine_generated": FineResponse.model_validate(fine) if fine else None
    }


@router.post("/renew", response_model=RenewalResponse, status_code=status.HTTP_201_CREATED)
def renew_book(payload: RenewalCreate, db: Session = Depends(get_db)):
    """Gia hạn thời gian mượn sách (mặc định thêm 7 ngày)."""
    return renewal_service.renew_book(
        db,
        loan_id=payload.loan_id,
        extension_days=payload.extension_days
    )


@router.post("/reserve", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def reserve_book(payload: ReservationCreate, db: Session = Depends(get_db)):
    """Đặt trước bản sao sách vật lý đang SanSang (giữ chỗ 3 ngày)."""
    return reservation_service.reserve_book(
        db,
        reader_id=payload.reader_id,
        hard_book_id=payload.hard_book_id,
        days=payload.days
    )


@router.put("/reserve/{id}/cancel", response_model=ReservationResponse)
def cancel_reservation(id: int, db: Session = Depends(get_db)):
    """Hủy lượt đặt trước sách và trả bản sao về trạng thái 'SanSang'."""
    return reservation_service.cancel_reservation(db, reservation_id=id)


@router.get("/active-loans")
def get_active_loans(
    db: Session = Depends(get_db),
    reader_id: Optional[int] = Query(None, description="Lọc theo độc giả"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Truy vấn danh sách các lượt mượn đang active (chưa trả) thông qua View `v_active_loans`."""
    sql = "SELECT id, reader_id, hard_book_id, borrowed_at, due_at FROM v_active_loans"
    params = {}
    if reader_id:
        sql += " WHERE reader_id = :reader_id"
        params["reader_id"] = reader_id
    sql += " ORDER BY borrowed_at DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip

    results = db.execute(text(sql), params).mappings().all()
    return [dict(row) for row in results]
