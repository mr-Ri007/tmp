from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BranchBase(BaseModel):
    name: str = Field(..., max_length=100, description="Tên chi nhánh thư viện")
    address: str = Field(..., max_length=255, description="Địa chỉ vật lý chi nhánh")


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)


class BranchResponse(BranchBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
