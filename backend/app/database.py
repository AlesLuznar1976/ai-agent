"""
Database modul - SQLAlchemy engine, session in base za ai_agent sistem.
Povezava na SQL Server (LUZNAR baza, ai_agent shema).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings


settings = get_settings()


# SQLAlchemy engine za MSSQL
# fast_executemany za hitrejše bulk inserte
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # SQL logging v development
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # recycle connections po 30min
    pool_pre_ping=True,  # preveri povezavo pred uporabo
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base razred za vse ORM modele"""
    pass


def get_db():
    """
    Dependency za FastAPI - vrne DB session.
    Uporaba:
        @router.get("/")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """Preveri povezavo do baze"""
    try:
        with engine.connect() as conn:
            conn.execute(
                __import__('sqlalchemy').text("SELECT 1")
            )
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
