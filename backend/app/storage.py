from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from .config import settings

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(40), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

engine = create_engine(settings.database_url, pool_pre_ping=True)

def initialize():
    Base.metadata.create_all(engine)

def save_documents(documents):
    with Session(engine) as session:
        # Replace the curated index so repeated ingestion does not accumulate stale chunks.
        for doc in session.scalars(select(Document)):
            session.delete(doc)
        session.flush()
        for doc in documents:
            session.add(Document(**{key: doc[key] for key in ['id', 'dataset', 'kind', 'source', 'content']}, ingested_at=datetime.now(timezone.utc)))
        session.commit()
