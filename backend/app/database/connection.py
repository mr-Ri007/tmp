from typing import Generator
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Tạo SQLAlchemy 2.0 Engine kết nối tới MySQL
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"connect_timeout": 3},
    pool_pre_ping=True,      # Tự động kiểm tra và kết nối lại nếu connection bị đứt
    pool_recycle=3600,       # Tái tạo connection sau 1 giờ để tránh timeout MySQL
    echo=settings.DEBUG,     # Hiển thị SQL query trong log khi ở chế độ DEBUG
)

# Factory tạo database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency cung cấp database session độc lập cho từng request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict:
    """Hàm kiểm tra trạng thái kết nối tới MySQL Database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS connected, DATABASE() AS db_name, VERSION() AS mysql_version")).mappings().one()
            return {
                "status": "connected",
                "database": result["db_name"],
                "version": result["mysql_version"]
            }
    except Exception as e:
        logger.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        return {
            "status": "disconnected",
            "error": str(e)
        }
