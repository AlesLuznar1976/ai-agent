# AI Agent System - Discovery Document

**Podjetje:** Luznar Electronics d.o.o.
**Zadnja posodobitev:** 25. februar 2026
**Avtor:** AI Agent System (Claude Code)

---

## 1. Povzetek sistema

AI Agent sistem za **Luznar d.o.o.** - podjetje za izdelavo elektronskih vezij (PCB, SMT montaža). Sistem avtomatizira poslovne procese: upravljanje emailov, projektno vodenje, ERP integracijo, generiranje dokumentov in konverzacijski AI vmesnik.

**Projekt:** `/home/luznar-ai/ai-agent/`

---

## 2. Tehnološki sklad

| Plast | Tehnologija | Verzija |
|-------|-------------|---------|
| **Backend** | FastAPI + Uvicorn | 0.115.0 |
| **Frontend** | Next.js + React + Tailwind | 16.1.6 / 19.2.3 / 4 |
| **Baza** | SQL Server (SQLAlchemy + pyodbc) | 2.0.35 |
| **Lokalni LLM** | Ollama (Llama 3.1 8b / Qwen) | latest |
| **Cloud LLM** | Anthropic Claude Opus 4.6 / Sonnet 4.5 | SDK >=0.42.0 |
| **Email** | Microsoft Graph API (Outlook) | 1.12.0 |
| **Dokumenti** | python-docx, openpyxl, fpdf2, PyMuPDF | razne |
| **Kontejnerji** | Docker Compose + NVIDIA GPU | - |
| **Mobilna app** | Flutter (Win/Android/iOS) | - |

---

## 3. Arhitektura

```
                    ┌─────────────┐
                    │  Brskalnik   │ :9090
                    │  (Next.js)   │
                    └──────┬──────┘
                           │ HTTP/WS
                    ┌──────┴──────┐
                    │   Backend    │ :8000
                    │  (FastAPI)   │
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              │            │            │
       ┌──────┴──────┐  ┌─┴──────┐  ┌──┴──────────┐
       │   Ollama     │  │ SQL    │  │  Claude API  │
       │ (lokalni LLM)│  │ Server │  │  (Anthropic) │
       │   :11434     │  │        │  │              │
       └─────────────┘  └────────┘  └──────────────┘
```

---

## 4. Docker Compose storitve

| Storitev | Image | Port | Namen |
|----------|-------|------|-------|
| `backend` | ghcr.io/.../ai-agent-backend | **8000** | FastAPI API |
| `ollama` | ollama/ollama:latest | **11434** | Lokalni LLM |
| `web` | ghcr.io/.../ai-agent-web | **9090** → 3000 | Next.js frontend |

---

## 5. Backend struktura

### 5.1 Datotečna struktura

```
backend/app/
├── main.py                    # FastAPI app, router setup, startup
├── config.py                  # Pydantic Settings (env vars)
├── database.py                # SQLAlchemy engine, session
├── models.py                  # Pydantic models (Token, TokenData, UserRole)
├── db_models/                 # SQLAlchemy ORM modeli
│   ├── uporabnik.py           # DBUporabnik
│   ├── projekt.py             # DBProjekt
│   ├── email.py               # DBEmail
│   ├── dokument.py            # DBDokument
│   ├── akcija.py              # DBCakajocaAkcija
│   ├── delovni_nalog.py       # DBDelovniNalog
│   └── ...
├── api/                       # FastAPI routers
│   ├── auth.py                # /api/auth/* (login, refresh, me)
│   ├── chat.py                # /api/chat/* (send, history, with-files, export-word, generate-document)
│   ├── projekti.py            # /api/projekti/* (CRUD)
│   ├── emaili.py              # /api/emaili/* (sync, analyze)
│   ├── dokumenti.py           # /api/dokumenti/* (upload, download)
│   ├── websocket.py           # /ws/{user_id}
│   └── system_status.py       # /api/system/* (health, metrics)
├── agents/                    # AI agenti
│   ├── orchestrator.py        # Glavni agent (Ollama tool use + Claude vision)
│   ├── tool_executor.py       # Implementacija vseh ERP orodij
│   ├── erp_tools.py           # Definicije orodij za Ollama
│   ├── email_agent.py         # Email kategorizacija
│   ├── claude_scriptwriter.py # Claude za SQL/Python skripte
│   └── python_executor.py     # Sandbox za Python izvajanje
├── services/                  # Poslovni servisi
│   ├── email_sync.py          # MS Graph sync (vsake 5 min)
│   ├── scheduler.py           # Async job scheduler
│   ├── file_processor.py      # Upload processing (slike→base64, PDF→base64, Excel→text)
│   ├── document_templates.py  # Word predloge (Reklamacija, RFQ, BOM, Poročilo)
│   ├── markdown_to_word.py    # Markdown → DOCX konverzija
│   ├── rfq_analyzer.py        # RFQ analiza emailov
│   ├── rfq_summary.py         # RFQ povzetki
│   ├── smb_service.py         # SMB file share (\\192.168.0.113\izdelki)
│   ├── email_send.py          # Pošiljanje emailov
│   ├── attachment_processor.py # Obdelava prilog
│   └── log_collector.py       # Centralizirano logiranje
├── crud/                      # Database abstraction
│   ├── uporabniki.py          # User CRUD
│   ├── projekti.py            # Project CRUD
│   ├── emaili.py              # Email CRUD
│   ├── dokumenti.py           # Document CRUD
│   ├── akcije.py              # Pending actions CRUD
│   └── chat_history.py        # Chat persistence
└── auth/
    └── jwt_handler.py         # JWT + bcrypt
```

### 5.2 API Endpoints

#### Avtentikacija
```
POST /api/auth/login           - Prijava
POST /api/auth/refresh         - Osveži token
GET  /api/auth/me              - Podatki o uporabniku
POST /api/auth/logout          - Odjava
```

#### Chat (glavna komunikacija z AI)
```
POST /api/chat                 - Pošlji sporočilo → Ollama orchestrator
POST /api/chat/with-files      - Pošlji sporočilo + datoteke → Claude Opus 4 vision
GET  /api/chat/history         - Zgodovina pogovorov
GET  /api/chat/history/{pid}   - Zgodovina za projekt
POST /api/chat/export-word     - Izvozi markdown → Word
POST /api/chat/generate-document - Generiraj profesionalen dokument iz predloge
GET  /api/chat/pending-actions - Čakajoče akcije
POST /api/chat/actions/{id}/confirm - Potrdi akcijo
POST /api/chat/actions/{id}/reject  - Zavrni akcijo
DELETE /api/chat/history       - Počisti zgodovino
```

#### Projekti
```
GET    /api/projekti           - Seznam projektov (s filtri)
POST   /api/projekti           - Ustvari projekt
GET    /api/projekti/{id}      - Podrobnosti projekta
GET    /api/projekti/{id}/full - Projekt + emaili + časovnica
PUT    /api/projekti/{id}      - Posodobi projekt
```

#### Emaili
```
GET    /api/emaili             - Seznam emailov (s filtri)
GET    /api/emaili/{id}/analysis - Analiza emaila
POST   /api/emaili/{id}/analyze  - Re-analiziraj z LLM
```

#### Sistem
```
GET    /api/system/health      - Zdravje sistema
GET    /api/system/db          - Status baze
GET    /api/system/ollama      - Status Ollama
```

### 5.3 Uporabniške vloge in dovoljenja

| Vloga | Opis | Dovoljenja |
|-------|------|-----------|
| `admin` | Administrator | Vse |
| `prodaja` | Prodaja | Projekti, dokumenti, ponudbe, emaili |
| `tehnologija` | Tehnologija | Teh. dokumenti, CalcuQuote, Largo |
| `proizvodnja` | Proizvodnja | Branje projektov/dokumentov/zalog |
| `nabava` | Nabava | Ponudbe, emaili |
| `racunovodstvo` | Računovodstvo | Projekti, dokumenti, Largo |
| `readonly` | Samo branje | Branje vseh podatkov |

---

## 6. Frontend struktura

### 6.1 Strani (Next.js App Router)

```
nextjs-app/src/app/
├── login/page.tsx              - Prijava
├── (dashboard)/
│   ├── layout.tsx              - Dashboard layout z navigacijo
│   ├── chat/page.tsx           - Chat vmesnik (glavna stran)
│   ├── projekti/
│   │   ├── page.tsx            - Seznam projektov
│   │   └── [id]/page.tsx       - Podrobnosti projekta
│   └── emaili/
│       ├── page.tsx            - Seznam emailov
│       └── [id]/page.tsx       - Podrobnosti emaila
```

### 6.2 Komponente

```
src/components/
├── brand/
│   ├── LuznarLogo.tsx          - Luznar logotip (SVG)
│   ├── DiamondPattern.tsx      - Vzorec za ozadja
│   └── GoldAccentLine.tsx      - Zlata črtna dekoracija
├── chat/
│   ├── ChatInput.tsx           - Vnos sporočila + file upload (paperclip, drag-drop)
│   ├── ChatWelcome.tsx         - Začetni zaslon chata
│   ├── MessageBubble.tsx       - Prikaz sporočil (Markdown, attachments, Word export)
│   ├── ActionButtons.tsx       - Potrdi/Zavrni gumbi za akcije
│   ├── SuggestedCommands.tsx   - Predlagani ukazi
│   └── TypingIndicator.tsx     - Indikator tipkanja
├── layout/
│   ├── AppBar.tsx              - Zgornja navigacijska vrstica
│   ├── BottomNav.tsx           - Spodnja navigacija (mobilno)
│   └── LogoutDialog.tsx        - Dialog za odjavo
├── projects/
│   └── ProjectCard.tsx         - Kartica projekta
├── emails/
│   └── EmailCard.tsx           - Kartica emaila
└── ui/
    ├── SectionCard.tsx         - Kartica razdelka
    ├── Badge.tsx               - Značka (status)
    ├── Spinner.tsx             - Nalaganje
    ├── EmptyState.tsx          - Prazno stanje
    ├── ErrorState.tsx          - Stanje napake
    └── FilterChipBar.tsx       - Filtrirni čipi
```

### 6.3 Tipi

```
src/types/
├── chat.ts                    - ChatMessage, ChatAttachment, ChatAction
├── email.ts                   - Email
├── projekt.ts                 - Projekt, ProjektFull, ProjektCasovnica
└── user.ts                    - User
```

### 6.4 API layer

```
src/lib/
├── api.ts                     - Vse API funkcije (login, chat, projekti, emaili, export)
└── utils.ts                   - Pomožne funkcije (formatTime, itd.)
```

---

## 7. AI Agent sistem

### 7.1 Orchestrator (Ollama)

**Glavni konverzacijski agent** za vsakodnevno delo z ERP-jem.

**Tok:**
```
Uporabniško sporočilo
  → System prompt (slovenščina, ERP kontekst, datum, orodja)
  → Ollama tool use loop (max 5 krogov)
    → Tool klici (search_partners, search_orders, ...)
    → Tool rezultati nazaj v kontekst
  → Končni odgovor v slovenščini
```

**Orodja (tools):**

| Kategorija | Orodja |
|------------|--------|
| Partnerji | search_partners, get_partner_details |
| Naročila | search_orders, get_order_details, count_records |
| Ponudbe | search_quotes, get_quote_details |
| Projekti | list_projects, get_project_details, create_project, update_project |
| Delovni nalogi | create_work_order, list_work_orders |
| Poročila | daily_report, summarize_emails |
| Napredno | ask_claude_for_script, ask_claude_for_analysis, run_custom_query |

**Write orodja** zahtevajo uporabnikovo potrditev (CakajocaAkcija).

### 7.2 Claude Vision (process_with_files)

Ko uporabnik pošlje **datoteko + sporočilo**, se uporabi **Claude Opus 4** (`claude-opus-4-6`):

```
Datoteke + sporočilo
  → file_processor.py:
    ├── Slike (image/*) → base64 → Claude image content block
    ├── PDF → base64 → Claude document content block
    ├── Excel (.xlsx) → openpyxl → tekst
    ├── Word (.docx) → python-docx → tekst
    └── CSV → tekst
  → Claude Opus 4 Messages API (content blocks)
  → Odgovor v slovenščini
```

### 7.3 Document Generation

Ko uporabnik klikne **Word** gumb pod agent sporočilom:

```
Agent odgovor (markdown)
  → Uporabnik izbere tip dokumenta:
    ├── Reklamacija (Supplier Quality Complaint)
    ├── RFQ analiza (Analiza povpraševanja)
    ├── BOM pregled (Pregled kosovnice)
    └── Poročilo o pregledu
  → Claude Sonnet ekstrahira strukturirane JSON podatke
  → document_templates.py generira Luznar-brandiran .docx
  → Prenos datoteke
```

### 7.4 LLM Routing

| Naloga | Primarni | Fallback |
|--------|----------|----------|
| Chat pogovori | Ollama (lokalno) | Claude |
| Email kategorizacija | Ollama | Claude |
| Datoteke + slike | Claude Opus 4 | - |
| Kompleksne SQL poizvedbe | Claude Sonnet 4.5 | - |
| Python analize | Claude Sonnet 4.5 | - |
| Ekstrakcija za dokumente | Claude Sonnet 4.5 | - |

---

## 8. Baza podatkov

### 8.1 Schema: ai_agent

| Tabela | Namen | Ključna polja |
|--------|-------|---------------|
| **Uporabniki** | Uporabniki sistema | username, password_hash, vloga, mailbox |
| **Projekti** | Projektno vodenje | stevilka_projekta, naziv, faza, status, stranka_id |
| **Emaili** | Sinhronizirani emaili | outlook_id, kategorija, rfq_podkategorija, izvleceni_podatki |
| **Dokumenti** | Projektna dokumentacija | tip, naziv_datoteke, verzija, pot_do_datoteke |
| **ChatHistory** | Zgodovina pogovorov | user_id, role, content, projekt_id |
| **CakajocaAkcije** | Čakajoče potrditve | tip_akcije, opis, predlagani_podatki, status |
| **DelovniNalogi** | Delovni nalogi | projekt_id, largo_dn_id, stevilka_dn, status |
| **ProjektCasovnica** | Časovnica projektov | dogodek, opis, stara/nova_vrednost |
| **AuditLog** | Revizijska sled | - |
| **Obvestila** | Obvestila | - |

### 8.2 ERP tabele (dbo schema - Largo)

| Tabela | Vrstic | Namen |
|--------|--------|-------|
| Partnerji | 2,385 | Stranke in dobavitelji |
| Narocilo | 23,016 | Naročila (P=prodaja, N=nabava) |
| NarociloPostav | - | Postavke naročil |
| Ponudba | 8,009 | Ponudbe |
| Dobavnica | 19,545 | Dobavnice |
| Faktura | - | Fakture |
| Promet | 509,008 | Skladiščni premiki |
| Materialni | 265,918 | Material/zaloge |
| Kalkulacija | 256,313 | Kalkulacije |
| Kosovnica | - | BOM/kosovnice |
| DelPostopek | 426,203 | Delovni postopki |
| DelovniNalog | - | Delovni nalogi |
| PotekDelovnegaNaloga | 489,530 | Potek proizvodnje |

---

## 9. Projektni lifecycle

```
1. RFQ Email prejet (Outlook → MS Graph sync)
   └── Email Agent kategorizira kot "RFQ"
   └── Izvleče: stranka, izdelek, količina, rok

2. Faza: RFQ
   └── Uporabnik ustvari projekt (ročno ali agent)
   └── Stevilka projekta generirana

3. Faza: Ponudba
   └── Agent pripravi ponudbo (CalcuQuote integracija)
   └── PDF ponudba generirana

4. Faza: Naročilo
   └── Stranka potrdi naročilo
   └── BOM uvoz, delovni postopki

5. Faza: Tehnologija
   └── Tehnični pregled, dokumentacija

6. Faza: Nabava
   └── Naročanje komponent

7. Faza: Proizvodnja
   └── Delovni nalogi v Largo
   └── Agent spremlja status

8. Faza: Dostava → Zaključek
   └── Dobavnice, fakture
```

---

## 10. Konfiguracija (.env)

```bash
# Aplikacija
APP_ENV=development
DEBUG=true

# Baza
DATABASE_URL=mssql+pyodbc://user:pass@SERVER/DB?driver=ODBC+Driver+17+for+SQL+Server

# JWT
JWT_SECRET_KEY=...
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Ollama (lokalni LLM)
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3:8b
OLLAMA_TOOL_MODEL=llama4:scout  # opcijsko

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
# ANTHROPIC_VISION_MODEL=claude-opus-4-6 (v config.py)

# Microsoft Graph (email sync)
MS_GRAPH_CLIENT_ID=...
MS_GRAPH_CLIENT_SECRET=...
MS_GRAPH_TENANT_ID=...
MS_GRAPH_MAILBOX=info@luznar.si,agent@luznar.com

# SMB (projektne mape)
SMB_SERVER=192.168.0.113
SMB_SHARE=izdelki

# CORS
CORS_ORIGINS=http://localhost:3000,http://192.168.0.66:9090,...
```

---

## 11. Deployment

### Build & Deploy

```bash
# Backend
docker compose build backend && docker compose up -d backend

# Frontend (web)
docker compose build web && docker compose up -d web

# Vse skupaj
docker compose up -d
```

### Omrežje

| Naslov | Storitev |
|--------|----------|
| 192.168.0.66:8000 | Backend API |
| 192.168.0.66:9090 | Web frontend |
| 192.168.0.66:11434 | Ollama LLM |
| 192.168.0.113 | SMB file share |

---

## 12. Kronologija sprememb (pogovor 25.02.2026)

### Implementirano danes:

1. **Chat File Upload + Claude Vision**
   - `ChatInput.tsx` - paperclip gumb, drag-drop, file chips
   - `MessageBubble.tsx` - attachment badges v user sporočilih
   - `api.ts` - `apiSendMessageWithFiles()` (FormData)
   - `chat.py` - `POST /chat/with-files` endpoint
   - `orchestrator.py` - `process_with_files()` z Claude Opus 4
   - `file_processor.py` - procesiranje slik, PDF, Excel, Word, CSV
   - `config.py` - `anthropic_vision_model = "claude-opus-4-6"`

2. **Word Document Export**
   - `markdown_to_word.py` - generičen markdown → Word
   - `chat.py` - `POST /chat/export-word` endpoint
   - `api.ts` - `apiExportWord()`

3. **Profesionalne Document Templates**
   - `document_templates.py` - 4 predloge z Luznar brandingom:
     - **Reklamacija** (Supplier Quality Complaint) - po vzoru 100100306.pdf
     - **RFQ analiza** (Analiza povpraševanja)
     - **BOM pregled** (Pregled kosovnice)
     - **Poročilo o pregledu**
   - `chat.py` - `POST /chat/generate-document` endpoint
   - `api.ts` - `apiGenerateDocument()`
   - `MessageBubble.tsx` - dropdown meni za izbiro tipa dokumenta

4. **Izboljšan error handling**
   - `chat/page.tsx` - specifične napake namesto generičnega sporočila

5. **Anthropic API key posodobljen**

---

## 13. Znane omejitve

- Ollama timeout pri kompleksnih poizvedbah (120s)
- Email sync limit 50 emailov na stran (pagination)
- Lokalni modeli slabši pri reasoning-u kot Claude
- Flutter mobilna app je ločen codebase
- Ni avtomatskega backupa baze
- Rate limiting ni implementiran

---

## 14. Ključne datoteke za razvoj

| Datoteka | Velikost | Namen |
|----------|----------|-------|
| `backend/app/agents/tool_executor.py` | ~54 KB | Implementacija vseh ERP orodij |
| `backend/app/agents/orchestrator.py` | ~14 KB | Glavni AI agent |
| `backend/app/services/document_templates.py` | ~17 KB | Word predloge |
| `backend/app/api/chat.py` | ~12 KB | Chat API endpoints |
| `backend/app/services/email_sync.py` | ~8 KB | MS Graph email sync |
| `nextjs-app/src/lib/api.ts` | ~6 KB | Vse frontend API funkcije |
| `nextjs-app/src/components/chat/MessageBubble.tsx` | ~6 KB | Prikaz sporočil |
