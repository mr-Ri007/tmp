import datetime as dt
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field


class FineAssessDamaged(BaseModel):
    return_record_id: int = Field(..., gt=0, description="Mã phiếu trả sách có tình trạng hỏng")
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Số tiền phạt do nhân viên quyết định (VNĐ > 0)")
    reason: str = Field(..., max_length=255, description="Chi tiết hư hại / lý do phạt")
    assessed_by: str = Field(..., max_length=100, description="Tên hoặc mã nhân viên thực hiện đánh giá")


class FinePayRequest(BaseModel):
    paid_at: Optional[dt.datetime] = Field(None, description="Thời điểm nộp phạt (mặc định lấy thời điểm hiện tại)")


class FineResponse(BaseModel):
    id: int
    return_record_id: int
    fine_type: Literal["Late", "Lost", "Damaged"]
    amount: Decimal
    reason: str
    created_at: dt.datetime
    late_amount: Decimal
    damaged_amount: Optional[Decimal] = None
    assessed_by: Optional[str] = None
    paid_at: Optional[dt.datetime] = None

    model_config = ConfigDict(from_attributes=True)
