from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.reader import Reader
from app.repositories.reader_repo import reader_repo
from app.schemas.reader import ReaderCreate, ReaderUpdate, ReaderResponse

router = APIRouter(prefix="/readers", tags=["Readers (Độc giả)"])


@router.get("", response_model=List[ReaderResponse])
def get_readers(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Tìm theo tên hoặc email"),
    reader_type: Optional[str] = Query(None, description="Lọc theo hạng: Sinh vien / Giang vien / Nghien cuu sinh"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách độc giả thư viện."""
    stmt = select(Reader)
    if query:
        stmt = stmt.where(Reader.full_name.ilike(f"%{query}%") | Reader.email.ilike(f"%{query}%"))
    if reader_type:
        stmt = stmt.where(Reader.reader_type == reader_type)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{id}", response_model=ReaderResponse)
def get_reader(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin chi tiết một độc giả theo ID."""
    reader = reader_repo.get(db, id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy độc giả có ID = {id}"
        )
    return reader


@router.post("", response_model=ReaderResponse, status_code=status.HTTP_201_CREATED)
def create_reader(reader_in: ReaderCreate, db: Session = Depends(get_db)):
    """Tạo mới tài khoản độc giả (Trigger kiểm tra đủ 16 tuổi)."""
    if reader_repo.get_by_email(db, reader_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{reader_in.email}' đã được đăng ký trong hệ thống."
        )
    if reader_in.national_id and reader_repo.get_by_national_id(db, reader_in.national_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Số CCCD '{reader_in.national_id}' đã tồn tại trong hệ thống."
        )
    return reader_repo.create(db, obj_in=reader_in)


@router.put("/{id}", response_model=ReaderResponse)
def update_reader(id: int, reader_in: ReaderUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin độc giả."""
    reader = reader_repo.get(db, id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy độc giả có ID = {id}"
        )
    return reader_repo.update(db, db_obj=reader, obj_in=reader_in)


@router.delete("/{id}", response_model=ReaderResponse)
def delete_reader(id: int, db: Session = Depends(get_db)):
    """Xóa độc giả (chỉ xóa được nếu chưa có lịch sử mượn/phạt)."""
    reader = reader_repo.get(db, id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy độc giả có ID = {id}"
        )
    try:
        return reader_repo.remove(db, id=id)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa độc giả do có dữ liệu liên quan: {e}"
        )
