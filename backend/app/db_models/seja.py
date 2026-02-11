"""SQLAlchemy model za ai_agent.AktivneSeje tabelo"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DBAktivnaSeja(Base):
    __tablename__ = "AktivneSeje"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ai_agent.Uporabniki.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=True)
    naprava = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    datum_ustvarjen = Column(DateTime, default=datetime.now)
    datum_poteka = Column(DateTime, nullable=True)

    # Relationships
    uporabnik = relationship("DBUporabnik", back_populates="seje")
