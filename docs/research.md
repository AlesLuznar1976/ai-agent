# Research: Multi-Agent Arhitektura za Luznar AI System

**Datum**: 2026-02-25
**Avtor**: AI Agent Development Team
**Status**: Raziskovalni dokument - predlog za implementacijo

---

## 1. Trenutno stanje (AS-IS)

### 1.1 Monolitni Orchestrator

Trenutni sistem uporablja **en sam agent** (`Orchestrator` v `orchestrator.py`) za vse naloge:

```
Uporabnik pošlje sporočilo
        ↓
┌──────────────────────────────┐
│     Orchestrator             │
│  - 1 system prompt (89 vrstic) │
│  - Vseh 36 orodij naenkrat    │
│  - MAX_TOOL_ROUNDS = 5        │
│  - Ollama (lokalni LLM)       │
└──────────┬───────────────────┘
           ↓
    ┌──────┴──────┐
    │ Tool Loop   │ ← max 5 krogov
    │ (Ollama)    │
    └──────┬──────┘
           ↓
┌──────────┴───────────┐
│    ToolExecutor      │
│  ┌─────────────────┐ │
│  │ READ (18 orodij)│ │ → Izvedi takoj
│  │ WRITE (9 orodij)│ │ → Čakaj potrditev
│  │ ESCALATION (2)  │ │ → Posreduj Claude
│  └─────────────────┘ │
└──────────────────────┘
```

### 1.2 Obstoječi LLM modeli

| Model | Uporaba | Kje |
|-------|---------|-----|
| Ollama (llama3:8b / qwen3) | Tool use loop, pogovor | orchestrator.py |
| Claude Sonnet 4.5 | SQL/Python skripte | claude_scriptwriter.py |
| Claude Opus 4.6 | Vision, PDF analiza | orchestrator.process_with_files() |

### 1.3 Obstoječa delna specializacija

Že obstaja **LLM Router** (`app/llm/router.py`) ki loči:
- **LOCAL_TASKS**: intent_recognition, email_categorization, data_extraction, simple_query → Ollama
- **CLOUD_TASKS**: document_generation, complex_reasoning, email_composition → Claude

Že obstaja **EmailAgent** (`app/agents/email_agent.py`) ki je specializiran za:
- Kategorizacijo emailov (RFQ, Naročilo, Sprememba, Dokumentacija, Reklamacija, Splošno)
- RFQ pod-kategorizacijo (Kompletno, Nepopolno, Povpraševanje, Repeat Order)
- Predlaganje odgovorov

### 1.4 Omejitve trenutnega pristopa

| Problem | Posledica |
|---------|-----------|
| **36 orodij naenkrat** | Ollama mora izbirati iz prevelike množice, manjša natančnost izbire |
| **Generičen system prompt** | 89 vrstic ki pokrivajo VSE domene - predolg, razvodenjen |
| **Brez domenskega konteksta** | Agent ne ve ali gre za nabavno, proizvodno ali email nalogo |
| **Fiksni MAX_TOOL_ROUNDS=5** | Preveč za preproste poizvedbe, premalo za kompleksne analize |
| **Monolitna arhitektura** | Ni možno optimizirati posamezne domene neodvisno |
| **Ni specializiranih promptov** | Enak napotek za BOM analizo kot za email odgovor |

---

## 2. Predlagana multi-agent arhitektura (TO-BE)

### 2.1 Pregled

```
Uporabnik pošlje sporočilo
           ↓
┌──────────────────────────────────┐
│         ROUTER AGENT             │
│  Klasificira tip naloge in      │
│  posreduje pravemu specialistu  │
└──────────┬───────────────────────┘
           ↓
     ┌─────┼─────┬──────┬──────┬──────┐
     ↓     ↓     ↓      ↓      ↓      ↓
  ┌─────┐┌─────┐┌──────┐┌─────┐┌─────┐┌──────┐
  │NABAV││EMAIL││PROIZ.││ANAL.││DOKU.││PROJ. │
  │Agent││Agent││Agent ││Agent││Agent││Agent │
  └──┬──┘└──┬──┘└──┬───┘└──┬──┘└──┬──┘└──┬───┘
     └──────┼──────┼───────┼──────┼──────┘
            ↓      ↓       ↓      ↓
     ┌──────────────────────────────────┐
     │         ToolExecutor             │
     │    (nespremenjen - skupen)       │
     └──────────────────────────────────┘
```

### 2.2 Tabela agentov

| # | Agent | Domena | LLM | Št. orodij | Max krogov |
|---|-------|--------|-----|------------|------------|
| 0 | **Router** | Klasifikacija | Ollama (hitro) | 0 | 1 |
| 1 | **Nabavni Agent** | Naročila, ponudbe, partnerji, dobavnice, fakture | Ollama | 10 | 5 |
| 2 | **Email Agent** | Kategorizacija, RFQ, povzetki, odgovori, sinhronizacija | Ollama + Claude | 9 | 4 |
| 3 | **Proizvodni Agent** | Zaloge, BOM, delovni nalogi, postopki, kalkulacije | Ollama | 8 | 5 |
| 4 | **Analitični Agent** | Trendi, statistike, TOP N, primerjave, napovedi | Claude Sonnet 4.5 | 4 | 3 |
| 5 | **Dokumentni Agent** | Slike, PDF-ji, Excel, Word, vision analiza | Claude Opus 4.6 | 2 | 2 |
| 6 | **Projektni Agent** | Projekti, časovnica, dokumenti, delovni nalogi | Ollama | 7 | 4 |

---

## 3. Podrobni opisi agentov

### 3.1 Router Agent (Dispatcher)

**Vloga**: Prejme uporabniško sporočilo in ga posreduje pravemu specializiranemu agentu.

**Kako klasificira**:

```python
class TaskType(Enum):
    NABAVA = "nabava"          # Naročila, ponudbe, partnerji, dobavnice, fakture
    EMAIL = "email"            # Emaili, povzetki, kategorizacija, odgovori
    PROIZVODNJA = "proizvodnja" # Zaloge, BOM, delovni nalogi, proizvodnja
    ANALITIKA = "analitika"    # Trendi, statistike, TOP N, primerjave
    DOKUMENT = "dokument"      # Datoteke, slike, PDF-ji, vision
    PROJEKT = "projekt"        # Projekti, časovnica, status
    GENERAL = "general"        # Vse ostalo → NabavniAgent kot fallback
```

**Ključne besede za klasifikacijo**:

| TaskType | Ključne besede (SL + EN) |
|----------|--------------------------|
| NABAVA | naročilo, ponudba, stranka, dobavitelj, partner, faktura, dobavnica, cena, plačilo |
| EMAIL | email, pošta, mail, povzetek mailov, dnevno poročilo, nabiralnik, odgovori na mail |
| PROIZVODNJA | zaloga, BOM, kosovnica, delovni nalog, proizvodnja, material, skladišče, artikel, postopek |
| ANALITIKA | trend, analiza, statistika, primerjava, top, povprečje, mesečno, letno, rast, padec |
| DOKUMENT | datoteka, slika, PDF, dokument, analiza slike, preberi datoteko |
| PROJEKT | projekt, ustvari projekt, faza, status projekta, časovnica, dodeli |

**System prompt za Router**:

```
Si router za Luznar AI sistem. Tvoja EDINA naloga je klasificirati
uporabnikovo sporočilo v eno od kategorij:
- NABAVA: naročila, ponudbe, stranke, dobavitelji, fakture, dobavnice
- EMAIL: emaili, povzetki, kategorizacija, sinhronizacija, odgovori
- PROIZVODNJA: zaloge, BOM, delovni nalogi, material, proizvodnja
- ANALITIKA: trendi, statistike, TOP N, primerjave, kompleksne analize
- DOKUMENT: datoteke, slike, PDF, vision analiza
- PROJEKT: projekti, časovnica, status, dodeljevanje
- GENERAL: ostalo

Vrni SAMO ime kategorije. Brez razlage.
```

**Eskalacija**: Router NE eskalira - samo posreduje.

**Alternativa brez LLM klica**: Lahko uporabimo keyword matching za hitrejšo klasifikacijo brez Ollama klica (prihranek ~200ms):

```python
def classify_fast(message: str, has_files: bool = False) -> TaskType:
    """Hitra klasifikacija brez LLM klica."""
    msg = message.lower()

    # Datoteke → vedno DOKUMENT
    if has_files:
        return TaskType.DOKUMENT

    # Keyword scoring
    scores = {t: 0 for t in TaskType}

    for keyword, task_type in KEYWORD_MAP.items():
        if keyword in msg:
            scores[task_type] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else TaskType.GENERAL
```

**Primeri klasifikacije**:

| Uporabnikovo sporočilo | → Agent |
|------------------------|---------|
| "Pokaži naročila za Würth" | NABAVA |
| "Koliko novih emailov imam?" | EMAIL |
| "Kakšna je zaloga za artikel X?" | PROIZVODNJA |
| "Top 10 strank po vrednosti letos" | ANALITIKA |
| (pošlje PDF) "Analiziraj ta dokument" | DOKUMENT |
| "Ustvari projekt za stranko Y" | PROJEKT |
| "Pomoč" | GENERAL |

---

### 3.2 Nabavni Agent (Procurement Agent)

**Vloga**: Specialist za nabavno-prodajne operacije - naročila, ponudbe, partnerji, dobavnice, fakture.

**Orodja** (10):

| Orodje | Tip | Opis |
|--------|-----|------|
| `search_partners` | READ | Iskanje strank/dobaviteljev |
| `get_partner_details` | READ | Podrobnosti partnerja |
| `search_orders` | READ | Iskanje naročil |
| `search_quotes` | READ | Iskanje ponudb |
| `get_delivery_notes` | READ | Dobavnice |
| `get_invoices` | READ | Fakture |
| `count_records` | READ | Štetje zapisov |
| `run_custom_query` | READ | Poljubna SELECT poizvedba |
| `ask_claude_for_script` | ESCALATION | SQL za kompleksne poizvedbe |
| `ask_claude_for_analysis` | ESCALATION | Python analiza nabavnih podatkov |

**System prompt**:

```
JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI.

Si AI asistent za LUZNAR d.o.o. - NABAVNI SPECIALIST.
Delaš z ERP sistemom LARGO. DANAŠNJI DATUM: {today}. Leto: {year}.

TVOJA SPECIALIZACIJA:
- Iskanje in pregled naročil (prodajnih NaModul=P in nabavnih NaModul=N)
- Iskanje in pregled ponudb
- Podatki o strankah in dobaviteljih
- Dobavnice in fakture
- Analiza nabavnih trendov

KLJUČNE TABELE:
- dbo.Partnerji (PaSifra, PaNaziv, PaKraj, PaEMail) - stranke in dobavitelji
- dbo.Narocilo (NaStNar, NaPartPlac, NaZnes, NaModul P/N, NaDatNar)
- dbo.NarociloPostav (NpStNar, NpSifra, NpNaziv, NpKol, NpCena, NpZnes)
- dbo.Ponudba (PonStPon, PonPart, PonZnes, PonDatPon, PonStatus)
- dbo.PonudbaPostav (PpStPon, PpSifra, PpNaziv, PpKol, PpCena)
- dbo.Dobavnica (DNsStDNs, DNsPartPlac, DNsDatDNs, DNsZnes)
- dbo.Faktura (FaStFak, FaPartPlac, FaDatFak, FaZnes)

IZBIRA ORODJA:
- "pokaži naročila" → search_orders
- "koliko naročil" → search_orders (z datumskim filtrom) ali count_records
- "poišči stranko" → search_partners
- "podrobnosti partnerja" → get_partner_details
- "ponudbe za" → search_quotes
- "dobavnice" → get_delivery_notes
- "fakture" → get_invoices
- Za trende, TOP N ali kompleksne analize → ask_claude_for_analysis
- Za nestandardne SQL poizvedbe → ask_claude_for_script

DATUMSKI PARAMETRI (leto {year}!):
- "v januarju" → date_from="{year}-01-01", date_to="{year}-01-31"
- "letos" → date_from="{year}-01-01", date_to="{today}"

PRAVILA:
1. Prikaži podatke v preglednih tabelah
2. Nikoli ne izmišljuj podatkov
3. Vedno uporabi leto {year} za datume
4. Bodi konkreten in jedrnati

Uporabnik: {username} (vloga: {role})
```

**Primeri pogovorov**:

**Primer 1 - Iskanje naročil**:
```
Uporabnik: "Pokaži naročila za Würth v februarju"
Agent: Pokliče search_orders(partner_name="Würth", date_from="2026-02-01", date_to="2026-02-28")
→ Prikaže tabelo naročil z zneskom, datumom, statusom
```

**Primer 2 - Analiza dobaviteljev**:
```
Uporabnik: "Kateri dobavitelj ima največji obrat letos?"
Agent: Pokliče ask_claude_for_analysis(task="TOP 10 dobaviteljev po obratu v 2026")
→ Claude napiše Python s pandas aggregacijo → prikaže lestvico
```

**Primer 3 - Podrobnosti partnerja**:
```
Uporabnik: "Podatki o stranki 1234"
Agent: Pokliče get_partner_details(partner_id=1234)
→ Prikaže kontaktne podatke, email, telefon, davčno
```

**Eskalacija**: Ko je poizvedba preveč kompleksna za obstoječa orodja (npr. cross-tabela JOIN), eskalira na `ask_claude_for_script` ali `ask_claude_for_analysis`.

---

### 3.3 Email Agent

**Vloga**: Specialist za upravljanje z emaili - kategorizacija, povzetki, RFQ analiza, odgovori, sinhronizacija.

**Orodja** (9):

| Orodje | Tip | Opis |
|--------|-----|------|
| `get_emails` | READ | Seznam emailov (po kategoriji, statusu) |
| `summarize_emails` | READ | Strukturiran povzetek po kategorijah |
| `daily_report` | READ | Dnevni pregled po nabiralnikih |
| `get_email_details` | READ | Celotna vsebina emaila |
| `get_related_emails` | READ | Povezani emaili (nit, pošiljatelj, projekt) |
| `assign_email_to_project` | WRITE | Dodeli email projektu |
| `categorize_email` | WRITE | Ponovna AI kategorizacija |
| `draft_email_response` | WRITE | Pripravi osnutek odgovora |
| `sync_emails` | WRITE | Sinhronizacija iz Outlook |

**System prompt**:

```
JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI.

Si AI asistent za LUZNAR d.o.o. - EMAIL SPECIALIST.
Delaš z ERP sistemom LARGO. DANAŠNJI DATUM: {today}. Leto: {year}.

TVOJA SPECIALIZACIJA:
- Pregled in povzetek emailov
- Kategorizacija novih emailov
- Analiza RFQ povpraševanj
- Priprava profesionalnih odgovorov
- Sinhronizacija z Outlook

EMAIL KATEGORIJE:
- RFQ: Povpraševanje za ponudbo (request for quote)
  - Kompletno: BOM + Gerber + specifikacije + količina
  - Nepopolno: Delni dokumenti, potrebna dopolnitev
  - Povpraševanje: Splošno vprašanje brez tehničnih dokumentov
  - Repeat Order: Ponovitev prejšnjega naročila
- Naročilo: Potrditev naročila, PO (purchase order)
- Sprememba: ECO/ECN, nova verzija specifikacij
- Dokumentacija: Gerber, BOM, specifikacije
- Reklamacija: Pritožba, težava s kvaliteto
- Splošno: Vse ostalo

NABIRALNIKI:
- info@luznar.com - splošna pošta, RFQ
- martina@luznar.com - prodaja
- spela@luznar.com - prodaja
- agent@luznar.com - avtomatska obdelava
- ales@luznar.com - vodstvo
- nabava@luznar.com - nabava

IZBIRA ORODJA:
- "povzetek emailov", "pregled mailov" → VEDNO summarize_emails
- "dnevno poročilo", "po nabiralnikih" → daily_report (BREZ parametra datum)
- "pokaži email" → get_emails ali get_email_details
- "povezani emaili" → get_related_emails
- "dodeli email projektu" → assign_email_to_project
- "kategoriziraj" → categorize_email
- "odgovori na email", "pripravi odgovor" → draft_email_response
- "sinhroniziraj" → sync_emails

PRAVILA:
1. Ko dobiš povzetek, prikaži CELOTNO besedilo DOBESEDNO
2. Nikoli ne izmišljuj podatkov o emailih
3. Za write operacije (assign, categorize, draft, sync) VEDNO zahtevaj potrditev
4. Bodi konkreten - prikaži pošiljatelja, zadevo, kategorijo

Uporabnik: {username} (vloga: {role})
```

**Primeri pogovorov**:

**Primer 1 - Povzetek emailov**:
```
Uporabnik: "Kakšna je pošta danes?"
Agent: Pokliče summarize_emails()
→ Prikaže: 3 RFQ (2 kompletna, 1 nepopolno), 1 Naročilo, 2 Splošno
```

**Primer 2 - Dnevno poročilo**:
```
Uporabnik: "Dnevni pregled po nabiralnikih"
Agent: Pokliče daily_report()
→ Prikaže pregled za vsak nabiralnik: info@ (5 emailov), ales@ (2 emaila), nabava@ (3 emaili)
```

**Primer 3 - Odgovor na email**:
```
Uporabnik: "Pripravi potrditev prejema za email 42"
Agent: Pokliče draft_email_response(email_id=42, response_type="acknowledge")
→ Prikaže osnutek odgovora v slovenščini/angleščini
→ Čaka potrditev uporabnika pred pošiljanjem
```

**Eskalacija**: Email Agent uporablja obstoječi `EmailAgent` razred za kategorizacijo. Za pripravo odgovorov lahko eskalira na Claude (task_type=EMAIL_COMPOSITION v LLM Router).

---

### 3.4 Proizvodni Agent (Production Agent)

**Vloga**: Specialist za proizvodnjo - zaloge, BOM (kosovnice), delovni nalogi, delovni postopki, kalkulacije.

**Orodja** (8):

| Orodje | Tip | Opis |
|--------|-----|------|
| `get_stock_info` | READ | Stanje zalog (Promet, Materialni) |
| `get_bom` | READ | Kosovnica/BOM za artikel |
| `get_work_operations` | READ | Delovni postopki (DelPostopek) |
| `get_production_status` | READ | Potek proizvodnje (PotekDelovnegaNaloga) |
| `get_calculations` | READ | Kalkulacije s postavkami |
| `count_records` | READ | Štetje zapisov |
| `create_work_order` | WRITE | Ustvari delovni nalog |
| `ask_claude_for_analysis` | ESCALATION | Python analiza proizvodnih podatkov |

**System prompt**:

```
JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI.

Si AI asistent za LUZNAR d.o.o. - PROIZVODNI SPECIALIST.
Podjetje izdeluje elektronske vezja (PCB) in SMT montažo.
Delaš z ERP sistemom LARGO. DANAŠNJI DATUM: {today}. Leto: {year}.

TVOJA SPECIALIZACIJA:
- Pregled zalog materiala in komponent
- Kosovnice (BOM - Bill of Materials)
- Delovni nalogi in proizvodnja
- Delovni postopki (operacije)
- Kalkulacije in stroški

KLJUČNE TABELE:
- dbo.Materialni (MaSifra, MaNaziv, MaSmSifra) - artikli in zaloge
- dbo.Promet (PrSifra, PrKol, PrDatum, PrSmSifra) - skladiščni premiki
- dbo.Kosovnica (KosSifra, KosSest, KosKol) - BOM struktura
- dbo.DelPostopek (DPSifra, DPStOp, DPNazOp) - delovni postopki
- dbo.DelovniNalog (DNsStDNs) - delovni nalogi
- dbo.PotekDelovnegaNaloga (PDNStDNs) - potek dela
- dbo.Kalkulacija (KStKalk, KNaziv) - kalkulacije
- ai_agent.DelovniNalogi - projektni delovni nalogi

IZBIRA ORODJA:
- "zaloga", "stock", "material" → get_stock_info
- "kosovnica", "BOM", "sestavine" → get_bom
- "postopki", "operacije" → get_work_operations
- "status proizvodnje", "potek dela" → get_production_status
- "kalkulacija", "stroški" → get_calculations
- "ustvari delovni nalog" → create_work_order
- Za primerjave, trende, optimizacijo → ask_claude_for_analysis

PCB/SMT KONTEKST:
- PCB = Printed Circuit Board (tiskano vezje)
- SMT = Surface Mount Technology (površinska montaža)
- THT = Through-Hole Technology (skoznja montaža)
- BOM tipično vsebuje: rezistorje, kondenzatorje, IC-je, konektorje, PCB
- Delovni postopki: priprava, tisk paste, polaganje, reflow, AOI, THT, testiranje

PRAVILA:
1. Prikaži BOM v pregledni tabeli (artikel, naziv, količina, enota)
2. Za zaloge prikaži trenutno stanje in lokacijo (skladišče)
3. Nikoli ne izmišljuj podatkov
4. Za create_work_order VEDNO zahtevaj potrditev

Uporabnik: {username} (vloga: {role})
```

**Primeri pogovorov**:

**Primer 1 - BOM pregled**:
```
Uporabnik: "Pokaži BOM za artikel 12345"
Agent: Pokliče get_bom(article_id="12345")
→ Prikaže tabelo: Sestavina | Naziv | Količina | Enota
```

**Primer 2 - Zaloga**:
```
Uporabnik: "Kakšna je zaloga kondenzatorjev 100nF?"
Agent: Pokliče get_stock_info(article_search="100nF")
→ Prikaže: Artikel | Naziv | Skladišče | Količina | Enota
```

**Primer 3 - Proizvodni status**:
```
Uporabnik: "Status delovnega naloga 5678"
Agent: Pokliče get_production_status(work_order_id=5678)
→ Prikaže potek dela: operacija, status, datum začetka/konca
```

**Eskalacija**: Za kompleksne analize (npr. "kateri materiali bodo zmanjkali v naslednjem mesecu") eskalira na `ask_claude_for_analysis` ki napiše Python analizo z pandas.

---

### 3.5 Analitični Agent (Analytics Agent)

**Vloga**: Specialist za kompleksne podatkovne analize - trendi, statistike, TOP N lestvice, primerjave, napovedi.

**LLM**: **Claude Sonnet 4.5** (ne Ollama!) - ker analize zahtevajo kompleksno razmišljanje.

**Orodja** (4):

| Orodje | Tip | Opis |
|--------|-----|------|
| `ask_claude_for_analysis` | ESCALATION | Python skripta s pandas/numpy |
| `ask_claude_for_script` | ESCALATION | SQL za kompleksne poizvedbe |
| `run_custom_query` | READ | Direktna SQL poizvedba |
| `count_records` | READ | Hitro štetje za kontekst |

**System prompt**:

```
JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI.

Si AI asistent za LUZNAR d.o.o. - ANALITIČNI SPECIALIST.
Delaš z ERP sistemom LARGO. DANAŠNJI DATUM: {today}. Leto: {year}.

TVOJA SPECIALIZACIJA:
- Mesečni/letni trendi (naročila, prodaja, nabava)
- TOP N lestvice (stranke, artikli, dobavitelji)
- Primerjave obdobij (letos vs. lani)
- Statistike in agregacije
- Finančni pregledi in povzetki
- Napovedi in prognoza

TIPI ANALIZ:
1. TREND: Časovna vrsta (po mesecih, tednih, dnevih)
   → ask_claude_for_analysis s pandas groupby + resample
2. TOP N: Lestvica po vrednosti/količini
   → ask_claude_for_analysis s groupby + nlargest
3. PRIMERJAVA: Dva ali več obdobij
   → ask_claude_for_analysis s pivot/merge
4. STATISTIKA: Povprečje, mediana, std, min/max
   → ask_claude_for_analysis z numpy/statistics
5. PROGNOZA: Napovedovanje na podlagi preteklih podatkov
   → ask_claude_for_analysis z linearno regresijo ali moving average

ERP TABELE (za analize):
- Narocilo: NaStNar, NaPartPlac, NaZnes, NaDatNar, NaModul (P/N)
- Ponudba: PonStPon, PonPart, PonZnes, PonDatPon
- Dobavnica: DNsStDNs, DNsPartPlac, DNsDatDNs, DNsZnes
- Faktura: FaStFak, FaPartPlac, FaDatFak, FaZnes
- Promet: PrSifra, PrKol, PrDatum, PrSmSifra
- Partnerji: PaSifra, PaNaziv

IZBIRA ORODJA:
- VEDNO uporabi ask_claude_for_analysis za analitične naloge
- ask_claude_for_script za SQL poizvedbe ki presegajo pandas
- count_records za hiter kontekst pred analizo
- run_custom_query SAMO kot zadnja možnost

FORMATIRANJE:
- Trende prikaži s tekstualnimi "grafikoni" (█ bar chart)
- Lestvice prikaži kot oštevilčen seznam z vrednostmi
- Primerjave prikaži v tabeli s stolpcem "Sprememba (%)"
- Vedno dodaj povzetek / zaključek pod podatki

PRAVILA:
1. Vedno navedi obdobje analize
2. Vedno navedi vir podatkov (katere tabele)
3. Za trende prikaži smer (↑ rast, ↓ padec, → stabilno)
4. Nikoli ne izmišljuj številk - uporabi dejanske podatke

Uporabnik: {username} (vloga: {role})
```

**Primeri pogovorov**:

**Primer 1 - TOP stranke**:
```
Uporabnik: "Top 10 strank po vrednosti naročil letos"
Agent: Pokliče ask_claude_for_analysis(
    task="TOP 10 strank po skupni vrednosti prodajnih naročil v 2026.
          Tabele: Narocilo (NaPartPlac, NaZnes, NaDatNar, NaModul='P'),
          Partnerji (PaSifra, PaNaziv). JOIN: NaPartPlac = PaSifra."
)
→ Claude napiše pandas skripto → prikaže lestvico z vrednostmi
```

**Primer 2 - Mesečni trend**:
```
Uporabnik: "Mesečni trend naročil v 2026"
Agent: Pokliče ask_claude_for_analysis(
    task="Mesečni trend prodajnih naročil (NaModul='P') v letu 2026.
          Prikaži po mesecih: število naročil, skupna vrednost, povprečna vrednost."
)
→ Prikaže tabelo po mesecih s stolpci in trendi (↑↓→)
```

**Primer 3 - Primerjava**:
```
Uporabnik: "Primerjaj nabavo Q1 2025 vs Q1 2026"
Agent: Pokliče ask_claude_for_analysis(
    task="Primerjava nabavnih naročil (NaModul='N') med Q1 2025 in Q1 2026.
          Prikaži: skupna vrednost, število naročil, povprečna vrednost, % sprememba."
)
→ Prikaže primerjalno tabelo s % spremembo
```

**Eskalacija**: Analitični agent SAM uporablja Claude za pisanje Python/SQL skript. Ne eskalira naprej - je že najvišja raven za analitiko.

---

### 3.6 Dokumentni Agent (Document Agent)

**Vloga**: Specialist za analizo datotek - slike PCB/elektronike, PDF dokumenti, Excel tabele, Word dokumenti. Uporablja Claude Opus 4.6 z vision podporo.

**LLM**: **Claude Opus 4.6** (vision model) - za slike in PDF-je.

**Orodja** (2):

| Orodje | Tip | Opis |
|--------|-----|------|
| `process_with_files` | INTERNO | Claude vision analiza (slike, PDF) |
| `generate_document` | WRITE | Generiranje Word dokumentov |

**System prompt**:

```
JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI.

Si AI asistent za LUZNAR d.o.o. - DOKUMENTNI SPECIALIST.
Podjetje izdeluje elektronske vezja (PCB) in SMT montažo.
DANAŠNJI DATUM: {today}. Leto: {year}.

TVOJA SPECIALIZACIJA:
- Analiza slik (PCB layout, slike komponent, fotografije defektov)
- Analiza PDF dokumentov (specifikacije, datasheets, RFQ)
- Analiza Excel tabel (BOM, ceniki, nabavne liste)
- Analiza Word dokumentov (pogodbe, specifikacije)
- Generiranje profesionalnih dokumentov

TIPI DATOTEK:

1. SLIKE (image/*):
   - PCB layout → opiši plasti, dimenzije, gostoto komponent
   - Fotografija defekta → identificiraj tip defekta (kratki stik, hladni spoj, ...)
   - Schematic → opiši funkcijske bloke, ključne komponente
   - Komponenta → identificiraj tip, oznake, specifikacije

2. PDF:
   - Datasheet → izvleci ključne parametre (Vcc, Imax, pakiranje, temperatura)
   - RFQ dokument → izvleci zahteve (količina, material, finish, tolerancetxt)
   - Specifikacija → povzemi zahteve in omejitve
   - Reklamacija → izvleci podatke za SQC dokument

3. EXCEL (.xlsx):
   - BOM → prikaži strukturo (del, količina, referenca, vrednost)
   - Cenik → izvleci cene po količinah
   - Nabavna lista → povzemi potrebe

4. WORD (.docx):
   - Pogodba → povzemi ključne točke
   - Specifikacija → izvleci zahteve

FORMATIRANJE:
- Uporabi Markdown za strukturiran odgovor
- Za podatke uporabi **tabele**
- Uporabi **krepko** za ključne vrednosti
- Uporabi ## naslove za razdelke
- Za slike: opiši kaj vidiš, komponente, oznake, stanje

PCB/SMT TERMINOLOGIJA:
- FR4 = standardni PCB material
- HASL/ENIG/OSP = površinski zaključki
- Gerber = standardni format za PCB proizvodnjo
- Aperture = odprtina v stencilu za tisk paste
- Reflow = postopek spajkanja SMT komponent
- AOI = Automated Optical Inspection
- SPI = Solder Paste Inspection
- ICT = In-Circuit Test
- Flying Probe = testiranje brez fiksture

Uporabnik: {username} (vloga: {role})
```

**Primeri pogovorov**:

**Primer 1 - Slika PCB**:
```
Uporabnik: (pošlje sliko PCB) "Analiziraj to vezje"
Agent: Claude Opus 4.6 vision analiza
→ "## Analiza PCB
   - **Dimenzije**: ~80x60mm
   - **Plasti**: 2-plastno vezje (top + bottom)
   - **Komponente**: 45 SMT, 3 THT konektorji
   - **Zaključek**: HASL (vidna srebrna površina)
   - **Opazke**: Gosta postavitev okoli IC U3 - preveriti DRC"
```

**Primer 2 - PDF reklamacija**:
```
Uporabnik: (pošlje PDF) "Naredi reklamacijski dokument iz tega"
Agent: Claude prebere PDF → izvleče podatke → ponudi generiranje Word dokumenta
→ "Iz dokumenta sem izvlekel:
   - Stranka: ABC Electronics
   - Artikel: PCB-2024-001
   - Količina: 500 kos
   - Problem: Hladni spoji na IC U7
   Ali naj generiram reklamacijski dokument (SQC)?"
```

**Primer 3 - Excel BOM**:
```
Uporabnik: (pošlje Excel) "Preveri ta BOM"
Agent: Ekstrahira Excel vsebino → Claude analiza
→ "## BOM Pregled
   - **Skupaj komponent**: 127 pozicij
   - **SMT**: 98 (77%), **THT**: 12 (9%), **Mehanski**: 17 (13%)
   - **⚠ Opozorila**:
     - R23 (10kΩ) - velikost 0201 je zahtevna za SMT
     - C45 (100μF) - elektrolitski v SMT - preveriti višino
   - **Manjkajoče info**: 3 pozicije brez MPN (Manufacturer Part Number)"
```

**Eskalacija**: Dokumentni agent NE eskalira - Claude Opus 4.6 je že najmočnejši model. Lahko pa predlaga uporabniku, da posreduje rezultat drugemu agentu (npr. "Ali naj ustvarim projekt za ta RFQ?").

---

### 3.7 Projektni Agent (Project Agent)

**Vloga**: Specialist za upravljanje projektov - ustvarjanje, posodabljanje, časovnica, dokumenti, dodeljevanje emailov.

**Orodja** (7):

| Orodje | Tip | Opis |
|--------|-----|------|
| `list_projects` | READ | Seznam projektov (po fazi, statusu, stranki) |
| `get_project_details` | READ | Podrobnosti projekta + časovnica + dokumenti |
| `search_partners` | READ | Iskanje stranke za projekt |
| `create_project` | WRITE | Ustvari nov projekt |
| `update_project` | WRITE | Posodobi fazo/status/opombe |
| `assign_email_to_project` | WRITE | Dodeli email projektu |
| `generate_rfq_summary` | WRITE | Generiraj RFQ summary dokument |

**System prompt**:

```
JEZIK: Odgovarjaj IZKLJUČNO v SLOVENŠČINI.

Si AI asistent za LUZNAR d.o.o. - PROJEKTNI SPECIALIST.
Delaš z ERP sistemom LARGO. DANAŠNJI DATUM: {today}. Leto: {year}.

TVOJA SPECIALIZACIJA:
- Ustvarjanje in upravljanje projektov
- Spremljanje faz in statusov
- Pregled časovnice (timeline)
- Dodeljevanje emailov projektom
- Generiranje RFQ summary dokumentov

PROJEKTNE FAZE (življenjski cikel):
1. RFQ → 2. Ponudba → 3. Naročilo → 4. Tehnologija →
5. Nabava → 6. Proizvodnja → 7. Dostava → 8. Zaključek

STATUSI:
- Aktiven: Projekt je v teku
- Na čakanju: Začasno ustavljen (čaka na stranko/material)
- Zaključen: Uspešno končan
- Preklican: Preklican (stranka odpovedala)

FORMAT ŠTEVILKE: PRJ-{year}-NNN (auto-generiran)

IZBIRA ORODJA:
- "seznam projektov", "pokaži projekte" → list_projects
- "podrobnosti projekta" → get_project_details
- "ustvari projekt" → create_project (ZAHTEVA POTRDITEV)
- "posodobi projekt", "spremeni fazo" → update_project (ZAHTEVA POTRDITEV)
- "dodeli email projektu" → assign_email_to_project (ZAHTEVA POTRDITEV)
- "generiraj RFQ summary" → generate_rfq_summary (ZAHTEVA POTRDITEV)
- Za iskanje stranke → search_partners

PRAVILA:
1. Vedno preveri ali projekt že obstaja preden ustvariš novega
2. Pri create_project VEDNO poprosi za potrditev
3. Pri update_project prikaži staro in novo vrednost
4. Prikaži časovnico kronološko (najnovejše najprej)
5. Za dodeljevanje emailov preveri ali je email že dodeljen

Uporabnik: {username} (vloga: {role})
Aktiven projekt: {current_project}
```

**Primeri pogovorov**:

**Primer 1 - Ustvari projekt**:
```
Uporabnik: "Ustvari projekt za stranko Würth, RFQ za PCB"
Agent: 1. Pokliče search_partners(search="Würth") → najde PaSifra=1234
       2. Pokliče create_project(naziv="PCB Würth", stranka_id=1234, faza="RFQ")
→ "Predlagam ustvarjanje projekta:
   - Naziv: PCB Würth
   - Stranka: Würth Elektronik (1234)
   - Faza: RFQ
   Ali potrdite?"
```

**Primer 2 - Pregled projekta**:
```
Uporabnik: "Podrobnosti projekta PRJ-2026-015"
Agent: Pokliče get_project_details(project_id=15)
→ Prikaže: naziv, stranka, faza, status, časovnica, dokumenti, delovni nalogi
```

**Primer 3 - Posodobitev faze**:
```
Uporabnik: "Premakni projekt 15 v fazo Naročilo"
Agent: Pokliče update_project(project_id=15, faza="Naročilo")
→ "Predlagam spremembo:
   - Projekt: PRJ-2026-015
   - Faza: Ponudba → Naročilo
   Ali potrdite?"
```

**Eskalacija**: Projektni agent NE eskalira na Claude. Za kompleksne projektne analize (npr. "kateri projekti zamujajo") bi lahko uporabil `ask_claude_for_analysis`, ki ga lahko dodamo v seznam orodij.

---

## 4. Router logika - podrobnosti

### 4.1 Hibridna klasifikacija

Priporočamo **hibridni pristop**: najprej hitra keyword klasifikacija, nato LLM samo če ni jasno.

```python
def classify_message(message: str, has_files: bool = False) -> TaskType:
    """Klasificiraj sporočilo v tip naloge."""

    # 1. Datoteke → vedno DOKUMENT
    if has_files:
        return TaskType.DOKUMENT

    msg = message.lower()

    # 2. Keyword scoring
    scores = {}
    for task_type, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in msg)
        if score > 0:
            scores[task_type] = score

    if not scores:
        return TaskType.GENERAL

    # 3. Če en tip jasno vodi, vrni ga
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) == 1 or sorted_scores[0][1] > sorted_scores[1][1]:
        return sorted_scores[0][0]

    # 4. Neodločeno → Ollama klasifikacija (fallback)
    return await _llm_classify(message)
```

### 4.2 Keyword mapa

```python
KEYWORD_MAP = {
    TaskType.NABAVA: [
        "naročilo", "naročila", "ponudba", "ponudbe", "stranka", "stranke",
        "dobavitelj", "partner", "faktura", "fakture", "dobavnica", "dobavnice",
        "cena", "znesek", "plačilo", "order", "quote",
    ],
    TaskType.EMAIL: [
        "email", "mail", "pošta", "sporočilo", "nabiralnik",
        "povzetek mailov", "pregled emailov", "preveri maile",
        "dnevno poročilo", "sinhroniziraj", "odgovori na",
        "kategoriziraj email",
    ],
    TaskType.PROIZVODNJA: [
        "zaloga", "stock", "material", "artikel", "skladišče",
        "bom", "kosovnica", "sestavina", "delovni nalog",
        "proizvodnja", "postopek", "operacija", "kalkulacija",
    ],
    TaskType.ANALITIKA: [
        "trend", "analiza", "statistika", "primerjava",
        "top", "povprečje", "mesečno", "letno", "tedensko",
        "rast", "padec", "prognoza", "napoved",
        "koliko skupaj", "skupna vrednost",
    ],
    TaskType.PROJEKT: [
        "projekt", "ustvari projekt", "faza", "status projekta",
        "časovnica", "dodeli", "premakni projekt",
        "rfq summary", "projektna mapa",
    ],
    TaskType.DOKUMENT: [
        "datoteka", "dokument", "slika", "fotografija",
        "pdf", "excel", "word", "preberi",
    ],
}
```

### 4.3 Fallback strategija

Če Router ne more klasificirati (ali je `TaskType.GENERAL`):
1. Uporabi **Nabavni Agent** kot privzetega (ker nabavno-prodajne poizvedbe so najpogostejše)
2. Nabavni Agent ima dostop do `ask_claude_for_script` ki lahko reši skoraj karkoli

### 4.4 Multi-agent scenariji

Nekatere naloge presegajo enega agenta. Router lahko sekvenčno pokliče več agentov:

| Scenarij | Agent 1 | Agent 2 |
|----------|---------|---------|
| "Ustvari projekt iz emaila 42" | Email Agent (preberi email) | Projektni Agent (ustvari projekt) |
| "Analiziraj ta PDF in ustvari projekt" | Dokumentni Agent (analiza) | Projektni Agent (ustvari) |
| "Kateri materiali zmanjkujejo za naročilo X?" | Nabavni Agent (naročilo) | Proizvodni Agent (zaloge) |

---

## 5. Implementacijski načrt

### 5.1 Datotečna struktura

```
backend/app/agents/
├── orchestrator.py          ← PREIMENUJ v multi_orchestrator.py
├── router.py                ← NOV: Router/Dispatcher
├── base_agent.py            ← NOV: BaseAgent abstract class
├── specialized/
│   ├── __init__.py
│   ├── nabava_agent.py      ← NOV
│   ├── email_agent_v2.py    ← NOV (razširi obstoječi email_agent.py)
│   ├── production_agent.py  ← NOV
│   ├── analytics_agent.py   ← NOV
│   ├── document_agent.py    ← NOV
│   └── project_agent.py     ← NOV
├── agent_factory.py         ← NOV: AgentFactory
├── erp_tools.py             ← RAZŠIRI: dodaj tool subsets
├── tool_executor.py          ← NESPREMENJEN
├── email_agent.py            ← OHRANI (za backward compatibility)
├── claude_scriptwriter.py    ← NESPREMENJEN
└── python_executor.py        ← NESPREMENJEN
```

### 5.2 BaseAgent

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Osnova za vse specializirane agente."""

    name: str                    # "nabava", "email", "proizvodnja", ...
    description: str             # Kratek opis
    tools: list[dict]            # Podmnožica orodij
    system_prompt_template: str  # System prompt za tega agenta
    max_tool_rounds: int = 5     # Max krogov tool calling
    llm_type: str = "ollama"     # "ollama" ali "claude"

    @abstractmethod
    async def process(self, message, user_id, username, user_role,
                      project_id, conversation_history) -> AgentResponse:
        """Procesira sporočilo z domensko specializacijo."""
        pass

    def get_system_prompt(self, **context) -> str:
        """Vrne formatirani system prompt."""
        return self.system_prompt_template.format(**context)
```

### 5.3 Faze implementacije

**Faza 1: Osnova (brez breaking changes)**
- Ustvari `BaseAgent`, `AgentFactory`, `Router`
- Preimenuj obstoječi `Orchestrator.process()` v `GeneralAgent`
- Router privzeto vrne `GeneralAgent` (enako obnašanje kot danes)
- Dodaj tool subsets v `erp_tools.py`

**Faza 2: Specializirani agenti**
- Implementiraj vseh 6 agentov s specifičnimi system prompti
- Vsak agent rozširja `BaseAgent`
- Router klasificira in posreduje

**Faza 3: Optimizacija**
- Fine-tune keyword klasifikacijo
- Dodaj metriko uspešnosti per agent
- Optimiziraj system prompte na podlagi dejanskih pogovorov
- Dodaj multi-agent sekvenčno izvajanje

### 5.4 Integracija z obstoječim kodom

**chat.py** (API endpoint) - minimalna sprememba:

```python
# Namesto:
orchestrator = get_orchestrator()
agent_response = await orchestrator.process(...)

# Uporabi:
from app.agents.agent_factory import get_agent_for_message
agent = get_agent_for_message(message.message, has_files=False)
agent_response = await agent.process(...)
```

**ToolExecutor** ostane **100% nespremenjen** - vsi agenti ga delijo.

---

## 6. Primerjava AS-IS vs TO-BE

| Aspekt | AS-IS (zdaj) | TO-BE (multi-agent) |
|--------|-------------|---------------------|
| **Agenti** | 1 (Orchestrator) | 7 (Router + 6 specialistov) |
| **System prompt** | 89 vrstic (vse domene) | 20-35 vrstic (fokusirano) |
| **Orodij na zahtevo** | 36 (vse naenkrat) | 4-10 (podmnožica) |
| **LLM izbira** | Vedno Ollama | Ollama ali Claude per agent |
| **Max tool krogov** | 5 (fiksno) | 2-5 (per agent) |
| **Email obdelava** | Generični tool loop | Specializiran EmailAgent z LLM Router |
| **Analitika** | ask_claude_for_analysis kot orodje | Specializiran AnalyticsAgent z Claude |
| **Datoteke** | Ločena metoda (process_with_files) | Specializiran DocumentAgent |
| **Kontekst** | Zadnjih 10 sporočil (vseh) | Domensko relevanten kontekst |
| **Testabilnost** | End-to-end | Per-agent unit testi |
| **Vzdrževanje** | Vse v enem mestu | Modularno, po domenah |
| **Dodajanje domene** | Spremeni monolitni prompt | Dodaj nov agent file |
| **Hitrost klasifikacije** | N/A (ni klasifikacije) | ~5ms (keywords) ali ~200ms (Ollama) |

---

## 7. Tveganja in omejitve

| Tveganje | Ukrep |
|----------|-------|
| Napačna klasifikacija | Fallback na GeneralAgent ki ima vsa orodja |
| Več agentov = več latence (router klic) | Keyword klasifikacija brez LLM klica (~5ms) |
| Podvajanje kode | BaseAgent abstract class prepreči podvajanje |
| Kompleksnost vzdrževanja | Jasna datotečna struktura, vsak agent v svoji datoteki |
| Multi-agent koordinacija | Faza 3 - sekvenčno izvajanje z jasnim protokolom |
| Sporočilo pripada dvema domenama | Keyword scoring z uteževanjem, LLM fallback |

---

## 8. Prihodnje razširitve

Po uspešni implementaciji multi-agent arhitekture se lahko nadgradimo z:

1. **Quality Agent** - Specialist za reklamacije in kvaliteto (8D report, SPC, SQC)
2. **Financial Agent** - Specialist za finance (fakture, plačila, DDV, bilance)
3. **Planning Agent** - Specialist za planiranje proizvodnje (kapacitete, terminski plan)
4. **Supplier Agent** - Specialist za dobaviteljsko verigo (lead time, alternativni dobavitelji)
5. **Agent Memory** - Dolgoročni spomin za vsakega agenta (učenje iz preteklih interakcij)
6. **Agent-to-Agent komunikacija** - Agenti si lahko medsebojno posredujejo zahteve
7. **Parallel Agent Execution** - Več agentov hkrati za kompleksne naloge

---

## 9. Zaključek

Prehod iz monolitnega orchestratorja na multi-agent arhitekturo prinaša:

- **Boljšo natančnost** - vsak agent pozna svojo domeno
- **Manjšo konfuzijo** - 5-10 orodij namesto 36
- **Fleksibilnost** - pravi LLM za pravo nalogo
- **Modularnost** - neodvisno vzdrževanje in testiranje
- **Razširljivost** - enostavno dodajanje novih agentov

Implementacija je **retrokompatibilna** - obstoječi ToolExecutor, erp_tools in chat.py API ostanejo enaki. Sprememba je v **routingu** sporočil in **specializaciji** system promptov.
