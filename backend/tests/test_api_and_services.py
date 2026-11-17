import sys
from pathlib import Path
from decimal import Decimal
import datetime as dt
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

# Đảm bảo import được backend/app
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.reader import ReaderCreate
from app.schemas.source import SourceCreate
from app.schemas.fine import FineAssessDamaged
from app.schemas.hard_book import HardBookCreate, HardBookListResponse
from app.schemas.loan import LoanCreate, ReturnRecordCreate
from app.schemas.reservation import ReservationCreate
from app.routers.circulation import get_loan_history
from app.routers.fines import get_fines_page
from app.repositories.fine_repo import fine_repo
from app.schemas.fine import FinePageResponse
from app.services.loan_service import LoanService
from app.services.reservation_service import ReservationService
from app.services.renewal_service import RenewalService
from app.services.return_service import ReturnService


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


def test_reader_phone_is_optional():
    today = dt.date.today()
    reader = ReaderCreate(
        full_name="Nguyen Van Co So",
        date_of_birth=dt.date(today.year - 20, today.month, today.day),
        email="coso@test.com",
        reader_type="Sinh vien",
        phone="0912345678"
    )
    assert reader.phone == "0912345678"


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
    """Kiểm tra trạng thái bản sao, bao gồm bản sao đã mất."""
    with pytest.raises(ValidationError):
        HardBookCreate(source_id=1, branch_id=1, status="Hong")  # Không có trong enum status

    valid_book = HardBookCreate(source_id=1, branch_id=1, status="SanSang")
    assert valid_book.status == "SanSang"
    lost_book = HardBookCreate(source_id=1, branch_id=1, status="MatSach")
    assert lost_book.status == "MatSach"


def test_lost_hard_book_cannot_be_borrowed():
    class FakeDB:
        def get(self, model, item_id):
            return SimpleNamespace(reader_type="Sinh vien")

        def scalar(self, statement):
            return SimpleNamespace(status="MatSach")

    with pytest.raises(HTTPException) as exc_info:
        LoanService.borrow_book(FakeDB(), reader_id=1, hard_book_id=7)

    assert exc_info.value.status_code == 400
    assert "đã được ghi nhận là mất" in exc_info.value.detail


def test_borrow_flushes_loan_before_marking_book_as_borrowed(monkeypatch):
    reader = SimpleNamespace(reader_type="Giang vien")
    book = SimpleNamespace(status="SanSang")
    monkeypatch.setattr(
        fine_repo, "get_unpaid_sum_by_reader", lambda db, reader_id: Decimal("0")
    )

    class FakeDB:
        def __init__(self):
            self.scalar_results = iter([book, None])
            self.loan = None
            self.flushed = False

        def get(self, model, item_id):
            return reader

        def scalar(self, statement):
            return next(self.scalar_results)

        def add(self, item):
            self.loan = item

        def flush(self):
            assert self.loan is not None
            assert book.status == "SanSang"
            self.flushed = True

        def commit(self):
            assert self.flushed
            assert book.status == "DangMuon"

        def refresh(self, item):
            item.id = 1

    loan = LoanService.borrow_book(
        FakeDB(), reader_id=1, hard_book_id=7, days=14
    )

    assert loan.id == 1
    assert book.status == "DangMuon"


def test_reserve_flushes_reservation_before_marking_book_reserved():
    reader = SimpleNamespace(id=1)
    book = SimpleNamespace(status="SanSang")

    class FakeDB:
        def __init__(self):
            self.reservation = None
            self.flushed = False

        def get(self, model, item_id):
            return reader

        def scalar(self, statement):
            return book

        def add(self, item):
            self.reservation = item

        def flush(self):
            assert self.reservation is not None
            assert book.status == "SanSang"
            self.flushed = True

        def commit(self):
            assert self.flushed
            assert book.status == "DangCho"

        def refresh(self, item):
            item.id = 1

    reservation = ReservationService.reserve_book(
        FakeDB(), reader_id=1, hard_book_id=7, days=3
    )

    assert reservation.id == 1
    assert book.status == "DangCho"


def test_renew_flushes_history_before_updating_loan_due_date():
    old_due = dt.datetime(2025, 1, 15, 10, 0)
    loan = SimpleNamespace(due_at=old_due)

    class FakeDB:
        def __init__(self):
            self.scalar_results = iter([loan, None])
            self.renewal = None
            self.flushed = False

        def scalar(self, statement):
            return next(self.scalar_results)

        def add(self, item):
            self.renewal = item

        def flush(self):
            assert self.renewal is not None
            assert loan.due_at == old_due
            self.flushed = True

        def commit(self):
            assert self.flushed
            assert loan.due_at == old_due + dt.timedelta(days=7)

        def refresh(self, item):
            item.id = 1

    renewal = RenewalService.renew_book(
        FakeDB(), loan_id=1, extension_days=7
    )

    assert renewal.id == 1
    assert renewal.old_due_at == old_due
    assert renewal.new_due_at == old_due + dt.timedelta(days=7)
    assert loan.due_at == renewal.new_due_at


def test_returning_lost_book_marks_copy_unavailable():
    borrowed_at = dt.datetime(2025, 1, 1, 10, 0)
    loan = SimpleNamespace(id=1, hard_book_id=7, borrowed_at=borrowed_at)
    book = SimpleNamespace(status="DangMuon")

    class FakeDB:
        def __init__(self):
            self.scalar_results = iter([loan, None, None])

        def scalar(self, statement):
            return next(self.scalar_results)

        def get(self, model, item_id):
            return book

        def add(self, item):
            pass

        def commit(self):
            pass

        def refresh(self, item):
            item.id = 9

    result, fine = ReturnService.return_book(
        FakeDB(),
        loan_id=1,
        return_condition="Mat",
        returned_at=dt.datetime(2025, 1, 2, 10, 0),
    )

    assert result.id == 9
    assert fine is None
    assert book.status == "MatSach"


def test_hard_book_list_includes_book_and_branch_details():
    response = HardBookListResponse.model_validate({
        "items": [{
            "id": 12,
            "source_id": 3,
            "branch_id": 2,
            "status": "SanSang",
            "source": {
                "id": 3,
                "title": "Sách mẫu",
                "author": "Tác giả",
                "price": "120000.00",
            },
            "branch": {
                "id": 2,
                "name": "Chi nhánh 2",
                "address": "Địa chỉ",
            },
        }],
        "total": 1,
    })

    assert response.total == 1
    assert response.items[0].source.title == "Sách mẫu"
    assert response.items[0].branch.name == "Chi nhánh 2"


def test_fines_page_returns_filtered_count(monkeypatch):
    fine = {
        "id": 1,
        "return_record_id": 2,
        "fine_type": "Late",
        "amount": Decimal("1000.00"),
        "reason": "Quá hạn",
        "created_at": dt.datetime(2025, 1, 1),
        "late_amount": Decimal("1000.00"),
    }
    monkeypatch.setattr(fine_repo, "get_multi", lambda db, **kwargs: [fine])
    monkeypatch.setattr(fine_repo, "get_count", lambda db, **kwargs: 51)

    result = get_fines_page(
        db=object(),
        reader_id=7,
        unpaid_only=True,
        fine_type="Late",
        skip=50,
        limit=50,
    )

    assert FinePageResponse.model_validate(result).total == 51
    assert result["items"] == [fine]


def test_loan_history_stats_cover_selected_month_and_full_result():
    class FakeResult:
        def __init__(self, rows):
            self.rows = rows

        def mappings(self):
            return self

        def one(self):
            return self.rows

        def all(self):
            return self.rows

    class FakeDB:
        def __init__(self):
            self.calls = []

        def execute(self, query, params):
            sql = str(query)
            self.calls.append((sql, params))
            if "AS total_loans" in sql:
                row = {"total_loans": 8, "member_count": 3, "returned_loans": 5}
            elif "AS reader_name" in sql and "loan_count" in sql:
                row = [{"reader_id": 4, "reader_name": "Hội viên A", "loan_count": 4}]
            elif "AS source_id" in sql:
                row = [{"source_id": 9, "title": "Sách A", "loan_count": 3}]
            else:
                row = [{"id": 2, "reader_id": 4, "reader_name": "Hội viên A"}]
            return FakeResult(row)

    db = FakeDB()
    result = get_loan_history(month=12, year=2024, skip=0, limit=1, db=db)

    assert result["total"] == 8
    assert result["stats"]["active_loans"] == 3
    assert result["stats"]["top_readers"][0]["loan_count"] == 4
    assert result["items"][0]["reader_name"] == "Hội viên A"
    assert all(call[1]["start"] == dt.datetime(2024, 12, 1) for call in db.calls)
    assert all(call[1]["end"] == dt.datetime(2025, 1, 1) for call in db.calls)
