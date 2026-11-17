from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.source import Source


class Course(Base):
    """Mô hình đại diện cho Môn học (Bảng Courses)."""
    __tablename__ = "Courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Quan hệ 1-N: Danh mục tài liệu giáo trình thuộc môn học
    course_resources: Mapped[List["CourseResource"]] = relationship("CourseResource", back_populates="course")

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name='{self.name}')>"


class CourseResource(Base):
    """Mô hình đại diện cho Danh mục giáo trình của từng môn (Bảng Course_resources).
    Bảng quan hệ N-N giữa Courses và Sources với khóa chính phức hợp (composite PK).
    """
    __tablename__ = "Course_resources"

    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Courses.id", ondelete="RESTRICT"),
        primary_key=True
    )
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Sources.id", ondelete="RESTRICT"),
        primary_key=True
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="TRUE = giáo trình bắt buộc, FALSE = tham khảo"
    )

    course: Mapped["Course"] = relationship("Course", back_populates="course_resources")
    source: Mapped["Source"] = relationship("Source", back_populates="course_resources")

    def __repr__(self) -> str:
        return f"<CourseResource(course_id={self.course_id}, source_id={self.source_id}, required={self.is_required})>"
