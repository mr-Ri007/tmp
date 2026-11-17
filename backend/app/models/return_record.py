import datetime as dt
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.loan import Loan
    from app.models.fine import Fine


class ReturnRecord(Base):
    """Mô hình đại diện cho Phiếu trả sách (Bảng Return_records).
    Mỗi lượt mượn có tối đa 1 phiếu trả (quan hệ 1-1).
    """
    __tablename__ = "Return_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Loans.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True
    )
    return_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        comment="Mã phiếu trả in trên phiếu"
    )
    returned_at: Mapped[dt.datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Thời điểm trả thực tế"
    )
    return_condition: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="Tot",
        comment="Tình trạng sách khi trả: Tot / Hong / Mat"
    )

    __table_args__ = (
        CheckConstraint("return_condition IN ('Tot','Hong','Mat')", name="chk_return_records_cond"),
    )

    # Quan hệ 1-1 với Loan
    loan: Mapped["Loan"] = relationship("Loan", back_populates="return_record")

    # Quan hệ 1-1 với Fine (mỗi phiếu trả phát sinh tối đa 1 khoản phạt)
    fine: Mapped[Optional["Fine"]] = relationship(
        "Fine",
        back_populates="return_record",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<ReturnRecord(id={self.id}, code='{self.return_code}', condition='{self.return_condition}')>"
