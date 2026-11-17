import datetime as dt
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.reader import Reader
    from app.models.hard_book import HardBook


class Reservation(Base):
    """Mô hình đại diện cho Lượt đặt trước bản cứng (Bảng Reservations)."""
    __tablename__ = "Reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Readers.id", ondelete="RESTRICT"),
        nullable=False
    )
    hard_book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Hard_books.id", ondelete="RESTRICT"),
        nullable=False
    )
    reserved_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    pickup_deadline: Mapped[dt.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Hạn chót đến nhận sách"
    )
    status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ChoNhan",
        comment="Trạng thái: ChoNhan / DaNhan / HetHan / Huy"
    )

    __table_args__ = (
        CheckConstraint("status IN ('ChoNhan','DaNhan','HetHan','Huy')", name="chk_reservations_status"),
        CheckConstraint("pickup_deadline > reserved_at", name="chk_reservations_deadline"),
    )

    reader: Mapped["Reader"] = relationship("Reader", back_populates="reservations")
    hard_book: Mapped["HardBook"] = relationship("HardBook", back_populates="reservations")

    def __repr__(self) -> str:
        return f"<Reservation(id={self.id}, reader_id={self.reader_id}, book_id={self.hard_book_id}, status='{self.status}')>"
