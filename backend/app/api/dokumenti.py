from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.orm import Session
import os

from app.auth import get_current_user, require_permission
from app.models import (
    TokenData, Permission,
    Dokument, DokumentCreate, DokumentTip, GenerateDocumentRequest
)
from app.database import get_db
from app.crud import dokumenti as crud_dokumenti

router = APIRouter()


def db_dokument_to_response(db_doc) -> dict:
    """Pretvori DB dokument v API response"""
    return {
        "id": db_doc.id,
        "projekt_id": db_doc.projekt_id,
        "tip": db_doc.tip,
        "naziv_datoteke": db_doc.naziv_datoteke,
        "verzija": db_doc.verzija,
        "pot_do_datoteke": db_doc.pot_do_datoteke,
        "datum_nalozeno": db_doc.datum_nalozeno.isoformat() if db_doc.datum_nalozeno else None,
        "nalozil_uporabnik": db_doc.nalozil_uporabnik,
    }


@router.get("")
async def list_dokumenti(
    projekt_id: Optional[int] = None,
    tip: Optional[DokumentTip] = None,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_VIEW)),
    db: Session = Depends(get_db),
):
    """Seznam dokumentov"""

    db_dokumenti = crud_dokumenti.list_dokumenti(
        db,
        projekt_id=projekt_id,
        tip=tip.value if tip else None,
    )

    dokumenti = [db_dokument_to_response(d) for d in db_dokumenti]
    return {"dokumenti": dokumenti, "total": len(dokumenti)}


@router.get("/{dokument_id}")
async def get_dokument(
    dokument_id: int,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_VIEW)),
    db: Session = Depends(get_db),
):
    """Podrobnosti dokumenta"""

    db_dokument = crud_dokumenti.get_dokument_by_id(db, dokument_id)
    if not db_dokument:
        raise HTTPException(status_code=404, detail="Dokument ne obstaja")

    return db_dokument_to_response(db_dokument)


@router.get("/{dokument_id}/download")
async def download_dokument(
    dokument_id: int,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_VIEW)),
    db: Session = Depends(get_db),
):
    """Prenesi dokument"""

    db_dokument = crud_dokumenti.get_dokument_by_id(db, dokument_id)
    if not db_dokument:
        raise HTTPException(status_code=404, detail="Dokument ne obstaja")

    if not os.path.exists(db_dokument.pot_do_datoteke):
        raise HTTPException(status_code=404, detail="Datoteka ne obstaja na disku")

    return FileResponse(
        db_dokument.pot_do_datoteke,
        filename=db_dokument.naziv_datoteke,
        media_type="application/octet-stream"
    )


@router.post("/generiraj")
async def generiraj_dokument(
    request: GenerateDocumentRequest,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_CREATE)),
    db: Session = Depends(get_db),
):
    """Generiraj dokument"""

    tip_nazivi = {
        DokumentTip.TIV: "TIV dokumentacija",
        DokumentTip.PONUDBA: "Ponudba",
        DokumentTip.BOM: "BOM poročilo",
        DokumentTip.DELOVNI_LIST: "Delovni list",
        DokumentTip.PROIZVODNI: "Proizvodna dokumentacija",
    }

    naziv = tip_nazivi.get(request.tip, request.tip.value)

    return {
        "message": f"Generiranje '{naziv}' za projekt {request.projekt_id}",
        "status": "V pripravi",
        "info": "Document Agent ni še implementiran - potrebna konfiguracija"
    }


@router.post("")
async def upload_dokument(
    data: DokumentCreate,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_CREATE)),
    db: Session = Depends(get_db),
):
    """Naloži dokument"""

    db_dokument = crud_dokumenti.create_dokument(
        db,
        projekt_id=data.projekt_id,
        naziv_datoteke=data.naziv_datoteke,
        pot_do_datoteke=data.pot_do_datoteke,
        tip=data.tip.value,
        nalozil_uporabnik=current_user.user_id,
    )

    return db_dokument_to_response(db_dokument)


@router.delete("/{dokument_id}")
async def delete_dokument(
    dokument_id: int,
    current_user: TokenData = Depends(require_permission(Permission.DOCUMENT_DELETE)),
    db: Session = Depends(get_db),
):
    """Izbriši dokument"""

    success = crud_dokumenti.delete_dokument(db, dokument_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dokument ne obstaja")

    return {"message": "Dokument izbrisan"}
