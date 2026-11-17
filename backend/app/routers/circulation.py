import datetime as dt
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
    branch_id: Optional[int] = Query(None, description="Lọc theo chi nhánh"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Truy vấn danh sách các lượt mượn đang active (chưa trả) thông qua View `v_active_loans`."""
    from_sql = (
        " FROM v_active_loans al "
        "JOIN Hard_books hb ON hb.id = al.hard_book_id "
        "JOIN Sources s ON s.id = hb.source_id "
        "JOIN Branches b ON b.id = hb.branch_id"
    )
    conditions = []
    params = {}
    if reader_id is not None:
        conditions.append("al.reader_id = :reader_id")
        params["reader_id"] = reader_id
    if branch_id is not None:
        conditions.append("hb.branch_id = :branch_id")
        params["branch_id"] = branch_id
    where_sql = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    total = db.execute(
        text("SELECT COUNT(*)" + from_sql + where_sql), params
    ).scalar_one()
    sql = (
        "SELECT al.id, al.reader_id, al.hard_book_id, al.borrowed_at, al.due_at, "
        "hb.branch_id, b.name AS branch_name, s.title AS source_title, "
        "(SELECT COUNT(*) FROM Renewals r WHERE r.loan_id = al.id) AS renewals_count"
        + from_sql
        + where_sql
        + " ORDER BY al.borrowed_at DESC LIMIT :limit OFFSET :skip"
    )
    params["limit"] = limit
    params["skip"] = skip

    results = db.execute(text(sql), params).mappings().all()
    return {"items": [dict(row) for row in results], "total": total}


@router.get("/history")
def get_loan_history(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lấy lịch sử mượn trong tháng cùng thống kê tính trên toàn bộ tháng."""
    start = dt.datetime(year, month, 1)
    end = dt.datetime(year + (month == 12), month % 12 + 1, 1)
    date_filter = "l.borrowed_at >= :start AND l.borrowed_at < :end"
    params = {"start": start, "end": end}

    totals = db.execute(
        text(
            "SELECT COUNT(*) AS total_loans, "
            "COUNT(DISTINCT l.reader_id) AS member_count, "
            "SUM(CASE WHEN rr.id IS NOT NULL THEN 1 ELSE 0 END) AS returned_loans "
            "FROM Loans l LEFT JOIN Return_records rr ON rr.loan_id = l.id "
            f"WHERE {date_filter}"
        ),
        params,
    ).mappings().one()

    total = int(totals["total_loans"] or 0)
    rows = db.execute(
        text(
            "SELECT l.id, l.reader_id, r.full_name AS reader_name, "
            "l.hard_book_id, s.title, l.borrowed_at, l.due_at, "
            "rr.returned_at, "
            "CASE WHEN rr.id IS NULL THEN 'Đang mượn' ELSE 'Đã trả' END AS status "
            "FROM Loans l "
            "JOIN Readers r ON r.id = l.reader_id "
            "JOIN Hard_books hb ON hb.id = l.hard_book_id "
            "JOIN Sources s ON s.id = hb.source_id "
            "LEFT JOIN Return_records rr ON rr.loan_id = l.id "
            f"WHERE {date_filter} "
            "ORDER BY l.borrowed_at DESC, l.id DESC "
            "LIMIT :limit OFFSET :skip"
        ),
        {**params, "limit": limit, "skip": skip},
    ).mappings().all()

    top_readers = db.execute(
        text(
            "SELECT r.id AS reader_id, r.full_name AS reader_name, "
            "COUNT(*) AS loan_count "
            "FROM Loans l JOIN Readers r ON r.id = l.reader_id "
            f"WHERE {date_filter} "
            "GROUP BY r.id, r.full_name "
            "ORDER BY loan_count DESC, r.full_name ASC "
            "LIMIT 5"
        ),
        params,
    ).mappings().all()
    top_books = db.execute(
        text(
            "SELECT s.id AS source_id, s.title, COUNT(*) AS loan_count "
            "FROM Loans l "
            "JOIN Hard_books hb ON hb.id = l.hard_book_id "
            "JOIN Sources s ON s.id = hb.source_id "
            f"WHERE {date_filter} "
            "GROUP BY s.id, s.title "
            "ORDER BY loan_count DESC, s.title ASC "
            "LIMIT 5"
        ),
        params,
    ).mappings().all()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "stats": {
            "total_loans": total,
            "member_count": int(totals["member_count"] or 0),
            "returned_loans": int(totals["returned_loans"] or 0),
            "active_loans": total - int(totals["returned_loans"] or 0),
            "top_readers": [dict(row) for row in top_readers],
            "top_books": [dict(row) for row in top_books],
        },
    }
