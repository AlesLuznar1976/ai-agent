from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmailKategorija(str, Enum):
    RFQ = "RFQ"
    NAROCILO = "Naročilo"
    SPREMEMBA = "Sprememba"
    DOKUMENTACIJA = "Dokumentacija"
    REKLAMACIJA = "Reklamacija"
    SPLOSNO = "Splošno"


class RfqPodkategorija(str, Enum):
    KOMPLETNO = "Kompletno"
    NEPOPOLNO = "Nepopolno"
    POVPRASEVANJE = "Povpraševanje"
    REPEAT_ORDER = "Repeat Order"


class EmailStatus(str, Enum):
    NOV = "Nov"
    PREBRAN = "Prebran"
    DODELJEN = "Dodeljen"
    OBDELAN = "Obdelan"


class EmailBase(BaseModel):
    zadeva: str
    posiljatelj: str
    prejemniki: str
    telo: Optional[str] = None


class EmailCreate(EmailBase):
    outlook_id: str
    kategorija: EmailKategorija = EmailKategorija.SPLOSNO
    izvleceni_podatki: Optional[dict] = None


class EmailUpdate(BaseModel):
    projekt_id: Optional[int] = None
    kategorija: Optional[EmailKategorija] = None
    status: Optional[EmailStatus] = None
    rfq_podkategorija: Optional[RfqPodkategorija] = None


class Email(EmailBase):
    id: int
    outlook_id: str
    projekt_id: Optional[int] = None
    kategorija: EmailKategorija
    rfq_podkategorija: Optional[RfqPodkategorija] = None
    status: EmailStatus = EmailStatus.NOV
    datum: datetime
    izvleceni_podatki: Optional[dict] = None
    priloge: Optional[list[str]] = None
    analiza_status: Optional[str] = None
    analiza_rezultat: Optional[dict] = None

    class Config:
        from_attributes = True


class EmailAnalysis(BaseModel):
    """Rezultat LLM analize emaila"""
    kategorija: EmailKategorija
    rfq_podkategorija: Optional[RfqPodkategorija] = None
    zaupanje: float  # 0-1
    izvleceni_podatki: dict
    predlagan_projekt_id: Optional[int] = None
    povzetek: str
