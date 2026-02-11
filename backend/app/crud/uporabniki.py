"""CRUD operacije za Uporabniki tabelo"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db_models.uporabnik import DBUporabnik


def get_uporabnik_by_id(db: Session, user_id: int) -> Optional[DBUporabnik]:
    """Pridobi uporabnika po ID"""
    return db.query(DBUporabnik).filter(DBUporabnik.id == user_id).first()


def get_uporabnik_by_username(db: Session, username: str) -> Optional[DBUporabnik]:
    """Pridobi uporabnika po username"""
    return db.query(DBUporabnik).filter(DBUporabnik.username == username).first()


def create_uporabnik(
    db: Session,
    username: str,
    password_hash: str,
    email: Optional[str] = None,
    ime: Optional[str] = None,
    priimek: Optional[str] = None,
    vloga: str = "readonly",
) -> DBUporabnik:
    """Ustvari novega uporabnika"""
    db_user = DBUporabnik(
        username=username,
        password_hash=password_hash,
        email=email,
        ime=ime,
        priimek=priimek,
        vloga=vloga,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_uporabnik(
    db: Session,
    user_id: int,
    **kwargs,
) -> Optional[DBUporabnik]:
    """Posodobi uporabnika"""
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
    """Posodobi zadnjo prijavo uporabnika"""
    db_user = get_uporabnik_by_id(db, user_id)
    if db_user:
        db_user.zadnja_prijava = datetime.now()
        db.commit()


def list_uporabniki(db: Session, aktiven: Optional[bool] = None) -> list[DBUporabnik]:
    """Seznam uporabnikov"""
    query = db.query(DBUporabnik)
    if aktiven is not None:
        query = query.filter(DBUporabnik.aktiven == aktiven)
    return query.order_by(DBUporabnik.username).all()
