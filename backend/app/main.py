import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, InterfaceError

from app.core.config import settings
from app.database.connection import check_db_connection
from app.database.base import Base

# Import all models to register them with Base.metadata
import app.models  # noqa: F401

# Import API Routers
from app.routers import (
    sources_router,
    hard_books_router,
    ebooks_router,
    readers_router,
    branches_router,
    courses_router,
    circulation_router,
    fines_router,
    access_logs_router,
)

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng FastAPI."""
    logger.info("Khởi động ứng dụng Library Management System Backend...")
    logger.info(f"Đã đăng ký {len(Base.metadata.tables)} bảng trong SQLAlchemy Models.")
    yield
    logger.info("Dừng ứng dụng Library Management System Backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


@app.exception_handler(DBAPIError)
async def handle_database_error(request: Request, exc: DBAPIError):
    error_args = getattr(exc.orig, "args", ())
    mysql_error_code = error_args[0] if error_args else None
    check_constraint_failed = mysql_error_code == 3819
    logger.error(
        "Database request failed (%s)",
        type(exc.orig).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    unavailable = (
        exc.connection_invalidated
        or isinstance(exc, InterfaceError)
        or mysql_error_code in {2002, 2003, 2006, 2013, 2055}
    )
    if check_constraint_failed:
        detail = (
            "Cơ sở dữ liệu từ chối dữ liệu do ràng buộc CHECK. "
            "Hãy xem tên constraint trong log backend; nếu lỗi xảy ra khi trả sách mất, "
            "chạy lại migration_lost_hard_book_status.sql."
        )
    elif unavailable:
        detail = (
            "Kết nối cơ sở dữ liệu bị gián đoạn. Hãy kiểm tra trạng thái backend/database "
            "trước khi thử lại để tránh gửi thao tác ghi trùng."
        )
    else:
        detail = "Thao tác cơ sở dữ liệu thất bại. Vui lòng kiểm tra log backend."

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE if unavailable else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


# Cấu hình CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Đăng ký các API Routers
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(hard_books_router, prefix=settings.API_V1_STR)
app.include_router(ebooks_router, prefix=settings.API_V1_STR)
app.include_router(readers_router, prefix=settings.API_V1_STR)
app.include_router(branches_router, prefix=settings.API_V1_STR)
app.include_router(courses_router, prefix=settings.API_V1_STR)
app.include_router(circulation_router, prefix=settings.API_V1_STR)
app.include_router(fines_router, prefix=settings.API_V1_STR)
app.include_router(access_logs_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["General"])
def root():
    """Endpoint gốc cung cấp thông tin hệ thống và đường dẫn tới Swagger UI."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_v1_prefix": settings.API_V1_STR,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "status": "running"
    }


@app.get("/health", tags=["General"])
def health_check():
    """Kiểm tra sức khỏe hệ thống và trạng thái kết nối MySQL Database."""
    db_info = check_db_connection()
    is_healthy = db_info.get("status") == "connected"
    
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "app_status": "healthy",
            "database": db_info,
            "registered_models_count": len(Base.metadata.tables)
        }
    )


@app.get(f"{settings.API_V1_STR}/meta/tables", tags=["System Meta"])
def list_mapped_tables():
    """Liệt kê danh sách toàn bộ các bảng và cột đã được ánh xạ bởi SQLAlchemy Models."""
    tables_meta = {}
    for table_name, table_obj in Base.metadata.tables.items():
        tables_meta[table_name] = {
            "columns": [
                {
                    "name": col.name,
                    "type": str(col.type),
                    "primary_key": col.primary_key,
                    "nullable": col.nullable,
                    "foreign_keys": [str(fk.target_fullname) for fk in col.foreign_keys]
                }
                for col in table_obj.columns
            ]
        }
    return {
        "total_tables": len(tables_meta),
        "tables": tables_meta
    }
