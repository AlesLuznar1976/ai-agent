from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DokumentTip(str, Enum):
    RFQ = "RFQ"
    PONUDBA = "Ponudba"
    NAROCILO = "Naročilo"
    BOM = "BOM"
    GERBER = "Gerber"
    SPECIFIKACIJA = "Specifikacija"
    TIV = "TIV"
    DELOVNI_LIST = "Delovni list"
    PROIZVODNI = "Proizvodni"
    REKLAMACIJA = "Reklamacija"
    DRUGO = "Drugo"


class DokumentBase(BaseModel):
    naziv_datoteke: str
    tip: DokumentTip = DokumentTip.DRUGO


class DokumentCreate(DokumentBase):
    projekt_id: int
    pot_do_datoteke: str


class Dokument(DokumentBase):
    id: int
    projekt_id: int
    verzija: int = 1
    pot_do_datoteke: str
    datum_nalozeno: datetime
    nalozil_uporabnik: Optional[int] = None

    class Config:
        from_attributes = True


class GenerateDocumentRequest(BaseModel):
    tip: DokumentTip
    projekt_id: int
