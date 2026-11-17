from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, SmallInteger, String, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.hard_book import HardBook
    from app.models.ebook import Ebook
    from app.models.course import CourseResource


class Source(Base):
    """Mô hình đại diện cho Tài liệu / Đầu sách chung (Bảng Sources).
    
    Lưu trữ thông tin thư mục và giá bìa dùng chung cho cả bản cứng và bản mềm.
    """
    __tablename__ = "Sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    genre: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Giá bìa hiện tại (VNĐ)"
    )

    __table_args__ = (
        CheckConstraint("publication_year BETWEEN 1000 AND 2100", name="chk_sources_pub_year"),
        CheckConstraint("page_count > 0", name="chk_sources_page_count"),
        CheckConstraint("price >= 0", name="chk_sources_price"),
    )

    # Quan hệ 1-N: 1 tài liệu có nhiều bản sao vật lý tại các chi nhánh
    hard_books: Mapped[List["HardBook"]] = relationship("HardBook", back_populates="source")

    # Quan hệ 1-1: Mỗi tài liệu có tối đa 1 file số
    ebook: Mapped[Optional["Ebook"]] = relationship("Ebook", back_populates="source", uselist=False)

    # Quan hệ 1-N: Danh mục giáo trình môn học
    course_resources: Mapped[List["CourseResource"]] = relationship("CourseResource", back_populates="source")

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, title='{self.title}', price={self.price})>"
