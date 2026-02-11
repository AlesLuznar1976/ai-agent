import json
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.llm import get_llm_router, TaskType
from app.models import EmailKategorija, EmailAnalysis


class EmailAgent:
    """
    Email Agent - obdelava emailov:
    - Kategorizacija novih emailov
    - Izvleček podatkov (stranka, količina, tip projekta)
    - Povezava z obstoječimi projekti
    - Priprava odgovorov (po potrditvi)
    """

    CATEGORIZE_PROMPT = """Si AI asistent za podjetje Luznar Electronics (izdelava PCB/SMT).
Analiziraj email in ga kategoriziraj.

**Kategorije:**
- RFQ: Povpraševanje za ponudbo (request for quote)
- Naročilo: Potrditev naročila, PO (purchase order)
- Sprememba: ECO/ECN, sprememba specifikacij, nova verzija
- Dokumentacija: Pošiljanje Gerber, BOM, specifikacij
- Reklamacija: Pritožba, težava s kvaliteto
- Splošno: Vse ostalo

**Email:**
Od: {sender}
Zadeva: {subject}
Vsebina:
{body}

Priloge: {attachments}

**Naloga:**
1. Določi kategorijo
2. Izvleci ključne podatke (stranka, količina, tip projekta, PO številka, verzija, ...)
3. Predlagaj ali obstaja povezan projekt
4. Napiši kratek povzetek

Vrni JSON:
{{
    "kategorija": "RFQ|Naročilo|Sprememba|Dokumentacija|Reklamacija|Splošno",
    "zaupanje": 0.0-1.0,
    "izvleceni_podatki": {{
        "stranka": "...",
        "kolicina": null,
        "tip_projekta": "...",
        "po_stevilka": null,
        "verzija": null,
        ...
    }},
    "predlagan_projekt_id": null,
    "povzetek": "..."
}}
"""

    def __init__(self):
        self.llm = get_llm_router()

    async def categorize_email(
        self,
        sender: str,
        subject: str,
        body: str,
        attachments: list[str] = None
    ) -> EmailAnalysis:
        """
        Kategorizira email in izvleče podatke.

        Args:
            sender: Pošiljatelj
            subject: Zadeva
            body: Vsebina emaila
            attachments: Seznam imen prilog
        """

        prompt = self.CATEGORIZE_PROMPT.format(
            sender=sender,
            subject=subject,
            body=body[:2000],  # Omejimo dolžino
            attachments=", ".join(attachments or []) or "Ni prilog"
        )

        try:
            response = await self.llm.complete(
                prompt,
                task_type=TaskType.EMAIL_CATEGORIZATION,
                contains_sensitive=True  # Emaili lahko vsebujejo občutljive podatke
            )

            # Parse JSON
            data = json.loads(response)

            kategorija_str = data.get("kategorija", "Splošno")
            try:
                kategorija = EmailKategorija(kategorija_str)
            except ValueError:
                kategorija = EmailKategorija.SPLOSNO

            return EmailAnalysis(
                kategorija=kategorija,
                zaupanje=data.get("zaupanje", 0.5),
                izvleceni_podatki=data.get("izvleceni_podatki", {}),
                predlagan_projekt_id=data.get("predlagan_projekt_id"),
                povzetek=data.get("povzetek", "")
            )

        except Exception as e:
            print(f"Email categorization error: {e}")
            # Fallback
            return self._simple_categorize(sender, subject, body, attachments)

    def _simple_categorize(
        self,
        sender: str,
        subject: str,
        body: str,
        attachments: list[str] = None
    ) -> EmailAnalysis:
        """Preprosta kategorizacija brez LLM (fallback)"""

        subject_lower = subject.lower()
        body_lower = body.lower() if body else ""
        combined = subject_lower + " " + body_lower

        # Poskusi določiti kategorijo
        if any(w in combined for w in ["rfq", "quote", "ponudba", "povpraševanje", "quotation"]):
            kategorija = EmailKategorija.RFQ
            zaupanje = 0.7
        elif any(w in combined for w in ["po", "purchase order", "naročilo", "order confirmation"]):
            kategorija = EmailKategorija.NAROCILO
            zaupanje = 0.7
        elif any(w in combined for w in ["eco", "ecn", "sprememba", "revision", "verzija", "popravek"]):
            kategorija = EmailKategorija.SPREMEMBA
            zaupanje = 0.7
        elif any(w in combined for w in ["gerber", "bom", "specification", "dokumentacija"]):
            kategorija = EmailKategorija.DOKUMENTACIJA
            zaupanje = 0.6
        elif any(w in combined for w in ["reklamacija", "complaint", "problem", "issue", "defect"]):
            kategorija = EmailKategorija.REKLAMACIJA
            zaupanje = 0.7
        else:
            kategorija = EmailKategorija.SPLOSNO
            zaupanje = 0.4

        # Izvleci podatke iz sender
        stranka = sender.split("@")[1].split(".")[0].capitalize() if "@" in sender else ""

        return EmailAnalysis(
            kategorija=kategorija,
            zaupanje=zaupanje,
            izvleceni_podatki={
                "stranka": stranka,
                "zadeva": subject
            },
            predlagan_projekt_id=None,
            povzetek=f"Email od {sender}: {subject[:50]}..."
        )

    RESPONSE_TYPE_INSTRUCTIONS = {
        "acknowledge": "Potrdi prejem emaila. Stranki sporoči da smo prejeli njihovo sporočilo in bomo odgovorili v najkrajšem času.",
        "request_info": "Zaprosi za dodatne informacije. Stranki pojasni katere podatke potrebujemo (Gerber datoteke, BOM, količine, specifikacije).",
        "quote": "Sporoči da pripravljamo ponudbo. Omeni predviden čas za pripravo ponudbe (2-3 delovne dni).",
        "reject": "Vljudno zavrni povpraševanje. Pojasni razlog (npr. ni v naši domeni, kapacitete zasedene) in predlagaj alternativo.",
        "general": "Napiši splošen profesionalen odgovor glede na vsebino emaila.",
    }

    async def suggest_response(
        self,
        original_email: dict,
        response_type: str = "acknowledge"
    ) -> str:
        """
        Predlaga odgovor na email z bogatim kontekstom.

        Args:
            original_email: Originalni email (sender, subject, body, kategorija, izvleceni_podatki, additional_context)
            response_type: Tip odgovora (acknowledge, request_info, quote, reject, general)
        """
        kategorija = original_email.get("kategorija", "")
        izvleceni = original_email.get("izvleceni_podatki", {})
        additional_context = original_email.get("additional_context", "")

        # Kontekst iz izvlečenih podatkov
        context_parts = []
        if izvleceni.get("stranka"):
            context_parts.append(f"Stranka: {izvleceni['stranka']}")
        if izvleceni.get("kolicina"):
            context_parts.append(f"Količina: {izvleceni['kolicina']}")
        if izvleceni.get("po_stevilka"):
            context_parts.append(f"PO: {izvleceni['po_stevilka']}")
        if izvleceni.get("povzetek"):
            context_parts.append(f"Povzetek: {izvleceni['povzetek']}")
        izvleceni_str = "\n".join(context_parts) if context_parts else "Ni dodatnih podatkov"

        type_instruction = self.RESPONSE_TYPE_INSTRUCTIONS.get(
            response_type, self.RESPONSE_TYPE_INSTRUCTIONS["general"]
        )

        prompt = f"""Pripravi profesionalen poslovni odgovor na email za podjetje Luznar Electronics d.o.o. (PCB/SMT izdelava).

**Original email:**
Od: {original_email.get('sender', '')}
Zadeva: {original_email.get('subject', '')}
Kategorija: {kategorija}
Vsebina: {original_email.get('body', '')[:800]}

**Izvlečeni podatki:**
{izvleceni_str}

**Tip odgovora:** {response_type}
**Navodilo:** {type_instruction}

{f'**Dodatni kontekst:** {additional_context}' if additional_context else ''}

**Pravila:**
- Piši v slovenščini (ali angleščini če je original v angleščini)
- Bodi profesionalen in prijazen
- Vključi "Spoštovani," na začetku
- Podpis: "Lep pozdrav,\nLuznar Electronics d.o.o."
- NE dodajaj placeholder teksta v oglatih oklepajih

Vrni samo besedilo odgovora."""

        try:
            response = await self.llm.complete(
                prompt,
                task_type=TaskType.EMAIL_COMPOSITION,
                contains_sensitive=False
            )
            return response
        except Exception as e:
            print(f"Email response generation error: {e}")
            return f"Spoštovani,\n\nHvala za vaše sporočilo. Odgovorili vam bomo v najkrajšem možnem času.\n\nLep pozdrav,\nLuznar Electronics d.o.o."

    async def extract_attachments_info(self, attachments: list[dict]) -> dict:
        """Analizira priloge in izvleče informacije"""

        info = {
            "bom_files": [],
            "gerber_files": [],
            "other_files": []
        }

        for att in attachments:
            name = att.get("name", "").lower()

            if any(ext in name for ext in [".xlsx", ".xls", ".csv"]):
                if "bom" in name:
                    info["bom_files"].append(att)
                else:
                    info["other_files"].append(att)
            elif any(ext in name for ext in [".zip", ".rar", ".7z"]):
                if "gerber" in name:
                    info["gerber_files"].append(att)
                else:
                    info["other_files"].append(att)
            else:
                info["other_files"].append(att)

        return info


# Singleton instance
_email_agent: Optional[EmailAgent] = None


def get_email_agent() -> EmailAgent:
    """Vrne Email Agent singleton"""
    global _email_agent
    if _email_agent is None:
        _email_agent = EmailAgent()
    return _email_agent
