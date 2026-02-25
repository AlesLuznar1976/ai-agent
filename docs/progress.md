# Progress: Luznar AI Agent - Spremljanje napredka

**Zadnja posodobitev**: 2026-02-25 (v3)
**Verzija**: 1.2
**Status**: Aktivno v razvoju in produkciji

---

## Legenda statusov

| Ikona | Pomen |
|-------|-------|
| ✅ | Končano in deployjano |
| 🔧 | V razvoju |
| 📋 | Planirano (research.md) |
| ⚠️ | Znana težava |
| ❌ | Ni implementirano |

---

## 1. Infrastruktura

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 1.1 | Docker Compose setup (backend, web, ollama) | ✅ | 2026-02 | Vsi 3 servisi tečejo |
| 1.2 | Backend FastAPI na portu 8000 | ✅ | 2026-02 | ghcr.io/alesluznar1976/ai-agent-backend |
| 1.3 | Frontend Next.js na portu 9090 | ✅ | 2026-02 | ghcr.io/alesluznar1976/ai-agent-web, Next.js proxy za API |
| 1.4 | Ollama na portu 11434 | ✅ | 2026-02 | Z NVIDIA RTX 5080 GPU (16GB VRAM) |
| 1.5 | SQL Server baza (LARGO ERP) | ✅ | 2026-02 | Povezava na LUZNAR-2018\LARGO |
| 1.6 | GHCR container registry | ✅ | 2026-02 | Avtomatski build & push |
| 1.7 | SMB file share (\\192.168.0.113\izdelki) | ✅ | 2026-02 | Za projektne mape |
| 1.8 | Next.js → Backend proxy (rewrites) | ✅ | 2026-02-25 | /api/* → backend:8000, proxyTimeout 180s |
| 1.9 | Chat uploads volume (persistent) | ✅ | 2026-02-25 | data/chat_uploads:/app/data/chat_uploads |
| 1.10 | SSL/HTTPS | ❌ | - | Ni implementirano (lokalno omrežje) |
| 1.11 | Monitoring/alerting | ❌ | - | Samo /api/system/health endpoint |
| 1.12 | Avtomatski backup baze | ❌ | - | Ni konfigurirano |

---

## 2. Avtentikacija in uporabniki

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 2.1 | JWT avtentikacija (access + refresh tokeni) | ✅ | 2026-02 | HS256, 30min access, 30d refresh |
| 2.2 | Login/logout | ✅ | 2026-02 | /api/auth/login, /api/auth/logout |
| 2.3 | Uporabniške vloge (admin, prodaja, tehnolog, ...) | ✅ | 2026-02 | 7 vlog v bazi |
| 2.4 | Bcrypt hash gesel | ✅ | 2026-02 | Varno shranjevanje |
| 2.5 | Audit log | ✅ | 2026-02 | ai_agent.AuditLog tabela |
| 2.6 | Upravljanje uporabnikov (CRUD) | ✅ | 2026-02 | Backend CRUD, brez frontend UI |
| 2.7 | Frontend admin panel za uporabnike | ❌ | - | Ni UI za upravljanje |

---

## 3. Chat (Glavni AI vmesnik)

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 3.1 | Tekstovni chat z AI agentom | ✅ | 2026-02 | Ollama qwen3:14b, tool use loop, smart tool selector |
| 3.2 | Zgodovina pogovorov v SQL bazi | ✅ | 2026-02 | ai_agent.ChatHistory |
| 3.3 | Predlagani ukazi (suggested commands) | ✅ | 2026-02 | Dinamično glede na kontekst |
| 3.4 | Potrditveni dialog za write operacije | ✅ | 2026-02 | Pending actions (Čakajoče akcije) |
| 3.5 | Upload datotek (slike, PDF, Excel, Word, CSV) | ✅ | 2026-02-25 | Paperclip, drag-drop, file chips |
| 3.6 | Claude Opus 4.6 vision za slike in PDF-je | ✅ | 2026-02-25 | process_with_files() |
| 3.7 | Markdown renderiranje odgovorov | ✅ | 2026-02 | ReactMarkdown v MessageBubble |
| 3.8 | Export v Word (.docx) | ✅ | 2026-02-25 | markdown_to_word.py |
| 3.9 | Generiranje profesionalnih dokumentov | ✅ | 2026-02-25 | 4 predloge (Reklamacija, RFQ, BOM, Poročilo) |
| 3.10 | Streaming odgovorov | ❌ | - | Trenutno čaka cel odgovor |
| 3.11 | Glasovno sporočanje | ❌ | - | Ni implementirano |
| 3.12 | Upload datotek iz brskalnika | ✅ | 2026-02-25 | Popravljeno z Next.js rewrites proxy |
| 3.13 | Next.js API proxy (rewrites) | ✅ | 2026-02-25 | Vsi /api/* klici gredo skozi proxy, brez CORS |
| 3.14 | 3-minutni timeout za AI procesiranje | ✅ | 2026-02-25 | AbortController (frontend) + proxyTimeout (Next.js) |

---

## 4. Email sistem

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 4.1 | MS Graph sinhronizacija emailov | ✅ | 2026-02 | Vsakih 5 minut |
| 4.2 | Več nabiralnikov (info@, ales@, nabava@, ...) | ✅ | 2026-02 | Konfigurirano v .env |
| 4.3 | AI kategorizacija emailov | ✅ | 2026-02 | RFQ, Naročilo, Sprememba, Dokumentacija, Reklamacija, Splošno |
| 4.4 | RFQ pod-kategorizacija | ✅ | 2026-02 | Kompletno, Nepopolno, Povpraševanje, Repeat Order |
| 4.5 | Izvleček podatkov iz emailov (JSON) | ✅ | 2026-02 | stranka, količina, PO, verzija |
| 4.6 | Dnevni povzetek po nabiralnikih | ✅ | 2026-02 | daily_report tool |
| 4.7 | Povzetek emailov po kategorijah | ✅ | 2026-02 | summarize_emails tool |
| 4.8 | Dodeljevanje emailov projektom | ✅ | 2026-02 | assign_email_to_project tool |
| 4.9 | Priprava odgovorov na emaile | ✅ | 2026-02 | draft_email_response tool |
| 4.10 | Pošiljanje emailov (MS Graph) | ✅ | 2026-02 | email_send.py |
| 4.11 | Agent mailbox (agent@luznar.com) | ✅ | 2026-02 | Avtomatsko ustvari projekt |
| 4.12 | RFQ deep analiza (priloge) | ✅ | 2026-02 | rfq_analyzer.py |
| 4.13 | Email frontend (seznam + podrobnosti) | ✅ | 2026-02 | /emaili, /emaili/[id] |
| 4.14 | Filtriranje po kategoriji na frontendu | ✅ | 2026-02 | FilterChipBar komponenta |

---

## 5. Projekti

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 5.1 | CRUD projektov (create, read, update) | ✅ | 2026-02 | API + frontend |
| 5.2 | Življenjski cikel (8 faz) | ✅ | 2026-02 | RFQ → Ponudba → ... → Zaključek |
| 5.3 | Avtomatska številka (PRJ-YYYY-NNN) | ✅ | 2026-02 | get_next_project_number() |
| 5.4 | Časovnica (timeline) | ✅ | 2026-02 | ProjektCasovnica tabela |
| 5.5 | Projektni dokumenti | ✅ | 2026-02 | Dokumenti tabela + SMB mapa |
| 5.6 | Delovni nalogi za projekte | ✅ | 2026-02 | DelovniNalogi tabela |
| 5.7 | Frontend seznam projektov | ✅ | 2026-02 | /projekti s filtri |
| 5.8 | Frontend podrobnosti projekta | ✅ | 2026-02 | /projekti/[id] z emaili, časovnico |
| 5.9 | RFQ summary generiranje | ✅ | 2026-02 | generate_rfq_summary tool |
| 5.10 | CalcuQuote integracija | 🔧 | - | Delno implementirano (tabela + CRUD) |
| 5.11 | Gantt diagram za projektne faze | ❌ | - | Ni implementirano |

---

## 6. ERP integracija (Largo)

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 6.1 | Iskanje partnerjev (Partnerji) | ✅ | 2026-02 | search_partners, get_partner_details |
| 6.2 | Iskanje naročil (Narocilo) | ✅ | 2026-02 | search_orders z datumskimi filtri |
| 6.3 | Iskanje ponudb (Ponudba) | ✅ | 2026-02 | search_quotes |
| 6.4 | Dobavnice (Dobavnica) | ✅ | 2026-02 | get_delivery_notes |
| 6.5 | Fakture (Faktura) | ✅ | 2026-02 | get_invoices |
| 6.6 | Zaloge (Promet, Materialni) | ✅ | 2026-02 | get_stock_info |
| 6.7 | BOM / Kosovnice (Kosovnica) | ✅ | 2026-02 | get_bom |
| 6.8 | Delovni postopki (DelPostopek) | ✅ | 2026-02 | get_work_operations |
| 6.9 | Proizvodnja (PotekDelovnegaNaloga) | ✅ | 2026-02 | get_production_status |
| 6.10 | Kalkulacije | ✅ | 2026-02 | get_calculations |
| 6.11 | Štetje zapisov | ✅ | 2026-02 | count_records (14 dbo + 4 ai_agent tabel) |
| 6.12 | Custom SQL poizvedbe | ✅ | 2026-02 | run_custom_query (samo SELECT) |
| 6.13 | Claude SQL skripta | ✅ | 2026-02 | ask_claude_for_script |
| 6.14 | Claude Python analiza | ✅ | 2026-02 | ask_claude_for_analysis + sandbox |

---

## 7. Dokumenti in datoteke

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 7.1 | Upload datotek v chat | ✅ | 2026-02-25 | file_processor.py |
| 7.2 | Claude vision za slike | ✅ | 2026-02-25 | Claude Opus 4.6 |
| 7.3 | Claude PDF analiza | ✅ | 2026-02-25 | Nativni document content block |
| 7.4 | Excel ekstrakcija (openpyxl) | ✅ | 2026-02-25 | Max 500 vrstic per sheet |
| 7.5 | Word ekstrakcija (python-docx) | ✅ | 2026-02-25 | Paragrafi + tabele |
| 7.6 | CSV ekstrakcija | ✅ | 2026-02-25 | Max 500 vrstic |
| 7.7 | Markdown → Word export | ✅ | 2026-02-25 | markdown_to_word.py |
| 7.8 | Reklamacija predloga (SQC) | ✅ | 2026-02-25 | Po vzoru 100100306.pdf |
| 7.9 | RFQ analiza predloga | ✅ | 2026-02-25 | document_templates.py |
| 7.10 | BOM pregled predloga | ✅ | 2026-02-25 | document_templates.py |
| 7.11 | Poročilo o pregledu predloga | ✅ | 2026-02-25 | document_templates.py |
| 7.12 | Luznar branding (navy + gold) | ✅ | 2026-02-25 | Profesionalni dokumenti |

---

## 8. AI modeli in agenti

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 8.1 | Ollama orchestrator (tool use loop) | ✅ | 2026-02 | qwen3:14b na GPU, smart tool selector |
| 8.2 | Smart tool selector | ✅ | 2026-02-25 | Izbere ~9 relevantnih orodij (od 31) glede na sporočilo |
| 8.3 | Claude Sonnet 4.5 za SQL/Python | ✅ | 2026-02 | claude_scriptwriter.py |
| 8.4 | Claude Opus 4.6 za vision | ✅ | 2026-02-25 | process_with_files() |
| 8.5 | LLM Router (local vs cloud) | ✅ | 2026-02 | app/llm/router.py |
| 8.6 | Email Agent (kategorizacija) | ✅ | 2026-02 | email_agent.py |
| 8.7 | Python Executor (sandbox) | ✅ | 2026-02 | 30s timeout, safe builtins |
| 8.8 | System prompt v slovenščini | ✅ | 2026-02 | 89 vrstic, datum injiciran |
| 8.9 | Multi-agent arhitektura (Router) | 📋 | - | research.md - Faza 1 |
| 8.10 | Nabavni Agent | 📋 | - | research.md - 10 orodij |
| 8.11 | Proizvodni Agent | 📋 | - | research.md - 8 orodij |
| 8.12 | Analitični Agent | 📋 | - | research.md - Claude Sonnet |
| 8.13 | Dokumentni Agent | 📋 | - | research.md - Claude Opus vision |
| 8.14 | Projektni Agent | 📋 | - | research.md - 7 orodij |
| 8.15 | Email Agent v2 (specializiran) | 📋 | - | research.md - 9 orodij |

---

## 9. Frontend komponente

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 9.1 | Login stran | ✅ | 2026-02 | /login |
| 9.2 | Dashboard layout (AppBar + BottomNav) | ✅ | 2026-02 | Responsiven |
| 9.3 | Chat stran | ✅ | 2026-02 | /chat - glavna funkcionalnost |
| 9.4 | ChatInput z file upload | ✅ | 2026-02-25 | Paperclip, drag-drop, chips |
| 9.5 | MessageBubble z Markdown | ✅ | 2026-02 | ReactMarkdown |
| 9.6 | MessageBubble z document dropdown | ✅ | 2026-02-25 | 4 tipe dokumentov |
| 9.7 | Attachment badges v sporočilih | ✅ | 2026-02-25 | Ikona + ime datoteke |
| 9.8 | Projekti seznam | ✅ | 2026-02 | /projekti s filtri |
| 9.9 | Projekt podrobnosti | ✅ | 2026-02 | /projekti/[id] |
| 9.10 | Emaili seznam | ✅ | 2026-02 | /emaili s filtri |
| 9.11 | Email podrobnosti | ✅ | 2026-02 | /emaili/[id] |
| 9.12 | Luznar branding (logo, barve) | ✅ | 2026-02 | Navy + Gold tema |
| 9.13 | Typing indicator | ✅ | 2026-02 | Animacija med čakanjem |
| 9.14 | Logout dialog | ✅ | 2026-02 | Potrditev pred odjavov |
| 9.15 | Dark mode | ❌ | - | Ni implementirano |
| 9.16 | PWA / offline podpora | ❌ | - | Ni implementirano |
| 9.17 | Obvestila (notifications) | ❌ | - | Tabela obstaja, brez UI |

---

## 10. Varnost

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 10.1 | JWT avtentikacija | ✅ | 2026-02 | Access + refresh tokeni |
| 10.2 | Bcrypt hashing gesel | ✅ | 2026-02 | Varno shranjevanje |
| 10.3 | SQL injection prevencija | ✅ | 2026-02 | Parametrizirane poizvedbe (pyodbc) |
| 10.4 | Python sandbox za analize | ✅ | 2026-02 | Prepovedani moduli, timeout 30s |
| 10.5 | SQL varnostna kontrola (SELECT only) | ✅ | 2026-02 | Forbidden: DROP, DELETE, UPDATE, ... |
| 10.6 | Write tools potrditev | ✅ | 2026-02 | Čakajoče akcije |
| 10.7 | Audit log | ✅ | 2026-02 | Vse spremembe beležene |
| 10.8 | CORS konfiguracija | ✅ | 2026-02 | Whitelist origins (backend), Next.js proxy eliminia CORS za frontend |
| 10.9 | Rate limiting | ❌ | - | Ni implementirano |
| 10.10 | HTTPS/TLS | ❌ | - | Lokalno omrežje |

---

## 11. Dokumentacija

| # | Naloga | Status | Datum | Opombe |
|---|--------|--------|-------|--------|
| 11.1 | discovery.md (arhitektura celotnega sistema) | ✅ | 2026-02-25 | 18.5 KB |
| 11.2 | research.md (multi-agent raziskava) | ✅ | 2026-02-25 | 39 KB, 6 agentov |
| 11.3 | progress.md (ta datoteka) | ✅ | 2026-02-25 | Spremljanje napredka |
| 11.4 | NAMESTITEV.md (instalacija) | ✅ | 2026-02 | 14.5 KB |
| 11.5 | API dokumentacija (OpenAPI/Swagger) | ✅ | 2026-02 | FastAPI auto-generated |
| 11.6 | README.md | ❌ | - | Ni ustvarjen |
| 11.7 | CHANGELOG.md | ❌ | - | Ni ustvarjen |

---

## 12. Znane težave

| # | Težava | Prioriteta | Status | Opis |
|---|--------|-----------|--------|------|
| 12.1 | ~~File upload iz brskalnika ne deluje~~ | ~~Visoka~~ | ✅ | **POPRAVLJENO** (2026-02-25): Vzrok je bil cross-origin fetch iz :9090 na :8000. Rešitev: Next.js rewrites proxy — vsi /api/* klici gredo same-origin skozi Next.js, ki interno preusmeri na backend. |
| 12.2 | Markdown renderiranje po file upload | Srednja | ⚠️ | Ni potrjeno ali deluje po posodobitvi system prompta |
| 12.3 | Chat streaming | Nizka | ❌ | Ni implementirano - uporabnik čaka cel odgovor |
| 12.4 | ~~Ollama počasen pri tool use~~ | ~~Nizka~~ | ✅ | **POPRAVLJENO** (2026-02-25): Zamenjava na qwen3:14b z GPU + smart tool selector (~9 orodij). Iskanje partnerja: 2.9s, štetje: 23s. |
| 12.5 | ~~Ollama model ne podpira tool use zanesljivo~~ | ~~Srednja~~ | ✅ | **POPRAVLJENO** (2026-02-25): qwen3:14b zanesljivo kliče orodja. Problem je bil llama3:8b + 31 orodij naenkrat. Smart tool selector pošlje max 12. |
| 12.6 | LLM Router email kategorizacija faila | Nizka | ⚠️ | `Lokalni LLM napaka: , poskušam cloud...` — LLMRouter (local_llm.py) za email kategorizacijo občasno failira, padec na cloud. Ni kritično. |

---

## 13. Naslednji koraki (po prioriteti)

### Kratkoročno (1-2 tedna)

| # | Naloga | Prioriteta | Odvisnost |
|---|--------|-----------|-----------|
| ~~A1~~ | ~~Popravi file upload iz brskalnika~~ | ~~🔴~~ | ✅ **KONČANO** |
| A2 | Preveri markdown renderiranje (#12.2) | 🟡 Srednja | - |
| A3 | Testiraj document generation end-to-end | 🟡 Srednja | - |
| ~~A4~~ | ~~Zamenjaj Ollama tool model~~ | ~~🔴~~ | ✅ **KONČANO** — qwen3:14b + smart tool selector |
| A5 | Testiraj file upload iz dejanskega brskalnika | 🟡 Srednja | Ročni test s strani uporabnika |

### Srednjeročno (2-4 tedne)

| # | Naloga | Prioriteta | Odvisnost |
|---|--------|-----------|-----------|
| B1 | Multi-agent: BaseAgent + Router (Faza 1) | 🟡 Srednja | research.md |
| B2 | Multi-agent: Nabavni + Email Agent (Faza 2a) | 🟡 Srednja | B1 |
| B3 | Multi-agent: Proizvodni + Projektni Agent (Faza 2b) | 🟡 Srednja | B1 |
| B4 | Multi-agent: Analitični + Dokumentni Agent (Faza 2c) | 🟡 Srednja | B1 |
| B5 | Chat streaming (SSE) | 🟢 Nizka | Neodvisno |

### Dolgoročno (1-3 mesece)

| # | Naloga | Prioriteta | Odvisnost |
|---|--------|-----------|-----------|
| C1 | Quality Agent (8D report, SPC) | 🟢 Nizka | B1 |
| C2 | Financial Agent (fakture, DDV) | 🟢 Nizka | B1 |
| C3 | Planning Agent (kapacitete, terminski plan) | 🟢 Nizka | B1 |
| C4 | Agent memory (učenje iz preteklih interakcij) | 🟢 Nizka | B1 |
| C5 | Notifications UI | 🟢 Nizka | Neodvisno |
| C6 | Admin panel za uporabnike | 🟢 Nizka | Neodvisno |
| C7 | PWA / offline podpora | 🟢 Nizka | Neodvisno |
| C8 | Dark mode | 🟢 Nizka | Neodvisno |

---

## 14. Git zgodovina (zadnjih 20 commitov)

| # | Hash | Opis |
|---|------|------|
| 1 | d4faf43 | Switch to qwen3:14b with smart tool selector for faster chat responses |
| 2 | 610c9b5 | Add chat file upload, Claude vision, document generation, and Next.js API proxy |
| 3 | 5047145 | Add agent mailbox for automatic project creation from forwarded emails |
| 4 | 0d74ac7 | Add personalized email dashboard with category grouping and mailbox filtering |
| 5 | 449ac15 | Fix email analysis result not displaying in detail view |
| 6 | 73dba1c | Improve orchestrator prompts, add Python analysis executor, cleanup models |
| 7 | 1ef9f2a | Fix missing DB model columns and CRUD for email analysis |
| 8 | b3ec6b3 | Exclude calcuquote.com emails from RFQ/Naročilo categorization |
| 9 | bf6729d | Replace Flutter frontend with Next.js app |
| 10 | c5bd5d5 | Restrict RFQ/Naročilo categorization to specific mailboxes |

---

## 15. Statistika kode

| Kategorija | Datotek | Približno vrstic |
|------------|---------|-----------------|
| Backend Python | 69 | ~11,600 |
| Frontend TypeScript/TSX | 37 | ~2,450 |
| SQL (schema) | 1 | ~300 |
| Dokumentacija | 5 | ~3,050 |
| Konfiguracija (Docker, env) | 5 | ~150 |
| **SKUPAJ** | **~117** | **~17,550** |

---

## 16. Ključni kontakti in viri

| Vir | Lokacija |
|-----|----------|
| Backend koda | `/home/luznar-ai/ai-agent/backend/` |
| Frontend koda | `/home/luznar-ai/ai-agent/nextjs-app/` |
| SQL schema | `/home/luznar-ai/ai-agent/database/schema.sql` |
| Docker Compose | `/home/luznar-ai/ai-agent/docker-compose.yml` |
| Environment | `/home/luznar-ai/ai-agent/.env` |
| Dokumentacija | `/home/luznar-ai/ai-agent/docs/` |
| Discovery | `/home/luznar-ai/ai-agent/docs/discovery.md` |
| Research | `/home/luznar-ai/ai-agent/docs/research.md` |
| Progress | `/home/luznar-ai/ai-agent/docs/progress.md` |

---

## 17. Dnevnik sprememb

### 2026-02-25 (v3) — Perf: qwen3:14b + smart tool selector

**Problem**: Ollama `llama3:8b` ni zanesljivo podpiral tool calling (31 orodij). Chat je trajal 2.5+ min ali timeout. Tudi `qwen3:14b` in `qwen3:30b` ne zmoreta 31 orodij naenkrat — prazen odgovor ali timeout.

**Rešitev**: Tri spremembe:
1. **Model**: `llama3:8b` → `qwen3:14b` (boljši tool calling, slovenščina)
2. **Smart tool selector**: Orchestrator izbere ~9 relevantnih orodij (od 31) glede na ključne besede v sporočilu. 5 domenskih skupin: nabava, email, projekt, proizvodnja, analitika.
3. **GPU**: Restart Ollama containerja za pravilno GPU alokacijo (qwen3:14b = 9.7GB VRAM na RTX 5080)

**Spremenjene datoteke:**

| Datoteka | Sprememba |
|----------|-----------|
| `backend/app/agents/orchestrator.py` | Dodan `select_tools()` z TOOL_GROUPS, CORE_TOOLS, MAX_TOOLS=12 |
| `backend/app/agents/tool_executor.py` | `count_records` podpira ai_agent schema (Projekti, Emaili, ...) |
| `backend/app/config.py` | Default model: `llama3:8b` → `qwen3:14b` |
| `backend/app/db_models/akcija.py` | Dodan manjkajoč `user_id` in `rezultat` stolpec |
| `docker-compose.yml` | `OLLAMA_TOOL_MODEL` default: `qwen3:14b` |

**Testi (vsi uspešni, z GPU):**

| Test | HTTP | Čas | Prej |
|------|------|-----|------|
| "Koliko projektov imamo?" | 200 OK | **23s** | timeout |
| "Poišči partnerja Heusinkveld" | 200 OK | **2.9s** | 154s+ |

**Domenski tool selector:**

| Ključne besede | Skupina | Primer orodij |
|----------------|---------|---------------|
| naročil, partner, dobavitelj | nabava | search_orders, get_invoices, ... |
| email, mail, povzetek | email | get_emails, summarize_emails, ... |
| projekt, rfq | projekt | list_projects, create_project, ... |
| zaloge, bom, proizvodnja | proizvodnja | get_stock_info, get_bom, ... |
| analiz, trend, python | analitika | ask_claude_for_script, ... |

---

### 2026-02-25 (v2) — Fix: File upload iz brskalnika

**Problem**: Upload datotek iz brskalnika (port 9090) na backend (port 8000) ni deloval — "Ne morem se povezati s strežnikom". Vzrok: cross-origin `fetch()` z `FormData` brez pravilne CORS konfiguracije.

**Rešitev**: Next.js rewrites proxy — vsi `/api/*` klici gredo same-origin skozi Next.js server, ki interno preusmeri na backend preko Docker omrežja.

**Spremenjene datoteke:**

| Datoteka | Sprememba |
|----------|-----------|
| `nextjs-app/next.config.ts` | Dodan `rewrites()` proxy (`/api/:path*` → `backend:8000`) + `proxyTimeout: 180_000` |
| `nextjs-app/src/lib/api.ts` | `API_BASE` spremenjen iz hardcoded URL v `/api` (relative, same-origin). Dodan `AbortController` s 3-min timeout za file upload. Boljše napake v slovenščini. |
| `nextjs-app/Dockerfile` | `NEXT_PUBLIC_API_BASE_URL` → `BACKEND_URL=http://backend:8000` (runtime env) |
| `docker-compose.yml` | Web env: `BACKEND_URL`. Dodan volume `data/chat_uploads`. Dodan `depends_on: backend`. |

**Testi (vsi uspešni):**

| Test | HTTP | Čas |
|------|------|-----|
| Login skozi proxy (:9090) | 200 OK | <1s |
| Text file upload (.txt) | 200 OK | ~8s |
| PDF upload (924K reklamacija) | 200 OK | ~31s |
| Navadni chat (Ollama + cloud) | 200 OK | ~154s |

**Odkritja med debuggingom:**
- Ollama `llama3:8b` pogosto faila pri tool use → cloud fallback (počasen)
- `Lokalni LLM napaka: , poskušam cloud...` — priporočilo: zamenjava na `qwen3:14b` ali `qwen3:30b`
- Proxy timeout je bil prej ~30s (default) → dvignjen na 180s

---

### 2026-02-25 (v1) — Feature: Chat file upload + Claude vision + dokumenti

**Dodane funkcionalnosti:**
- Upload datotek v chat (slike, PDF, Excel, Word, CSV)
- Claude Opus 4.6 vision za analizo slik in PDF-jev
- File processor za Excel/Word/CSV ekstrakcijo
- Markdown → Word export
- 4 profesionalne Word predloge (Reklamacija SQC, RFQ analiza, BOM pregled, Poročilo)
- Luznar branding (navy + gold)
- discovery.md, research.md, progress.md dokumentacija
