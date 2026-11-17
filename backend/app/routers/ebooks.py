from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.models.ebook import Ebook
from app.models.source import Source
from app.repositories.base import CRUDBase
from app.schemas.ebook import EbookCreate, EbookListResponse, EbookUpdate, EbookResponse

router = APIRouter(prefix="/ebooks", tags=["Ebooks (Bản mềm / Tài liệu số)"])
ebook_repo = CRUDBase[Ebook, EbookCreate, EbookUpdate](Ebook)


@router.get("", response_model=EbookListResponse)
def get_ebooks(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Tìm theo tên đầu sách hoặc tác giả"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách các bản mềm ebook."""
    stmt = select(Ebook).options(selectinload(Ebook.source))
    count_stmt = select(func.count()).select_from(Ebook)
    if query:
        search_pattern = f"%{query}%"
        search_filter = or_(
            Source.title.ilike(search_pattern),
            Source.author.ilike(search_pattern)
        )
        stmt = stmt.join(Ebook.source).where(search_filter)
        count_stmt = count_stmt.join(Ebook.source).where(search_filter)
    stmt = stmt.offset(skip).limit(limit)
    return {
        "items": list(db.scalars(stmt).all()),
        "total": db.scalar(count_stmt) or 0
    }


@router.get("/{id}", response_model=EbookResponse)
def get_ebook(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin một ebook theo ID."""
    ebook = ebook_repo.get(db, id)
    if not ebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy ebook có ID = {id}"
        )
    return ebook


@router.post("", response_model=EbookResponse, status_code=status.HTTP_201_CREATED)
def create_ebook(ebook_in: EbookCreate, db: Session = Depends(get_db)):
    """Tạo mới một file ebook gắn với đầu sách (mỗi đầu sách tối đa 1 file số)."""
    return ebook_repo.create(db, obj_in=ebook_in)


@router.put("/{id}", response_model=EbookResponse)
def update_ebook(id: int, ebook_in: EbookUpdate, db: Session = Depends(get_db)):
    """Cập nhật dung lượng hoặc thông tin file ebook."""
    ebook = ebook_repo.get(db, id)
    if not ebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy ebook có ID = {id}"
        )
    return ebook_repo.update(db, db_obj=ebook, obj_in=ebook_in)


@router.delete("/{id}", response_model=EbookResponse)
def delete_ebook(id: int, db: Session = Depends(get_db)):
    """Xóa file ebook."""
    ebook = ebook_repo.get(db, id)
    if not ebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy ebook có ID = {id}"
        )
    return ebook_repo.remove(db, id=id)
