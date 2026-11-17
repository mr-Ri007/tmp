from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.branch import Branch
    from app.models.loan import Loan
    from app.models.reservation import Reservation


class HardBook(Base):
    """Mô hình đại diện cho Bản sao vật lý / Sách in (Bảng Hard_books)."""
    __tablename__ = "Hard_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Sources.id", ondelete="RESTRICT"),
        nullable=False
    )
    branch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Branches.id", ondelete="RESTRICT"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="SanSang",
        comment="Trạng thái: SanSang / DangCho / DangMuon / MatSach"
    )

    __table_args__ = (
        CheckConstraint("status IN ('SanSang','DangCho','DangMuon','MatSach')", name="chk_hard_books_status"),
    )

    # Quan hệ N-1: Thuộc về đầu sách nào
    source: Mapped["Source"] = relationship("Source", back_populates="hard_books")

    # Quan hệ N-1: Đặt tại chi nhánh nào
    branch: Mapped["Branch"] = relationship("Branch", back_populates="hard_books")

    # Quan hệ 1-N: Lịch sử các lượt mượn
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="hard_book")

    # Quan hệ 1-N: Lịch sử các lượt đặt trước
    reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="hard_book")

    def __repr__(self) -> str:
        return f"<HardBook(id={self.id}, source_id={self.source_id}, branch_id={self.branch_id}, status='{self.status}')>"
