from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Library Management System API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend API cho Hệ thống Quản lý Thư viện Số Đa Chi Nhánh (FastAPI + SQLAlchemy 2.0 + MySQL 8.4)"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database connection parameters
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "library"
    DATABASE_URL: str | None = None

    # CORS configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",  # Live server phổ biến cho vanilla HTML/JS
        "http://127.0.0.1:5500",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Tạo chuỗi kết nối chuẩn pymysql với utf8mb4
        # Mã hóa an toàn pass nếu có ký tự đặc biệt
        from urllib.parse import quote_plus
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{user}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
