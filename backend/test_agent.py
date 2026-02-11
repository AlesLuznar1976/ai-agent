"""
Hiter test za AI Agent pipeline.
Pošlje sporočilo na Ollama → dobi tool call → izvede SQL → vrne odgovor.

Uporaba: python test_agent.py
"""

import asyncio
import json
import httpx
import os
import sys

# Dodaj backend v path
sys.path.insert(0, os.path.dirname(__file__))

OLLAMA_URL = "http://192.168.0.66:11434"
MODEL = "llama3.1:8b"

# Poenostavljen nabor tools za test
TEST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "count_records",
            "description": "Preštej zapise v tabeli. Uporabno za hitre statistike.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Ime tabele",
                        "enum": ["Partnerji", "Narocilo", "Ponudba", "Dobavnica",
                                 "Faktura", "Promet", "Materialni", "Kalkulacija",
                                 "DelPostopek", "DelovniNalog"]
                    }
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_partners",
            "description": "Iskanje poslovnih partnerjev po imenu ali šifri.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Iskalni niz"},
                    "limit": {"type": "integer", "description": "Max rezultatov", "default": 10}
                },
                "required": ["search"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Iskanje naročil. Filtri: partner, datum, modul (P=prodaja, N=nabava).",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_name": {"type": "string", "description": "Ime partnerja"},
                    "date_from": {"type": "string", "description": "Datum od (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Datum do (YYYY-MM-DD)"},
                    "limit": {"type": "integer", "description": "Max rezultatov", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "Seznam projektov iz ai_agent.Projekti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter po statusu"},
                    "limit": {"type": "integer", "description": "Max rezultatov", "default": 10}
                }
            }
        }
    },
]

SYSTEM_PROMPT = """Si AI asistent za LUZNAR d.o.o. - podjetje za izdelavo elektronskih vezij (PCB, SMT montaža).
Delaš z ERP sistemom LARGO.

TVOJA VLOGA:
- Pomagaš uporabnikom pri vsakodnevnem delu z ERP sistemom
- Iščeš in prikazuješ podatke iz baze
- Odgovarjaj v slovenščini
- Bodi konkreten - prikaži podatke v preglednih tabelah
- Za pridobitev podatkov VEDNO uporabi razpoložljiva orodja

ERP STRUKTURA:
- Partnerji (2385) - stranke in dobavitelji
- Narocilo (23016) - naročila (P=prodaja, N=nabava)
- Ponudba (8009) - ponudbe
- Dobavnica (19545) - dobavnice
- Promet (509008) - skladiščni premiki
- Materialni (265918) - material/zaloge
- Kalkulacija (256313) - kalkulacije
- DelPostopek (426203) - delovni postopki
- ai_agent.Projekti - projektno vodenje

Uporabnik: admin (vloga: admin)
"""


# Simulirani tool rezultati (da ne rabimo DB povezave za test)
MOCK_RESULTS = {
    "count_records": lambda args: json.dumps({
        "success": True,
        "data": {"table": args["table_name"], "count": {
            "Partnerji": 2385, "Narocilo": 23016, "Ponudba": 8009,
            "Dobavnica": 19545, "Faktura": 5420, "Promet": 509008,
            "Materialni": 265918, "Kalkulacija": 256313,
            "DelPostopek": 426203, "DelovniNalog": 3150
        }.get(args["table_name"], 0)}
    }),
    "search_partners": lambda args: json.dumps({
        "success": True,
        "data": [
            {"PaSifra": 1, "PaNaziv": "LUZNAR d.o.o.", "PaKraj": "Kranj", "PaDrzava": "SI"},
            {"PaSifra": 42, "PaNaziv": "Siemens AG", "PaKraj": "München", "PaDrzava": "DE"},
            {"PaSifra": 103, "PaNaziv": "Iskra Mehanizmi", "PaKraj": "Kranj", "PaDrzava": "SI"},
        ][:int(args.get("limit", 10))],
        "count": 3
    }),
    "search_orders": lambda args: json.dumps({
        "success": True,
        "data": [
            {"NaStNar": 24001, "NaStatus": "Odprt", "NaDatNar": "2026-01-15", "NaZnes": 12500.00, "PartnerNaziv": "Siemens AG"},
            {"NaStNar": 24002, "NaStatus": "V delu", "NaDatNar": "2026-01-20", "NaZnes": 8200.00, "PartnerNaziv": "Iskra Mehanizmi"},
        ],
        "count": 2
    }),
    "list_projects": lambda args: json.dumps({
        "success": True,
        "data": [
            {"id": 1, "stevilka_projekta": "PRJ-2026-001", "naziv": "Test projekt iz baze", "faza": "RFQ", "status": "Aktiven"},
        ],
        "count": 1
    }),
}


async def test_query(query: str):
    """Pošlje poizvedbo na Ollama in izvede tool calling cikel."""

    print(f"\n{'='*60}")
    print(f"UPORABNIK: {query}")
    print(f"{'='*60}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for round_num in range(3):  # Max 3 krogov
            print(f"\n--- Krog {round_num + 1} ---")

            # Pokliči Ollama
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "tools": TEST_TOOLS,
                    "stream": False,
                }
            )

            if response.status_code != 200:
                print(f"NAPAKA: {response.status_code} - {response.text}")
                return

            data = response.json()
            assistant_msg = data["message"]
            content = assistant_msg.get("content", "")
            tool_calls = assistant_msg.get("tool_calls", [])

            eval_count = data.get("eval_count", 0)
            eval_duration = data.get("eval_duration", 1)
            tokens_per_sec = (eval_count / eval_duration * 1_000_000_000) if eval_duration else 0

            print(f"   Tokens: {eval_count}, Hitrost: {tokens_per_sec:.1f} tok/s")

            if not tool_calls:
                # Končni odgovor
                print(f"\nAGENT: {content}")
                return

            # Izvedi tool klice
            messages.append(assistant_msg)

            for tc in tool_calls:
                func = tc["function"]
                tool_name = func["name"]
                arguments = func.get("arguments", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                print(f"   TOOL: {tool_name}({json.dumps(arguments, ensure_ascii=False)})")

                # Simulirani rezultat
                mock_handler = MOCK_RESULTS.get(tool_name)
                if mock_handler:
                    result = mock_handler(arguments)
                else:
                    result = json.dumps({"success": False, "error": f"Neznan tool: {tool_name}"})

                print(f"   RESULT: {result[:200]}...")

                messages.append({
                    "role": "tool",
                    "content": result
                })

    print(f"\nAGENT: (presežen max krogov)")


async def main():
    print("=" * 60)
    print("AI AGENT TEST - LUZNAR ERP")
    print(f"Model: {MODEL}")
    print(f"Ollama: {OLLAMA_URL}")
    print("=" * 60)

    # Test 1: Preprosta štetje
    await test_query("Koliko partnerjev imamo v bazi?")

    # Test 2: Iskanje
    await test_query("Poišči partnerja Siemens")

    # Test 3: Več orodij
    await test_query("Pokaži mi zadnja naročila in koliko projektov imamo")

    # Test 4: Splošno vprašanje (ne bi smel klicati tool)
    await test_query("Kaj je PCB?")

    print("\n" + "=" * 60)
    print("TESTI KONČANI")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
