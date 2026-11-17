from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.branch import BranchResponse
from app.schemas.source import SourceResponse


class HardBookBase(BaseModel):
    source_id: int = Field(..., gt=0, description="Mã tài liệu")
    branch_id: int = Field(..., gt=0, description="Mã chi nhánh")
    status: Literal["SanSang", "DangCho", "DangMuon"] = Field(
        default="SanSang",
        description="Trạng thái bản sao vật lý"
    )


class HardBookCreate(HardBookBase):
    pass


class HardBookUpdate(BaseModel):
    branch_id: Optional[int] = Field(None, gt=0)
    status: Optional[Literal["SanSang", "DangCho", "DangMuon"]] = None


class HardBookResponse(HardBookBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class HardBookDetailResponse(HardBookResponse):
    source: Optional[SourceResponse] = None
    branch: Optional[BranchResponse] = None
