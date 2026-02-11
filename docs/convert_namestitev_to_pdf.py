from fpdf import FPDF
from pathlib import Path


class PDFManual(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('Arial', '', 'C:/Windows/Fonts/arial.ttf')
        self.add_font('Arial', 'B', 'C:/Windows/Fonts/arialbd.ttf')
        self.add_font('Arial', 'I', 'C:/Windows/Fonts/ariali.ttf')
        self.add_font('Consolas', '', 'C:/Windows/Fonts/consola.ttf')

    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, 'AI Agent - Navodila za namestitev', 0, 0, 'L')
            self.cell(0, 10, f'Stran {self.page_no()}', 0, 1, 'R')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Luznar Electronics | Februar 2026', 0, 0, 'C')

    def chapter(self, title, level=1):
        if level == 1:
            self.ln(8)
            self.set_font('Arial', 'B', 16)
            self.set_text_color(26, 54, 93)
            self.cell(0, 10, title, 0, 1)
            self.set_draw_color(237, 137, 54)
            self.set_line_width(0.8)
            self.line(10, self.get_y(), 80, self.get_y())
            self.ln(5)
        elif level == 2:
            self.ln(5)
            self.set_font('Arial', 'B', 13)
            self.set_text_color(44, 82, 130)
            self.cell(0, 8, title, 0, 1)
            self.ln(2)
        else:
            self.ln(3)
            self.set_font('Arial', 'B', 11)
            self.set_text_color(51, 51, 51)
            self.cell(0, 6, title, 0, 1)
            self.ln(1)

    def text(self, content):
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, content)
        self.ln(2)

    def bullet(self, items):
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 51, 51)
        for item in items:
            self.cell(8, 5, '  -')
            self.multi_cell(175, 5, item)

    def code(self, content):
        self.ln(2)
        self.set_fill_color(240, 240, 240)
        self.set_font('Consolas', '', 8)
        self.set_text_color(51, 51, 51)

        lines = content.strip().split('\n')
        y_start = self.get_y()
        height = len(lines) * 4 + 6

        if self.get_y() + height > 270:
            self.add_page()
            y_start = self.get_y()

        self.rect(10, y_start, 190, height, 'F')
        self.set_xy(12, y_start + 3)

        for line in lines:
            if len(line) > 100:
                line = line[:97] + '...'
            self.cell(0, 4, line, 0, 1)
            self.set_x(12)

        self.ln(3)

    def table(self, headers, data, widths=None):
        if widths is None:
            widths = [190 // len(headers)] * len(headers)

        self.set_fill_color(44, 82, 130)
        self.set_text_color(255)
        self.set_font('Arial', 'B', 9)

        for i, h in enumerate(headers):
            self.cell(widths[i], 7, h, 1, 0, 'C', True)
        self.ln()

        self.set_text_color(51, 51, 51)
        self.set_font('Arial', '', 9)
        fill = False

        for row in data:
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)

            for i, cell in enumerate(row):
                self.cell(widths[i], 6, str(cell), 1, 0, 'L', True)
            self.ln()
            fill = not fill

        self.ln(3)


def create_pdf():
    pdf = PDFManual()
    pdf.set_auto_page_break(True, 20)

    # Naslovna stran
    pdf.add_page()
    pdf.set_fill_color(26, 54, 93)
    pdf.rect(0, 0, 210, 100, 'F')
    pdf.set_fill_color(237, 137, 54)
    pdf.rect(0, 95, 210, 5, 'F')

    pdf.set_y(35)
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(255)
    pdf.cell(0, 12, 'AI AGENT SISTEM', 0, 1, 'C')
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, 'Navodila za namestitev', 0, 1, 'C')
    pdf.set_font('Arial', 'I', 12)
    pdf.set_text_color(237, 137, 54)
    pdf.cell(0, 10, 'Luznar Electronics d.o.o.', 0, 1, 'C')

    pdf.set_y(120)
    pdf.set_text_color(51, 51, 51)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, 'Verzija: 1.0', 0, 1, 'C')
    pdf.cell(0, 8, 'Datum: Februar 2026', 0, 1, 'C')

    # Kazalo
    pdf.add_page()
    pdf.chapter('Kazalo vsebine')
    pdf.text('''
1. Zahteve za strojno opremo
2. Operacijski sistem
3. Namestitev na Ubuntu Server
   3.1 Osnovna konfiguracija
   3.2 NVIDIA Driver
   3.3 NVIDIA Container Toolkit
   3.4 Docker
   3.5 Python 3.12
   3.6 Microsoft ODBC Driver
   3.7 Firewall
4. Namestitev na Windows Server
5. Namestitev AI Agent aplikacije
6. SQL Server priprava
7. Preverjanje namestitve
8. Sistemd servis
9. Varnostne kopije
10. Odpravljanje težav
''')

    # 1. Zahteve
    pdf.add_page()
    pdf.chapter('1. Zahteve za strojno opremo')
    pdf.table(
        ['Komponenta', 'Minimalno', 'Priporočeno'],
        [
            ['CPU', '8 jeder', '16 jeder'],
            ['RAM', '16 GB', '32 GB'],
            ['GPU', 'RTX 3060 (12GB)', 'RTX 5070 (12GB+)'],
            ['Disk', '256 GB SSD', '1 TB NVMe SSD'],
            ['Omrežje', '100 Mbps', '1 Gbps'],
        ],
        [50, 70, 70]
    )

    # 2. OS
    pdf.chapter('2. Operacijski sistem')
    pdf.text('Priporočeni operacijski sistemi:')
    pdf.bullet([
        'Ubuntu Server 24.04 LTS (priporočeno)',
        'Windows Server 2022 Standard/Datacenter',
    ])

    # 3. Ubuntu
    pdf.add_page()
    pdf.chapter('3. Namestitev na Ubuntu Server')

    pdf.chapter('3.1 Osnovna konfiguracija', 2)
    pdf.code('''# Posodobi sistem
sudo apt update && sudo apt upgrade -y

# Namesti osnovne pakete
sudo apt install -y curl wget git htop nano unzip

# Nastavi casovni pas
sudo timedatectl set-timezone Europe/Ljubljana''')

    pdf.chapter('3.2 NVIDIA Driver', 2)
    pdf.code('''# Preveri GPU
lspci | grep -i nvidia

# Dodaj repozitorij in namesti driver
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update
sudo apt install -y nvidia-driver-550

# Ponovno zazeni
sudo reboot

# Preveri
nvidia-smi''')

    pdf.chapter('3.3 NVIDIA Container Toolkit', 2)
    pdf.text('Za uporabo GPU v Docker kontejnerjih:')
    pdf.code('''# Dodaj repozitorij
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \\
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Namesti
sudo apt install -y nvidia-container-toolkit

# Konfiguriraj Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker''')

    pdf.chapter('3.4 Docker', 2)
    pdf.code('''# Namesti Docker
curl -fsSL https://get.docker.com | sudo sh

# Dodaj uporabnika v skupino
sudo usermod -aG docker $USER

# Test
docker run hello-world''')

    pdf.add_page()
    pdf.chapter('3.5 Python 3.12', 2)
    pdf.code('''# Namesti Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Preveri
python3 --version''')

    pdf.chapter('3.6 Microsoft ODBC Driver', 2)
    pdf.code('''# Dodaj Microsoft repozitorij
curl https://packages.microsoft.com/keys/microsoft.asc | \\
  sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

# Namesti driver
sudo ACCEPT_EULA=Y apt install -y msodbcsql18 mssql-tools18 unixodbc-dev''')

    pdf.chapter('3.7 Firewall', 2)
    pdf.code('''sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp''')

    # 4. Windows
    pdf.add_page()
    pdf.chapter('4. Namestitev na Windows Server')
    pdf.text('Za Windows Server sledite tem korakom:')
    pdf.bullet([
        'Namestite NVIDIA driver z nvidia.com',
        'Namestite Docker Desktop ali Docker Engine',
        'Namestite Python 3.12 z python.org',
        'ODBC driver je ze vkljucen v Windows',
        'Konfigurirajte Windows Firewall',
    ])

    # 5. Aplikacija
    pdf.add_page()
    pdf.chapter('5. Namestitev AI Agent aplikacije')

    pdf.chapter('5.1 Prenesi projekt', 2)
    pdf.code('''cd /opt
sudo mkdir ai-agent && sudo chown $USER:$USER ai-agent
cd ai-agent
# Kopiraj datoteke (SCP, Git, ...)''')

    pdf.chapter('5.2 Konfiguracija', 2)
    pdf.code('''cp .env.example .env
nano .env
# Nastavi: DATABASE_URL, JWT_SECRET_KEY, ...''')

    pdf.chapter('5.3 SSL certifikat', 2)
    pdf.code('''mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
  -keyout nginx/ssl/server.key \\
  -out nginx/ssl/server.crt \\
  -subj "/CN=ai-agent.luznar.local"''')

    pdf.chapter('5.4 Zagon', 2)
    pdf.code('''# Z Docker Compose
docker compose up -d

# Nalozi LLM model
docker exec ai-agent-ollama ollama pull llama3:8b''')

    # 6. SQL
    pdf.add_page()
    pdf.chapter('6. SQL Server priprava')
    pdf.text('Izvedi na SQL Server kot administrator:')
    pdf.code('''-- Ustvari login
CREATE LOGIN ai_agent_user WITH PASSWORD = 'VarnoGeslo123';

-- V LargoDb bazi
USE LargoDb;
CREATE SCHEMA ai_agent;
CREATE USER ai_agent_user FOR LOGIN ai_agent_user;

-- Dodeli pravice
GRANT SELECT ON SCHEMA::dbo TO ai_agent_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::ai_agent TO ai_agent_user;''')

    # 7. Preverjanje
    pdf.chapter('7. Preverjanje namestitve')
    pdf.code('''# Health check
curl http://localhost:8000/health

# Test prijave
curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "admin123"}' ''')

    # 8. Sistemd
    pdf.add_page()
    pdf.chapter('8. Sistemd servis (Ubuntu)')
    pdf.text('Za avtomatski zagon ob ponovnem zagonu sistema:')
    pdf.code('''# /etc/systemd/system/ai-agent.service
[Unit]
Description=AI Agent System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ai-agent
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target''')
    pdf.code('''sudo systemctl daemon-reload
sudo systemctl enable ai-agent
sudo systemctl start ai-agent''')

    # 9. Backup
    pdf.chapter('9. Varnostne kopije')
    pdf.text('Nastavite dnevno varnostno kopijo v cron:')
    pdf.code('''# Dodaj v crontab
0 2 * * * /opt/ai-agent/scripts/backup.sh''')

    # 10. Troubleshooting
    pdf.add_page()
    pdf.chapter('10. Odpravljanje tezav')

    pdf.chapter('GPU ni zaznan', 3)
    pdf.code('''nvidia-smi
# Ce ne deluje, ponovno namesti driver''')

    pdf.chapter('Docker ne vidi GPU', 3)
    pdf.code('''sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker''')

    pdf.chapter('SQL Server povezava', 3)
    pdf.code('''sqlcmd -S 192.168.1.50 -U user -P 'pass' -C -Q "SELECT 1"''')

    pdf.chapter('Ollama ne deluje', 3)
    pdf.code('''docker logs ai-agent-ollama
docker exec -it ai-agent-ollama ollama list''')

    # Shrani
    output = Path(__file__).parent / 'NAMESTITEV.pdf'
    pdf.output(str(output))
    print(f'PDF ustvarjen: {output}')


if __name__ == '__main__':
    create_pdf()
