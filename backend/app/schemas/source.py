from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    title: str = Field(..., max_length=255, description="Tên tác phẩm / nhan đề sách")
    author: str = Field(..., max_length=100, description="Tên tác giả")
    genre: Optional[str] = Field(None, max_length=50, description="Thể loại sách")
    publication_year: Optional[int] = Field(None, ge=1000, le=2100, description="Năm xuất bản (1000-2100)")
    page_count: Optional[int] = Field(None, gt=0, description="Số trang (> 0)")
    price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Giá bìa hiện tại (VNĐ >= 0)")


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=100)
    genre: Optional[str] = Field(None, max_length=50)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    page_count: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))


class SourceResponse(SourceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
