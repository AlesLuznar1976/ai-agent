from sqlalchemy.orm import Session
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
