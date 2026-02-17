"""CRUD operacije za Emaili tabelo"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
from typing import Optional
import json

from app.db_models.email import DBEmail


def get_email_by_id(db: Session, email_id: int) -> Optional[DBEmail]:
    """Pridobi email po ID"""
    return db.query(DBEmail).filter(DBEmail.id == email_id).first()


def get_latest_email_date(db: Session) -> Optional[datetime]:
    """Vrni datum najnovejšega emaila za inkrementalno sinhronizacijo."""
    result = db.query(func.max(DBEmail.datum)).scalar()
    return result


def get_email_by_outlook_id(db: Session, outlook_id: str) -> Optional[DBEmail]:
    """Pridobi email po Outlook ID (za sinhronizacijo)"""
    return db.query(DBEmail).filter(DBEmail.outlook_id == outlook_id).first()


def list_emaili(
    db: Session,
    kategorija: Optional[str] = None,
    status: Optional[str] = None,
    projekt_id: Optional[int] = None,
    rfq_podkategorija: Optional[str] = None,
) -> list[DBEmail]:
    """Seznam emailov s filtri"""
    query = db.query(DBEmail)

    if kategorija:
        query = query.filter(DBEmail.kategorija == kategorija)
    if status:
        query = query.filter(DBEmail.status == status)
    if projekt_id:
        query = query.filter(DBEmail.projekt_id == projekt_id)
    if rfq_podkategorija:
        query = query.filter(DBEmail.rfq_podkategorija == rfq_podkategorija)

    return query.order_by(desc(DBEmail.datum)).all()


def list_nekategorizirani(db: Session) -> list[DBEmail]:
    """Seznam emailov ki niso dodeljeni projektu"""
    return (
        db.query(DBEmail)
        .filter(DBEmail.projekt_id.is_(None))
        .filter(DBEmail.status.in_(["Nov", "Prebran"]))
        .order_by(desc(DBEmail.datum))
        .all()
    )


def list_emails_pending_analysis(db: Session) -> list[DBEmail]:
    """Vrne emaile z analiza_status='Čaka'"""
    return (
        db.query(DBEmail)
        .filter(DBEmail.analiza_status == "Čaka")
        .order_by(DBEmail.datum)
        .all()
    )


def create_email(
    db: Session,
    outlook_id: str,
    zadeva: str,
    posiljatelj: str,
    datum: datetime,
    prejemniki: Optional[str] = None,
    telo: Optional[str] = None,
    kategorija: str = "Splošno",
    izvleceni_podatki: Optional[dict] = None,
    priloge: Optional[list[str]] = None,
) -> DBEmail:
    """Ustvari nov email zapis"""
    db_email = DBEmail(
        outlook_id=outlook_id,
        zadeva=zadeva,
        posiljatelj=posiljatelj,
        prejemniki=prejemniki,
        telo=telo,
        kategorija=kategorija,
        status="Nov",
        datum=datum,
        izvleceni_podatki=json.dumps(izvleceni_podatki) if izvleceni_podatki else None,
        priloge=json.dumps(priloge) if priloge else None,
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email


def update_email(
    db: Session,
    email_id: int,
    **kwargs,
) -> Optional[DBEmail]:
    """Posodobi email"""
    db_email = get_email_by_id(db, email_id)
    if not db_email:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(db_email, key):
            # JSON polja serializiraj
            if key in ("izvleceni_podatki", "priloge", "analiza_rezultat") and isinstance(value, (dict, list)):
                value = json.dumps(value)
            setattr(db_email, key, value)

    db.commit()
    db.refresh(db_email)
    return db_email
