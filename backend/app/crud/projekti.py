"""CRUD operacije za Projekti in ProjektCasovnica tabeli"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import Optional

from app.db_models.projekt import DBProjekt
from app.db_models.casovnica import DBProjektCasovnica


def get_projekt_by_id(db: Session, projekt_id: int) -> Optional[DBProjekt]:
    """Pridobi projekt po ID"""
    return db.query(DBProjekt).filter(DBProjekt.id == projekt_id).first()


def list_projekti(
    db: Session,
    faza: Optional[str] = None,
    status: Optional[str] = None,
    stranka_id: Optional[int] = None,
    search: Optional[str] = None,
) -> list[DBProjekt]:
    """Seznam projektov s filtri"""
    query = db.query(DBProjekt)

    if faza:
        query = query.filter(DBProjekt.faza == faza)
    if status:
        query = query.filter(DBProjekt.status == status)
    if stranka_id:
        query = query.filter(DBProjekt.stranka_id == stranka_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (DBProjekt.naziv.ilike(search_pattern)) |
            (DBProjekt.stevilka_projekta.ilike(search_pattern))
        )

    return query.order_by(desc(DBProjekt.datum_rfq)).all()


def get_next_project_number(db: Session) -> str:
    """Generiraj naslednjo številko projekta (PRJ-YYYY-NNN)"""
    year = datetime.now().year
    prefix = f"PRJ-{year}-"

    # Najdi najvišjo številko za to leto
    last = (
        db.query(DBProjekt)
        .filter(DBProjekt.stevilka_projekta.like(f"{prefix}%"))
        .order_by(desc(DBProjekt.stevilka_projekta))
        .first()
    )

    if last:
        try:
            last_num = int(last.stevilka_projekta.replace(prefix, ""))
            next_num = last_num + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:03d}"


def create_projekt(
    db: Session,
    naziv: str,
    stranka_id: Optional[int] = None,
    opombe: Optional[str] = None,
    username: str = "system",
) -> DBProjekt:
    """Ustvari nov projekt"""
    stevilka = get_next_project_number(db)

    db_projekt = DBProjekt(
        stevilka_projekta=stevilka,
        naziv=naziv,
        stranka_id=stranka_id,
        faza="RFQ",
        status="Aktiven",
        datum_rfq=datetime.now(),
        opombe=opombe,
    )
    db.add(db_projekt)
    db.commit()
    db.refresh(db_projekt)

    # Dodaj v časovnico
    add_casovnica_event(
        db,
        projekt_id=db_projekt.id,
        dogodek="Ustvarjen",
        opis=f"Projekt ustvarjen: {naziv}",
        uporabnik_ali_agent=username,
    )

    return db_projekt


def update_projekt(
    db: Session,
    projekt_id: int,
    username: str = "system",
    **kwargs,
) -> Optional[DBProjekt]:
    """Posodobi projekt in zabeleži v časovnico"""
    db_projekt = get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        return None

    old_faza = db_projekt.faza
    old_status = db_projekt.status

    for key, value in kwargs.items():
        if value is not None and hasattr(db_projekt, key):
            setattr(db_projekt, key, value)

    # Zabeleži spremembe v časovnico
    if "faza" in kwargs and kwargs["faza"] and kwargs["faza"] != old_faza:
        add_casovnica_event(
            db,
            projekt_id=projekt_id,
            dogodek="Sprememba faze",
            opis="Faza spremenjena",
            stara_vrednost=old_faza,
            nova_vrednost=kwargs["faza"],
            uporabnik_ali_agent=username,
        )

    if "status" in kwargs and kwargs["status"] and kwargs["status"] != old_status:
        add_casovnica_event(
            db,
            projekt_id=projekt_id,
            dogodek="Sprememba statusa",
            opis="Status spremenjen",
            stara_vrednost=old_status,
            nova_vrednost=kwargs["status"],
            uporabnik_ali_agent=username,
        )

    db.commit()
    db.refresh(db_projekt)
    return db_projekt


def get_casovnica(db: Session, projekt_id: int) -> list[DBProjektCasovnica]:
    """Pridobi časovnico projekta"""
    return (
        db.query(DBProjektCasovnica)
        .filter(DBProjektCasovnica.projekt_id == projekt_id)
        .order_by(desc(DBProjektCasovnica.datum))
        .all()
    )


def add_casovnica_event(
    db: Session,
    projekt_id: int,
    dogodek: str,
    opis: str,
    stara_vrednost: Optional[str] = None,
    nova_vrednost: Optional[str] = None,
    uporabnik_ali_agent: str = "system",
) -> DBProjektCasovnica:
    """Dodaj dogodek v časovnico"""
    event = DBProjektCasovnica(
        projekt_id=projekt_id,
        dogodek=dogodek,
        opis=opis,
        stara_vrednost=stara_vrednost,
        nova_vrednost=nova_vrednost,
        datum=datetime.now(),
        uporabnik_ali_agent=uporabnik_ali_agent,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
