from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.course import Course, CourseResource
from app.repositories.base import CRUDBase
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse,
    CourseResourceCreate, CourseResourceResponse
)

router = APIRouter(prefix="/courses", tags=["Courses (Môn học & Giáo trình)"])
course_repo = CRUDBase[Course, CourseCreate, CourseUpdate](Course)


@router.get("", response_model=List[CourseResponse])
def get_courses(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách các môn học."""
    return course_repo.get_multi(db, skip=skip, limit=limit)


@router.get("/{id}", response_model=CourseResponse)
def get_course(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin chi tiết một môn học theo ID."""
    course = course_repo.get(db, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy môn học có ID = {id}"
        )
    return course


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)):
    """Tạo mới một môn học."""
    return course_repo.create(db, obj_in=course_in)


@router.put("/{id}", response_model=CourseResponse)
def update_course(id: int, course_in: CourseUpdate, db: Session = Depends(get_db)):
    """Cập nhật tên môn học."""
    course = course_repo.get(db, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy môn học có ID = {id}"
        )
    return course_repo.update(db, db_obj=course, obj_in=course_in)


@router.delete("/{id}", response_model=CourseResponse)
def delete_course(id: int, db: Session = Depends(get_db)):
    """Xóa môn học."""
    course = course_repo.get(db, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy môn học có ID = {id}"
        )
    return course_repo.remove(db, id=id)


# Danh mục giáo trình thuộc môn học (Course_resources)
@router.get("/{id}/resources", response_model=List[CourseResourceResponse])
def get_course_resources(id: int, db: Session = Depends(get_db)):
    """Lấy danh sách giáo trình bắt buộc và tham khảo của môn học."""
    stmt = select(CourseResource).where(CourseResource.course_id == id)
    return list(db.scalars(stmt).all())


@router.post("/{id}/resources", response_model=CourseResourceResponse, status_code=status.HTTP_201_CREATED)
def add_course_resource(id: int, res_in: CourseResourceCreate, db: Session = Depends(get_db)):
    """Thêm tài liệu làm giáo trình (bắt buộc / tham khảo) cho môn học."""
    if res_in.course_id != id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course ID trên URL không khớp với body."
        )
    existing = db.scalar(
        select(CourseResource).where(
            CourseResource.course_id == id,
            CourseResource.source_id == res_in.source_id
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài liệu này đã có trong danh mục giáo trình của môn học."
        )
    cr = CourseResource(
        course_id=id,
        source_id=res_in.source_id,
        is_required=res_in.is_required
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


@router.delete("/{id}/resources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_course_resource(id: int, source_id: int, db: Session = Depends(get_db)):
    """Xóa tài liệu khỏi danh mục giáo trình môn học."""
    cr = db.scalar(
        select(CourseResource).where(
            CourseResource.course_id == id,
            CourseResource.source_id == source_id
        )
    )
    if not cr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài liệu trong môn học này."
        )
    db.delete(cr)
    db.commit()
