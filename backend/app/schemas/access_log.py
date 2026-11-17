import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AccessLogStart(BaseModel):
    reader_id: int = Field(..., gt=0, description="Mã độc giả truy cập")
    ebook_id: int = Field(..., gt=0, description="Mã bản mềm ebook")


class AccessLogEnd(BaseModel):
    ended_at: Optional[dt.datetime] = Field(None, description="Thời điểm kết thúc đọc")


class AccessLogResponse(BaseModel):
    id: int
    reader_id: int
    ebook_id: int
    started_at: dt.datetime
    ended_at: Optional[dt.datetime] = None

    model_config = ConfigDict(from_attributes=True)
