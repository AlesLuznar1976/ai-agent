from sqlalchemy.orm import Session
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
                status: Optional[str] = None, projekt_id: Optional[int] = None,
                rfq_podkategorija: Optional[str] = None) -> list[DBEmail]:
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


def get_latest_email_date(db: Session) -> Optional[datetime]:
    """Vrni datum zadnjega emaila za inkrementalno sinhronizacijo."""
    latest = db.query(DBEmail.datum).order_by(desc(DBEmail.datum)).first()
    return latest[0] if latest else None


def list_nekategorizirani(db: Session) -> list[DBEmail]:
    return db.query(DBEmail).filter(DBEmail.projekt_id.is_(None)).filter(
        DBEmail.status.in_(["Nov", "Prebran"])).order_by(desc(DBEmail.datum)).all()


def list_emails_pending_analysis(db: Session) -> list[DBEmail]:
    """Vrni emaile ki čakajo na analizo (status NULL ali Čaka), samo od 2026-02-19 naprej."""
    from sqlalchemy import or_
    return db.query(DBEmail).filter(
        DBEmail.datum >= "2026-02-19",
        or_(
            DBEmail.analiza_status.is_(None),
            DBEmail.analiza_status == "",
            DBEmail.analiza_status == "Čaka",
        ),
    ).order_by(DBEmail.id).all()


def list_agent_emails_ready(db: Session) -> list[DBEmail]:
    """Vrni analizirane agent emaile brez projekta (za avtomatsko ustvarjanje projektov).

    Pogoji:
    - mailbox = agent@luznar.com (v izvleceni_podatki JSON)
    - analiza_status = "Končano"
    - projekt_id IS NULL
    """
    return db.query(DBEmail).filter(
        DBEmail.analiza_status == "Končano",
        DBEmail.projekt_id.is_(None),
        DBEmail.izvleceni_podatki.contains('"mailbox": "agent@luznar.com"'),
    ).order_by(DBEmail.id).all()


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
            if key in ("izvleceni_podatki", "priloge", "analiza_rezultat") and isinstance(value, (dict, list)):
                value = json.dumps(value)
            setattr(db_email, key, value)
    db.commit()
    db.refresh(db_email)
    return db_email
