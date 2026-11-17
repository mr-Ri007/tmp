import datetime as dt
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.reader import Reader
    from app.models.ebook import Ebook


class AccessLog(Base):
    """Mô hình đại diện cho Lịch sử truy cập tài liệu số (Bảng Access_logs)."""
    __tablename__ = "Access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Readers.id", ondelete="RESTRICT"),
        nullable=False
    )
    ebook_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Ebooks.id", ondelete="RESTRICT"),
        nullable=False
    )
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="NULL = đang truy cập đọc"
    )

    __table_args__ = (
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="chk_access_logs_ended"),
    )

    reader: Mapped["Reader"] = relationship("Reader", back_populates="access_logs")
    ebook: Mapped["Ebook"] = relationship("Ebook", back_populates="access_logs")

    def __repr__(self) -> str:
        return f"<AccessLog(id={self.id}, reader_id={self.reader_id}, ebook_id={self.ebook_id})>"
