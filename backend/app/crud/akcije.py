"""CRUD operacije za CakajočeAkcije tabelo"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import json

from app.db_models.akcija import DBCakajocaAkcija


def create_pending_action(
    db: Session,
    user_id: int,
    tip_akcije: str,
    opis: str,
    predlagani_podatki: Optional[dict] = None,
    projekt_id: Optional[int] = None,
) -> DBCakajocaAkcija:
    """Ustvari čakajočo akcijo"""
    akcija = DBCakajocaAkcija(
        user_id=user_id,
        tip_akcije=tip_akcije,
        opis=opis,
        predlagani_podatki=json.dumps(predlagani_podatki) if predlagani_podatki else None,
        projekt_id=projekt_id,
        status="Čaka",
    )
    db.add(akcija)
    db.commit()
    db.refresh(akcija)
    return akcija


def get_pending_action(db: Session, action_id: int) -> Optional[DBCakajocaAkcija]:
    """Pridobi akcijo po ID"""
    return db.query(DBCakajocaAkcija).filter(DBCakajocaAkcija.id == action_id).first()


def list_pending_actions(
    db: Session, user_id: int, status: str = "Čaka"
) -> list[DBCakajocaAkcija]:
    """Seznam čakajočih akcij za uporabnika"""
    return (
        db.query(DBCakajocaAkcija)
        .filter(
            DBCakajocaAkcija.user_id == user_id,
            DBCakajocaAkcija.status == status,
        )
        .order_by(DBCakajocaAkcija.datum_ustvarjeno.desc())
        .all()
    )


def confirm_action(
    db: Session,
    action_id: int,
    user_id: int,
    rezultat: Optional[str] = None,
) -> Optional[DBCakajocaAkcija]:
    """Potrdi akcijo"""
    akcija = get_pending_action(db, action_id)
    if not akcija:
        return None
    akcija.status = "Potrjeno"
    akcija.potrdil_uporabnik = user_id
    akcija.datum_potrjeno = datetime.now()
    akcija.rezultat = rezultat
    db.commit()
    db.refresh(akcija)
    return akcija


def reject_action(db: Session, action_id: int) -> Optional[DBCakajocaAkcija]:
    """Zavrni akcijo"""
    akcija = get_pending_action(db, action_id)
    if not akcija:
        return None
    akcija.status = "Zavrnjeno"
    db.commit()
    db.refresh(akcija)
    return akcija


def fail_action(
    db: Session, action_id: int, error: str
) -> Optional[DBCakajocaAkcija]:
    """Označi akcijo kot neuspešno"""
    akcija = get_pending_action(db, action_id)
    if not akcija:
        return None
    akcija.status = "Napaka"
    akcija.rezultat = json.dumps({"error": error})
    db.commit()
    db.refresh(akcija)
    return akcija
