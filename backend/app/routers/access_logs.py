from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.access_log import AccessLog
from app.schemas.access_log import AccessLogStart, AccessLogEnd, AccessLogResponse
from app.services.access_log_service import access_log_service

router = APIRouter(prefix="/access-logs", tags=["Access Logs (Nhật ký truy cập Ebook)"])


@router.get("", response_model=List[AccessLogResponse])
def get_access_logs(
    db: Session = Depends(get_db),
    reader_id: Optional[int] = Query(None, description="Lọc theo độc giả"),
    ebook_id: Optional[int] = Query(None, description="Lọc theo ebook"),
    active_only: bool = Query(False, description="Chỉ lấy các phiên đang mở (chưa kết thúc)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy lịch sử các phiên đọc tài liệu số."""
    stmt = select(AccessLog)
    if reader_id:
        stmt = stmt.where(AccessLog.reader_id == reader_id)
    if ebook_id:
        stmt = stmt.where(AccessLog.ebook_id == ebook_id)
    if active_only:
        stmt = stmt.where(AccessLog.ended_at.is_(None))
    stmt = stmt.order_by(AccessLog.started_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.post("/start", response_model=AccessLogResponse, status_code=status.HTTP_201_CREATED)
def start_reading_session(payload: AccessLogStart, db: Session = Depends(get_db)):
    """Ghi nhận thời điểm độc giả bắt đầu mở đọc một ebook."""
    return access_log_service.start_session(
        db,
        reader_id=payload.reader_id,
        ebook_id=payload.ebook_id
    )


@router.post("/{id}/end", response_model=AccessLogResponse)
def end_reading_session(id: int, payload: AccessLogEnd, db: Session = Depends(get_db)):
    """Ghi nhận thời điểm độc giả kết thúc phiên đọc ebook."""
    return access_log_service.end_session(
        db,
        log_id=id,
        ended_at=payload.ended_at
    )
