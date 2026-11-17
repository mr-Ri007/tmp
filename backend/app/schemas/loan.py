import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LoanBase(BaseModel):
    reader_id: int = Field(..., gt=0, description="Mã độc giả mượn")
    hard_book_id: int = Field(..., gt=0, description="Mã bản sao sách vật lý")
    borrowed_at: dt.datetime = Field(default_factory=dt.datetime.now, description="Thời điểm mượn")
    due_at: dt.datetime = Field(..., description="Hạn trả sách")


class LoanCreate(BaseModel):
    reader_id: int = Field(..., gt=0, description="Mã độc giả mượn")
    hard_book_id: int = Field(..., gt=0, description="Mã bản sao sách cần mượn")
    days: Optional[int] = Field(
        None,
        gt=0,
        le=60,
        description="Số ngày mượn (để trống sẽ tự tính: 14 ngày cho SV, 30 ngày cho GV/NCS)"
    )


class LoanResponse(LoanBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RenewalCreate(BaseModel):
    loan_id: int = Field(..., gt=0, description="Mã lượt mượn cần gia hạn")
    extension_days: int = Field(7, gt=0, le=30, description="Số ngày gia hạn thêm (mặc định 7 ngày)")


class RenewalResponse(BaseModel):
    id: int
    loan_id: int
    old_due_at: dt.datetime
    new_due_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class ReturnRecordCreate(BaseModel):
    loan_id: int = Field(..., gt=0, description="Mã lượt mượn cần trả")
    return_condition: str = Field("Tot", description="Tình trạng sách khi trả: Tot / Hong / Mat")
    returned_at: Optional[dt.datetime] = Field(None, description="Thời điểm trả (để trống sẽ lấy thời điểm hiện tại)")


class ReturnRecordResponse(BaseModel):
    id: int
    loan_id: int
    return_code: str
    returned_at: dt.datetime
    return_condition: str

    model_config = ConfigDict(from_attributes=True)
