"""Các tiện ích bảo mật (security utilities).
Sẵn sàng mở rộng khi triển khai Authentication / JWT trong tương lai.
"""
import hashlib
import secrets


def generate_random_token(length: int = 32) -> str:
    """Sinh token ngẫu nhiên an toàn cho các tác vụ tạm thời."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Băm SHA-256 cho token hoặc mã kiểm tra."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
