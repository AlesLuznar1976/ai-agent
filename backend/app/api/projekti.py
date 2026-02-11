from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
import json

from app.auth import get_current_user, require_permission
from app.models import (
    TokenData, Permission,
    Projekt, ProjektCreate, ProjektUpdate,
    ProjektFaza, ProjektStatus, ProjektCasovnica
)
from app.database import get_db
from app.crud import projekti as crud_projekti
from app.crud import dokumenti as crud_dokumenti

router = APIRouter()


def db_projekt_to_response(db_proj) -> dict:
    """Pretvori DB projekt v API response"""
    return {
        "id": db_proj.id,
        "stevilka_projekta": db_proj.stevilka_projekta,
        "naziv": db_proj.naziv,
        "stranka_id": db_proj.stranka_id,
        "faza": db_proj.faza,
        "status": db_proj.status,
        "datum_rfq": db_proj.datum_rfq.isoformat() if db_proj.datum_rfq else None,
        "datum_zakljucka": db_proj.datum_zakljucka.isoformat() if db_proj.datum_zakljucka else None,
        "odgovorni_prodaja": db_proj.odgovorni_prodaja,
        "odgovorni_tehnolog": db_proj.odgovorni_tehnolog,
        "opombe": db_proj.opombe,
    }


@router.get("")
async def list_projekti(
    faza: Optional[ProjektFaza] = None,
    status: Optional[ProjektStatus] = None,
    stranka_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_VIEW)),
    db: Session = Depends(get_db),
):
    """Seznam vseh projektov"""

    db_projekti = crud_projekti.list_projekti(
        db,
        faza=faza.value if faza else None,
        status=status.value if status else None,
        stranka_id=stranka_id,
        search=search,
    )

    projekti = [db_projekt_to_response(p) for p in db_projekti]
    return {"projekti": projekti, "total": len(projekti)}


@router.get("/{projekt_id}")
async def get_projekt(
    projekt_id: int,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_VIEW)),
    db: Session = Depends(get_db),
):
    """Podrobnosti projekta"""

    db_projekt = crud_projekti.get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        raise HTTPException(status_code=404, detail="Projekt ne obstaja")

    return db_projekt_to_response(db_projekt)


@router.post("")
async def create_projekt(
    data: ProjektCreate,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_CREATE)),
    db: Session = Depends(get_db),
):
    """Ustvari nov projekt"""

    db_projekt = crud_projekti.create_projekt(
        db,
        naziv=data.naziv,
        stranka_id=data.stranka_id,
        opombe=data.opombe,
        username=current_user.username,
    )

    return db_projekt_to_response(db_projekt)


@router.patch("/{projekt_id}")
async def update_projekt(
    projekt_id: int,
    data: ProjektUpdate,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_EDIT)),
    db: Session = Depends(get_db),
):
    """Posodobi projekt"""

    db_projekt = crud_projekti.get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        raise HTTPException(status_code=404, detail="Projekt ne obstaja")

    update_data = data.model_dump(exclude_unset=True)

    # Pretvori enum v string za DB
    if "faza" in update_data and update_data["faza"]:
        update_data["faza"] = update_data["faza"].value
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].value

    db_projekt = crud_projekti.update_projekt(
        db,
        projekt_id=projekt_id,
        username=current_user.username,
        **update_data,
    )

    return db_projekt_to_response(db_projekt)


@router.get("/{projekt_id}/casovnica")
async def get_casovnica(
    projekt_id: int,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_VIEW)),
    db: Session = Depends(get_db),
):
    """Časovnica projekta"""

    db_projekt = crud_projekti.get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        raise HTTPException(status_code=404, detail="Projekt ne obstaja")

    db_casovnica = crud_projekti.get_casovnica(db, projekt_id)

    casovnica = [
        {
            "id": c.id,
            "projekt_id": c.projekt_id,
            "dogodek": c.dogodek,
            "opis": c.opis,
            "stara_vrednost": c.stara_vrednost,
            "nova_vrednost": c.nova_vrednost,
            "datum": c.datum.isoformat() if c.datum else None,
            "uporabnik_ali_agent": c.uporabnik_ali_agent,
        }
        for c in db_casovnica
    ]

    return {"casovnica": casovnica}


@router.get("/{projekt_id}/dokumenti")
async def get_projekt_dokumenti(
    projekt_id: int,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_VIEW)),
    db: Session = Depends(get_db),
):
    """Dokumenti projekta"""

    db_projekt = crud_projekti.get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        raise HTTPException(status_code=404, detail="Projekt ne obstaja")

    db_dokumenti = crud_dokumenti.list_dokumenti(db, projekt_id=projekt_id)

    dokumenti = [
        {
            "id": d.id,
            "projekt_id": d.projekt_id,
            "tip": d.tip,
            "naziv_datoteke": d.naziv_datoteke,
            "verzija": d.verzija,
            "pot_do_datoteke": d.pot_do_datoteke,
            "datum_nalozeno": d.datum_nalozeno.isoformat() if d.datum_nalozeno else None,
            "nalozil_uporabnik": d.nalozil_uporabnik,
        }
        for d in db_dokumenti
    ]

    return {"dokumenti": dokumenti}


@router.get("/{projekt_id}/delovni-nalogi")
async def get_projekt_dn(
    projekt_id: int,
    current_user: TokenData = Depends(require_permission(Permission.LARGO_VIEW)),
    db: Session = Depends(get_db),
):
    """Delovni nalogi projekta"""

    db_projekt = crud_projekti.get_projekt_by_id(db, projekt_id)
    if not db_projekt:
        raise HTTPException(status_code=404, detail="Projekt ne obstaja")

    # TODO: implementiraj ko bo Largo integracija
    return {"delovni_nalogi": []}
