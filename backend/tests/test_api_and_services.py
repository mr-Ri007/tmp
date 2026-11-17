import sys
from pathlib import Path
from decimal import Decimal
import datetime as dt
import pytest
from pydantic import ValidationError

# Đảm bảo import được backend/app
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.reader import ReaderCreate
from app.schemas.source import SourceCreate
from app.schemas.fine import FineAssessDamaged
from app.schemas.hard_book import HardBookCreate
from app.schemas.loan import LoanCreate, ReturnRecordCreate
from app.schemas.reservation import ReservationCreate


def test_reader_validation_under_16_fails():
    """Kiểm tra Pydantic validation chặn độc giả dưới 16 tuổi."""
    today = dt.date.today()
    too_young_dob = dt.date(today.year - 15, today.month, today.day)
    with pytest.raises(ValidationError) as exc_info:
        ReaderCreate(
            full_name="Le Van Be",
            date_of_birth=too_young_dob,
            email="be@test.com",
            reader_type="Sinh vien"
        )
    assert "16 tuổi" in str(exc_info.value)


def test_reader_validation_16_succeeds():
    """Kiểm tra độc giả đủ 16 tuổi được chấp thuận."""
    today = dt.date.today()
    valid_dob = dt.date(today.year - 16, today.month, today.day)
    reader = ReaderCreate(
        full_name="Nguyen Van Du Tuoi",
        date_of_birth=valid_dob,
        email="dutuoi@test.com",
        reader_type="Sinh vien"
    )
    assert reader.full_name == "Nguyen Van Du Tuoi"


def test_source_validation_negative_price_fails():
    """Kiểm tra Source không cho phép giá âm."""
    with pytest.raises(ValidationError):
        SourceCreate(
            title="Sach Gia Am",
            author="Tac Gia",
            price=Decimal("-1000.00")
        )


def test_source_validation_publication_year_range():
    """Kiểm tra năm xuất bản trong khoảng 1000 - 2100."""
    with pytest.raises(ValidationError):
        SourceCreate(title="Sach Nam 500", author="Tac Gia", publication_year=500)
    with pytest.raises(ValidationError):
        SourceCreate(title="Sach Nam 3000", author="Tac Gia", publication_year=3000)


def test_fine_assess_damaged_validation():
    """Kiểm tra validation cho nghiệp vụ đánh giá sách hỏng."""
    # amount > 0
    with pytest.raises(ValidationError):
        FineAssessDamaged(
            return_record_id=1,
            amount=Decimal("0.00"),
            reason="Loi nhe",
            assessed_by="NV01"
        )

    # hop le
    fine_in = FineAssessDamaged(
        return_record_id=1,
        amount=Decimal("50000.00"),
        reason="Rach trang bia",
        assessed_by="NV_ThuThu_01"
    )
    assert fine_in.amount == Decimal("50000.00")
    assert fine_in.assessed_by == "NV_ThuThu_01"


def test_hard_book_status_constraint():
    """Kiểm tra trạng thái bản sao sách chỉ nhận SanSang / DangCho / DangMuon."""
    with pytest.raises(ValidationError):
        HardBookCreate(source_id=1, branch_id=1, status="Hong")  # Không có trong enum status

    valid_book = HardBookCreate(source_id=1, branch_id=1, status="SanSang")
    assert valid_book.status == "SanSang"
