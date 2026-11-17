import datetime as dt
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReaderBase(BaseModel):
    full_name: str = Field(..., max_length=100, description="Họ và tên độc giả")
    date_of_birth: dt.date = Field(..., description="Ngày sinh (phải đủ 16 tuổi)")
    email: str = Field(
        ...,
        max_length=100,
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        description="Email độc giả (không trùng, định dạng hợp lệ)"
    )
    phone: Optional[str] = Field(None, max_length=20, description="Số điện thoại độc giả")
    national_id: Optional[str] = Field(None, max_length=12, description="Số CCCD (12 chữ số nếu có)")
    reader_type: Literal["Sinh vien", "Giang vien", "Nghien cuu sinh"] = Field(
        ...,
        description="Hạng độc giả: Sinh vien / Giang vien / Nghien cuu sinh"
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_age_at_least_16(cls, dob: dt.date) -> dt.date:
        today = dt.date.today()
        # Tính đủ 16 tuổi chính xác
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 16:
            raise ValueError("Độc giả phải đủ từ 16 tuổi trở lên theo quy định thư viện.")
        return dob


class ReaderCreate(ReaderBase):
    pass


class ReaderUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[dt.date] = None
    email: Optional[str] = Field(None, max_length=100, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    phone: Optional[str] = Field(None, max_length=20)
    national_id: Optional[str] = Field(None, max_length=12)
    reader_type: Optional[Literal["Sinh vien", "Giang vien", "Nghien cuu sinh"]] = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_age_if_present(cls, dob: Optional[dt.date]) -> Optional[dt.date]:
        if dob is not None:
            today = dt.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise ValueError("Độc giả phải đủ từ 16 tuổi trở lên.")
        return dob


class ReaderResponse(ReaderBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ReaderListResponse(BaseModel):
    items: List[ReaderResponse]
    total: int
