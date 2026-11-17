from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.fine_repo import fine_repo
from app.schemas.fine import FineAssessDamaged, FinePageResponse, FinePayRequest, FineResponse
from app.services.fine_service import fine_service

router = APIRouter(prefix="/fines", tags=["Fines (Quản lý Tiền phạt)"])


@router.get("/page", response_model=FinePageResponse)
def get_fines_page(
    db: Session = Depends(get_db),
    reader_id: Optional[int] = Query(None, ge=1, description="Lọc theo hội viên"),
    unpaid_only: bool = Query(False, description="Chỉ lấy các khoản phạt chưa thanh toán"),
    fine_type: Optional[str] = Query(None, description="Lọc theo loại phạt: Late / Lost / Damaged"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Lấy một trang tiền phạt kèm tổng số bản ghi khớp bộ lọc."""
    filters = {
        "reader_id": reader_id,
        "unpaid_only": unpaid_only,
        "fine_type": fine_type,
    }
    return {
        "items": fine_repo.get_multi(db, **filters, skip=skip, limit=limit),
        "total": fine_repo.get_count(db, **filters),
    }


@router.get("", response_model=List[FineResponse])
def get_fines(
    db: Session = Depends(get_db),
    reader_id: Optional[int] = Query(None, description="Lọc theo độc giả"),
    unpaid_only: bool = Query(False, description="Chỉ lấy các khoản phạt chưa thanh toán"),
    fine_type: Optional[str] = Query(None, description="Lọc theo loại phạt: Late / Lost / Damaged"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách các khoản phạt vi phạm."""
    return fine_repo.get_multi(
        db,
        reader_id=reader_id,
        unpaid_only=unpaid_only,
        fine_type=fine_type,
        skip=skip,
        limit=limit
    )


@router.get("/{id}", response_model=FineResponse)
def get_fine(id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết một khoản phạt theo ID."""
    fine = fine_repo.get(db, id)
    if not fine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khoản phạt có ID = {id}"
        )
    return fine


@router.post("/assess-damaged", response_model=FineResponse, status_code=status.HTTP_201_CREATED)
def assess_damaged_book(payload: FineAssessDamaged, db: Session = Depends(get_db)):
    """Nghiệp vụ dành cho Nhân viên: Xác nhận tình trạng sách hỏng và nhập mức phạt thực tế.
    
    Yêu cầu:
      - Phiếu trả sách phải ở tình trạng 'Hong'.
      - Lưu thông tin nhân viên đánh giá (assessed_by).
      - Không tạo khoản phạt trùng lặp.
    """
    return fine_service.assess_damaged_fine(
        db,
        return_record_id=payload.return_record_id,
        amount=payload.amount,
        reason=payload.reason,
        assessed_by=payload.assessed_by
    )


@router.post("/{id}/pay", response_model=FineResponse)
def pay_fine(id: int, payload: FinePayRequest, db: Session = Depends(get_db)):
    """Ghi nhận độc giả nộp phạt."""
    return fine_service.pay_fine(db, fine_id=id, paid_at=payload.paid_at)


@router.get("/debtors/check/{reader_id}")
def check_reader_unpaid_fines(reader_id: int, db: Session = Depends(get_db)):
    """Kiểm tra tổng tiền phạt chưa nộp của độc giả và trạng thái có bị chặn mượn hay không."""
    total_unpaid = fine_repo.get_unpaid_sum_by_reader(db, reader_id)
    is_blocked = total_unpaid > 100000
    return {
        "reader_id": reader_id,
        "total_unpaid_fines": float(total_unpaid),
        "is_borrow_blocked": is_blocked,
        "max_unpaid_threshold": 100000.0,
        "notice": "Độc giả bị chặn mượn sách nếu tiền phạt chưa trả vượt 100.000 VNĐ." if is_blocked else "Độc giả đủ điều kiện mượn sách về mặt tài chính."
    }
