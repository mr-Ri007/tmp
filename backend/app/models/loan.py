import datetime as dt
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.reader import Reader
    from app.models.hard_book import HardBook
    from app.models.renewal import Renewal
    from app.models.return_record import ReturnRecord


class Loan(Base):
    """Mô hình đại diện cho Lịch sử mượn sách cứng (Bảng Loans).
    Mỗi dòng tương ứng với 1 bản sao được mượn 1 lần.
    """
    __tablename__ = "Loans"

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
    borrowed_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    due_at: Mapped[dt.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Hạn trả (được cập nhật khi gia hạn)"
    )

    __table_args__ = (
        CheckConstraint("due_at > borrowed_at", name="chk_loans_due_at"),
    )

    # Quan hệ N-1: Độc giả mượn
    reader: Mapped["Reader"] = relationship("Reader", back_populates="loans")

    # Quan hệ N-1: Bản sao được mượn
    hard_book: Mapped["HardBook"] = relationship("HardBook", back_populates="loans")

    # Quan hệ 1-N: Lịch sử các lần gia hạn
    renewals: Mapped[List["Renewal"]] = relationship("Renewal", back_populates="loan")

    # Quan hệ 1-1: Phiếu trả sách tương ứng (tối đa 1 phiếu trả)
    return_record: Mapped[Optional["ReturnRecord"]] = relationship(
        "ReturnRecord",
        back_populates="loan",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<Loan(id={self.id}, reader_id={self.reader_id}, hard_book_id={self.hard_book_id}, due_at={self.due_at})>"
