"""
Orchestrator - Glavni AI agent ki upravlja pogovor z uporabnikom.

Uporablja Ollama (lokalni LLM) s tool use za interakcijo z ERP bazo.
Claude API se pokliče SAMO ko lokalni agent ne zna rešiti zahteve.
"""

import json
import logging
import re
import httpx
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from app.config import get_settings
from app.agents.erp_tools import ALL_TOOLS, WRITE_TOOL_NAMES, ESCALATION_TOOL_NAMES
from app.agents.tool_executor import get_tool_executor

settings = get_settings()

SYSTEM_PROMPT = """JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI. NIKOLI ne odgovarjaj v angleščini ali kateremkoli drugem jeziku.

Si AI asistent za LUZNAR d.o.o. - podjetje za izdelavo elektronskih vezij (PCB, SMT montaža).
Delaš z ERP sistemom LARGO. DANAŠNJI DATUM JE: {today}. Trenutno leto je {year}. VEDNO uporabi leto {year} za vse poizvedbe.

TVOJA VLOGA:
- Pomagaš uporabnikom pri vsakodnevnem delu z ERP sistemom
- Iščeš in prikazuješ podatke iz baze
- Ustvarjaš/posodabljaš zapise (vedno s potrditivjo uporabnika)
- Za kompleksne analize/skripte pokličeš ask_claude_for_script ali ask_claude_for_analysis

IZBIRA ORODJA:
- "koliko naročil" → search_orders (z date_from/date_to) ali count_records (tabela Narocilo)
- "pokaži naročila" → search_orders
- "poišči partnerja" → search_partners
- "koliko zapisov" → count_records
- trendi, TOP N, primerjave, statistike → ask_claude_for_analysis
- kompleksne poizvedbe → ask_claude_for_script
- SAMO če noben drug tool ne ustreza → run_custom_query

PRIMERI DATUMSKIH PARAMETROV (leto {year}!):
- "v januarju" → date_from="{year}-01-01", date_to="{year}-01-31"
- "v februarju" → date_from="{year}-02-01", date_to="{year}-02-28"
- "v marcu" → date_from="{year}-03-01", date_to="{year}-03-31"
- "letos" → date_from="{year}-01-01", date_to="{today}"

ERP TABELE (dbo schema, MSSQL):
- dbo.Partnerji (PaSifra, PaNaziv, PaKraj, PaEMail) - stranke in dobavitelji
- dbo.Narocilo (NaStNar, NaPartPlac, NaZnes, NaModul P/N, NaDatNar) - NAROČILA
- dbo.Ponudba (PonStPon, PonPart, PonZnes, PonDatPon) - ponudbe
- dbo.Dobavnica (DNsStDNs, DNsPartPlac, DNsDatDNs) - dobavnice
- dbo.Faktura - fakture
- dbo.Promet - skladiščni premiki
- dbo.Materialni - material/zaloge
- dbo.Kalkulacija - kalkulacije
- dbo.Kosovnica - BOM/kosovnice
- dbo.DelPostopek - delovni postopki
- dbo.DelovniNalog - delovni nalogi
- dbo.PotekDelovnegaNaloga - potek proizvodnje
- ai_agent.Projekti - projektno vodenje
- ai_agent.Emaili - emaili
- ai_agent.DelovniNalogi - delovni nalogi za projekte

PRAVILA:
1. Za branje podatkov uporabi ustrezno orodje (search_partners, search_orders, itd.)
2. Za pisanje (create_project, update_project, itd.) VEDNO poprosi za potrditev
3. Če ne znaš rešiti ali je zahteva kompleksna - uporabi ask_claude_for_script
4. VEDNO odgovarjaj v SLOVENŠČINI - nikoli v angleščini ali drugem jeziku!
5. Bodi konkreten - prikaži podatke v preglednih tabelah
6. Nikoli ne izmišljuj podatkov - vedno uporabi orodja za pridobitev pravih podatkov
7. Pri run_custom_query vedno uporabi dbo. prefix in SELECT s TOP omejitvijo
8. Ko uporabnik vpraša za "povzetek mailov", "pregled emailov", "preveri maile" - VEDNO uporabi summarize_emails
9. Ko uporabnik vpraša za "dnevno poročilo", "povzetek po nabiralnikih" - uporabi daily_report BREZ parametra datum
10. Ko dobiš rezultat s poljem "povzetek", prikaži CELOTNO besedilo DOBESEDNO
11. NIKOLI ne izmišljuj datumov - uporabi {today} kot današnji datum, leto je {year}
12. Za podatkovne analize (trendi, primerjave, statistike, agregacije, TOP N) uporabi ask_claude_for_analysis
13. Za preproste poizvedbe (iskanje, filtriranje, štetje) uporabi obstoječa orodja ali ask_claude_for_script
14. Parametri za datume v orodjih so: date_from in date_to (NE datum_od/datum_do/start_date/end_date)
15. Leto za datume je VEDNO {year} - NIKOLI ne uporabi 2023, 2024 ali 2025!

KONTEKST:
- Uporabnik: {username} (vloga: {role})
- Aktiven projekt: {current_project}

POMEMBNO: Tvoj odgovor MORA biti v slovenščini!
"""


class AgentResponse(BaseModel):
    """Odgovor agenta"""
    message: str
    actions: list[dict] = []
    needs_confirmation: bool = False
    suggested_commands: list[str] = []
    tool_calls_made: list[dict] = []


class Orchestrator:
    """
    Glavni agent:
    - Prejme sporočilo od uporabnika
    - Pošlje Ollama modelu z orodji
    - Izvede tool klice
    - Zbere rezultate in odgovori uporabniku
    """

    MAX_TOOL_ROUNDS = 5  # Max krogov tool calling

    # Regex za odstranitev <think>...</think> blokov iz qwen3 odgovorov
    _THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

    @classmethod
    def _strip_think(cls, text: str) -> str:
        """Odstrani <think>...</think> bloke iz qwen3 odgovorov."""
        if not text:
            return text
        return cls._THINK_RE.sub("", text).strip()

    def __init__(self):
        self.ollama_url = settings.ollama_url
        self.model = settings.ollama_tool_model or settings.ollama_model
        self.executor = get_tool_executor()

    async def process(
        self,
        message: str,
        user_id: int,
        username: str,
        user_role: str,
        current_project_id: Optional[int] = None,
        conversation_history: Optional[list[dict]] = None
    ) -> AgentResponse:
        """Procesira uporabniško sporočilo."""

        now = datetime.now()
        system_prompt = SYSTEM_PROMPT.format(
            today=now.strftime("%Y-%m-%d"),
            year=now.year,
            username=username,
            role=user_role,
            current_project=current_project_id or "ni izbran"
        )

        # Sestavi messages za Ollama
        messages = [{"role": "system", "content": system_prompt}]

        # Dodaj zgodovino pogovora (zadnjih N sporočil)
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Dodaj novo sporočilo z injiciranim kontekstom (LLM bolje upošteva user message)
        augmented_message = f"[Datum: {now.strftime('%Y-%m-%d')}, leto: {now.year}. Odgovori v slovenščini.]\n{message}"
        messages.append({"role": "user", "content": augmented_message})

        # Tool use loop
        all_tool_calls = []
        pending_actions = []

        for round_num in range(self.MAX_TOOL_ROUNDS):
            # Pokliči Ollama
            response = await self._call_ollama(messages, ALL_TOOLS)

            if not response:
                print(f"[ORCHESTRATOR] Ollama returned None!", flush=True)
                return AgentResponse(
                    message="Oprostite, prišlo je do napake pri obdelavi. Poskusite znova.",
                    suggested_commands=["Pomoč", "Seznam projektov"]
                )

            assistant_message = response.get("message", {})
            content = self._strip_think(assistant_message.get("content", ""))
            # Posodobi content v sporočilu (brez <think> blokov)
            assistant_message["content"] = content
            tool_calls = assistant_message.get("tool_calls", [])

            print(f"[ORCHESTRATOR] Round {round_num} | Content: {(content or '')[:200]} | Tool calls: {len(tool_calls)} | Tools: {[tc.get('function',{}).get('name','?') for tc in tool_calls]}", flush=True)

            # Če ni tool klicev, vrni odgovor
            if not tool_calls:
                return AgentResponse(
                    message=content or "Kako vam lahko pomagam?",
                    actions=[a["pending_action"] for a in pending_actions],
                    needs_confirmation=len(pending_actions) > 0,
                    suggested_commands=self._suggest_commands(content),
                    tool_calls_made=all_tool_calls
                )

            # Dodaj assistant sporočilo v messages
            messages.append(assistant_message)

            # Izvedi tool klice
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                arguments = func.get("arguments", {})

                # Parse arguments če so string
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                print(f"[ORCHESTRATOR] Tool call: {tool_name} | Args: {json.dumps(arguments, ensure_ascii=False, default=str)[:500]}", flush=True)

                # Izvedi tool
                result = await self.executor.execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    user_id=user_id,
                    user_role=user_role
                )

                print(f"[ORCHESTRATOR] Tool result: {tool_name} | success={result.get('success')} | error={result.get('error', '-')} | keys={list(result.keys())}", flush=True)

                all_tool_calls.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result_success": result.get("success", False)
                })

                # Če write tool - shrani pending action
                if result.get("needs_confirmation"):
                    pending_actions.append(result)

                # Dodaj tool rezultat v messages za naslednji krog
                result_content = json.dumps(result, ensure_ascii=False, default=str)
                # Omejimo velikost rezultata za LLM kontekst
                if len(result_content) > 4000:
                    # Skrajšaj - obdrži strukturo ampak omejimo podatke
                    truncated = result.copy()
                    if "data" in truncated and isinstance(truncated["data"], list):
                        truncated["data"] = truncated["data"][:10]
                        truncated["_truncated"] = True
                        truncated["_total"] = result.get("count", len(result.get("data", [])))
                    result_content = json.dumps(truncated, ensure_ascii=False, default=str)

                messages.append({
                    "role": "tool",
                    "content": result_content
                })

        # Če smo prišli čez max krogov
        return AgentResponse(
            message="Obdelava je bila preveč kompleksna. Poskusite s preprostejšo zahtevo.",
            suggested_commands=["Pomoč"]
        )

    async def _call_ollama(self, messages: list[dict], tools: list[dict]) -> Optional[dict]:
        """Pokliči Ollama API z tool use."""

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "tools": tools,
                        "stream": False,
                        "think": False,
                    }
                )

                if response.status_code != 200:
                    print(f"Ollama napaka: {response.status_code} - {response.text}")
                    return None

                return response.json()

        except httpx.TimeoutException:
            print("Ollama timeout")
            return None
        except Exception as e:
            print(f"Ollama napaka: {e}")
            return None

    def _suggest_commands(self, content: str) -> list[str]:
        """Predlagaj ukaze glede na kontekst odgovora."""
        suggestions = []
        content_lower = (content or "").lower()

        if "partner" in content_lower or "stranka" in content_lower:
            suggestions.extend(["Pokaži naročila za to stranko", "Podrobnosti partnerja"])
        if "naročil" in content_lower:
            suggestions.extend(["Pokaži postavke naročila", "Stanje dobav"])
        if "projekt" in content_lower:
            suggestions.extend(["Časovnica projekta", "Dokumenti projekta"])
        if "email" in content_lower:
            suggestions.extend(["Dodeli email projektu", "Kategoriziraj email"])

        if not suggestions:
            suggestions = ["Pomoč", "Seznam projektov", "Preveri emaile"]

        return suggestions[:4]


    async def process_with_files(
        self,
        message: str,
        file_infos: list[dict],
        user_id: int,
        username: str,
        user_role: str,
        current_project_id: Optional[int] = None,
    ) -> AgentResponse:
        """
        Procesira sporočilo z datotekami preko Claude Opus 4 (vision/document support).

        file_infos: seznam dict-ov iz file_processor.process_uploaded_file()
        """
        import anthropic

        if not settings.anthropic_api_key:
            return AgentResponse(
                message="Anthropic API ključ ni konfiguriran. Nastavi ANTHROPIC_API_KEY.",
                suggested_commands=["Pomoč"],
            )

        now = datetime.now()

        system_prompt = (
            f"JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI. NIKOLI ne odgovarjaj v angleščini.\n\n"
            f"Si AI asistent za LUZNAR d.o.o. - podjetje za izdelavo elektronskih vezij (PCB, SMT montaža).\n"
            f"Delaš z ERP sistemom LARGO. DANAŠNJI DATUM JE: {now.strftime('%Y-%m-%d')}.\n\n"
            f"Uporabnik ti je poslal datoteke skupaj s sporočilom. Analiziraj datoteke in odgovori na zahtevo.\n"
            f"Bodi natančen, konkreten in uporaben. Če je dokument v angleščini, vseeno odgovori v slovenščini.\n\n"
            f"FORMATIRANJE ODGOVORA:\n"
            f"- Uporabi Markdown za strukturiran, pregleden odgovor\n"
            f"- Za podatke iz dokumentov uporabi **tabele** (| Stolpec | Stolpec |)\n"
            f"- Uporabi **krepko pisavo** za ključne vrednosti in naslove\n"
            f"- Uporabi ## naslove za razdelke (npr. ## Povzetek, ## Ključni podatki, ## Ugotovitve)\n"
            f"- Za sezname uporabi - ali številčne sezname\n"
            f"- Za slike PCB/elektronike: opiši komponente, oznake, stanje, morebitne napake\n"
            f"- Za dokumente: izvleci ključne podatke strukturirano\n"
            f"- Kratko in jedrnato, brez odvečnega besedila\n\n"
            f"Kontekst:\n"
            f"- Uporabnik: {username} (vloga: {user_role})\n"
            f"- Aktiven projekt: {current_project_id or 'ni izbran'}\n"
        )

        # Zgradi content blocks za Claude Messages API
        content_blocks: list[dict] = []

        # Najprej slike in PDF-ji kot native content blocks
        text_parts: list[str] = []

        for fi in file_infos:
            if fi["type"] in ("image", "document"):
                content_blocks.append(fi["content_block"])
            elif fi["type"] == "text":
                text_parts.append(fi["text"])
            elif fi["type"] == "unsupported":
                text_parts.append(fi["text"])

        # Dodaj ekstrahirane tekste kot en text block
        if text_parts:
            content_blocks.append({
                "type": "text",
                "text": "\n\n".join(text_parts),
            })

        # Uporabniško sporočilo vedno na koncu
        if message:
            content_blocks.append({
                "type": "text",
                "text": message,
            })
        elif not content_blocks:
            content_blocks.append({
                "type": "text",
                "text": "Analiziraj priložene datoteke.",
            })

        try:
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            model = settings.anthropic_vision_model

            logger.info(f"[ORCHESTRATOR] Calling Claude {model} with {len(content_blocks)} content blocks")

            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": content_blocks}],
            )

            response_text = response.content[0].text

            logger.info(f"[ORCHESTRATOR] Claude response: {response_text[:200]}")

            return AgentResponse(
                message=response_text,
                suggested_commands=self._suggest_commands(response_text),
            )

        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Claude API error: {e}")
            return AgentResponse(
                message=f"Napaka pri klicu Claude API: {str(e)}",
                suggested_commands=["Pomoč"],
            )


# Singleton
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
