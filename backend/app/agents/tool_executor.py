"""
Tool Executor - Varno izvajanje tool klicev iz AI agenta.

Vsak tool call iz Ollama modela se izvede tukaj.
- Bralni tools: direkten SQL na bazo (parametrizirano)
- Pisalni tools: gredo čez CakajočeAkcije (čakajo potrditev)
- Escalation: posreduje Claude-u
"""

import json
import re
import pyodbc
from decimal import Decimal
from typing import Any, Optional
from datetime import datetime, date

from app.config import get_settings
from app.agents.erp_tools import WRITE_TOOL_NAMES, READ_TOOL_NAMES, ESCALATION_TOOL_NAMES

settings = get_settings()


class ToolExecutor:
    """Izvaja tool klice iz AI agenta."""

    def __init__(self):
        self._conn_str = self._build_connection_string()

    def _build_connection_string(self) -> str:
        """Zgradi pyodbc connection string iz SQLAlchemy URL."""
        from urllib.parse import urlparse, parse_qs, unquote
        url = settings.database_url

        # Format 1: odbc_connect parameter (direkten ODBC string)
        if "odbc_connect=" in url:
            clean_url = url.replace("mssql+pyodbc://", "http://localhost/")
            parsed = urlparse(clean_url)
            params = parse_qs(parsed.query)
            odbc_str = params.get("odbc_connect", [""])[0]
            return unquote(odbc_str) if "%3" in odbc_str else odbc_str

        # Format 2: Standardni SQLAlchemy URL
        clean_url = url.replace("mssql+pyodbc://", "http://")
        parsed = urlparse(clean_url)

        user = unquote(parsed.username or "")
        password = unquote(parsed.password or "")
        host = unquote(parsed.hostname or "localhost")
        port = parsed.port
        db_name = parsed.path.lstrip("/")

        params = parse_qs(parsed.query)
        driver = params.get("driver", ["ODBC Driver 17 for SQL Server"])[0].replace("+", " ")
        trust_cert = params.get("TrustServerCertificate", ["yes"])[0]

        server = host
        if port:
            server = f"{host},{port}"

        conn_parts = [
            f"DRIVER={{{driver}}};",
            f"SERVER={server};",
            f"DATABASE={db_name};",
        ]

        if user and password:
            conn_parts.append(f"UID={user};")
            conn_parts.append(f"PWD={password};")

        conn_parts.append(f"TrustServerCertificate={trust_cert};")

        return "".join(conn_parts)

    def _get_connection(self) -> pyodbc.Connection:
        """Pridobi novo DB povezavo."""
        return pyodbc.connect(self._conn_str)

    def _execute_select(self, query: str, params: tuple = ()) -> list[dict]:
        """Izvede SELECT poizvedbo in vrne rezultate kot seznam slovarjev."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, val in enumerate(row):
                    if isinstance(val, datetime):
                        row_dict[columns[i]] = val.isoformat()
                    elif isinstance(val, date):
                        row_dict[columns[i]] = val.isoformat()
                    elif isinstance(val, Decimal):
                        row_dict[columns[i]] = float(val)
                    elif isinstance(val, bytes):
                        row_dict[columns[i]] = val.hex()
                    elif isinstance(val, str):
                        row_dict[columns[i]] = val.strip()
                    else:
                        row_dict[columns[i]] = val
                rows.append(row_dict)
            return rows
        finally:
            conn.close()

    def _execute_count(self, query: str, params: tuple = ()) -> int:
        """Izvede COUNT poizvedbo."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _get_user_email(self, user_id: int) -> str:
        """Pridobi email uporabnika iz baze."""
        rows = self._execute_select(
            "SELECT email FROM ai_agent.Uporabniki WHERE id = ?",
            (user_id,)
        )
        if rows and rows[0].get("email"):
            return rows[0]["email"]
        return ""

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        user_id: int,
        user_role: str
    ) -> dict:
        """
        Izvede tool klic.

        Returns:
            dict z ključi:
            - success: bool
            - data: rezultat (za bralne tools)
            - needs_confirmation: bool (za pisalne tools)
            - pending_action: dict (opis akcije za potrditev)
            - error: str (ob napaki)
        """

        # Nastavi kontekst uporabnika za tool klice
        self._current_user_id = user_id
        self._current_user_role = user_role

        try:
            # Escalation tools
            if tool_name in ESCALATION_TOOL_NAMES:
                return await self._execute_escalation(tool_name, arguments)

            # Write tools - ne izvedi, samo pripravi za potrditev
            if tool_name in WRITE_TOOL_NAMES:
                return self._prepare_write_action(tool_name, arguments, user_id)

            # Read tools - izvedi takoj
            if tool_name in READ_TOOL_NAMES:
                return self._execute_read_tool(tool_name, arguments)

            return {"success": False, "error": f"Neznan tool: {tool_name}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # READ TOOLS
    # ============================================================

    @staticmethod
    def _safe_int(value, default: int = 20, min_val: int = 1) -> int:
        """Varno pretvori v int (LLM včasih pošlje string ali 0)."""
        try:
            result = int(value)
            return result if result >= min_val else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _get_date_from(args: dict) -> str | None:
        """Ekstrahiraj date_from iz args (LLM pošilja različne ključe)."""
        return (args.get("date_from") or args.get("datum_od") or args.get("datum_from")
                or args.get("start_date") or args.get("od") or args.get("from_date") or None)

    @staticmethod
    def _get_date_to(args: dict) -> str | None:
        """Ekstrahiraj date_to iz args (LLM pošilja različne ključe)."""
        return (args.get("date_to") or args.get("datum_do") or args.get("datum_to")
                or args.get("end_date") or args.get("do") or args.get("to_date") or None)

    def _execute_read_tool(self, tool_name: str, args: dict) -> dict:
        """Izvede bralni tool."""

        handlers = {
            "search_partners": self._search_partners,
            "get_partner_details": self._get_partner_details,
            "list_projects": self._list_projects,
            "get_project_details": self._get_project_details,
            "search_orders": self._search_orders,
            "search_quotes": self._search_quotes,
            "get_delivery_notes": self._get_delivery_notes,
            "get_invoices": self._get_invoices,
            "get_stock_info": self._get_stock_info,
            "get_bom": self._get_bom,
            "get_work_operations": self._get_work_operations,
            "get_calculations": self._get_calculations,
            "get_production_status": self._get_production_status,
            "count_records": self._count_records,
            "get_emails": self._get_emails,
            "summarize_emails": self._summarize_emails,
            "daily_report": self._daily_report,
            "run_custom_query": self._run_custom_query,
            "get_email_details": self._get_email_details,
            "get_related_emails": self._get_related_emails,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"success": False, "error": f"Bralni tool ne obstaja: {tool_name}"}

        return handler(args)

    def _search_partners(self, args: dict) -> dict:
        search = args.get("search", args.get("search_term", ""))
        limit = min(self._safe_int(args.get("limit"), 20), 100)

        query = """
            SELECT TOP (?) PaSifra, RTRIM(PaNaziv) as PaNaziv,
                   RTRIM(PaKraj) as PaKraj, RTRIM(PaSifDrzave) as PaDrzava,
                   RTRIM(PaEMail) as PaEMail, RTRIM(PaTelefon1) as PaTelefon
            FROM dbo.Partnerji
            WHERE PaNaziv LIKE ? OR CAST(PaSifra AS VARCHAR) = ?
            ORDER BY PaNaziv
        """
        rows = self._execute_select(query, (limit, f"%{search}%", search))
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_partner_details(self, args: dict) -> dict:
        pid = args["partner_id"]

        partner = self._execute_select(
            "SELECT * FROM dbo.Partnerji WHERE PaSifra = ?", (pid,)
        )
        if not partner:
            return {"success": False, "error": f"Partner {pid} ne obstaja"}

        contacts = self._execute_select(
            "SELECT TOP 10 * FROM dbo.partnerjiKontOseba WHERE PaSifra = ?", (pid,)
        )

        return {"success": True, "data": {"partner": partner[0], "contacts": contacts}}

    def _list_projects(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("faza"):
            conditions.append("faza LIKE ?")
            params.append(args["faza"])
        if args.get("status"):
            # Case-insensitive matching (LLM lahko pošlje "aktivni", "Aktiven", itd.)
            conditions.append("status LIKE ?")
            params.append(f"%{args['status'][:5]}%")
        if args.get("search"):
            conditions.append("(naziv LIKE ? OR stevilka_projekta LIKE ?)")
            params.extend([f"%{args['search']}%", f"%{args['search']}%"])

        where = " AND ".join(conditions)
        params.append(limit)

        rows = self._execute_select(
            f"SELECT TOP (?) * FROM ai_agent.Projekti WHERE {where} ORDER BY datum_rfq DESC",
            tuple(params[::-1])  # limit first for TOP
        )
        # Fix: reorder - TOP needs to be first param
        rows = self._execute_select(
            f"""SELECT TOP (?) id, stevilka_projekta, naziv, stranka_id, faza, status,
                       datum_rfq, datum_zakljucka, opombe
                FROM ai_agent.Projekti WHERE {where} ORDER BY datum_rfq DESC""",
            tuple([limit] + params[:-1])
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_project_details(self, args: dict) -> dict:
        pid = args["project_id"]

        project = self._execute_select(
            "SELECT * FROM ai_agent.Projekti WHERE id = ?", (pid,)
        )
        if not project:
            return {"success": False, "error": f"Projekt {pid} ne obstaja"}

        timeline = self._execute_select(
            "SELECT TOP 20 * FROM ai_agent.ProjektCasovnica WHERE projekt_id = ? ORDER BY datum DESC",
            (pid,)
        )
        docs = self._execute_select(
            "SELECT * FROM ai_agent.Dokumenti WHERE projekt_id = ?", (pid,)
        )
        work_orders = self._execute_select(
            "SELECT * FROM ai_agent.DelovniNalogi WHERE projekt_id = ?", (pid,)
        )

        return {
            "success": True,
            "data": {
                "project": project[0],
                "timeline": timeline,
                "documents": docs,
                "work_orders": work_orders
            }
        }

    def _search_orders(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("partner_id"):
            conditions.append("(n.NaPartPlac = ? OR n.NaPartPrjm = ?)")
            params.extend([args["partner_id"], args["partner_id"]])
        if args.get("partner_name"):
            conditions.append("p.PaNaziv LIKE ?")
            params.append(f"%{args['partner_name']}%")
        if args.get("status"):
            conditions.append("n.NaStatus = ?")
            params.append(args["status"])
        if args.get("modul"):
            conditions.append("n.NaModul = ?")
            params.append(args["modul"])
        # LLM včasih pošlje drug ključ za datume
        date_from = self._get_date_from(args)
        date_to = self._get_date_to(args)
        if date_from:
            conditions.append("n.NaDatNar >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("n.NaDatNar <= ?")
            params.append(date_to)

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"""SELECT TOP (?) n.NaStNar, RTRIM(n.NaStatus) as NaStatus,
                       n.NaDatNar, n.NaZnes, RTRIM(n.NaModul) as NaModul,
                       n.NaPartPlac, RTRIM(p.PaNaziv) as PartnerNaziv
                FROM dbo.Narocilo n
                LEFT JOIN dbo.Partnerji p ON n.NaPartPlac = p.PaSifra
                WHERE {where}
                ORDER BY n.NaDatNar DESC""",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _search_quotes(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("partner_id"):
            conditions.append("pon.PonPart = ?")
            params.append(args["partner_id"])
        if args.get("partner_name"):
            conditions.append("p.PaNaziv LIKE ?")
            params.append(f"%{args['partner_name']}%")
        if args.get("status"):
            conditions.append("pon.PonStatus = ?")
            params.append(args["status"])
        date_from = self._get_date_from(args)
        date_to = self._get_date_to(args)
        if date_from:
            conditions.append("pon.PonDatPon >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("pon.PonDatPon <= ?")
            params.append(date_to)

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"""SELECT TOP (?) pon.PonStPon, RTRIM(pon.PonStatus) as PonStatus,
                       pon.PonDatPon, pon.PonZnes, RTRIM(pon.PonModul) as PonModul,
                       pon.PonPart, RTRIM(p.PaNaziv) as PartnerNaziv
                FROM dbo.Ponudba pon
                LEFT JOIN dbo.Partnerji p ON pon.PonPart = p.PaSifra
                WHERE {where}
                ORDER BY pon.PonDatPon DESC""",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_delivery_notes(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("partner_id"):
            conditions.append("d.DNsPartPlac = ?")
            params.append(args["partner_id"])
        date_from = self._get_date_from(args)
        date_to = self._get_date_to(args)
        if date_from:
            conditions.append("d.DNsDatDNs >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("d.DNsDatDNs <= ?")
            params.append(date_to)

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"""SELECT TOP (?) d.DNsStDNs, RTRIM(d.DNsStatus) as DNsStatus,
                       d.DNsDatDNs, d.DNsZnes, d.DNsPartPlac,
                       RTRIM(p.PaNaziv) as PartnerNaziv
                FROM dbo.Dobavnica d
                LEFT JOIN dbo.Partnerji p ON d.DNsPartPlac = p.PaSifra
                WHERE {where}
                ORDER BY d.DNsDatDNs DESC""",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_invoices(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("partner_id"):
            conditions.append("f.FaPartPlac = ?")
            params.append(args["partner_id"])
        date_from = self._get_date_from(args)
        date_to = self._get_date_to(args)
        if date_from:
            conditions.append("f.Datum >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("f.Datum <= ?")
            params.append(date_to)

        where = " AND ".join(conditions)

        # Faktura columns may differ - try safe query
        try:
            rows = self._execute_select(
                f"""SELECT TOP (?) f.*, RTRIM(p.PaNaziv) as PartnerNaziv
                    FROM dbo.Faktura f
                    LEFT JOIN dbo.Partnerji p ON f.FaPartPlac = p.PaSifra
                    WHERE {where}
                    ORDER BY f.Datum DESC""",
                tuple([limit] + params)
            )
        except Exception:
            # Fallback: basic query
            rows = self._execute_select(
                f"SELECT TOP (?) * FROM dbo.Faktura WHERE {where} ORDER BY Datum DESC",
                tuple([limit] + params)
            )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_stock_info(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)

        # Materialni tabela vsebuje material/article info
        conditions = ["1=1"]
        params = []

        if args.get("article_search"):
            conditions.append("MaNaziv LIKE ?")
            params.append(f"%{args['article_search']}%")
        if args.get("warehouse"):
            conditions.append("MaSmSifra = ?")
            params.append(args["warehouse"])

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"SELECT TOP (?) * FROM dbo.Materialni WHERE {where}",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_bom(self, args: dict) -> dict:
        conditions = ["1=1"]
        params = []

        if args.get("article_id"):
            conditions.append("KosSifra = ?")
            params.append(args["article_id"])
        if args.get("work_order_id"):
            conditions.append("KosStDNs = ?")
            params.append(args["work_order_id"])

        if not params:
            return {"success": False, "error": "Navedi article_id ali work_order_id"}

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"SELECT TOP 100 * FROM dbo.Kosovnica WHERE {where}",
            tuple(params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_work_operations(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 50), 200)
        conditions = ["1=1"]
        params = []

        if args.get("article_id"):
            conditions.append("DPSifra = ?")
            params.append(args["article_id"])
        if args.get("work_order_id"):
            conditions.append("DPStDNs = ?")
            params.append(args["work_order_id"])

        if not params:
            return {"success": False, "error": "Navedi article_id ali work_order_id"}

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"SELECT TOP (?) * FROM dbo.DelPostopek WHERE {where}",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_calculations(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("calculation_id"):
            conditions.append("KStKalk = ?")
            params.append(args["calculation_id"])
        if args.get("document_type"):
            conditions.append("KTipDok = ?")
            params.append(args["document_type"])
        if args.get("document_id"):
            conditions.append("KStDok = ?")
            params.append(args["document_id"])

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"SELECT TOP (?) * FROM dbo.Kalkulacija WHERE {where} ORDER BY Datum DESC",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _get_production_status(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = ["1=1"]
        params = []

        if args.get("work_order_id"):
            conditions.append("PDNStDNs = ?")
            params.append(args["work_order_id"])
        date_from = self._get_date_from(args)
        date_to = self._get_date_to(args)
        if date_from:
            conditions.append("Datum >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("Datum <= ?")
            params.append(date_to)

        where = " AND ".join(conditions)

        rows = self._execute_select(
            f"SELECT TOP (?) * FROM dbo.PotekDelovnegaNaloga WHERE {where} ORDER BY Datum DESC",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _count_records(self, args: dict) -> dict:
        table = args["table_name"]

        # Whitelist tabel
        allowed_tables = {
            "Partnerji", "Narocilo", "Ponudba", "Dobavnica",
            "Faktura", "Promet", "Materialni", "Kalkulacija",
            "Kosovnica", "DelPostopek", "DelovniNalog",
            "PotekDelovnegaNaloga", "Rezervacije", "Cenik"
        }

        if table not in allowed_tables:
            return {"success": False, "error": f"Tabela {table} ni dovoljena za štetje"}

        where = ""
        params = ()
        if args.get("where_clause"):
            # Samo preproste pogoje dovolimo
            clause = args["where_clause"]
            if not self._is_safe_where(clause):
                return {"success": False, "error": "Nevaren WHERE pogoj"}
            where = f"WHERE {clause}"

        count = self._execute_count(f"SELECT COUNT(*) FROM dbo.{table} {where}", params)
        return {"success": True, "data": {"table": table, "count": count}}

    # Vzorci za nezaželeno pošto (LIKE matching za encoding issues)
    JUNK_EMAIL_PATTERNS = ("Splo%",)

    def _get_emails(self, args: dict) -> dict:
        limit = min(self._safe_int(args.get("limit"), 20), 100)
        conditions = []
        params = []

        # Filtriraj po uporabnikovem emailu (vsak vidi samo svoje)
        user_email = self._get_user_email(getattr(self, '_current_user_id', 0))
        if user_email:
            conditions.append("(prejemniki LIKE ? OR posiljatelj LIKE ?)")
            params.extend([f"%{user_email}%", f"%{user_email}%"])

        # Privzeto pokaži samo neprebrane (status = 'Nov'), razen če uporabnik izrecno želi vse
        if args.get("status"):
            conditions.append("status = ?")
            params.append(args["status"])
        elif not args.get("all_statuses"):
            conditions.append("status = ?")
            params.append("Nov")

        # Izključi nezaželeno pošto - vedno, razen če include_junk=true
        # LLM 8B rad pošlje napačne kategorije - validiramo
        VALID_CATEGORIES = {"RFQ", "Naročilo", "Sprememba", "Dokumentacija", "Reklamacija"}
        raw_kat = (args.get("kategorija") or "").strip()
        if raw_kat and raw_kat in VALID_CATEGORIES:
            conditions.append("kategorija = ?")
            params.append(raw_kat)
        # Vedno izključi junk (razen če eksplicitno želi)
        if not args.get("include_junk"):
            for pattern in self.JUNK_EMAIL_PATTERNS:
                conditions.append("kategorija NOT LIKE ?")
                params.append(pattern)

        if args.get("projekt_id"):
            conditions.append("projekt_id = ?")
            params.append(args["projekt_id"])

        # RFQ pod-kategorija filter
        VALID_RFQ_SUBCATEGORIES = {"Kompletno", "Nepopolno", "Povpraševanje", "Repeat Order"}
        raw_podkat = (args.get("rfq_podkategorija") or "").strip()
        if raw_podkat and raw_podkat in VALID_RFQ_SUBCATEGORIES:
            conditions.append("rfq_podkategorija = ?")
            params.append(raw_podkat)

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self._execute_select(
            f"""SELECT TOP (?) id, zadeva, posiljatelj, prejemniki, kategorija, rfq_podkategorija, status, datum, projekt_id
                FROM ai_agent.Emaili WHERE {where} ORDER BY datum DESC""",
            tuple([limit] + params)
        )
        return {"success": True, "data": rows, "count": len(rows)}

    def _summarize_emails(self, args: dict) -> dict:
        """Serversko generiran povzetek emailov - model le prikaže rezultat."""
        from datetime import timedelta

        days = self._safe_int(args.get("days"), 7)
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        conditions = ["datum >= ?"]
        params = [date_from]

        if args.get("status") and not args.get("all_statuses"):
            conditions.append("status = ?")
            params.append(args["status"])
        elif not args.get("all_statuses"):
            conditions.append("status = ?")
            params.append("Nov")

        # Izključi junk
        for pattern in self.JUNK_EMAIL_PATTERNS:
            conditions.append("kategorija NOT LIKE ?")
            params.append(pattern)

        where = " AND ".join(conditions)

        # Pridobi emaile
        rows = self._execute_select(
            f"""SELECT id, zadeva, posiljatelj, kategorija, rfq_podkategorija, status, datum, prejemniki
                FROM ai_agent.Emaili WHERE {where} ORDER BY datum DESC""",
            tuple(params)
        )

        if not rows:
            return {
                "success": True,
                "povzetek": "Ni novih emailov v zadnjih {} dneh.".format(days),
                "skupaj": 0,
                "po_kategorijah": {},
                "po_nabiralnikih": {}
            }

        # Grupiraj po kategorijah (RFQ prikaže pod-kategorijo)
        po_kategorijah = {}
        for r in rows:
            kat = r.get("kategorija", "Nekategorizirano") or "Nekategorizirano"
            # Za RFQ prikaži pod-kategorijo v imenu skupine
            podkat = r.get("rfq_podkategorija")
            if kat == "RFQ" and podkat:
                kat = f"RFQ - {podkat}"
            if kat not in po_kategorijah:
                po_kategorijah[kat] = {"stevilo": 0, "emaili": []}
            po_kategorijah[kat]["stevilo"] += 1
            if len(po_kategorijah[kat]["emaili"]) < 5:  # Max 5 primerov na kategorijo
                po_kategorijah[kat]["emaili"].append({
                    "id": r["id"],
                    "od": r.get("posiljatelj", "?"),
                    "zadeva": r.get("zadeva", "?"),
                    "datum": str(r.get("datum", ""))[:16],
                })

        # Grupiraj po nabiralnikih (prejemniki IN posiljatelj)
        all_mailboxes = [
            "ales", "info", "spela", "nabava", "tehnolog",
            "martina", "oddaja", "anela", "cam", "matej", "prevzem", "skladisce"
        ]
        po_nabiralnikih = {mb: 0 for mb in all_mailboxes}
        for r in rows:
            combined = ((r.get("prejemniki", "") or "") + "," + (r.get("posiljatelj", "") or "")).lower()
            for mb in all_mailboxes:
                if f"{mb}@luznar.com" in combined:
                    po_nabiralnikih[mb] += 1
        # Odstrani nabiralnike brez emailov
        po_nabiralnikih = {k: v for k, v in po_nabiralnikih.items() if v > 0}

        # Sestavi besedilni povzetek
        lines = [f"POVZETEK EMAILOV (zadnjih {days} dni):"]
        lines.append(f"Skupaj: {len(rows)} emailov\n")

        lines.append("PO KATEGORIJAH:")
        for kat, info in sorted(po_kategorijah.items(), key=lambda x: -x[1]["stevilo"]):
            lines.append(f"  {kat}: {info['stevilo']} emailov")
            for e in info["emaili"]:
                lines.append(f"    - [{e['id']}] {e['od']}: {e['zadeva']} ({e['datum']})")

        if po_nabiralnikih:
            lines.append("\nPO NABIRALNIKIH:")
            for mailbox, cnt in sorted(po_nabiralnikih.items(), key=lambda x: -x[1]):
                lines.append(f"  {mailbox}@luznar.com: {cnt}")

        return {
            "success": True,
            "povzetek": "\n".join(lines),
            "skupaj": len(rows),
            "po_kategorijah": {k: v["stevilo"] for k, v in po_kategorijah.items()},
            "po_nabiralnikih": po_nabiralnikih
        }

    def _daily_report(self, args: dict) -> dict:
        """Dnevno poročilo po nabiralnikih. Vedno uporabi današnji datum."""
        datum = datetime.now().strftime("%Y-%m-%d")

        samo_nabiralnik = (args.get("nabiralnik") or "").strip().lower()

        # Pridobi vse emaile za ta dan
        conditions = ["CAST(datum AS DATE) = ?"]
        params = [datum]

        # Izključi junk
        for pattern in self.JUNK_EMAIL_PATTERNS:
            conditions.append("kategorija NOT LIKE ?")
            params.append(pattern)

        where = " AND ".join(conditions)
        rows = self._execute_select(
            f"""SELECT id, zadeva, posiljatelj, prejemniki, kategorija, rfq_podkategorija, status, datum
                FROM ai_agent.Emaili WHERE {where} ORDER BY datum DESC""",
            tuple(params)
        )

        # Določi nabiralnike
        all_mailboxes = [
            "ales", "info", "spela", "nabava", "tehnolog",
            "martina", "oddaja", "anela", "cam", "matej", "prevzem", "skladisce"
        ]
        if samo_nabiralnik:
            all_mailboxes = [samo_nabiralnik]

        # Grupiraj emaile po nabiralnikih
        mailbox_data = {}
        for mb in all_mailboxes:
            mb_email = f"{mb}@luznar.com"
            mb_rows = [
                r for r in rows
                if mb_email in (r.get("prejemniki", "") or "").lower()
                or mb_email in (r.get("posiljatelj", "") or "").lower()
            ]
            if not mb_rows:
                continue

            # Grupiraj po kategorijah (RFQ prikaže pod-kategorijo)
            po_kat = {}
            for r in mb_rows:
                kat = r.get("kategorija", "Nekategorizirano") or "Nekategorizirano"
                podkat = r.get("rfq_podkategorija")
                if kat == "RFQ" and podkat:
                    kat = f"RFQ - {podkat}"
                if kat not in po_kat:
                    po_kat[kat] = []
                po_kat[kat].append({
                    "id": r["id"],
                    "od": r.get("posiljatelj", "?"),
                    "zadeva": r.get("zadeva", "?"),
                    "status": r.get("status", "?"),
                })

            mailbox_data[mb] = {
                "skupaj": len(mb_rows),
                "po_kategorijah": po_kat,
            }

        # Sestavi besedilni povzetek
        lines = [f"DNEVNO POROČILO EMAILOV za {datum}"]
        lines.append(f"Skupaj vseh emailov: {len(rows)}")
        lines.append("=" * 50)

        for mb in all_mailboxes:
            if mb not in mailbox_data:
                continue
            info = mailbox_data[mb]
            lines.append(f"\n📬 {mb.upper()}@luznar.com — {info['skupaj']} emailov")
            lines.append("-" * 40)

            for kat, emaili in sorted(info["po_kategorijah"].items(), key=lambda x: -len(x[1])):
                lines.append(f"  {kat} ({len(emaili)}):")
                for e in emaili[:5]:
                    status_icon = {"Nov": "🆕", "Prebran": "📖", "Dodeljen": "📌", "Obdelan": "✅"}.get(e["status"], "")
                    lines.append(f"    {status_icon} [{e['id']}] {e['od'].split('<')[0].strip()}: {e['zadeva'][:80]}")
                if len(emaili) > 5:
                    lines.append(f"    ... in še {len(emaili) - 5} emailov")

        if not mailbox_data:
            lines.append(f"\nNi emailov za datum {datum}.")

        return {
            "success": True,
            "povzetek": "\n".join(lines),
            "datum": datum,
            "skupaj": len(rows),
            "nabiralniki": {
                f"{mb}@luznar.com": {
                    "skupaj": info["skupaj"],
                    "po_kategorijah": {k: len(v) for k, v in info["po_kategorijah"].items()}
                }
                for mb, info in mailbox_data.items()
            }
        }

    def _run_custom_query(self, args: dict) -> dict:
        query = args["query"].strip()

        # Varnostne kontrole
        if not query.upper().startswith("SELECT"):
            return {"success": False, "error": "Samo SELECT poizvedbe so dovoljene"}

        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "EXEC", "EXECUTE", "TRUNCATE", "CREATE"]
        query_upper = query.upper()
        for kw in dangerous:
            # Check for keyword as whole word (not part of column name)
            if re.search(rf'\b{kw}\b', query_upper):
                return {"success": False, "error": f"Nevarna operacija: {kw} ni dovoljena"}

        # Dodaj TOP omejitev če ni prisotna
        if "TOP" not in query_upper:
            query = query.replace("SELECT", "SELECT TOP 100", 1)

        rows = self._execute_select(query)
        return {
            "success": True,
            "data": rows,
            "count": len(rows),
            "query": query
        }

    def _get_email_details(self, args: dict) -> dict:
        """Podrobnosti emaila po ID z parsanim JSON."""
        email_id = args["email_id"]

        rows = self._execute_select(
            "SELECT * FROM ai_agent.Emaili WHERE id = ?", (email_id,)
        )
        if not rows:
            return {"success": False, "error": f"Email {email_id} ne obstaja"}

        email = rows[0]
        # Parse JSON polja
        for field in ("izvleceni_podatki", "priloge"):
            if email.get(field):
                try:
                    email[field] = json.loads(email[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        return {"success": True, "data": email}

    def _get_related_emails(self, args: dict) -> dict:
        """Poišči povezane emaile na 3 načine."""
        email_id = args["email_id"]
        mode = args.get("mode", "all")

        # Pridobi izhodišni email
        rows = self._execute_select(
            "SELECT * FROM ai_agent.Emaili WHERE id = ?", (email_id,)
        )
        if not rows:
            return {"success": False, "error": f"Email {email_id} ne obstaja"}

        email = rows[0]
        related = []
        seen_ids = {email_id}

        # Po projektu
        if mode in ("project", "all") and email.get("projekt_id"):
            project_emails = self._execute_select(
                """SELECT TOP 20 id, zadeva, posiljatelj, kategorija, status, datum, projekt_id
                   FROM ai_agent.Emaili WHERE projekt_id = ? AND id != ?
                   ORDER BY datum DESC""",
                (email["projekt_id"], email_id)
            )
            for e in project_emails:
                if e["id"] not in seen_ids:
                    seen_ids.add(e["id"])
                    e["relation"] = "project"
                    related.append(e)

        # Po pošiljatelju/domeni
        if mode in ("sender", "all"):
            sender = email.get("posiljatelj", "")
            domain = ""
            if "<" in sender and ">" in sender:
                addr = sender.split("<")[1].split(">")[0]
                if "@" in addr:
                    domain = addr.split("@")[1]
            if domain:
                sender_emails = self._execute_select(
                    """SELECT TOP 20 id, zadeva, posiljatelj, kategorija, status, datum, projekt_id
                       FROM ai_agent.Emaili WHERE posiljatelj LIKE ? AND id != ?
                       ORDER BY datum DESC""",
                    (f"%{domain}%", email_id)
                )
                for e in sender_emails:
                    if e["id"] not in seen_ids:
                        seen_ids.add(e["id"])
                        e["relation"] = "sender"
                        related.append(e)

        # Po email niti (RE:/FW: matching)
        if mode in ("thread", "all"):
            import re as regex
            zadeva = email.get("zadeva", "")
            clean_subject = regex.sub(r"^(RE:|FW:|Fwd:|Re:|Fw:)\s*", "", zadeva, flags=regex.IGNORECASE).strip()
            if clean_subject and len(clean_subject) > 3:
                thread_emails = self._execute_select(
                    """SELECT TOP 20 id, zadeva, posiljatelj, kategorija, status, datum, projekt_id
                       FROM ai_agent.Emaili WHERE zadeva LIKE ? AND id != ?
                       ORDER BY datum DESC""",
                    (f"%{clean_subject[:100]}%", email_id)
                )
                for e in thread_emails:
                    if e["id"] not in seen_ids:
                        seen_ids.add(e["id"])
                        e["relation"] = "thread"
                        related.append(e)

        return {"success": True, "data": related, "count": len(related)}

    # ============================================================
    # WRITE TOOLS (priprava za potrditev)
    # ============================================================

    def _prepare_write_action(self, tool_name: str, args: dict, user_id: int) -> dict:
        """Pripravi pisalno akcijo za potrditev uporabnika."""

        descriptions = {
            "create_project": f"Ustvari nov projekt: {args.get('naziv', '?')}",
            "update_project": f"Posodobi projekt #{args.get('project_id', '?')}",
            "create_work_order": f"Ustvari delovni nalog za projekt #{args.get('projekt_id', '?')}",
            "assign_email_to_project": f"Dodeli email #{args.get('email_id', '?')} projektu #{args.get('projekt_id', '?')}",
            "generate_document": f"Generiraj {args.get('doc_type', '?')} za projekt #{args.get('projekt_id', '?')}",
            "categorize_email": f"Kategoriziraj email #{args.get('email_id', '?')} z AI",
            "draft_email_response": f"Pripravi odgovor na email #{args.get('email_id', '?')} ({args.get('response_type', 'acknowledge')})",
            "sync_emails": f"Sinhroniziraj emaile iz Outlook (top {args.get('top', 50)})",
            "generate_rfq_summary": f"Generiraj RFQ Summary za projekt #{args.get('projekt_id', '?')}",
        }

        return {
            "success": True,
            "needs_confirmation": True,
            "pending_action": {
                "tool_name": tool_name,
                "arguments": args,
                "description": descriptions.get(tool_name, f"Izvedi {tool_name}"),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        }

    async def execute_confirmed_action(self, tool_name: str, args: dict, user_id: int) -> dict:
        """Izvede potrjeno pisalno akcijo."""

        handlers = {
            "create_project": self._exec_create_project,
            "update_project": self._exec_update_project,
            "create_work_order": self._exec_create_work_order,
            "assign_email_to_project": self._exec_assign_email,
            "generate_document": self._exec_generate_document,
            "categorize_email": self._exec_categorize_email,
            "draft_email_response": self._exec_draft_email_response,
            "sync_emails": self._exec_sync_emails,
            "generate_rfq_summary": self._exec_generate_rfq_summary,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"success": False, "error": f"Pisalni tool ne obstaja: {tool_name}"}

        return await handler(args, user_id)

    async def _exec_create_project(self, args: dict, user_id: int) -> dict:
        """Ustvari nov projekt."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Generiraj številko projekta
            year = datetime.now().year
            cursor.execute(
                "SELECT COUNT(*) + 1 FROM ai_agent.Projekti WHERE stevilka_projekta LIKE ?",
                (f"PRJ-{year}-%",)
            )
            seq = cursor.fetchone()[0]
            stevilka = f"PRJ-{year}-{seq:03d}"

            cursor.execute(
                """INSERT INTO ai_agent.Projekti
                   (stevilka_projekta, naziv, stranka_id, faza, status, datum_rfq, opombe)
                   VALUES (?, ?, ?, ?, 'Aktiven', GETDATE(), ?)""",
                (stevilka, args["naziv"], args.get("stranka_id"),
                 args.get("faza", "RFQ"), args.get("opombe", ""))
            )

            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = cursor.fetchone()[0]

            # Zapiši v časovnico
            cursor.execute(
                """INSERT INTO ai_agent.ProjektCasovnica
                   (projekt_id, dogodek, opis, nova_vrednost, datum, uporabnik_ali_agent)
                   VALUES (?, 'Ustvarjen', 'Projekt ustvarjen preko AI agenta', ?, GETDATE(), 'agent')""",
                (new_id, stevilka)
            )

            conn.commit()
            return {
                "success": True,
                "data": {"id": int(new_id), "stevilka_projekta": stevilka}
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    async def _exec_update_project(self, args: dict, user_id: int) -> dict:
        """Posodobi projekt."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            pid = args["project_id"]

            updates = []
            params = []
            if args.get("faza"):
                updates.append("faza = ?")
                params.append(args["faza"])
            if args.get("status"):
                updates.append("status = ?")
                params.append(args["status"])
            if args.get("opombe"):
                updates.append("opombe = ?")
                params.append(args["opombe"])

            if not updates:
                return {"success": False, "error": "Ni sprememb za posodobitev"}

            params.append(pid)
            cursor.execute(
                f"UPDATE ai_agent.Projekti SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )

            # Časovnica
            changes = []
            if args.get("faza"):
                changes.append(f"Faza → {args['faza']}")
            if args.get("status"):
                changes.append(f"Status → {args['status']}")

            cursor.execute(
                """INSERT INTO ai_agent.ProjektCasovnica
                   (projekt_id, dogodek, opis, nova_vrednost, datum, uporabnik_ali_agent)
                   VALUES (?, 'Posodobitev', ?, ?, GETDATE(), 'agent')""",
                (pid, "; ".join(changes), json.dumps(args, ensure_ascii=False))
            )

            conn.commit()
            return {"success": True, "data": {"project_id": pid, "changes": changes}}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    async def _exec_create_work_order(self, args: dict, user_id: int) -> dict:
        """Ustvari delovni nalog."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO ai_agent.DelovniNalogi
                   (projekt_id, artikel_id, kolicina, status, datum_plan_zacetek, datum_plan_konec)
                   VALUES (?, ?, ?, 'Planiran', ?, ?)""",
                (args["projekt_id"], args.get("artikel_id"),
                 args["kolicina"], args.get("datum_plan_zacetek"),
                 args.get("datum_plan_konec"))
            )
            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = cursor.fetchone()[0]
            conn.commit()
            return {"success": True, "data": {"id": int(new_id)}}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    async def _exec_assign_email(self, args: dict, user_id: int) -> dict:
        """Dodeli email projektu in sproži obdelavo prilog."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ai_agent.Emaili SET projekt_id = ?, status = 'Dodeljen' WHERE id = ?",
                (args["projekt_id"], args["email_id"])
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

        # Avtomatsko obdelaj priloge
        attachment_result = None
        try:
            from app.database import SessionLocal
            from app.crud import emaili as crud_emaili
            from app.services.attachment_processor import process_email_attachments

            db = SessionLocal()
            try:
                db_email = crud_emaili.get_email_by_id(db, args["email_id"])
                if db_email and db_email.priloge:
                    attachment_result = await process_email_attachments(db, db_email)
            finally:
                db.close()
        except Exception as e:
            attachment_result = {"error": str(e)}

        return {
            "success": True,
            "data": {
                "email_id": args["email_id"],
                "projekt_id": args["projekt_id"],
                "attachments": attachment_result,
            }
        }

    async def _exec_generate_document(self, args: dict, user_id: int) -> dict:
        """Generiraj dokument - placeholder za pravo implementacijo."""
        return {
            "success": True,
            "data": {
                "message": f"Dokument {args['doc_type']} za projekt #{args['projekt_id']} bo generiran.",
                "status": "V pripravi"
            }
        }

    async def _exec_categorize_email(self, args: dict, user_id: int) -> dict:
        """Ponovna AI kategorizacija emaila."""
        email_id = args["email_id"]

        rows = self._execute_select(
            "SELECT id, posiljatelj, zadeva, telo, priloge FROM ai_agent.Emaili WHERE id = ?",
            (email_id,)
        )
        if not rows:
            return {"success": False, "error": f"Email {email_id} ne obstaja"}

        email = rows[0]

        # Parse priloge za imena
        attachment_names = []
        if email.get("priloge"):
            try:
                priloge = json.loads(email["priloge"])
                attachment_names = [p.get("name", "") for p in priloge if isinstance(p, dict)]
            except (json.JSONDecodeError, TypeError):
                pass

        from app.agents.email_agent import get_email_agent
        from app.utils.html_utils import strip_html_to_text

        agent = get_email_agent()
        body = strip_html_to_text(email.get("telo", "")) if email.get("telo") else ""

        analysis = await agent.categorize_email(
            sender=email.get("posiljatelj", ""),
            subject=email.get("zadeva", ""),
            body=body,
            attachments=attachment_names,
        )

        # Posodobi v bazi
        izvleceni = {
            "kategorija": analysis.kategorija.value,
            "rfq_podkategorija": analysis.rfq_podkategorija.value if analysis.rfq_podkategorija else None,
            "zaupanje": analysis.zaupanje,
            "povzetek": analysis.povzetek,
            "predlagan_projekt_id": analysis.predlagan_projekt_id,
            **analysis.izvleceni_podatki,
        }

        rfq_podkat_value = analysis.rfq_podkategorija.value if analysis.rfq_podkategorija else None

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ai_agent.Emaili SET kategorija = ?, rfq_podkategorija = ?, izvleceni_podatki = ? WHERE id = ?",
                (analysis.kategorija.value, rfq_podkat_value, json.dumps(izvleceni, ensure_ascii=False), email_id)
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "success": True,
            "data": {
                "email_id": email_id,
                "kategorija": analysis.kategorija.value,
                "rfq_podkategorija": rfq_podkat_value,
                "zaupanje": analysis.zaupanje,
                "povzetek": analysis.povzetek,
                "izvleceni_podatki": analysis.izvleceni_podatki,
            }
        }

    async def _exec_draft_email_response(self, args: dict, user_id: int) -> dict:
        """Pripravi osnutek odgovora na email."""
        email_id = args["email_id"]
        response_type = args.get("response_type", "acknowledge")

        rows = self._execute_select(
            "SELECT * FROM ai_agent.Emaili WHERE id = ?", (email_id,)
        )
        if not rows:
            return {"success": False, "error": f"Email {email_id} ne obstaja"}

        email = rows[0]

        # Parse izvlečene podatke za boljši kontekst
        izvleceni = {}
        if email.get("izvleceni_podatki"):
            try:
                izvleceni = json.loads(email["izvleceni_podatki"])
            except (json.JSONDecodeError, TypeError):
                pass

        from app.agents.email_agent import get_email_agent
        from app.utils.html_utils import strip_html_to_text

        agent = get_email_agent()
        body = strip_html_to_text(email.get("telo", "")) if email.get("telo") else ""

        original = {
            "sender": email.get("posiljatelj", ""),
            "subject": email.get("zadeva", ""),
            "body": body,
            "kategorija": email.get("kategorija", ""),
            "izvleceni_podatki": izvleceni,
            "additional_context": args.get("additional_context", ""),
        }

        draft = await agent.suggest_response(original, response_type)

        return {
            "success": True,
            "data": {
                "email_id": email_id,
                "response_type": response_type,
                "draft": draft,
                "to": email.get("posiljatelj", ""),
                "subject": f"RE: {email.get('zadeva', '')}",
            }
        }

    async def _exec_sync_emails(self, args: dict, user_id: int) -> dict:
        """Sproži sinhronizacijo emailov iz Outlook."""
        from app.services.email_sync import sync_emails_from_outlook
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            result = await sync_emails_from_outlook(db, top=args.get("top", 50))
            return {"success": True, "data": result}
        finally:
            db.close()

    async def _exec_generate_rfq_summary(self, args: dict, user_id: int) -> dict:
        """Generiraj RFQ Summary PDF za projekt."""
        from app.services.rfq_summary import generate_rfq_summary
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            result = await generate_rfq_summary(
                db,
                projekt_id=args["projekt_id"],
                email_id=args.get("email_id"),
            )
            return {"success": True, "data": result}
        finally:
            db.close()

    # ============================================================
    # ESCALATION
    # ============================================================

    def _execute_select_safe(self, query: str) -> list[dict]:
        """
        Izvede SELECT poizvedbo z varnostnimi kontrolami.

        Uporablja se kot query funkcija za PythonExecutor.
        Reuse varnostnih kontrol iz _run_custom_query.
        """
        query = query.strip()

        # Mora biti SELECT
        if not query.upper().startswith("SELECT"):
            raise ValueError("Samo SELECT poizvedbe so dovoljene")

        # Prepovedane operacije
        dangerous = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
            "EXEC", "EXECUTE", "TRUNCATE", "CREATE"
        ]
        query_upper = query.upper()
        for kw in dangerous:
            if re.search(rf'\b{kw}\b', query_upper):
                raise ValueError(f"Nevarna operacija: {kw} ni dovoljena")

        # Dodaj TOP omejitev če ni prisotna
        if "TOP" not in query_upper:
            query = query.replace("SELECT", "SELECT TOP 1000", 1)

        return self._execute_select(query)

    async def _execute_escalation(self, tool_name: str, args: dict) -> dict:
        """Posreduj Claude-u za pisanje skript."""
        from app.agents.claude_scriptwriter import get_scriptwriter

        writer = get_scriptwriter()

        if tool_name == "ask_claude_for_analysis":
            result = await writer.write_and_execute_python(
                task_description=args["task_description"],
                context=args.get("context", ""),
                executor=self
            )
        else:
            # ask_claude_for_script (SQL)
            result = await writer.write_and_execute(
                task_description=args["task_description"],
                context=args.get("context", ""),
                executor=self
            )
        return result

    # ============================================================
    # SECURITY
    # ============================================================

    @staticmethod
    def _is_safe_where(clause: str) -> bool:
        """Preveri ali je WHERE pogoj varen."""
        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "EXEC",
                      "EXECUTE", "--", ";", "xp_", "sp_"]
        clause_upper = clause.upper()
        return not any(kw in clause_upper for kw in dangerous)


# Singleton
_executor = None


def get_tool_executor() -> ToolExecutor:
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
