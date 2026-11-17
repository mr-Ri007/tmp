from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.hard_book_repo import hard_book_repo
from app.schemas.hard_book import HardBookCreate, HardBookUpdate, HardBookResponse

router = APIRouter(prefix="/hard-books", tags=["Hard Books (Bản sao vật lý)"])


@router.get("", response_model=List[HardBookResponse])
def get_hard_books(
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Query(None, description="Lọc theo chi nhánh"),
    source_id: Optional[int] = Query(None, description="Lọc theo đầu sách"),
    book_status: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái (SanSang, DangCho, DangMuon)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách các bản sao sách vật lý."""
    return hard_book_repo.get_by_branch_and_status(
        db,
        branch_id=branch_id,
        source_id=source_id,
        status=book_status,
        skip=skip,
        limit=limit
    )


@router.get("/{id}", response_model=HardBookResponse)
def get_hard_book(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin một bản sao sách vật lý theo ID/mã vạch."""
    book = hard_book_repo.get(db, id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bản sao sách có ID = {id}"
        )
    return book


@router.post("", response_model=HardBookResponse, status_code=status.HTTP_201_CREATED)
def create_hard_book(book_in: HardBookCreate, db: Session = Depends(get_db)):
    """Tạo mới một bản sao sách vật lý tại một chi nhánh."""
    return hard_book_repo.create(db, obj_in=book_in)


@router.put("/{id}", response_model=HardBookResponse)
def update_hard_book(id: int, book_in: HardBookUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin bản sao sách vật lý (chi nhánh hoặc trạng thái)."""
    book = hard_book_repo.get(db, id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bản sao sách có ID = {id}"
        )
    return hard_book_repo.update(db, db_obj=book, obj_in=book_in)


@router.delete("/{id}", response_model=HardBookResponse)
def delete_hard_book(id: int, db: Session = Depends(get_db)):
    """Xóa một bản sao sách vật lý."""
    book = hard_book_repo.get(db, id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bản sao sách có ID = {id}"
        )
    try:
        return hard_book_repo.remove(db, id=id)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa bản sao sách do có ràng buộc lượt mượn: {e}"
        )
