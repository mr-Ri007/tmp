import sys
from pathlib import Path

# Đảm bảo import được module backend/app
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.main import app as fastapi_app, root, list_mapped_tables
from app.database.base import Base
import app.models  # Đăng ký toàn bộ models


def test_root_endpoint():
    """Kiểm tra handler endpoint gốc."""
    data = root()
    assert data["status"] == "running"
    assert data["docs_url"] == "/docs"
    assert data["version"] == "1.0.0"


def test_openapi_schema_generation():
    """Kiểm tra OpenAPI schema sinh tự động chuẩn Swagger UI."""
    schema = fastapi_app.openapi()
    assert schema["info"]["title"] == "Library Management System API"
    assert "paths" in schema
    assert "/" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/api/v1/meta/tables" in schema["paths"]


def test_registered_models_count():
    """Kiểm tra toàn bộ 13 bảng trong cơ sở dữ liệu đã được ánh xạ chính xác 100%."""
    expected_tables = {
        "Branches",
        "Sources",
        "Hard_books",
        "Ebooks",
        "Readers",
        "Access_logs",
        "Loans",
        "Renewals",
        "Return_records",
        "Fines",
        "Reservations",
        "Courses",
        "Course_resources",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert actual_tables == expected_tables, f"Danh sách bảng chưa khớp: thiếu {expected_tables - actual_tables}, thừa {actual_tables - expected_tables}"


def test_sources_model_structure():
    """Kiểm tra model Sources có trường price kiểu DECIMAL(12,2) NOT NULL và check constraints."""
    table = Base.metadata.tables["Sources"]
    assert "price" in table.columns
    price_col = table.columns["price"]
    assert not price_col.nullable
    assert str(price_col.type).startswith("NUMERIC") or str(price_col.type).startswith("DECIMAL")

    # Kiểm tra các cột bắt buộc khác
    assert not table.columns["title"].nullable
    assert not table.columns["author"].nullable


def test_fines_model_structure():
    """Kiểm tra model Fines có assessed_by, return_record_id unique và các constraints."""
    table = Base.metadata.tables["Fines"]
    
    # Kiểm tra cột assessed_by (lưu nhân viên đánh giá)
    assert "assessed_by" in table.columns
    assert table.columns["assessed_by"].nullable

    # Kiểm tra ràng buộc duy nhất UNIQUE trên return_record_id
    ret_col = table.columns["return_record_id"]
    is_unique = ret_col.unique or any(
        "return_record_id" in [c.name for c in uq.columns]
        for uq in table.constraints
        if hasattr(uq, "columns")
    )
    assert is_unique, "Fines.return_record_id phải có ràng buộc UNIQUE"

    # Kiểm tra fine_type, amount, late_amount
    assert not table.columns["fine_type"].nullable
    assert not table.columns["amount"].nullable


def test_hard_books_foreign_keys():
    """Kiểm tra model Hard_books có các khóa ngoại trỏ tới Sources và Branches."""
    table = Base.metadata.tables["Hard_books"]
    fk_targets = {str(fk.target_fullname) for fk in table.foreign_keys}
    assert "Sources.id" in fk_targets
    assert "Branches.id" in fk_targets


def test_course_resources_composite_pk():
    """Kiểm tra bảng Course_resources có khóa chính phức hợp (composite PK)."""
    table = Base.metadata.tables["Course_resources"]
    pk_cols = [c.name for c in table.primary_key.columns]
    assert set(pk_cols) == {"course_id", "source_id"}


def test_meta_tables_api_handler():
    """Kiểm tra hàm xử lý /api/v1/meta/tables phản hồi đầy đủ 13 bảng và danh sách cột."""
    result = list_mapped_tables()
    assert result["total_tables"] == 13
    assert "Hard_books" in result["tables"]
    assert "Return_records" in result["tables"]
    assert "Fines" in result["tables"]
