from fpdf import FPDF
from pathlib import Path
import re

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', 'C:/Windows/Fonts/arial.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'C:/Windows/Fonts/arialbd.ttf', uni=True)
        self.add_font('DejaVu', 'I', 'C:/Windows/Fonts/ariali.ttf', uni=True)
        self.add_font('Consolas', '', 'C:/Windows/Fonts/consola.ttf', uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font('DejaVu', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'AI Agent Sistem - Luznar Electronics', 0, 0, 'L')
            self.cell(0, 10, f'Stran {self.page_no()}', 0, 1, 'R')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Verzija 1.0 | Februar 2026', 0, 0, 'C')

    def cover_page(self):
        self.add_page()

        # Header background
        self.set_fill_color(26, 54, 93)
        self.rect(0, 0, 210, 120, 'F')

        # Orange accent
        self.set_fill_color(237, 137, 54)
        self.rect(0, 115, 210, 5, 'F')

        # Title
        self.set_y(40)
        self.set_font('DejaVu', 'B', 32)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'AI AGENT SISTEM', 0, 1, 'C')

        self.set_font('DejaVu', '', 16)
        self.cell(0, 10, 'za Luznar Electronics d.o.o.', 0, 1, 'C')

        self.ln(5)
        self.set_font('DejaVu', 'I', 12)
        self.set_text_color(237, 137, 54)
        self.cell(0, 10, 'Tehnični dizajn dokument', 0, 1, 'C')

        # Info box
        self.set_y(140)
        self.set_text_color(51, 51, 51)
        self.set_font('DejaVu', '', 11)

        info = [
            ('Verzija:', '1.0'),
            ('Datum:', '3. februar 2026'),
            ('Status:', 'Odobren za implementacijo'),
        ]

        for label, value in info:
            self.set_font('DejaVu', 'B', 11)
            self.cell(40, 8, label, 0, 0, 'R')
            self.set_font('DejaVu', '', 11)
            self.cell(0, 8, value, 0, 1, 'L')

        # Description
        self.ln(20)
        self.set_font('DejaVu', '', 10)
        self.set_text_color(80, 80, 80)
        desc = """Ta dokument opisuje tehnični dizajn AI Agent sistema za avtomatizacijo
poslovnih procesov pri Luznar Electronics. Sistem vključuje obdelavo emailov,
sledenje projektov, integracijo s CalcuQuote in Largo ERP, generiranje
dokumentacije ter komunikacijo preko desktop in mobilnih aplikacij."""
        self.multi_cell(0, 6, desc, 0, 'C')

    def chapter_title(self, title, level=1):
        if level == 1:
            self.ln(10)
            self.set_font('DejaVu', 'B', 16)
            self.set_text_color(26, 54, 93)
            self.cell(0, 10, title, 0, 1, 'L')
            self.set_draw_color(237, 137, 54)
            self.set_line_width(0.8)
            self.line(10, self.get_y(), 80, self.get_y())
            self.ln(5)
        elif level == 2:
            self.ln(8)
            self.set_font('DejaVu', 'B', 13)
            self.set_text_color(44, 82, 130)
            self.cell(0, 8, title, 0, 1, 'L')
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        else:
            self.ln(5)
            self.set_font('DejaVu', 'B', 11)
            self.set_text_color(45, 55, 72)
            self.cell(0, 7, title, 0, 1, 'L')
            self.ln(2)

    def body_text(self, text):
        self.set_font('DejaVu', '', 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet_list(self, items):
        self.set_font('DejaVu', '', 10)
        self.set_text_color(51, 51, 51)
        for item in items:
            x = self.get_x()
            self.cell(8, 5, '  -')
            self.multi_cell(175, 5, item)
            self.set_x(x)

    def add_table(self, headers, data, col_widths=None):
        self.ln(3)
        if col_widths is None:
            col_widths = [190 // len(headers)] * len(headers)

        # Header
        self.set_fill_color(44, 82, 130)
        self.set_text_color(255, 255, 255)
        self.set_font('DejaVu', 'B', 9)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, 'C', True)
        self.ln()

        # Data
        self.set_text_color(51, 51, 51)
        self.set_font('DejaVu', '', 9)
        fill = False
        for row in data:
            if fill:
                self.set_fill_color(247, 250, 252)
            else:
                self.set_fill_color(255, 255, 255)

            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, str(cell), 1, 0, 'L', True)
            self.ln()
            fill = not fill
        self.ln(3)

    def code_block(self, code):
        self.ln(2)
        self.set_fill_color(26, 32, 44)
        self.set_text_color(226, 232, 240)
        self.set_font('Consolas', '', 8)

        lines = code.strip().split('\n')
        y_start = self.get_y()
        height = len(lines) * 4 + 6

        # Check if we need a new page
        if self.get_y() + height > 280:
            self.add_page()
            y_start = self.get_y()

        self.rect(10, y_start, 190, height, 'F')
        self.set_xy(13, y_start + 3)

        for line in lines:
            if len(line) > 95:
                line = line[:92] + '...'
            self.cell(0, 4, line, 0, 1)
            self.set_x(13)

        self.ln(3)
        self.set_text_color(51, 51, 51)


def create_pdf():
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover page
    pdf.cover_page()

    # Content pages
    pdf.add_page()

    # 1. Povzetek
    pdf.chapter_title('1. Povzetek')
    pdf.body_text('AI Agent sistem za avtomatizacijo poslovnih procesov pri Luznar Electronics. Sistem vključuje obdelavo emailov, sledenje projektov, integracijo s CalcuQuote in Largo ERP, generiranje dokumentacije ter komunikacijo preko desktop in mobilnih aplikacij.')

    pdf.chapter_title('Ključne funkcionalnosti', 2)
    pdf.add_table(
        ['Funkcionalnost', 'Opis'],
        [
            ['Email obdelava', 'Avtomatska kategorizacija, izvleček podatkov'],
            ['Sledenje projektov', 'Lifecycle od RFQ do zaključka, časovnica'],
            ['CalcuQuote', 'Vnos RFQ, uvoz BOM/labor/vendors'],
            ['Dokumentacija', 'TIV, proizvodna dok., ponudbe, poročila'],
            ['Delovni nalogi', 'Ustvarjanje DN v Largo, spremljanje'],
            ['Human-in-the-loop', 'Agent predlaga, uporabnik potrdi'],
            ['Real-time obvestila', 'WebSocket + push notifikacije'],
            ['Multi-platform', 'Windows, Android, iPhone (Flutter)'],
        ],
        [60, 130]
    )

    # 2. Arhitektura
    pdf.add_page()
    pdf.chapter_title('2. Arhitektura')
    pdf.body_text('Sistem je sestavljen iz treh glavnih plasti: aplikacije (Flutter), backend (Python FastAPI) in integracije (MS Graph, SQL Server, CalcuQuote).')

    pdf.chapter_title('Komponente', 2)
    pdf.bullet_list([
        'Flutter aplikacije - Windows, Android, iOS iz ene kode',
        'Orchestrator - usmerja naloge med agente',
        'Email Agent - spremlja in kategorizira emaile',
        'Projekt Agent - upravlja projekte in časovnico',
        'CalcuQuote Agent - integracija s CQ sistemom',
        'Largo Agent - povezava z ERP sistemom',
        'Document Agent - generiranje PDF/Excel dokumentov',
        'LLM Engine - hibridni (lokalni Ollama + cloud OpenAI)',
    ])

    # 3. Tehnični sklad
    pdf.chapter_title('3. Tehnični sklad')
    pdf.add_table(
        ['Komponenta', 'Tehnologija', 'Namen'],
        [
            ['Backend', 'Python 3.12 + FastAPI', 'API strežnik'],
            ['Lokalni LLM', 'Ollama + Llama 3', 'Občutljivi podatki'],
            ['Cloud LLM', 'OpenAI GPT-4', 'Kompleksne naloge'],
            ['Baza', 'SQL Server', 'Largo + ai_agent shema'],
            ['Aplikacije', 'Flutter (Dart)', 'Win/Android/iOS'],
            ['Email', 'Microsoft Graph API', 'Outlook integracija'],
            ['Quoting', 'CalcuQuote API', 'RFQ, BOM, ponudbe'],
            ['Dokumenti', 'WeasyPrint, openpyxl', 'PDF, Excel'],
            ['Kontejnerji', 'Docker Compose', 'Deployment'],
        ],
        [45, 55, 90]
    )

    # 4. Tok dela
    pdf.add_page()
    pdf.chapter_title('4. Tok dela')

    pdf.chapter_title('Faza 1: RFQ', 3)
    pdf.bullet_list([
        'Email pride (RFQ od stranke)',
        'Agent kategorizira, sporoči uporabniku',
        'Uporabnik: "Ustvari projekt, vnesi v CQ"',
        'Agent ustvari projekt + vnese v CalcuQuote',
        'Uporabnik ROČNO doda BOM v CalcuQuote',
        'Agent pripravi TIV dokumentacijo',
    ])

    pdf.chapter_title('Faza 2: Ponudba', 3)
    pdf.bullet_list([
        'Uporabnik: "Pripravi ponudbo"',
        'Agent generira PDF ponudbo iz CQ podatkov',
        'Uporabnik pregleda, odobri pošiljanje',
        'Agent pošlje email (po potrditvi)',
    ])

    pdf.chapter_title('Faza 3: Naročilo', 3)
    pdf.bullet_list([
        'Email pride (naročilo od stranke)',
        'Agent zazna, poveže s projektom',
        'Uporabnik: "Potegni podatke iz CQ"',
        'Agent uvozi: BOM, labor, approved vendors',
        'Agent pripravi proizvodno dokumentacijo',
        'Uporabnik pregleda, potrdi vnos DN',
        'Agent ustvari delovni nalog v Largo',
    ])

    pdf.chapter_title('Faza 4: Proizvodnja', 3)
    pdf.bullet_list([
        'Agent spremlja status DN v Largo',
        'Ob spremembah obvešča uporabnike',
        'Uporabnik lahko vpraša za status',
        'Agent generira poročila',
    ])

    pdf.chapter_title('Faza 5: Zaključek', 3)
    pdf.bullet_list([
        'DN zaključen, agent obvesti',
        'Agent pripravi končno poročilo',
        'Projekt označen kot zaključen',
    ])

    # 5. Podatkovna struktura
    pdf.add_page()
    pdf.chapter_title('5. Podatkovna struktura')
    pdf.body_text('Vsi podatki se hranijo v SQL Server v novi shemi ai_agent, ločeno od Largo podatkov.')

    pdf.chapter_title('Glavne tabele', 2)
    pdf.add_table(
        ['Tabela', 'Namen', 'Ključna polja'],
        [
            ['Projekti', 'Sledenje projektov', 'stevilka, faza, status, stranka_id'],
            ['Dokumenti', 'Shramba dokumentov', 'projekt_id, tip, verzija, pot'],
            ['Emaili', 'Kategorizirani emaili', 'kategorija, izvleceni_podatki'],
            ['CakajočeAkcije', 'Human-in-the-loop', 'tip_akcije, status, predlagani_podatki'],
            ['DelovniNalogi', 'Povezava z Largo DN', 'largo_dn_id, status'],
            ['CalcuQuoteRFQ', 'CQ integracija', 'calcuquote_rfq_id, bom_verzija'],
            ['ProjektCasovnica', 'Zgodovina sprememb', 'dogodek, stara/nova vrednost'],
            ['Uporabniki', 'Avtentikacija', 'username, vloga, password_hash'],
            ['AuditLog', 'Revizijska sled', 'action, resource, timestamp'],
        ],
        [45, 55, 90]
    )

    # 6. API
    pdf.add_page()
    pdf.chapter_title('6. API Endpointi')

    pdf.chapter_title('Chat / Agent', 2)
    pdf.code_block('''POST /api/chat                    -> Pošlji sporočilo agentu
GET  /api/chat/history/{projekt}  -> Zgodovina pogovora
POST /api/actions/{id}/confirm    -> Potrdi akcijo
POST /api/actions/{id}/reject     -> Zavrni akcijo''')

    pdf.chapter_title('Projekti', 2)
    pdf.code_block('''GET  /api/projekti                -> Seznam projektov
GET  /api/projekti/{id}           -> Podrobnosti projekta
GET  /api/projekti/{id}/casovnica -> Časovnica
GET  /api/projekti/{id}/dokumenti -> Dokumenti projekta''')

    pdf.chapter_title('Emaili', 2)
    pdf.code_block('''GET  /api/emaili                  -> Seznam emailov
GET  /api/emaili/nekategorizirani -> Nedodeljeni emaili
POST /api/emaili/{id}/dodeli      -> Dodeli projektu''')

    pdf.chapter_title('CalcuQuote', 2)
    pdf.code_block('''POST /api/calcuquote/sync/{id}    -> Sinhroniziraj iz CQ
GET  /api/calcuquote/rfq/{id}     -> Status RFQ''')

    # 7. Agenti
    pdf.add_page()
    pdf.chapter_title('7. Agenti')

    pdf.add_table(
        ['Agent', 'Naloge'],
        [
            ['Orchestrator', 'Usmerja naloge, analizira intent, komunicira z uporabnikom'],
            ['Email Agent', 'Spremlja inbox, kategorizira, izvleče podatke, pošilja'],
            ['Projekt Agent', 'CRUD projektov, faze, časovnica, povezave'],
            ['CalcuQuote Agent', 'Vnos RFQ, sync BOM/labor/vendors, status ponudb'],
            ['Largo Agent', 'Branje strank/artiklov, ustvarjanje DN, spremljanje'],
            ['Document Agent', 'Generiranje PDF (TIV, ponudbe), Excel (BOM), delovni listi'],
        ],
        [45, 145]
    )

    # 8. LLM
    pdf.chapter_title('8. LLM Integracija')
    pdf.body_text('Hibridni pristop: lokalni model za občutljive podatke, cloud za kompleksne naloge.')

    pdf.chapter_title('Lokalni LLM (Ollama)', 2)
    pdf.bullet_list([
        'Analiza emailov z občutljivimi podatki',
        'Kategorizacija dokumentov',
        'Osnovni ukazi',
        'Vse kar vsebuje: cene, stranke, interne podatke',
    ])

    pdf.chapter_title('Cloud LLM (OpenAI GPT-4)', 2)
    pdf.bullet_list([
        'Kompleksno razumevanje navodil',
        'Generiranje besedil (ponudbe, emaili)',
        'Analiza kompleksnih dokumentov',
        'Fallback ko lokalni ne razume',
    ])

    # 9. Varnost
    pdf.add_page()
    pdf.chapter_title('9. Varnost')

    pdf.chapter_title('Varnostne plasti', 2)
    pdf.bullet_list([
        'Omrežna varnost - HTTPS/TLS, firewall',
        'Avtentikacija - JWT tokeni, refresh tokeni',
        'Avtorizacija - Vloge in dovoljenja',
        'Podatki - Šifriranje, audit log, backup',
    ])

    pdf.chapter_title('Vloge', 2)
    pdf.add_table(
        ['Vloga', 'Pravice'],
        [
            ['admin', 'Vse pravice'],
            ['prodaja', 'Projekti, dokumenti, CQ, email'],
            ['tehnologija', 'Projekti, dokumenti, CQ, Largo DN'],
            ['proizvodnja', 'Branje projektov, dokumentov, DN'],
            ['nabava', 'Projekti, dokumenti, CQ, email'],
            ['racunovodstvo', 'Projekti, dokumenti, Largo'],
            ['readonly', 'Samo branje'],
        ],
        [50, 140]
    )

    # 10. Flutter
    pdf.chapter_title('10. Flutter aplikacija')
    pdf.body_text('Ena koda za Windows, Android in iOS.')

    pdf.chapter_title('Zasloni', 2)
    pdf.bullet_list([
        'Login - Prijava uporabnika',
        'Chat - Pogovor z agentom',
        'Projekti - Seznam in filtri',
        'Projekt detajl - Časovnica, dokumenti, DN',
        'Dokumenti - Pregled in prenos',
    ])

    pdf.chapter_title('Notifikacije', 2)
    pdf.bullet_list([
        'WebSocket za real-time (ko je app aktivna)',
        'Push notifikacije (ko app ni aktivna)',
        'Badge z neprebrano število',
    ])

    # 11. Namestitev
    pdf.add_page()
    pdf.chapter_title('11. Namestitev')

    pdf.chapter_title('Infrastruktura', 2)
    pdf.add_table(
        ['Komponenta', 'Specifikacije'],
        [
            ['AI strežnik', 'Windows Server / Ubuntu, RTX 5070, 32GB RAM, 1TB SSD'],
            ['SQL Server', 'Obstoječ (Largo baza)'],
            ['Omrežje', 'LAN 1Gbps'],
        ],
        [50, 140]
    )

    pdf.chapter_title('Docker komponente', 2)
    pdf.bullet_list([
        'backend - Python FastAPI',
        'ollama - Lokalni LLM z GPU',
        'nginx - Reverse proxy, SSL',
    ])

    # 12. Implementacija
    pdf.add_page()
    pdf.chapter_title('12. Implementacijski načrt')

    pdf.add_table(
        ['Faza', 'Vsebina', 'Trajanje'],
        [
            ['Faza 1: Osnova', 'Infrastruktura, Email Agent, Flutter osnova', '4-6 tednov'],
            ['Faza 2: Projekti + CQ', 'Projekt Agent, CalcuQuote Agent, Flutter razširitev', '6-8 tednov'],
            ['Faza 3: Dokumenti + Largo', 'Document Agent, Largo Agent, push notifikacije', '6-8 tednov'],
            ['Faza 4: Produkcija', 'Varnost, testiranje, uvajanje, polna produkcija', '4-6 tednov'],
        ],
        [50, 100, 40]
    )

    # 13. Potrebno za začetek
    pdf.chapter_title('13. Potrebno za začetek')
    pdf.add_table(
        ['Potrebujem', 'Opis'],
        [
            ['SQL Server dostop', 'IP, port, credentials'],
            ['Microsoft 365 admin', 'Za Graph API registracijo'],
            ['CalcuQuote API', 'API key in dokumentacija'],
            ['Strežnik', 'Pripravljen z RTX 5070'],
            ['Testni podatki', 'Primeri emailov, vzorec BOM'],
            ['Kontaktna oseba', 'Za vprašanja o procesih'],
        ],
        [55, 135]
    )

    # Save
    pdf_path = Path(__file__).parent / "2026-02-03-ai-agent-design.pdf"
    pdf.output(str(pdf_path))
    print(f"PDF ustvarjen: {pdf_path}")


if __name__ == '__main__':
    create_pdf()
