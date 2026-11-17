import datetime as dt
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.loan import Loan


class Renewal(Base):
    """Mô hình đại diện cho Lịch sử gia hạn sách (Bảng Renewals)."""
    __tablename__ = "Renewals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Loans.id", ondelete="RESTRICT"),
        nullable=False
    )
    old_due_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    new_due_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("new_due_at > old_due_at", name="chk_renewals_due_at"),
    )

    loan: Mapped["Loan"] = relationship("Loan", back_populates="renewals")

    def __repr__(self) -> str:
        return f"<Renewal(id={self.id}, loan_id={self.loan_id}, old_due={self.old_due_at}, new_due={self.new_due_at})>"
