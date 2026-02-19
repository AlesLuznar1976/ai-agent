from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class DBEmail(Base):
    __tablename__ = "Emaili"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    outlook_id = Column(String(255), unique=True, nullable=False)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=True)
    zadeva = Column(String(500), nullable=False)
    posiljatelj = Column(String(255), nullable=False)
    prejemniki = Column(Text, nullable=True)
    telo = Column(Text, nullable=True)
    kategorija = Column(String(50), nullable=False, default="Splosno")
    status = Column(String(50), nullable=False, default="Nov")
    datum = Column(DateTime, nullable=False)
    rfq_podkategorija = Column(String(50), nullable=True)
    izvleceni_podatki = Column(Text, nullable=True)
    priloge = Column(Text, nullable=True)
    analiza_status = Column(String(50), nullable=True)
    analiza_rezultat = Column(Text, nullable=True)

    projekt = relationship("DBProjekt", back_populates="emaili")
