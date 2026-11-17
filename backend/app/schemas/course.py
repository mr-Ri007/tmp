from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.source import SourceResponse


class CourseBase(BaseModel):
    name: str = Field(..., max_length=100, description="Tên môn học (không trùng)")


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)


class CourseResponse(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CourseResourceCreate(BaseModel):
    course_id: int = Field(..., gt=0)
    source_id: int = Field(..., gt=0)
    is_required: bool = Field(True, description="TRUE = giáo trình bắt buộc, FALSE = tham khảo")


class CourseResourceResponse(BaseModel):
    course_id: int
    source_id: int
    is_required: bool
    source: Optional[SourceResponse] = None

    model_config = ConfigDict(from_attributes=True)
