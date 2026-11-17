import datetime as dt
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String, Date, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.loan import Loan
    from app.models.reservation import Reservation
    from app.models.access_log import AccessLog


class Reader(Base):
    """Mô hình đại diện cho Độc giả thư viện (Bảng Readers)."""
    __tablename__ = "Readers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[dt.date] = mapped_column(Date, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    national_id: Mapped[Optional[str]] = mapped_column(String(12), nullable=True, unique=True)
    reader_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Hạng độc giả: Sinh vien / Giang vien / Nghien cuu sinh"
    )

    __table_args__ = (
        CheckConstraint("reader_type IN ('Sinh vien','Giang vien','Nghien cuu sinh')", name="chk_readers_type"),
    )

    # Quan hệ 1-N: Lịch sử mượn sách
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="reader")

    # Quan hệ 1-N: Lịch sử đặt trước
    reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="reader")

    # Quan hệ 1-N: Lịch sử đọc ebook
    access_logs: Mapped[List["AccessLog"]] = relationship("AccessLog", back_populates="reader")

    def __repr__(self) -> str:
        return f"<Reader(id={self.id}, full_name='{self.full_name}', reader_type='{self.reader_type}')>"
