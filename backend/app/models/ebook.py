from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.access_log import AccessLog


class Ebook(Base):
    """Mô hình đại diện cho Bản mềm / Ebook (Bảng Ebooks).
    Mỗi tài liệu có tối đa 1 file số (quan hệ 1-1).
    """
    __tablename__ = "Ebooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Sources.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True
    )
    file_size_mb: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Dung lượng file (MB)"
    )

    __table_args__ = (
        CheckConstraint("file_size_mb > 0", name="chk_ebooks_file_size"),
    )

    # Quan hệ 1-1 ngược lại với Source
    source: Mapped["Source"] = relationship("Source", back_populates="ebook")

    # Quan hệ 1-N: Lịch sử các phiên truy cập đọc ebook
    access_logs: Mapped[List["AccessLog"]] = relationship("AccessLog", back_populates="ebook")

    def __repr__(self) -> str:
        return f"<Ebook(id={self.id}, source_id={self.source_id}, file_size_mb={self.file_size_mb})>"
