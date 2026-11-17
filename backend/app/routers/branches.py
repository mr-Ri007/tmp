from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.branch import Branch
from app.repositories.base import CRUDBase
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse

router = APIRouter(prefix="/branches", tags=["Branches (Chi nhánh thư viện)"])
branch_repo = CRUDBase[Branch, BranchCreate, BranchUpdate](Branch)


@router.get("", response_model=List[BranchResponse])
def get_branches(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Lấy danh sách các chi nhánh thư viện."""
    return branch_repo.get_multi(db, skip=skip, limit=limit)


@router.get("/{id}", response_model=BranchResponse)
def get_branch(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin một chi nhánh theo ID."""
    branch = branch_repo.get(db, id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy chi nhánh có ID = {id}"
        )
    return branch


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(branch_in: BranchCreate, db: Session = Depends(get_db)):
    """Tạo mới một chi nhánh thư viện."""
    return branch_repo.create(db, obj_in=branch_in)


@router.put("/{id}", response_model=BranchResponse)
def update_branch(id: int, branch_in: BranchUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin chi nhánh."""
    branch = branch_repo.get(db, id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy chi nhánh có ID = {id}"
        )
    return branch_repo.update(db, db_obj=branch, obj_in=branch_in)


@router.delete("/{id}", response_model=BranchResponse)
def delete_branch(id: int, db: Session = Depends(get_db)):
    """Xóa chi nhánh thư viện."""
    branch = branch_repo.get(db, id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy chi nhánh có ID = {id}"
        )
    try:
        return branch_repo.remove(db, id=id)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa chi nhánh do còn sách đang đặt tại đây: {e}"
        )
