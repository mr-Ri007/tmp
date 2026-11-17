from app.routers.sources import router as sources_router
from app.routers.hard_books import router as hard_books_router
from app.routers.ebooks import router as ebooks_router
from app.routers.readers import router as readers_router
from app.routers.branches import router as branches_router
from app.routers.courses import router as courses_router
from app.routers.circulation import router as circulation_router
from app.routers.fines import router as fines_router
from app.routers.access_logs import router as access_logs_router

__all__ = [
    "sources_router",
    "hard_books_router",
    "ebooks_router",
    "readers_router",
    "branches_router",
    "courses_router",
    "circulation_router",
    "fines_router",
    "access_logs_router",
]
