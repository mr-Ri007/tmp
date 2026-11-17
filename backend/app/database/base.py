from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Lớp cơ sở trừu tượng cho toàn bộ SQLAlchemy Models (SQLAlchemy 2.0 style).
    
    Lưu ý quan trọng:
    Hệ thống KHÔNG sử dụng `Base.metadata.create_all()` vì database và trigger 
    đã được thiết kế và quản lý chính thức bằng các file SQL migration.
    """
    pass
