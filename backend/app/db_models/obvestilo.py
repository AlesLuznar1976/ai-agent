"""SQLAlchemy model za ai_agent.Obvestila tabelo"""

from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DBObvestilo(Base):
    __tablename__ = "Obvestila"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ai_agent.Uporabniki.id", ondelete="CASCADE"), nullable=False)
    tip = Column(String(50), nullable=False)
    naslov = Column(String(200), nullable=False)
    sporocilo = Column(String(500), nullable=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=True)
    prioriteta = Column(String(20), default="normal")
    prebrano = Column(Boolean, default=False)
    akcija_potrebna = Column(Boolean, default=False)
    datum = Column(DateTime, default=datetime.now)

    # Relationships
    uporabnik = relationship("DBUporabnik", back_populates="obvestila")
    projekt = relationship("DBProjekt", back_populates="obvestila")
