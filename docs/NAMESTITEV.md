# Navodila za namestitev AI Agent sistema

## Pregled

Ta dokument opisuje korak-po-korak namestitev AI Agent sistema na strežnik.

---

## 1. Zahteve za strojno opremo

| Komponenta | Minimalno | Priporočeno |
|------------|-----------|-------------|
| CPU | 8 jeder | 16 jeder |
| RAM | 16 GB | 32 GB |
| GPU | RTX 3060 (12GB) | RTX 5070 (12GB+) |
| Disk | 256 GB SSD | 1 TB NVMe SSD |
| Omrežje | 100 Mbps | 1 Gbps |

---

## 2. Operacijski sistem

### Opcija A: Ubuntu Server 24.04 LTS (priporočeno)

```bash
# 1. Prenesi Ubuntu Server 24.04 LTS
# https://ubuntu.com/download/server

# 2. Ustvari bootable USB (z Rufus ali balenaEtcher)

# 3. Namesti Ubuntu Server
# - Izberi "Ubuntu Server (minimized)"
# - Nastavi statičen IP
# - Omogoči OpenSSH server
# - Ustvari uporabnika (npr. "aiagent")
```

### Opcija B: Windows Server 2022

```
1. Namesti Windows Server 2022 Standard/Datacenter
2. Omogoči Remote Desktop
3. Nastavi statičen IP
4. Namesti Windows Terminal (opcijsko)
```

---

## 3. Namestitev na Ubuntu Server

### 3.1 Osnovna konfiguracija

```bash
# Prijava na strežnik
ssh aiagent@192.168.1.100

# Posodobi sistem
sudo apt update && sudo apt upgrade -y

# Namesti osnovne pakete
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    nano \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Nastavi časovni pas
sudo timedatectl set-timezone Europe/Ljubljana

# Nastavi hostname
sudo hostnamectl set-hostname ai-agent-server
```

### 3.2 NVIDIA Driver (za GPU)

```bash
# Preveri ali je GPU zaznan
lspci | grep -i nvidia

# Dodaj NVIDIA repozitorij
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update

# Namesti NVIDIA driver (preveri najnovejšo verzijo)
sudo apt install -y nvidia-driver-550

# Ponovno zaženi
sudo reboot

# Po ponovnem zagonu preveri driver
nvidia-smi
```

Pričakovan output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 550.xx       Driver Version: 550.xx       CUDA Version: 12.x     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0 Off |                  N/A |
|  0%   35C    P8    10W / 200W |      0MiB / 12288MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### 3.3 NVIDIA Container Toolkit (za Docker + GPU)

```bash
# Dodaj NVIDIA Container Toolkit repozitorij
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update

# Namesti toolkit
sudo apt install -y nvidia-container-toolkit

# Konfiguriraj Docker za NVIDIA
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test
sudo docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 3.4 Docker

```bash
# Namesti Docker
curl -fsSL https://get.docker.com | sudo sh

# Dodaj uporabnika v docker skupino
sudo usermod -aG docker $USER

# Odjavi se in prijavi nazaj (ali uporabi newgrp)
newgrp docker

# Preveri namestitev
docker --version
docker compose version

# Test
docker run hello-world
```

### 3.5 Python 3.12

```bash
# Dodaj deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Namesti Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Nastavi kot privzeto (opcijsko)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Preveri
python3 --version
```

### 3.6 Microsoft ODBC Driver za SQL Server

```bash
# Dodaj Microsoft repozitorij
curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt update

# Namesti ODBC driver
sudo ACCEPT_EULA=Y apt install -y msodbcsql18

# Namesti orodja (opcijsko)
sudo ACCEPT_EULA=Y apt install -y mssql-tools18
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc

# Namesti unixODBC development pakete
sudo apt install -y unixodbc-dev

# Test povezave (zamenjaj s pravimi podatki)
sqlcmd -S 192.168.1.50 -U ai_agent_user -P 'geslo' -Q "SELECT @@VERSION"
```

### 3.7 Firewall

```bash
# Omogoči UFW
sudo ufw enable

# Dovoli SSH
sudo ufw allow ssh

# Dovoli HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Dovoli API port (za razvoj)
sudo ufw allow 8000/tcp

# Preveri status
sudo ufw status
```

---

## 4. Namestitev na Windows Server

### 4.1 NVIDIA Driver

```powershell
# 1. Prenesi driver z nvidia.com
# https://www.nvidia.com/Download/index.aspx
# Izberi: GeForce/RTX 50 Series / Windows Server 2022

# 2. Namesti driver (dvojni klik na .exe)

# 3. Preveri namestitev
nvidia-smi
```

### 4.2 Docker Desktop ali Docker Engine

**Opcija A: Docker Desktop (lažje)**

1. Prenesi Docker Desktop: https://www.docker.com/products/docker-desktop
2. Namesti in omogoči WSL 2 backend
3. V nastavitvah omogoči "Use the WSL 2 based engine"

**Opcija B: Docker Engine (brez GUI)**

```powershell
# Namesti Windows Containers feature
Install-WindowsFeature -Name Containers

# Prenesi in namesti Docker
Invoke-WebRequest -Uri https://download.docker.com/win/static/stable/x86_64/docker-24.0.7.zip -OutFile docker.zip
Expand-Archive docker.zip -DestinationPath $Env:ProgramFiles

# Dodaj v PATH
$env:Path += ";$Env:ProgramFiles\docker"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::Machine)

# Registriraj kot servis
dockerd --register-service
Start-Service docker
```

### 4.3 Python 3.12

```powershell
# 1. Prenesi Python 3.12 z python.org
# https://www.python.org/downloads/

# 2. Namesti z opcijami:
#    - "Add Python to PATH" ✓
#    - "Install for all users" ✓

# 3. Preveri
python --version
pip --version
```

### 4.4 Microsoft ODBC Driver

```powershell
# Že nameščen na Windows Server, samo preveri verzijo
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}

# Če ni nameščen, prenesi z:
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### 4.5 Git

```powershell
# Prenesi in namesti Git
winget install Git.Git

# Ali ročno z: https://git-scm.com/download/win
```

### 4.6 Firewall

```powershell
# Odpri port 8000 (API)
New-NetFirewallRule -DisplayName "AI Agent API" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow

# Odpri port 443 (HTTPS)
New-NetFirewallRule -DisplayName "AI Agent HTTPS" -Direction Inbound -Port 443 -Protocol TCP -Action Allow

# Odpri port 80 (HTTP redirect)
New-NetFirewallRule -DisplayName "AI Agent HTTP" -Direction Inbound -Port 80 -Protocol TCP -Action Allow
```

---

## 5. Namestitev AI Agent aplikacije

### 5.1 Prenesi projekt

```bash
# Ubuntu
cd /opt
sudo mkdir ai-agent
sudo chown $USER:$USER ai-agent
cd ai-agent

# Kopiraj datoteke (SCP, SFTP, ali Git)
# Opcija 1: SCP
scp -r /lokalna/pot/AI-AGENT/* aiagent@192.168.1.100:/opt/ai-agent/

# Opcija 2: Git (če je v repozitoriju)
git clone https://github.com/luznar/ai-agent.git .
```

```powershell
# Windows
cd C:\
mkdir AI-Agent
cd AI-Agent

# Kopiraj datoteke
# Ali uporabi Git
git clone https://github.com/luznar/ai-agent.git .
```

### 5.2 Konfiguracija

```bash
# Kopiraj vzorec konfiguracije
cp .env.example .env

# Uredi konfiguracijo
nano .env
```

**.env vsebina:**

```bash
# Aplikacija
APP_ENV=production
DEBUG=false

# Baza podatkov (prilagodi!)
DATABASE_URL=mssql+pyodbc://ai_agent_user:VarnoGeslo123@192.168.1.50:1433/LargoDb?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes

# JWT (generiraj novo!)
# python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=tukaj-vnesi-generirani-kljuc-32-znakov-ali-vec

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# OpenAI (opcijsko)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Microsoft Graph (opcijsko - za email)
MS_GRAPH_CLIENT_ID=
MS_GRAPH_CLIENT_SECRET=
MS_GRAPH_TENANT_ID=
MS_GRAPH_MAILBOX=info@luznar.si

# CalcuQuote (opcijsko)
CALCUQUOTE_API_KEY=
CALCUQUOTE_URL=https://api.calcuquote.com/v1

# Šifriranje (generiraj!)
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=

# CORS
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:8000
```

### 5.3 SSL certifikat (za HTTPS)

```bash
# Ustvari self-signed certifikat (za interno uporabo)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/server.key \
    -out nginx/ssl/server.crt \
    -subj "/C=SI/ST=Slovenia/L=Ljubljana/O=Luznar Electronics/CN=ai-agent.luznar.local"

# Nastavi pravice
chmod 600 nginx/ssl/server.key
```

### 5.4 Zaženi z Docker Compose

```bash
# Zgradi in zaženi
docker compose up -d

# Preveri status
docker compose ps

# Poglej loge
docker compose logs -f

# Počakaj da se Ollama zažene, nato naloži model
docker exec ai-agent-ollama ollama pull llama3:8b
```

### 5.5 Zaženi brez Dockerja (alternativa)

```bash
# Ustvari virtualno okolje
cd /opt/ai-agent/backend
python3 -m venv venv
source venv/bin/activate

# Namesti odvisnosti
pip install -r requirements.txt

# Zaženi Ollama (v drugem terminalu)
ollama serve &
ollama pull llama3:8b

# Zaženi API
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. SQL Server priprava

Izvedi na SQL Server kot administrator:

```sql
-- 1. Ustvari login
CREATE LOGIN ai_agent_user WITH PASSWORD = 'VarnoGeslo123';

-- 2. V LargoDb bazi
USE LargoDb;

-- 3. Ustvari shemo
CREATE SCHEMA ai_agent;
GO

-- 4. Ustvari uporabnika
CREATE USER ai_agent_user FOR LOGIN ai_agent_user;

-- 5. Dodeli pravice
-- Branje iz Largo tabel
GRANT SELECT ON SCHEMA::dbo TO ai_agent_user;

-- Polne pravice na ai_agent shemi
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE TABLE ON SCHEMA::ai_agent TO ai_agent_user;
ALTER AUTHORIZATION ON SCHEMA::ai_agent TO ai_agent_user;

-- 6. Poženi schema.sql za ustvarjanje tabel
-- (kopiraj vsebino database/schema.sql in poženi)
```

---

## 7. Preverjanje namestitve

### 7.1 Preveri API

```bash
# Health check
curl http://localhost:8000/health

# Pričakovan odgovor:
# {"status":"healthy","app":"AI Agent Sistem","env":"production"}
```

### 7.2 Preveri Ollama

```bash
# Seznam modelov
curl http://localhost:11434/api/tags

# Test generiranja
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Pozdravljeni!",
  "stream": false
}'
```

### 7.3 Test prijave

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Pričakovan odgovor:
# {"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer"}
```

---

## 8. Sistemd servis (Ubuntu)

Za avtomatski zagon ob ponovnem zagonu:

```bash
# Ustvari servis datoteko
sudo nano /etc/systemd/system/ai-agent.service
```

Vsebina:

```ini
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
User=aiagent
Group=docker

[Install]
WantedBy=multi-user.target
```

```bash
# Omogoči servis
sudo systemctl daemon-reload
sudo systemctl enable ai-agent
sudo systemctl start ai-agent

# Preveri status
sudo systemctl status ai-agent
```

---

## 9. Varnostne kopije

### 9.1 Ustvari backup skripto

```bash
sudo nano /opt/ai-agent/scripts/backup.sh
```

```bash
#!/bin/bash

# Konfiguracija
BACKUP_DIR="/backup/ai-agent"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Ustvari direktorij
mkdir -p $BACKUP_DIR

# Backup SQL Server (preko sqlcmd)
/opt/mssql-tools18/bin/sqlcmd -S 192.168.1.50 -U backup_user -P 'backup_geslo' -C -Q "
BACKUP DATABASE LargoDb
TO DISK = '/tmp/ai_agent_backup.bak'
WITH FORMAT, COMPRESSION;
"
mv /tmp/ai_agent_backup.bak "$BACKUP_DIR/db_$DATE.bak"

# Backup dokumentov
tar -czf "$BACKUP_DIR/documents_$DATE.tar.gz" /opt/ai-agent/data/documents

# Backup konfiguracije
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /opt/ai-agent/.env \
    /opt/ai-agent/nginx/ \
    /opt/ai-agent/docker-compose.yml

# Počisti stare backupe
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

```bash
# Naredi izvršljivo
sudo chmod +x /opt/ai-agent/scripts/backup.sh

# Dodaj v cron (vsak dan ob 2:00)
sudo crontab -e
# Dodaj vrstico:
# 0 2 * * * /opt/ai-agent/scripts/backup.sh >> /var/log/ai-agent-backup.log 2>&1
```

---

## 10. Odpravljanje težav

### GPU ni zaznan

```bash
# Preveri ali je driver nameščen
nvidia-smi

# Če ni, ponovno namesti driver
sudo apt remove --purge nvidia-*
sudo apt autoremove
sudo reboot
# Potem ponovno namesti driver
```

### Docker ne vidi GPU

```bash
# Preveri NVIDIA Container Toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Ne morem se povezati na SQL Server

```bash
# Test povezave
sqlcmd -S 192.168.1.50 -U ai_agent_user -P 'geslo' -C -Q "SELECT 1"

# Preveri firewall na SQL strežniku (port 1433)
# Preveri da je TCP/IP omogočen v SQL Server Configuration Manager
```

### Ollama ne deluje

```bash
# Preveri loge
docker logs ai-agent-ollama

# Ročno zaženi
docker exec -it ai-agent-ollama ollama list
docker exec -it ai-agent-ollama ollama pull llama3:8b
```

### API vrača napake

```bash
# Preveri loge
docker logs ai-agent-backend

# Ali brez Dockerja
cd /opt/ai-agent/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 11. Kontakti in podpora

- **Dokumentacija:** `docs/plans/2026-02-03-ai-agent-design.md`
- **API dokumentacija:** http://localhost:8000/docs (Swagger UI)

---

*Zadnja posodobitev: Februar 2026*
