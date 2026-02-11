#!/usr/bin/env python3
"""
Skript za deploy DB integracijskih datotek na Ubuntu strežnik.
Zaženite na Ubuntu strežniku:
    python3 ~/ai-agent/deploy_db_update.py
"""

import os

BASE = os.path.expanduser("~/ai-agent/backend/app")

# Ustvari direktorije
os.makedirs(f"{BASE}/db_models", exist_ok=True)
os.makedirs(f"{BASE}/crud", exist_ok=True)

files = {}

# ============================================================
# database.py
# ============================================================
files[f"{BASE}/database.py"] = '''"""
Database modul - SQLAlchemy engine, session in base za ai_agent sistem.
Povezava na SQL Server (LUZNAR baza, ai_agent shema).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings


settings = get_settings()


# SQLAlchemy engine za MSSQL
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base razred za vse ORM modele"""
    pass


def get_db():
    """Dependency za FastAPI - vrne DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """Preveri povezavo do baze"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
'''

# ============================================================
# db_models/__init__.py
# ============================================================
files[f"{BASE}/db_models/__init__.py"] = '''"""SQLAlchemy ORM modeli za ai_agent shemo."""

from app.db_models.uporabnik import DBUporabnik
from app.db_models.projekt import DBProjekt
from app.db_models.email import DBEmail
from app.db_models.dokument import DBDokument
from app.db_models.akcija import DBCakajocaAkcija
from app.db_models.delovni_nalog import DBDelovniNalog
from app.db_models.calcuquote import DBCalcuQuoteRFQ
from app.db_models.casovnica import DBProjektCasovnica
from app.db_models.audit import DBAuditLog
from app.db_models.seja import DBAktivnaSeja
from app.db_models.obvestilo import DBObvestilo

__all__ = [
    "DBUporabnik", "DBProjekt", "DBEmail", "DBDokument",
    "DBCakajocaAkcija", "DBDelovniNalog", "DBCalcuQuoteRFQ",
    "DBProjektCasovnica", "DBAuditLog", "DBAktivnaSeja", "DBObvestilo",
]
'''

# ============================================================
# db_models/uporabnik.py
# ============================================================
files[f"{BASE}/db_models/uporabnik.py"] = '''from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
'''

# ============================================================
# db_models/projekt.py
# ============================================================
files[f"{BASE}/db_models/projekt.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBProjekt(Base):
    __tablename__ = "Projekti"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    stevilka_projekta = Column(String(50), unique=True, nullable=False)
    naziv = Column(String(255), nullable=False)
    stranka_id = Column(Integer, nullable=True)
    faza = Column(String(50), nullable=False, default="RFQ")
    status = Column(String(50), nullable=False, default="Aktiven")
    datum_rfq = Column(DateTime, nullable=False, default=datetime.now)
    datum_zakljucka = Column(DateTime, nullable=True)
    odgovorni_prodaja = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    odgovorni_tehnolog = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    opombe = Column(Text, nullable=True)

    prodajalec = relationship("DBUporabnik", foreign_keys=[odgovorni_prodaja], back_populates="projekti_prodaja")
    tehnolog = relationship("DBUporabnik", foreign_keys=[odgovorni_tehnolog], back_populates="projekti_tehnolog")
    dokumenti = relationship("DBDokument", back_populates="projekt", cascade="all, delete-orphan")
    emaili = relationship("DBEmail", back_populates="projekt")
    casovnica = relationship("DBProjektCasovnica", back_populates="projekt", cascade="all, delete-orphan")
    delovni_nalogi = relationship("DBDelovniNalog", back_populates="projekt")
    calcuquote_rfqs = relationship("DBCalcuQuoteRFQ", back_populates="projekt")
    cakajce_akcije = relationship("DBCakajocaAkcija", back_populates="projekt")
    obvestila = relationship("DBObvestilo", back_populates="projekt")
'''

# ============================================================
# db_models/email.py
# ============================================================
files[f"{BASE}/db_models/email.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
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
    izvleceni_podatki = Column(Text, nullable=True)
    priloge = Column(Text, nullable=True)

    projekt = relationship("DBProjekt", back_populates="emaili")
'''

# ============================================================
# db_models/dokument.py
# ============================================================
files[f"{BASE}/db_models/dokument.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBDokument(Base):
    __tablename__ = "Dokumenti"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id", ondelete="CASCADE"), nullable=False)
    tip = Column(String(50), nullable=False, default="Drugo")
    naziv_datoteke = Column(String(255), nullable=False)
    verzija = Column(Integer, nullable=False, default=1)
    pot_do_datoteke = Column(String(500), nullable=False)
    datum_nalozeno = Column(DateTime, default=datetime.now)
    nalozil_uporabnik = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)

    projekt = relationship("DBProjekt", back_populates="dokumenti")
    uporabnik = relationship("DBUporabnik")
'''

# ============================================================
# db_models/akcija.py
# ============================================================
files[f"{BASE}/db_models/akcija.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBCakajocaAkcija(Base):
    __tablename__ = "CakajočeAkcije"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=True)
    tip_akcije = Column(String(100), nullable=False)
    opis = Column(String(500), nullable=False)
    predlagani_podatki = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Caka")
    ustvaril_agent = Column(String(100), nullable=True)
    datum_ustvarjeno = Column(DateTime, default=datetime.now)
    potrdil_uporabnik = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    datum_potrjeno = Column(DateTime, nullable=True)

    projekt = relationship("DBProjekt", back_populates="cakajce_akcije")
    uporabnik = relationship("DBUporabnik")
'''

# ============================================================
# db_models/delovni_nalog.py
# ============================================================
files[f"{BASE}/db_models/delovni_nalog.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBDelovniNalog(Base):
    __tablename__ = "DelovniNalogi"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=False)
    largo_dn_id = Column(Integer, nullable=True)
    stevilka_dn = Column(String(50), nullable=True)
    artikel_id = Column(Integer, nullable=True)
    kolicina = Column(Numeric(18, 4), nullable=True)
    status = Column(String(50), nullable=True)
    datum_plan_zacetek = Column(DateTime, nullable=True)
    datum_plan_konec = Column(DateTime, nullable=True)
    datum_dejanski_zacetek = Column(DateTime, nullable=True)
    datum_dejanski_konec = Column(DateTime, nullable=True)
    zadnja_sinhronizacija = Column(DateTime, default=datetime.now)

    projekt = relationship("DBProjekt", back_populates="delovni_nalogi")
'''

# ============================================================
# db_models/calcuquote.py
# ============================================================
files[f"{BASE}/db_models/calcuquote.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBCalcuQuoteRFQ(Base):
    __tablename__ = "CalcuQuoteRFQ"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=False)
    calcuquote_rfq_id = Column(String(100), nullable=True)
    status = Column(String(50), default="Osnutek")
    datum_vnosa = Column(DateTime, default=datetime.now)
    bom_verzija = Column(Integer, nullable=True)
    cena_ponudbe = Column(Numeric(18, 2), nullable=True)
    datum_ponudbe = Column(DateTime, nullable=True)

    projekt = relationship("DBProjekt", back_populates="calcuquote_rfqs")
'''

# ============================================================
# db_models/casovnica.py
# ============================================================
files[f"{BASE}/db_models/casovnica.py"] = '''from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBProjektCasovnica(Base):
    __tablename__ = "ProjektCasovnica"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id", ondelete="CASCADE"), nullable=False)
    dogodek = Column(String(100), nullable=False)
    opis = Column(String(500), nullable=True)
    stara_vrednost = Column(String(255), nullable=True)
    nova_vrednost = Column(String(255), nullable=True)
    datum = Column(DateTime, default=datetime.now)
    uporabnik_ali_agent = Column(String(100), nullable=True)

    projekt = relationship("DBProjekt", back_populates="casovnica")
'''

# ============================================================
# db_models/audit.py
# ============================================================
files[f"{BASE}/db_models/audit.py"] = '''from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Text
from datetime import datetime
from app.database import Base


class DBAuditLog(Base):
    __tablename__ = "AuditLog"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
'''

# ============================================================
# db_models/seja.py
# ============================================================
files[f"{BASE}/db_models/seja.py"] = '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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

    uporabnik = relationship("DBUporabnik", back_populates="seje")
'''

# ============================================================
# db_models/obvestilo.py
# ============================================================
files[f"{BASE}/db_models/obvestilo.py"] = '''from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Boolean
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

    uporabnik = relationship("DBUporabnik", back_populates="obvestila")
    projekt = relationship("DBProjekt", back_populates="obvestila")
'''

# ============================================================
# crud/__init__.py
# ============================================================
files[f"{BASE}/crud/__init__.py"] = '''"""CRUD operacije za ai_agent bazo"""

from app.crud.uporabniki import (
    get_uporabnik_by_id, get_uporabnik_by_username,
    create_uporabnik, update_uporabnik, update_zadnja_prijava, list_uporabniki,
)
from app.crud.projekti import (
    get_projekt_by_id, list_projekti, create_projekt, update_projekt,
    get_casovnica, add_casovnica_event, get_next_project_number,
)
from app.crud.emaili import (
    get_email_by_id, get_email_by_outlook_id, list_emaili,
    create_email, update_email, list_nekategorizirani,
)
from app.crud.dokumenti import (
    get_dokument_by_id, list_dokumenti, create_dokument, delete_dokument,
)
'''

# ============================================================
# crud/uporabniki.py
# ============================================================
files[f"{BASE}/crud/uporabniki.py"] = '''from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.db_models.uporabnik import DBUporabnik


def get_uporabnik_by_id(db: Session, user_id: int) -> Optional[DBUporabnik]:
    return db.query(DBUporabnik).filter(DBUporabnik.id == user_id).first()


def get_uporabnik_by_username(db: Session, username: str) -> Optional[DBUporabnik]:
    return db.query(DBUporabnik).filter(DBUporabnik.username == username).first()


def create_uporabnik(db: Session, username: str, password_hash: str,
                     email: Optional[str] = None, ime: Optional[str] = None,
                     priimek: Optional[str] = None, vloga: str = "readonly") -> DBUporabnik:
    db_user = DBUporabnik(username=username, password_hash=password_hash,
                          email=email, ime=ime, priimek=priimek, vloga=vloga)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_uporabnik(db: Session, user_id: int, **kwargs) -> Optional[DBUporabnik]:
    db_user = get_uporabnik_by_id(db, user_id)
    if not db_user:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(db_user, key):
            setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_zadnja_prijava(db: Session, user_id: int) -> None:
    db_user = get_uporabnik_by_id(db, user_id)
    if db_user:
        db_user.zadnja_prijava = datetime.now()
        db.commit()


def list_uporabniki(db: Session, aktiven: Optional[bool] = None) -> list[DBUporabnik]:
    query = db.query(DBUporabnik)
    if aktiven is not None:
        query = query.filter(DBUporabnik.aktiven == aktiven)
    return query.order_by(DBUporabnik.username).all()
'''

# ============================================================
# crud/projekti.py
# ============================================================
files[f"{BASE}/crud/projekti.py"] = '''from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.db_models.projekt import DBProjekt
from app.db_models.casovnica import DBProjektCasovnica


def get_projekt_by_id(db: Session, projekt_id: int) -> Optional[DBProjekt]:
    return db.query(DBProjekt).filter(DBProjekt.id == projekt_id).first()


def list_projekti(db: Session, faza: Optional[str] = None, status: Optional[str] = None,
                  stranka_id: Optional[int] = None, search: Optional[str] = None) -> list[DBProjekt]:
    query = db.query(DBProjekt)
    if faza:
        query = query.filter(DBProjekt.faza == faza)
    if status:
        query = query.filter(DBProjekt.status == status)
    if stranka_id:
        query = query.filter(DBProjekt.stranka_id == stranka_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter((DBProjekt.naziv.ilike(pattern)) | (DBProjekt.stevilka_projekta.ilike(pattern)))
    return query.order_by(desc(DBProjekt.datum_rfq)).all()


def get_next_project_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"PRJ-{year}-"
    last = db.query(DBProjekt).filter(DBProjekt.stevilka_projekta.like(f"{prefix}%")).order_by(desc(DBProjekt.stevilka_projekta)).first()
    if last:
        try:
            next_num = int(last.stevilka_projekta.replace(prefix, "")) + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1
    return f"{prefix}{next_num:03d}"


def create_projekt(db: Session, naziv: str, stranka_id: Optional[int] = None,
                   opombe: Optional[str] = None, username: str = "system") -> DBProjekt:
    stevilka = get_next_project_number(db)
    db_projekt = DBProjekt(stevilka_projekta=stevilka, naziv=naziv, stranka_id=stranka_id,
                           faza="RFQ", status="Aktiven", datum_rfq=datetime.now(), opombe=opombe)
    db.add(db_projekt)
    db.commit()
    db.refresh(db_projekt)
    add_casovnica_event(db, projekt_id=db_projekt.id, dogodek="Ustvarjen",
                        opis=f"Projekt ustvarjen: {naziv}", uporabnik_ali_agent=username)
    return db_projekt


def update_projekt(db: Session, projekt_id: int, username: str = "system", **kwargs) -> Optional[DBProjekt]:
    db_projekt = get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        return None
    old_faza = db_projekt.faza
    old_status = db_projekt.status
    for key, value in kwargs.items():
        if value is not None and hasattr(db_projekt, key):
            setattr(db_projekt, key, value)
    if "faza" in kwargs and kwargs["faza"] and kwargs["faza"] != old_faza:
        add_casovnica_event(db, projekt_id=projekt_id, dogodek="Sprememba faze", opis="Faza spremenjena",
                            stara_vrednost=old_faza, nova_vrednost=kwargs["faza"], uporabnik_ali_agent=username)
    if "status" in kwargs and kwargs["status"] and kwargs["status"] != old_status:
        add_casovnica_event(db, projekt_id=projekt_id, dogodek="Sprememba statusa", opis="Status spremenjen",
                            stara_vrednost=old_status, nova_vrednost=kwargs["status"], uporabnik_ali_agent=username)
    db.commit()
    db.refresh(db_projekt)
    return db_projekt


def get_casovnica(db: Session, projekt_id: int) -> list[DBProjektCasovnica]:
    return db.query(DBProjektCasovnica).filter(DBProjektCasovnica.projekt_id == projekt_id).order_by(desc(DBProjektCasovnica.datum)).all()


def add_casovnica_event(db: Session, projekt_id: int, dogodek: str, opis: str,
                        stara_vrednost: Optional[str] = None, nova_vrednost: Optional[str] = None,
                        uporabnik_ali_agent: str = "system") -> DBProjektCasovnica:
    event = DBProjektCasovnica(projekt_id=projekt_id, dogodek=dogodek, opis=opis,
                               stara_vrednost=stara_vrednost, nova_vrednost=nova_vrednost,
                               datum=datetime.now(), uporabnik_ali_agent=uporabnik_ali_agent)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
'''

# ============================================================
# crud/emaili.py
# ============================================================
files[f"{BASE}/crud/emaili.py"] = '''from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
import json
from app.db_models.email import DBEmail


def get_email_by_id(db: Session, email_id: int) -> Optional[DBEmail]:
    return db.query(DBEmail).filter(DBEmail.id == email_id).first()


def get_email_by_outlook_id(db: Session, outlook_id: str) -> Optional[DBEmail]:
    return db.query(DBEmail).filter(DBEmail.outlook_id == outlook_id).first()


def list_emaili(db: Session, kategorija: Optional[str] = None,
                status: Optional[str] = None, projekt_id: Optional[int] = None) -> list[DBEmail]:
    query = db.query(DBEmail)
    if kategorija:
        query = query.filter(DBEmail.kategorija == kategorija)
    if status:
        query = query.filter(DBEmail.status == status)
    if projekt_id:
        query = query.filter(DBEmail.projekt_id == projekt_id)
    return query.order_by(desc(DBEmail.datum)).all()


def list_nekategorizirani(db: Session) -> list[DBEmail]:
    return db.query(DBEmail).filter(DBEmail.projekt_id.is_(None)).filter(
        DBEmail.status.in_(["Nov", "Prebran"])).order_by(desc(DBEmail.datum)).all()


def create_email(db: Session, outlook_id: str, zadeva: str, posiljatelj: str, datum: datetime,
                 prejemniki: Optional[str] = None, telo: Optional[str] = None,
                 kategorija: str = "Splosno", izvleceni_podatki: Optional[dict] = None,
                 priloge: Optional[list] = None) -> DBEmail:
    db_email = DBEmail(outlook_id=outlook_id, zadeva=zadeva, posiljatelj=posiljatelj,
                       prejemniki=prejemniki, telo=telo, kategorija=kategorija, status="Nov",
                       datum=datum, izvleceni_podatki=json.dumps(izvleceni_podatki) if izvleceni_podatki else None,
                       priloge=json.dumps(priloge) if priloge else None)
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email


def update_email(db: Session, email_id: int, **kwargs) -> Optional[DBEmail]:
    db_email = get_email_by_id(db, email_id)
    if not db_email:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(db_email, key):
            if key in ("izvleceni_podatki", "priloge") and isinstance(value, (dict, list)):
                value = json.dumps(value)
            setattr(db_email, key, value)
    db.commit()
    db.refresh(db_email)
    return db_email
'''

# ============================================================
# crud/dokumenti.py
# ============================================================
files[f"{BASE}/crud/dokumenti.py"] = '''from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.db_models.dokument import DBDokument


def get_dokument_by_id(db: Session, dokument_id: int) -> Optional[DBDokument]:
    return db.query(DBDokument).filter(DBDokument.id == dokument_id).first()


def list_dokumenti(db: Session, projekt_id: Optional[int] = None, tip: Optional[str] = None) -> list[DBDokument]:
    query = db.query(DBDokument)
    if projekt_id:
        query = query.filter(DBDokument.projekt_id == projekt_id)
    if tip:
        query = query.filter(DBDokument.tip == tip)
    return query.order_by(desc(DBDokument.datum_nalozeno)).all()


def create_dokument(db: Session, projekt_id: int, naziv_datoteke: str, pot_do_datoteke: str,
                    tip: str = "Drugo", nalozil_uporabnik: Optional[int] = None) -> DBDokument:
    existing = db.query(DBDokument).filter(DBDokument.projekt_id == projekt_id).filter(
        DBDokument.naziv_datoteke == naziv_datoteke).order_by(desc(DBDokument.verzija)).first()
    verzija = (existing.verzija + 1) if existing else 1
    db_dokument = DBDokument(projekt_id=projekt_id, tip=tip, naziv_datoteke=naziv_datoteke,
                             verzija=verzija, pot_do_datoteke=pot_do_datoteke,
                             datum_nalozeno=datetime.now(), nalozil_uporabnik=nalozil_uporabnik)
    db.add(db_dokument)
    db.commit()
    db.refresh(db_dokument)
    return db_dokument


def delete_dokument(db: Session, dokument_id: int) -> bool:
    db_dokument = get_dokument_by_id(db, dokument_id)
    if not db_dokument:
        return False
    db.delete(db_dokument)
    db.commit()
    return True
'''

# Zapiši vse datoteke
print("Zapisujem datoteke...")
for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK: {filepath}")

print(f"\nSkupaj {len(files)} datotek zapisanih!")
print("\nZdaj moraš še posodobiti API datoteke.")
print("Zaženi: scp -r ales@WINDOWS_IP:A:/AI-AGENT/backend/app/api ~/ai-agent/backend/app/")
print("  ali pa ročno prenesi config.py, main.py, auth.py, projekti.py, emaili.py, dokumenti.py")
