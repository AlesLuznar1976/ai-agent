from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProjektFaza(str, Enum):
    RFQ = "RFQ"
    PONUDBA = "Ponudba"
    NAROCILO = "Naročilo"
    TEHNOLOGIJA = "Tehnologija"
    NABAVA = "Nabava"
    PROIZVODNJA = "Proizvodnja"
    DOSTAVA = "Dostava"
    ZAKLJUCEK = "Zaključek"


class ProjektStatus(str, Enum):
    AKTIVEN = "Aktiven"
    NA_CAKANJU = "Na čakanju"
    ZAKLJUCEN = "Zaključen"
    PREKLICAN = "Preklican"


class ProjektBase(BaseModel):
    naziv: str
    stranka_id: Optional[int] = None
    opombe: Optional[str] = None


class ProjektCreate(ProjektBase):
    pass


class ProjektUpdate(BaseModel):
    naziv: Optional[str] = None
    faza: Optional[ProjektFaza] = None
    status: Optional[ProjektStatus] = None
    opombe: Optional[str] = None
    odgovorni_prodaja: Optional[int] = None
    odgovorni_tehnolog: Optional[int] = None


class Projekt(ProjektBase):
    id: int
    stevilka_projekta: str
    faza: ProjektFaza = ProjektFaza.RFQ
    status: ProjektStatus = ProjektStatus.AKTIVEN
    datum_rfq: datetime
    datum_zakljucka: Optional[datetime] = None
    odgovorni_prodaja: Optional[int] = None
    odgovorni_tehnolog: Optional[int] = None

    class Config:
        from_attributes = True


class ProjektCasovnicaEvent(str, Enum):
    USTVARJEN = "Ustvarjen"
    SPREMEMBA_FAZE = "Sprememba faze"
    SPREMEMBA_STATUSA = "Sprememba statusa"
    NOV_DOKUMENT = "Nov dokument"
    NOV_EMAIL = "Nov email"
    DN_USTVARJEN = "DN ustvarjen"
    DN_STATUS = "DN status"
    CQ_RFQ = "CQ RFQ vnesen"
    CQ_SYNC = "CQ sinhronizacija"
    KOMENTAR = "Komentar"


class ProjektCasovnica(BaseModel):
    id: int
    projekt_id: int
    dogodek: ProjektCasovnicaEvent
    opis: str
    stara_vrednost: Optional[str] = None
    nova_vrednost: Optional[str] = None
    datum: datetime
    uporabnik_ali_agent: str

    class Config:
        from_attributes = True
