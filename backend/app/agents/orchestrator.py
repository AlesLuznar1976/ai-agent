"""
Orchestrator - Glavni AI agent ki upravlja pogovor z uporabnikom.

Uporablja Ollama (lokalni LLM) s tool use za interakcijo z ERP bazo.
Claude API se pokliče SAMO ko lokalni agent ne zna rešiti zahteve.
"""

import json
import httpx
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.config import get_settings
from app.agents.erp_tools import ALL_TOOLS, WRITE_TOOL_NAMES, ESCALATION_TOOL_NAMES
from app.agents.tool_executor import get_tool_executor

settings = get_settings()

SYSTEM_PROMPT = """Si AI asistent za LUZNAR d.o.o. - podjetje za izdelavo elektronskih vezij (PCB, SMT montaža).
Delaš z ERP sistemom LARGO.

TVOJA VLOGA:
- Pomagaš uporabnikom pri vsakodnevnem delu z ERP sistemom
- Iščeš in prikazuješ podatke iz baze
- Ustvarjaš/posodabljaš zapise (vedno s potrditivjo uporabnika)
- Za kompleksne analize/skripte pokličeš ask_claude_for_script

ERP STRUKTURA:
- Partnerji (PaSifra, PaNaziv, PaKraj, PaEMail) - stranke in dobavitelji (2385)
- Narocilo (NaStNar, NaPartPlac, NaZnes, NaModul P/N, NaDatNar) - naročila (23016)
- Ponudba (PonStPon, PonPart, PonZnes, PonDatPon) - ponudbe (8009)
- Dobavnica (DNsStDNs, DNsPartPlac, DNsDatDNs) - dobavnice (19545)
- Faktura - fakture
- Promet - skladiščni premiki (509008)
- Materialni - material/zaloge (265918)
- Kalkulacija - kalkulacije (256313)
- Kosovnica - BOM/kosovnice
- DelPostopek - delovni postopki (426203)
- DelovniNalog - delovni nalogi
- PotekDelovnegaNaloga - potek proizvodnje (489530)
- ai_agent.Projekti - projektno vodenje (faze: RFQ→Ponudba→Naročilo→Proizvodnja→Dobava)
- ai_agent.Emaili - emaili
- ai_agent.DelovniNalogi - delovni nalogi za projekte

PRAVILA:
1. Za branje podatkov uporabi ustrezno orodje (search_partners, search_orders, itd.)
2. Za pisanje (create_project, update_project, itd.) VEDNO poprosi za potrditev
3. Če ne znaš rešiti ali je zahteva kompleksna - uporabi ask_claude_for_script
4. VEDNO odgovarjaj v slovenščini
5. Bodi konkreten - prikaži podatke v preglednih tabelah
6. Nikoli ne izmišljuj podatkov - vedno uporabi orodja za pridobitev pravih podatkov
7. Pri run_custom_query vedno uporabi SELECT s TOP omejitvijo
8. Ko uporabnik vpraša za "povzetek mailov", "pregled emailov", "preveri maile", "stanje pošte" - VEDNO uporabi summarize_emails orodje
9. Ko uporabnik vpraša za "dnevno poročilo", "povzetek po nabiralnikih", "poročilo za danes" - uporabi daily_report orodje
10. Ko dobiš rezultat od orodja, ga CELOTNO prikaži uporabniku - ne skrajšuj in ne spreminjaj besedila

KONTEKST:
- Današnji datum: {today}
- Uporabnik: {username} (vloga: {role})
- Aktiven projekt: {current_project}
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

        system_prompt = SYSTEM_PROMPT.format(
            today=datetime.now().strftime("%Y-%m-%d"),
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

        # Dodaj novo sporočilo
        messages.append({"role": "user", "content": message})

        # Tool use loop
        all_tool_calls = []
        pending_actions = []

        for round_num in range(self.MAX_TOOL_ROUNDS):
            # Pokliči Ollama
            response = await self._call_ollama(messages, ALL_TOOLS)

            if not response:
                return AgentResponse(
                    message="Oprostite, prišlo je do napake pri obdelavi. Poskusite znova.",
                    suggested_commands=["Pomoč", "Seznam projektov"]
                )

            assistant_message = response.get("message", {})
            content = assistant_message.get("content", "")
            tool_calls = assistant_message.get("tool_calls", [])

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

                # Izvedi tool
                result = await self.executor.execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    user_id=user_id,
                    user_role=user_role
                )

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
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "tools": tools,
                        "stream": False,
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


# Singleton
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
