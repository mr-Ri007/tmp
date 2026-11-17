from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.source import SourceResponse


class EbookBase(BaseModel):
    source_id: int = Field(..., gt=0, description="Mã tài liệu tương ứng (1-1)")
    file_size_mb: Optional[int] = Field(None, gt=0, description="Dung lượng file (MB)")


class EbookCreate(EbookBase):
    pass


class EbookUpdate(BaseModel):
    file_size_mb: Optional[int] = Field(None, gt=0)


class EbookResponse(EbookBase):
    id: int
    source: Optional[SourceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class EbookDetailResponse(EbookResponse):
    source: Optional[SourceResponse] = None


class EbookListResponse(BaseModel):
    items: List[EbookResponse]
    total: int
