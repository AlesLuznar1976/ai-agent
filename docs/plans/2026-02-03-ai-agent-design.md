# AI Agent sistem za Luznar Electronics

**Datum:** 2026-02-03
**Verzija:** 1.0
**Status:** Odobren za implementacijo

---

## 1. Povzetek

AI Agent sistem za avtomatizacijo poslovnih procesov pri Luznar Electronics. Sistem vključuje obdelavo emailov, sledenje projektov, integracijo s CalcuQuote in Largo ERP, generiranje dokumentacije ter komunikacijo preko desktop in mobilnih aplikacij.

### Ključne funkcionalnosti

| Funkcionalnost | Opis |
|----------------|------|
| Email obdelava | Avtomatska kategorizacija, izvleček podatkov, povezava s projekti |
| Sledenje projektov | Celoten lifecycle od RFQ do zaključka, časovnica, statusi |
| CalcuQuote integracija | Vnos RFQ, uvoz BOM/labor/vendors po naročilu |
| Dokumentacija | TIV (pri RFQ), proizvodna dokumentacija, ponudbe, poročila |
| Delovni nalogi | Ustvarjanje DN v Largo, spremljanje statusa |
| Human-in-the-loop | Agent predlaga, uporabnik potrdi pred izvedbo |
| Real-time obvestila | WebSocket + push notifikacije na vse naprave |
| Multi-platform | Windows, Android, iPhone iz ene kode (Flutter) |

---

## 2. Arhitektura

```
┌─────────────────────────────────────────────────────────────────┐
│ APLIKACIJE                                                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ Windows  │    │ Android  │    │  iPhone  │    Flutter        │
│  │   App    │    │   App    │    │   App    │    (ena koda)     │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                   │
│       └───────────────┼───────────────┘                         │
│                       │ REST API + WebSocket                    │
└───────────────────────┼─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ BACKEND (Python FastAPI)                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATOR                          │    │
│  │            (usmerja naloge, komunicira)                  │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│  ┌─────────┬───────────┬───┴────┬────────────┬─────────────┐    │
│  │  Email  │  Projekt  │   CQ   │   Largo    │  Document   │    │
│  │  Agent  │   Agent   │ Agent  │   Agent    │   Agent     │    │
│  └────┬────┴─────┬─────┴───┬────┴──────┬─────┴──────┬──────┘    │
│       │          │         │           │            │            │
│  ┌────▼──────────▼─────────▼───────────▼────────────▼──────┐    │
│  │              LLM ENGINE (Hibridni)                       │    │
│  │         Lokalni (Ollama) + Cloud (OpenAI)               │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ INTEGRACIJE                                                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐   │
│  │ Microsoft  │  │ SQL Server │  │ CalcuQuote │  │ Datoteke │   │
│  │   Graph    │  │   Largo    │  │    API     │  │  (PDF,   │   │
│  │  (Email)   │  │  + Agent   │  │            │  │  Excel)  │   │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Tehnični sklad

| Komponenta | Tehnologija | Namen |
|------------|-------------|-------|
| Backend | Python 3.12 + FastAPI | API strežnik |
| Lokalni LLM | Ollama + Llama 3 | Občutljivi podatki |
| Cloud LLM | OpenAI GPT-4 | Kompleksne naloge |
| Baza | SQL Server | Largo + ai_agent shema |
| Aplikacije | Flutter (Dart) | Win/Android/iOS |
| Email | Microsoft Graph API | Outlook integracija |
| Quoting | CalcuQuote API | RFQ, BOM, ponudbe |
| Dokumenti | WeasyPrint, openpyxl | PDF, Excel |
| Kontejnerji | Docker Compose | Deployment |
| Proxy | Nginx | HTTPS, load balancing |

---

## 4. Tok dela

### Faza 1: RFQ

1. Email pride (RFQ od stranke)
2. Agent kategorizira → Sporoči uporabniku
3. Uporabnik: "Ustvari projekt, vnesi v CQ"
4. Agent ustvari projekt + vnese v CalcuQuote
5. Uporabnik ROČNO doda BOM v CalcuQuote
6. Agent pripravi TIV dokumentacijo

### Faza 2: Ponudba

1. Uporabnik: "Pripravi ponudbo"
2. Agent generira PDF ponudbo iz CQ podatkov
3. Uporabnik pregleda → "Pošlji stranki"
4. Agent pošlje email (po potrditvi)

### Faza 3: Naročilo

1. Email pride (naročilo od stranke)
2. Agent zazna, poveže s projektom → Sporoči
3. Uporabnik: "Potegni podatke iz CQ"
4. Agent uvozi: BOM, labor, approved vendors
5. Agent pripravi proizvodno dokumentacijo
6. Uporabnik pregleda → "Ustvari DN"
7. Agent ustvari delovni nalog v Largo (po potrditvi)

### Faza 4: Proizvodnja

1. Agent spremlja status DN v Largo
2. Ob spremembah → Obvesti uporabnike
3. Uporabnik lahko kadarkoli vpraša za status
4. Agent odgovarja, generira poročila

### Faza 5: Zaključek

1. DN zaključen → Agent obvesti
2. Agent pripravi končno poročilo projekta
3. Projekt označen kot zaključen

---

## 5. Podatkovna struktura

### SQL Server shema (ai_agent)

```sql
-- Projekti
ai_agent.Projekti
├── id (PK)
├── stevilka_projekta
├── naziv
├── stranka_id (FK → Largo.Stranke)
├── faza (RFQ|Ponudba|Naročilo|Tehnologija|Nabava|Proizvodnja|Dostava|Zaključek)
├── status (Aktiven|Na čakanju|Zaključen|Preklican)
├── datum_rfq
├── datum_zakljucka
├── odgovorni_prodaja
├── odgovorni_tehnolog
└── opombe

-- Dokumenti
ai_agent.Dokumenti
├── id (PK)
├── projekt_id (FK)
├── tip (RFQ|Ponudba|Naročilo|BOM|Gerber|Specifikacija|TIV|Delovni_list|Drugo)
├── naziv_datoteke
├── verzija
├── pot_do_datoteke
├── datum_nalozeno
└── nalozil_uporabnik

-- Emaili
ai_agent.Emaili
├── id (PK)
├── projekt_id (FK, lahko NULL)
├── outlook_id
├── zadeva
├── posiljatelj
├── prejemniki
├── datum
├── kategorija (RFQ|Naročilo|Sprememba|Dokumentacija|Reklamacija|Splošno)
├── status (Nov|Prebran|Dodeljen|Obdelan)
└── izvleceni_podatki (JSON)

-- Čakajoče akcije (human-in-the-loop)
ai_agent.CakajočeAkcije
├── id (PK)
├── projekt_id (FK)
├── tip_akcije
├── opis
├── predlagani_podatki (JSON)
├── status (Čaka|Potrjeno|Zavrnjeno)
├── ustvaril_agent
├── datum_ustvarjeno
└── potrdil_uporabnik

-- Delovni nalogi
ai_agent.DelovniNalogi
├── id (PK)
├── projekt_id (FK)
├── largo_dn_id (FK → Largo.DelovniNalogi)
├── stevilka_dn
├── artikel_id
├── kolicina
├── status
├── datum_plan_zacetek
├── datum_plan_konec
├── datum_dejanski_zacetek
├── datum_dejanski_konec
└── zadnja_sinhronizacija

-- CalcuQuote povezava
ai_agent.CalcuQuoteRFQ
├── id (PK)
├── projekt_id (FK)
├── calcuquote_rfq_id
├── status
├── datum_vnosa
├── bom_verzija
├── cena_ponudbe
└── datum_ponudbe

-- Časovnica projekta
ai_agent.ProjektCasovnica
├── id (PK)
├── projekt_id (FK)
├── dogodek
├── opis
├── stara_vrednost
├── nova_vrednost
├── datum
└── uporabnik_ali_agent

-- Uporabniki
ai_agent.Uporabniki
├── id (PK)
├── username
├── password_hash
├── email
├── ime
├── priimek
├── vloga
├── aktiven
├── datum_ustvarjen
├── zadnja_prijava
└── push_token

-- Audit log
ai_agent.AuditLog
├── id (PK)
├── user_id
├── action
├── resource_type
├── resource_id
├── details (JSON)
├── ip_address
└── timestamp
```

---

## 6. API Endpointi

### Chat / Agent

```
POST /api/chat                    → Pošlji sporočilo agentu
GET  /api/chat/history/{projekt}  → Zgodovina pogovora
POST /api/actions/{id}/confirm    → Potrdi akcijo
POST /api/actions/{id}/reject     → Zavrni akcijo
```

### Projekti

```
GET  /api/projekti                → Seznam projektov
GET  /api/projekti/{id}           → Podrobnosti projekta
GET  /api/projekti/{id}/casovnica → Časovnica
GET  /api/projekti/{id}/dokumenti → Dokumenti
GET  /api/projekti/{id}/dn        → Delovni nalogi
```

### Emaili

```
GET  /api/emaili                  → Seznam emailov
GET  /api/emaili/nekategorizirani → Nedodeljeni emaili
POST /api/emaili/{id}/dodeli      → Dodeli projektu
```

### Dokumenti

```
POST /api/dokumenti/generiraj     → Generiraj dokument
GET  /api/dokumenti/{id}/download → Prenesi dokument
```

### CalcuQuote

```
POST /api/calcuquote/sync/{id}    → Sinhroniziraj iz CQ
GET  /api/calcuquote/rfq/{id}     → Status RFQ
```

### Obvestila

```
GET       /api/obvestila          → Seznam obvestil
WebSocket /ws/obvestila           → Real-time obvestila
```

---

## 7. Agenti

### 7.1 Orchestrator

Glavni agent ki usmerja naloge in komunicira z uporabnikom.

- Prejme sporočilo od uporabnika
- Analizira namen (intent)
- Delegira nalogo ustreznemu agentu
- Zbere rezultate
- Sporoči nazaj uporabniku

### 7.2 Email Agent

- Spremlja inbox (MS Graph API)
- Kategorizira nove emaile
- Izvleče podatke (stranka, zadeva, priloge)
- Poveže email s projektom
- Pošilja emaile (po potrditvi)

### 7.3 Projekt Agent

- Ustvarja nove projekte
- Spreminja faze projekta
- Vodi časovnico
- Povezuje vse elemente

### 7.4 CalcuQuote Agent

- Vnos RFQ v CalcuQuote
- Sinhronizacija podatkov (BOM, labor, vendors)
- Preverjanje statusa ponudb

### 7.5 Largo Agent

- Branje strank, artiklov iz Largo
- Ustvarjanje delovnih nalogov
- Spremljanje statusa DN
- Vnos dobavnic, faktur (po potrditvi)

### 7.6 Document Agent

- Generiranje PDF dokumentov
- TIV dokumentacija
- Ponudbe, BOM poročila
- Delovni listi

---

## 8. LLM Integracija

### Hibridni pristop

**Lokalni LLM (Ollama):**
- Analiza emailov z občutljivimi podatki
- Kategorizacija dokumentov
- Osnovni ukazi
- Vse kar vsebuje: cene, stranke, interne podatke

**Cloud LLM (OpenAI GPT-4):**
- Kompleksno razumevanje navodil
- Generiranje besedil
- Analiza kompleksnih dokumentov
- Fallback ko lokalni ne razume

---

## 9. Varnost

### Plasti

1. **Omrežna varnost** - HTTPS/TLS, firewall
2. **Avtentikacija** - JWT tokeni, refresh tokeni
3. **Avtorizacija** - Vloge in dovoljenja
4. **Podatki** - Šifriranje, audit log, backup

### Vloge

| Vloga | Opis |
|-------|------|
| admin | Vse pravice |
| prodaja | Projekti, dokumenti, CQ, email |
| tehnologija | Projekti, dokumenti, CQ, Largo DN |
| proizvodnja | Branje projektov, dokumentov, DN |
| nabava | Projekti, dokumenti, CQ, email |
| racunovodstvo | Projekti, dokumenti, Largo |
| readonly | Samo branje |

---

## 10. Flutter aplikacija

### Zasloni

1. **Login** - Prijava uporabnika
2. **Chat** - Pogovor z agentom
3. **Projekti** - Seznam in filtri
4. **Projekt detajl** - Časovnica, dokumenti, DN
5. **Dokumenti** - Pregled in prenos

### Notifikacije

- WebSocket za real-time (ko je app aktivna)
- Push notifikacije (ko app ni aktivna)
- Badge z neprebrano število

---

## 11. Namestitev

### Infrastruktura

- **AI strežnik:** Windows Server / Ubuntu, RTX 5070, 32GB RAM, 1TB SSD
- **SQL Server:** Obstoječ (Largo baza)
- **Omrežje:** LAN 1Gbps

### Docker komponente

- `backend` - Python FastAPI
- `ollama` - Lokalni LLM z GPU
- `nginx` - Reverse proxy, SSL

### Konfiguracija

```bash
# .env
DATABASE_URL=mssql+pyodbc://...
OLLAMA_URL=http://localhost:11434
OPENAI_API_KEY=sk-...
CALCUQUOTE_API_KEY=cq_...
MS_GRAPH_CLIENT_ID=...
MS_GRAPH_CLIENT_SECRET=...
MS_GRAPH_TENANT_ID=...
JWT_SECRET_KEY=...
ENCRYPTION_KEY=...
```

---

## 12. Implementacijski načrt

### Faza 1: Osnova (4-6 tednov)

- Infrastruktura (Docker, Ollama, SQL shema)
- Email Agent
- Flutter osnova (login, chat)

### Faza 2: Projekti + CQ (6-8 tednov)

- Projekt Agent
- CalcuQuote Agent
- Flutter razširitev

### Faza 3: Dokumenti + Largo (6-8 tednov)

- Document Agent
- Largo Agent
- Push notifikacije

### Faza 4: Produkcija (4-6 tednov)

- Varnost, testiranje
- Uvajanje uporabnikov
- Polna produkcija

---

## 13. Potrebno za začetek

| Potrebujem | Opis |
|------------|------|
| SQL Server dostop | IP, port, credentials |
| Microsoft 365 admin | Za Graph API registracijo |
| CalcuQuote API | API key in dokumentacija |
| Strežnik | Pripravljen z RTX 5070 |
| Testni podatki | Primeri emailov, vzorec BOM |
| Kontaktna oseba | Za vprašanja o procesih |

---

## 14. Spremembe

Dizajn se lahko spreminja med implementacijo glede na povratne informacije in nove zahteve.

| Datum | Sprememba | Avtor |
|-------|-----------|-------|
| 2026-02-03 | Začetni dizajn | - |
