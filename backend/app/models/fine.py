import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.return_record import ReturnRecord


class Fine(Base):
    """Mô hình đại diện cho Khoản phạt vi phạm trả sách (Bảng Fines).
    
    Quy tắc nghiệp vụ:
      - Late: Trả quá hạn (10% * giá bìa * số ngày quá hạn)
      - Lost: Làm mất sách (100% * giá bìa)
      - Damaged: Làm hỏng sách (nhân viên đánh giá và nhập số tiền)
    Mỗi phiếu trả sách có tối đa 1 khoản phạt (ràng buộc UNIQUE return_record_id).
    """
    __tablename__ = "Fines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Return_records.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True
    )
    fine_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Late / Lost / Damaged"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Số tiền phạt thực tế (VNĐ)"
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Lý do / ghi chú phạt"
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="Thời điểm phát sinh khoản phạt"
    )
    late_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Cấu phần quá hạn được ghi nhận"
    )
    damaged_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="NULL = chưa đánh giá hỏng, hoặc không thuộc loại hư hại"
    )
    assessed_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nhân viên thực hiện đánh giá hư hại (cho trường hợp Damaged)"
    )
    paid_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Thời điểm đã nộp phạt (NULL = chưa nộp)"
    )

    __table_args__ = (
        UniqueConstraint("return_record_id", name="uq_fines_return_record"),
        CheckConstraint("fine_type IN ('Late','Lost','Damaged')", name="chk_fines_type"),
        CheckConstraint("amount >= 0", name="chk_fines_amount"),
        CheckConstraint("late_amount >= 0", name="chk_fines_late_amount"),
        CheckConstraint("damaged_amount IS NULL OR damaged_amount >= 0", name="chk_fines_damaged_amount"),
    )

    return_record: Mapped["ReturnRecord"] = relationship("ReturnRecord", back_populates="fine")

    def __repr__(self) -> str:
        return f"<Fine(id={self.id}, type='{self.fine_type}', amount={self.amount}, paid={self.paid_at is not None})>"
