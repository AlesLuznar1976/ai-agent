"""
Claude Script Writer - Claude API za pisanje SQL/Python skript.

Pokliče se SAMO ko lokalni agent (Ollama) ne zna rešiti zahteve.
Claude dobi kontekst o ERP strukturi in napiše skripto ki jo
agent nato varno izvede.
"""

import re
from typing import Optional

from app.config import get_settings

settings = get_settings()

ERP_CONTEXT = """
LARGO ERP (MSSQL) baza za LUZNAR d.o.o. - proizvodnja elektronskih vezij (PCB/SMT).

KLJUČNE TABELE (dbo schema):
- Partnerji (2385 vrstic): PaSifra (PK int), PaNaziv (char 35), PaKraj, PaSifDrzave, PaEMail, PaTelefon1, PaEDavStDDV (davčna), PaSifVrst (tip)
- Narocilo (23016): NaStNar (PK int), NaPartPlac (partner plačnik), NaPartPrjm (partner prejemnik), NaDatNar (datum), NaZnes (znesek), NaStatus, NaModul (P=prodaja, N=nabava)
- NarociloPostav: NpStNar, NpPostSt (zaporedna), NpSifra (artikel), NpNaziv, NpKol (količina), NpCena, NpZnes
- Ponudba (8009): PonStPon (PK), PonPart, PonDatPon, PonZnes, PonStatus, PonModul
- PonudbaPostav: PpStPon, PpPostSt, PpSifra, PpNaziv, PpKol, PpCena, PpZnes
- Dobavnica (19545): DNsStDNs (PK), DNsPartPlac, DNsDatDNs, DNsZnes, DNsStatus
- Faktura: FaStFak (PK), FaPartPlac, FaDatFak, FaZnes
- Promet (509008): skladiščni premiki, PrSmSifra (skladišče), PrSifra (artikel), PrKol (količina), PrDatum
- Materialni (265918): MaSifra (artikel), MaNaziv, MaSmSifra (skladišče), stanje zalog
- Kalkulacija (256313): KStKalk (PK), KNaziv, KTipDok, KStDok
- KalkulacijaPostav (1.28M): postavke kalkulacije
- Kosovnica: KosSifra (artikel), KosSest (sestavina), KosKol (količina) - BOM
- DelPostopek (426203): DPSifra (artikel), DPStOp (št. operacije), DPNazOp (naziv) - delovni postopki
- DelovniNalog: DNsStDNs - delovni nalogi
- PotekDelovnegaNaloga (489530): PDNStDNs, potek dela

- ai_agent.Projekti: id, stevilka_projekta, naziv, stranka_id, faza, status, datum_rfq
- ai_agent.Emaili: id, zadeva, posiljatelj, kategorija, status, datum, projekt_id
- ai_agent.DelovniNalogi: id, projekt_id, largo_dn_id, stevilka_dn, kolicina, status

NAMING CONVENTIONS:
- Stolpci imajo prefix = okrajšava tabele (Pa=Partnerji, Na=Narocilo, Pon=Ponudba, DNs=DelovniNalog)
- NameOper + Datum = operater in datum v vsaki tabeli
- ZG suffix = zgodovina, Postav = postavke/line items, DP = dodatna polja, Arh = arhiv
- Leto suffix = letni agregati

PRAVILA ZA PISANJE SQL:
1. Uporabi SAMO SELECT stavke
2. VEDNO dodaj TOP omejitev (max 1000)
3. NIKOLI ne piši DROP, DELETE, UPDATE, INSERT, ALTER, EXEC
4. Uporabi RTRIM() za char polja (imajo trailing spaces)
5. Za JOIN uporabi ustrezne PK/FK relacije
6. Če je mogoče, dodaj komentarje kaj poizvedba dela
"""


class ClaudeScriptWriter:
    """Kliče Claude API za pisanje SQL/Python skript."""

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model or "claude-sonnet-4-5-20250929"
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def write_script(self, task_description: str, context: str = "") -> dict:
        """
        Claude napiše SQL skripto za dano nalogo.

        Returns:
            dict z ključi:
            - script_type: "sql" ali "python"
            - script: dejanska skripta
            - explanation: razlaga kaj dela
        """

        if not self.api_key:
            return {
                "success": False,
                "error": "Claude API ključ ni konfiguriran. Nastavi ANTHROPIC_API_KEY."
            }

        prompt = f"""Napiši SQL poizvedbo za naslednjo nalogo:

NALOGA: {task_description}

{f"DODATNI KONTEKST: {context}" if context else ""}

ZAHTEVE:
- Vrni SAMO SQL poizvedbo (SELECT)
- Dodaj TOP omejitev
- Uporabi RTRIM() za char polja
- Dodaj komentar kaj poizvedba dela
- Vrni v formatu:
```sql
-- Opis
SELECT ...
```"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=ERP_CONTEXT,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract SQL iz odgovora
            sql_match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
            if sql_match:
                script = sql_match.group(1).strip()
            else:
                # Poskusi najti SELECT
                lines = content.strip().split('\n')
                sql_lines = []
                in_sql = False
                for line in lines:
                    if line.strip().upper().startswith('SELECT') or line.strip().startswith('--'):
                        in_sql = True
                    if in_sql:
                        sql_lines.append(line)
                script = '\n'.join(sql_lines) if sql_lines else content

            # Razlaga
            explanation = content.split('```')[0].strip() if '```' in content else "Claude je napisal poizvedbo."

            return {
                "success": True,
                "script_type": "sql",
                "script": script,
                "explanation": explanation
            }

        except Exception as e:
            return {"success": False, "error": f"Claude API napaka: {str(e)}"}

    async def write_and_execute(
        self,
        task_description: str,
        context: str,
        executor  # ToolExecutor instance
    ) -> dict:
        """Napiše skripto IN jo izvede (po varnostni kontroli)."""

        # 1. Claude napiše skripto
        script_result = await self.write_script(task_description, context)
        if not script_result.get("success"):
            return script_result

        script = script_result["script"]

        # 2. Varnostna kontrola
        safety = self._safety_check(script)
        if not safety["safe"]:
            return {
                "success": False,
                "error": f"Skripta ni varna: {safety['reason']}",
                "script": script
            }

        # 3. Izvedi skripto
        try:
            exec_result = executor._run_custom_query({
                "description": f"Claude skripta: {task_description}",
                "query": script
            })

            return {
                "success": True,
                "script": script,
                "explanation": script_result.get("explanation", ""),
                "data": exec_result.get("data", []),
                "count": exec_result.get("count", 0)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Napaka pri izvajanju skripte: {str(e)}",
                "script": script
            }

    @staticmethod
    def _safety_check(script: str) -> dict:
        """Preveri varnost SQL skripte."""
        script_upper = script.upper()

        # Prepovedane operacije
        forbidden = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
            "EXEC", "EXECUTE", "TRUNCATE", "CREATE", "GRANT",
            "REVOKE", "DENY", "xp_", "sp_"
        ]

        for kw in forbidden:
            if re.search(rf'\b{kw}\b', script_upper):
                return {"safe": False, "reason": f"Vsebuje prepovedano operacijo: {kw}"}

        # Mora se začeti s SELECT ali komentarjem
        first_statement = script.strip()
        while first_statement.startswith('--'):
            first_statement = '\n'.join(first_statement.split('\n')[1:]).strip()

        if not first_statement.upper().startswith('SELECT'):
            return {"safe": False, "reason": "Skripta se ne začne s SELECT"}

        return {"safe": True}


# Singleton
_writer: Optional[ClaudeScriptWriter] = None


def get_scriptwriter() -> ClaudeScriptWriter:
    global _writer
    if _writer is None:
        _writer = ClaudeScriptWriter()
    return _writer
