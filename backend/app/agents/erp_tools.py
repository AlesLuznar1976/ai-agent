"""
ERP Tools - Definicije orodij za AI agenta.

Ollama model (Llama 3.1, Qwen2.5, Mistral) kliče ta orodja
za interakcijo z LARGO ERP bazo.

Bralna orodja: brez potrditve uporabnika
Pisalna orodja: zahtevajo potrditev uporabnika
"""

# ============================================================
# TOOL DEFINITIONS (Ollama tool use format)
# ============================================================

READ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_partners",
            "description": "Iskanje poslovnih partnerjev (strank, dobaviteljev) po imenu, šifri ali kraju. Tabela: dbo.Partnerji",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Iskalni niz (ime, del imena, šifra ali kraj partnerja)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov (privzeto 20)",
                        "default": 20
                    }
                },
                "required": ["search"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_partner_details",
            "description": "Pridobi podrobnosti partnerja po šifri (PaSifra). Vrne kontaktne podatke, davčno, email, kontaktne osebe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_id": {
                        "type": "integer",
                        "description": "Šifra partnerja (PaSifra)"
                    }
                },
                "required": ["partner_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "Seznam projektov iz ai_agent.Projekti. Lahko filtriraš po fazi, statusu ali stranki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "faza": {
                        "type": "string",
                        "description": "Filter po fazi: RFQ, Ponudba, Naročilo, Tehnologija, Nabava, Proizvodnja, Dostava, Zaključek",
                        "enum": ["RFQ", "Ponudba", "Naročilo", "Tehnologija", "Nabava", "Proizvodnja", "Dostava", "Zaključek"]
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter po statusu: Aktiven, Na čakanju, Zaključen, Preklican",
                        "enum": ["Aktiven", "Na čakanju", "Zaključen", "Preklican"]
                    },
                    "search": {
                        "type": "string",
                        "description": "Iskanje po nazivu ali številki projekta"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_details",
            "description": "Podrobnosti projekta vključno s časovnico, dokumenti in delovnimi nalogi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "ID projekta ali številka projekta"
                    }
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Iskanje naročil (dbo.Narocilo). Lahko filtriraš po partnerju, statusu, datumu, modulu (P=prodaja, N=nabava).",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_id": {
                        "type": "integer",
                        "description": "Šifra partnerja (NaPartPlac ali NaPartPrjm)"
                    },
                    "partner_name": {
                        "type": "string",
                        "description": "Ime partnerja (iskanje)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Status naročila"
                    },
                    "modul": {
                        "type": "string",
                        "description": "Modul: P=prodaja, N=nabava"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_quotes",
            "description": "Iskanje ponudb (dbo.Ponudba). Filtri: partner, status, datum, modul.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_id": {
                        "type": "integer",
                        "description": "Šifra partnerja (PonPart)"
                    },
                    "partner_name": {
                        "type": "string",
                        "description": "Ime partnerja (iskanje)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Status ponudbe"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_delivery_notes",
            "description": "Pridobi dobavnice (dbo.Dobavnica). Filtri: partner, datum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_id": {
                        "type": "integer",
                        "description": "Šifra partnerja"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoices",
            "description": "Pridobi fakture (dbo.Faktura). Filtri: partner, datum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_id": {
                        "type": "integer",
                        "description": "Šifra partnerja"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_info",
            "description": "Stanje zalog - podatki iz dbo.Promet in dbo.Materialni. Iskanje po artiklu ali skladišču.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_search": {
                        "type": "string",
                        "description": "Iskanje po artiklu (naziv ali šifra)"
                    },
                    "warehouse": {
                        "type": "string",
                        "description": "Šifra skladišča"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_bom",
            "description": "Pridobi kosovnico (BOM - Bill of Materials) iz dbo.Kosovnica za določen artikel ali delovni nalog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "Šifra artikla"
                    },
                    "work_order_id": {
                        "type": "integer",
                        "description": "Številka delovnega naloga"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_work_operations",
            "description": "Pridobi delovne postopke (dbo.DelPostopek) za artikel ali delovni nalog. Operacije v proizvodnem procesu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "Šifra artikla"
                    },
                    "work_order_id": {
                        "type": "integer",
                        "description": "Številka delovnega naloga"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 50
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calculations",
            "description": "Pridobi kalkulacije (dbo.Kalkulacija) s postavkami in vrednostmi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calculation_id": {
                        "type": "integer",
                        "description": "Številka kalkulacije (KStKalk)"
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Tip dokumenta (KTipDok)"
                    },
                    "document_id": {
                        "type": "integer",
                        "description": "Številka dokumenta (KStDok)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_production_status",
            "description": "Status proizvodnje - podatki iz dbo.PotekDelovnegaNaloga. Potek dela na delovnih nalogih.",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_order_id": {
                        "type": "integer",
                        "description": "Številka delovnega naloga"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Datum od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Datum do (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_records",
            "description": "Preštej zapise v tabeli. Uporabno za hitre statistike (koliko partnerjev, naročil, itd.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Ime tabele (npr. Partnerji, Narocilo, Ponudba, Promet, itd.)",
                        "enum": [
                            "Partnerji", "Narocilo", "Ponudba", "Dobavnica",
                            "Faktura", "Promet", "Materialni", "Kalkulacija",
                            "Kosovnica", "DelPostopek", "DelovniNalog",
                            "PotekDelovnegaNaloga", "Rezervacije", "Cenik"
                        ]
                    },
                    "where_clause": {
                        "type": "string",
                        "description": "Opcijski WHERE pogoj za filtriranje (npr. 'NaModul = P' za prodajna naročila)"
                    }
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_emails",
            "description": "Seznam emailov uporabnika. Privzeto vrne samo neprebrane (status=Nov) in izključi nezaželeno pošto (kategorija Splošno). Za vse statuse nastavi all_statuses=true, za vključitev nezaželene pošte nastavi include_junk=true.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kategorija": {
                        "type": "string",
                        "description": "Filtriraj po poslovni kategoriji emaila. Ne nastavljaj za vse emaile.",
                        "enum": ["RFQ", "Naročilo", "Sprememba", "Dokumentacija", "Reklamacija"]
                    },
                    "rfq_podkategorija": {
                        "type": "string",
                        "description": "Filtriraj RFQ emaile po pod-kategoriji. Relevantno samo ko je kategorija=RFQ.",
                        "enum": ["Kompletno", "Nepopolno", "Povpraševanje", "Repeat Order"]
                    },
                    "status": {
                        "type": "string",
                        "description": "Filtriraj po statusu (privzeto Nov)",
                        "enum": ["Nov", "Prebran", "Dodeljen", "Obdelan"]
                    },
                    "all_statuses": {
                        "type": "boolean",
                        "description": "Prikaži emaile vseh statusov (ne samo Nov)",
                        "default": False
                    },
                    "include_junk": {
                        "type": "boolean",
                        "description": "Vključi tudi nezaželeno pošto (kategorija Splošno)",
                        "default": False
                    },
                    "projekt_id": {
                        "type": "integer",
                        "description": "ID projekta"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimalno število rezultatov",
                        "default": 20
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_emails",
            "description": "Povzetek novih emailov - vrne strukturiran pregled po kategorijah s številom emailov, pošiljatelji in zadevami. Uporabi VEDNO ko uporabnik vpraša za povzetek, pregled ali stanje emailov.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Status emailov za povzetek (privzeto Nov)",
                        "enum": ["Nov", "Prebran", "Dodeljen", "Obdelan"],
                        "default": "Nov"
                    },
                    "all_statuses": {
                        "type": "boolean",
                        "description": "Vključi vse statuse",
                        "default": False
                    },
                    "days": {
                        "type": "integer",
                        "description": "Število dni nazaj (privzeto 7)",
                        "default": 7
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "daily_report",
            "description": "Dnevni povzetek emailov za VSAK nabiralnik posebej. Pokaže koliko emailov po kategorijah za vsakega (ales@, info@, nabava@, ...). Uporabi ko uporabnik vpraša za dnevno poročilo, povzetek po nabiralnikih, ali pregled pošte po zaposlenih. NE pošiljaj parametra datum - sistem sam uporabi današnji datum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nabiralnik": {
                        "type": "string",
                        "description": "Opcijsko: samo en nabiralnik (npr. ales, nabava, info). Brez @luznar.com."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_custom_query",
            "description": "Izvedi poljubno SELECT poizvedbo na bazi. SAMO za branje (SELECT). Uporabi ko noben drug tool ne zadostuje.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Kratek opis kaj poizvedba naredi (za audit log)"
                    },
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT poizvedba. MORA se začeti s SELECT. Uporabi TOP za omejitev rezultatov."
                    }
                },
                "required": ["description", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_details",
            "description": "Podrobnosti emaila po ID - celotna vsebina, kategorija, izvlečeni podatki, priloge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "integer",
                        "description": "ID emaila"
                    }
                },
                "required": ["email_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_emails",
            "description": "Poišči povezane emaile - po projektu, pošiljatelju/domeni, ali email niti (RE:/FW: matching). Uporabno za pregled konteksta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "integer",
                        "description": "ID izhodišnega emaila"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Način iskanja povezanih emailov",
                        "enum": ["project", "sender", "thread", "all"],
                        "default": "all"
                    }
                },
                "required": ["email_id"]
            }
        }
    },
]


WRITE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Ustvari nov projekt v ai_agent.Projekti. ZAHTEVA POTRDITEV uporabnika.",
            "parameters": {
                "type": "object",
                "properties": {
                    "naziv": {
                        "type": "string",
                        "description": "Naziv projekta"
                    },
                    "stranka_id": {
                        "type": "integer",
                        "description": "Šifra stranke (PaSifra iz Partnerji)"
                    },
                    "faza": {
                        "type": "string",
                        "description": "Začetna faza projekta",
                        "enum": ["RFQ", "Ponudba", "Naročilo"],
                        "default": "RFQ"
                    },
                    "opombe": {
                        "type": "string",
                        "description": "Opombe k projektu"
                    }
                },
                "required": ["naziv"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_project",
            "description": "Posodobi obstoječ projekt (faza, status, opombe). ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "ID projekta"
                    },
                    "faza": {
                        "type": "string",
                        "description": "Nova faza",
                        "enum": ["RFQ", "Ponudba", "Naročilo", "Tehnologija", "Nabava", "Proizvodnja", "Dostava", "Zaključek"]
                    },
                    "status": {
                        "type": "string",
                        "description": "Nov status",
                        "enum": ["Aktiven", "Na čakanju", "Zaključen", "Preklican"]
                    },
                    "opombe": {
                        "type": "string",
                        "description": "Posodobljene opombe"
                    }
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_work_order",
            "description": "Ustvari delovni nalog za projekt. ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "projekt_id": {
                        "type": "integer",
                        "description": "ID projekta"
                    },
                    "artikel_id": {
                        "type": "integer",
                        "description": "Šifra artikla"
                    },
                    "kolicina": {
                        "type": "number",
                        "description": "Količina"
                    },
                    "datum_plan_zacetek": {
                        "type": "string",
                        "description": "Planirani začetek (YYYY-MM-DD)"
                    },
                    "datum_plan_konec": {
                        "type": "string",
                        "description": "Planirani konec (YYYY-MM-DD)"
                    }
                },
                "required": ["projekt_id", "kolicina"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assign_email_to_project",
            "description": "Dodeli email projektu. ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "integer",
                        "description": "ID emaila"
                    },
                    "projekt_id": {
                        "type": "integer",
                        "description": "ID projekta"
                    }
                },
                "required": ["email_id", "projekt_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_document",
            "description": "Generiraj dokument za projekt (TIV, ponudba, BOM, delovni list, reklamacija). ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "projekt_id": {
                        "type": "integer",
                        "description": "ID projekta"
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Tip dokumenta",
                        "enum": ["TIV", "Ponudba", "BOM", "Delovni_list", "Proizvodni", "Reklamacija"]
                    },
                    "content": {
                        "type": "string",
                        "description": "Besedilo/podatki za dokument (iz pogovora ali analize). Če ni podano, se podatki pridobijo iz projekta."
                    }
                },
                "required": ["doc_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "categorize_email",
            "description": "Ponovna AI kategorizacija emaila. Uporabi ko želiš posodobiti kategorijo ali ko je zaupanje nizko. ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "integer",
                        "description": "ID emaila za kategorizacijo"
                    }
                },
                "required": ["email_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_email_response",
            "description": "Pripravi osnutek odgovora na email. Agent napiše profesionalen odgovor na podlagi vsebine in kategorije. ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "integer",
                        "description": "ID emaila na katerega odgovarjamo"
                    },
                    "response_type": {
                        "type": "string",
                        "description": "Tip odgovora",
                        "enum": ["acknowledge", "request_info", "quote", "reject", "general"],
                        "default": "acknowledge"
                    },
                    "additional_context": {
                        "type": "string",
                        "description": "Dodatne informacije za vključitev v odgovor"
                    }
                },
                "required": ["email_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sync_emails",
            "description": "Sproži sinhronizacijo emailov iz Outlook. Prenese nove emaile in jih kategorizira. ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top": {
                        "type": "integer",
                        "description": "Maksimalno število emailov za sinhronizacijo",
                        "default": 50
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_rfq_summary",
            "description": "Generiraj sumarni dokument (RFQ Summary PDF) za projekt iz povpraševanja. Zbere podatke iz emailov, prilog in BOM-a. ZAHTEVA POTRDITEV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "projekt_id": {
                        "type": "integer",
                        "description": "ID projekta"
                    },
                    "email_id": {
                        "type": "integer",
                        "description": "ID povezanega emaila (opcijsko)"
                    }
                },
                "required": ["projekt_id"]
            }
        }
    },
]


ESCALATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ask_claude_for_script",
            "description": "Ko ne zmoreš rešiti zahteve sam, pokliči Claude AI za pomoč. Claude napiše SQL poizvedbo ali Python skripto. Uporabi za kompleksne analize, nestandardne poizvedbe, ali kadar ne veš kako pristopiti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Opis naloge ki jo mora Claude rešiti. Bodi čim bolj natančen."
                    },
                    "context": {
                        "type": "string",
                        "description": "Dodatni kontekst (katere tabele so relevantne, kaj uporabnik želi, itd.)"
                    }
                },
                "required": ["task_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_claude_for_analysis",
            "description": "Pokliči Claude za podatkovno analizo s Python skripto. Claude napiše Python kodo ki poizveduje ERP bazo in naredi analizo (agregacije, trendi, primerjave, statistike). Uporabi za: mesečne trende, primerjave partnerjev, analizo prodaje, statistike naročil, TOP stranke, itd.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Opis analize (natančno navedi tabele, obdobje, metrike)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Dodatni kontekst - podatki ki jih že imaš"
                    }
                },
                "required": ["task_description"]
            }
        }
    },
]


# All tools combined
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS + ESCALATION_TOOLS

# Tool names that require user confirmation before execution
WRITE_TOOL_NAMES = {t["function"]["name"] for t in WRITE_TOOLS}

# Tool names that are safe to execute without confirmation
READ_TOOL_NAMES = {t["function"]["name"] for t in READ_TOOLS}

# Tool name for escalation to Claude
ESCALATION_TOOL_NAMES = {t["function"]["name"] for t in ESCALATION_TOOLS}
