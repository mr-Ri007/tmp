from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories.source_repo import source_repo
from app.schemas.source import SourceCreate, SourceListResponse, SourceUpdate, SourceResponse

router = APIRouter(prefix="/sources", tags=["Sources (Tài liệu / Đầu sách)"])


@router.get("", response_model=SourceListResponse)
def get_sources(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Tìm kiếm theo tên sách hoặc tác giả"),
    genre: Optional[str] = Query(None, description="Lọc theo thể loại"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách đầu sách có hỗ trợ tìm kiếm và phân trang."""
    return {
        "items": source_repo.search(db, query=query, genre=genre, skip=skip, limit=limit),
        "total": source_repo.count(db, query=query, genre=genre)
    }


@router.get("/{id}", response_model=SourceResponse)
def get_source(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin chi tiết một đầu sách theo ID."""
    source = source_repo.get(db, id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tài liệu có ID = {id}"
        )
    return source


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(source_in: SourceCreate, db: Session = Depends(get_db)):
    """Tạo mới một đầu sách."""
    return source_repo.create(db, obj_in=source_in)


@router.put("/{id}", response_model=SourceResponse)
def update_source(id: int, source_in: SourceUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin đầu sách (tên, tác giả, giá bìa, thể loại,...)."""
    source = source_repo.get(db, id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tài liệu có ID = {id}"
        )
    return source_repo.update(db, db_obj=source, obj_in=source_in)


@router.delete("/{id}", response_model=SourceResponse)
def delete_source(id: int, db: Session = Depends(get_db)):
    """Xóa một đầu sách (sẽ bị chặn nếu đã có bản sao hoặc giáo trình ràng buộc)."""
    source = source_repo.get(db, id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tài liệu có ID = {id}"
        )
    try:
        return source_repo.remove(db, id=id)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa tài liệu này do có ràng buộc dữ liệu: {e}"
        )
