import datetime as dt
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field


class ReservationCreate(BaseModel):
    reader_id: int = Field(..., gt=0, description="Mã độc giả đặt trước")
    hard_book_id: int = Field(..., gt=0, description="Mã bản sao sách vật lý cần đặt trước (phải đang SanSang)")
    days: int = Field(3, gt=0, le=7, description="Số ngày giữ chỗ đến hạn nhận (mặc định 3 ngày)")


class ReservationUpdateStatus(BaseModel):
    status: Literal["DaNhan", "HetHan", "Huy"] = Field(..., description="Trạng thái cập nhật")


class ReservationResponse(BaseModel):
    id: int
    reader_id: int
    hard_book_id: int
    reserved_at: dt.datetime
    pickup_deadline: dt.datetime
    status: str

    model_config = ConfigDict(from_attributes=True)
