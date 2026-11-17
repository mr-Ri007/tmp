from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.hard_book import HardBook


class Branch(Base):
    """Mô hình đại diện cho Chi nhánh thư viện (Bảng Branches)."""
    __tablename__ = "Branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)

    # Quan hệ 1-N: 1 chi nhánh có nhiều bản sao sách vật lý
    hard_books: Mapped[List["HardBook"]] = relationship("HardBook", back_populates="branch")

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, name='{self.name}')>"
