"""
Test AI Agent pipeline z PRAVO SQL bazo.
Standalone - ne rabi celotne app strukture.

Uporaba: python test_agent_real.py
"""

import asyncio
import json
import httpx
import pyodbc
from datetime import datetime

OLLAMA_URL = "http://192.168.0.66:11434"
MODEL = "llama3.1:8b"

# DB connection - prilagodi!
DB_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LUZNAR-2018\\LARGO;"
    "DATABASE=LUZNAR;"
    "UID=Alesl;"
    "PWD=homeland;"
    "TrustServerCertificate=yes;"
)

# Tools za Ollama
TOOLS = [
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
- Za pridobitev podatkov VEDNO uporabi razpoložljiva orodja
- Odgovarjaj v slovenščini
- Bodi konkreten - prikaži podatke v preglednih tabelah

ERP STRUKTURA:
- Partnerji (PaSifra, PaNaziv, PaKraj) - stranke in dobavitelji (2385)
- Narocilo (NaStNar, NaPartPlac, NaZnes, NaModul P/N) - naročila (23016)
- Ponudba (PonStPon, PonPart, PonZnes) - ponudbe (8009)
- ai_agent.Projekti - projektno vodenje

Uporabnik: admin (vloga: admin)
"""


def execute_sql(query, params=()):
    """Izvede SQL in vrne rezultate."""
    conn = pyodbc.connect(DB_CONN_STR)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, val in enumerate(row):
                    if isinstance(val, datetime):
                        row_dict[columns[i]] = val.isoformat()
                    elif isinstance(val, bytes):
                        row_dict[columns[i]] = val.hex()
                    elif isinstance(val, str):
                        row_dict[columns[i]] = val.strip()
                    else:
                        row_dict[columns[i]] = val
                rows.append(row_dict)
            return rows
        return []
    finally:
        conn.close()


def execute_tool(tool_name, args):
    """Izvede tool klic z pravim SQL."""

    if tool_name == "count_records":
        table = args["table_name"]
        allowed = {"Partnerji", "Narocilo", "Ponudba", "Dobavnica",
                    "Faktura", "Promet", "Materialni", "Kalkulacija",
                    "DelPostopek", "DelovniNalog"}
        if table not in allowed:
            return {"success": False, "error": f"Tabela {table} ni dovoljena"}
        rows = execute_sql(f"SELECT COUNT(*) as cnt FROM dbo.{table}")
        return {"success": True, "data": {"table": table, "count": rows[0]["cnt"]}}

    elif tool_name == "search_partners":
        search = args.get("search", "")
        limit = min(args.get("limit", 10), 50)
        rows = execute_sql(
            "SELECT TOP (?) PaSifra, RTRIM(PaNaziv) as PaNaziv, RTRIM(PaKraj) as PaKraj, "
            "RTRIM(PaSifDrzave) as PaDrzava, RTRIM(PaEMail) as PaEMail "
            "FROM dbo.Partnerji WHERE PaNaziv LIKE ? ORDER BY PaNaziv",
            (limit, f"%{search}%")
        )
        return {"success": True, "data": rows, "count": len(rows)}

    elif tool_name == "search_orders":
        limit = min(args.get("limit", 10), 50)
        conditions = ["1=1"]
        params = []
        if args.get("partner_name"):
            conditions.append("p.PaNaziv LIKE ?")
            params.append(f"%{args['partner_name']}%")
        if args.get("date_from"):
            conditions.append("n.NaDatNar >= ?")
            params.append(args["date_from"])
        where = " AND ".join(conditions)
        rows = execute_sql(
            f"SELECT TOP (?) n.NaStNar, RTRIM(n.NaStatus) as NaStatus, n.NaDatNar, "
            f"n.NaZnes, RTRIM(p.PaNaziv) as PartnerNaziv "
            f"FROM dbo.Narocilo n LEFT JOIN dbo.Partnerji p ON n.NaPartPlac = p.PaSifra "
            f"WHERE {where} ORDER BY n.NaDatNar DESC",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    elif tool_name == "list_projects":
        limit = min(args.get("limit", 10), 50)
        conditions = ["1=1"]
        params = []
        if args.get("status"):
            conditions.append("status = ?")
            params.append(args["status"])
        where = " AND ".join(conditions)
        rows = execute_sql(
            f"SELECT TOP (?) id, stevilka_projekta, naziv, faza, status "
            f"FROM ai_agent.Projekti WHERE {where} ORDER BY datum_rfq DESC",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    return {"success": False, "error": f"Neznan tool: {tool_name}"}


async def test_query(query):
    """Pošlje poizvedbo in izvede tool calling cikel."""

    print(f"\n{'='*60}")
    print(f"UPORABNIK: {query}")
    print(f"{'='*60}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for round_num in range(3):
            print(f"\n--- Krog {round_num + 1} ---")

            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False}
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
            tok_s = (eval_count / eval_duration * 1e9) if eval_duration else 0
            print(f"   Tokens: {eval_count}, Hitrost: {tok_s:.1f} tok/s")

            if not tool_calls:
                print(f"\nAGENT: {content}")
                return

            messages.append(assistant_msg)

            for tc in tool_calls:
                func = tc["function"]
                tool_name = func["name"]
                arguments = func.get("arguments", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                print(f"   TOOL: {tool_name}({json.dumps(arguments, ensure_ascii=False)})")

                # PRAVI SQL!
                result = execute_tool(tool_name, arguments)
                result_json = json.dumps(result, ensure_ascii=False, default=str)

                display = result_json[:500] + "..." if len(result_json) > 500 else result_json
                print(f"   RESULT: {display}")

                messages.append({"role": "tool", "content": result_json})

    print("\nAGENT: (presežen max krogov)")


async def main():
    print("=" * 60)
    print("AI AGENT TEST - PRAVI SQL")
    print(f"Model: {MODEL}")
    print(f"Ollama: {OLLAMA_URL}")
    print("=" * 60)

    # Preveri DB
    print("\nPreverjam DB povezavo...")
    try:
        rows = execute_sql("SELECT COUNT(*) as cnt FROM dbo.Partnerji")
        print(f"   OK - {rows[0]['cnt']} partnerjev v bazi")
    except Exception as e:
        print(f"   NAPAKA DB: {e}")
        print("   Prilagodi DB_CONN_STR v test_agent_real.py!")
        return

    # Testi
    await test_query("Koliko partnerjev imamo v bazi?")
    await test_query("Poišči partnerja LUZNAR")
    await test_query("Pokaži mi aktivne projekte")
    await test_query("Pokaži mi zadnja naročila")

    print("\n" + "=" * 60)
    print("TESTI KONČANI")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
