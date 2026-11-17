import datetime as dt
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_log import AccessLog
from app.models.reader import Reader
from app.models.ebook import Ebook


class AccessLogService:
    @staticmethod
    def start_session(db: Session, *, reader_id: int, ebook_id: int) -> AccessLog:
        """Bắt đầu phiên đọc tài liệu số (Ebook)."""
        if not db.get(Reader, reader_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy độc giả có ID = {reader_id}"
            )

        if not db.get(Ebook, ebook_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy ebook có ID = {ebook_id}"
            )

        log = AccessLog(
            reader_id=reader_id,
            ebook_id=ebook_id,
            started_at=dt.datetime.now(),
            ended_at=None
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def end_session(
        db: Session,
        *,
        log_id: int,
        ended_at: Optional[dt.datetime] = None
    ) -> AccessLog:
        """Kết thúc phiên đọc tài liệu số (Ebook)."""
        log = db.scalar(select(AccessLog).where(AccessLog.id == log_id).with_for_update())
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lượt truy cập có ID = {log_id}"
            )

        if log.ended_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phiên đọc ebook này đã được kết thúc trước đó."
            )

        end_time = ended_at or dt.datetime.now()
        if end_time < log.started_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thời điểm kết thúc không thể trước thời điểm bắt đầu đọc."
            )

        log.ended_at = end_time
        db.commit()
        db.refresh(log)
        return log


access_log_service = AccessLogService()
