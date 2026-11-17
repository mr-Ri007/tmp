from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ebook import Ebook
from app.repositories.base import CRUDBase
from app.schemas.ebook import EbookCreate, EbookUpdate, EbookResponse

router = APIRouter(prefix="/ebooks", tags=["Ebooks (Bản mềm / Tài liệu số)"])
ebook_repo = CRUDBase[Ebook, EbookCreate, EbookUpdate](Ebook)


@router.get("", response_model=List[EbookResponse])
def get_ebooks(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách các bản mềm ebook."""
    return ebook_repo.get_multi(db, skip=skip, limit=limit)


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
