from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate
from app.repositories.base import CRUDBase


class CRUDSource(CRUDBase[Source, SourceCreate, SourceUpdate]):
    def search(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Source]:
        stmt = select(Source)
        if query:
            stmt = stmt.where(
                or_(
                    Source.title.ilike(f"%{query}%"),
                    Source.author.ilike(f"%{query}%")
                )
            )
        if genre:
            stmt = stmt.where(Source.genre == genre)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())


source_repo = CRUDSource(Source)
