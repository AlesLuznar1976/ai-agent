from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBUporabnik(Base):
    __tablename__ = "Uporabniki"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100))
    ime = Column(String(100))
    priimek = Column(String(100))
    vloga = Column(String(50), nullable=False, default="readonly")
    aktiven = Column(Boolean, default=True)
    datum_ustvarjen = Column(DateTime, default=datetime.now)
    zadnja_prijava = Column(DateTime, nullable=True)
    push_token = Column(String(255), nullable=True)

    projekti_prodaja = relationship("DBProjekt", foreign_keys="DBProjekt.odgovorni_prodaja", back_populates="prodajalec")
    projekti_tehnolog = relationship("DBProjekt", foreign_keys="DBProjekt.odgovorni_tehnolog", back_populates="tehnolog")
    seje = relationship("DBAktivnaSeja", back_populates="uporabnik", cascade="all, delete-orphan")
    obvestila = relationship("DBObvestilo", back_populates="uporabnik", cascade="all, delete-orphan")
