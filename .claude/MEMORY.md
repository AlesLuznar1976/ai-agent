# AI-AGENT Project - AI Server (192.168.0.66)

## Overview
- Manufacturing ERP AI Agent for LUZNAR d.o.o. (PCB/SMT, Kranj, Slovenia)
- ERP: LARGO (MSSQL on 192.168.0.191:11433)
- Stack: Flutter web + FastAPI backend + Ollama (llama3.1:8b) + Docker

## Architecture
- Backend: FastAPI in Docker (port 8000)
- Ollama: Docker with RTX 5080 GPU (port 11434, llama3.1:8b for tool use)
- Web: Flutter app served via nginx (port 9090)
- DB: MSSQL LUZNAR database (UID=Alesl, PWD=homeland)

## Key Directories
- ~/ai-agent/backend/app/agents/ - AI agent (orchestrator, erp_tools, tool_executor, claude_scriptwriter)
- ~/ai-agent/backend/app/api/ - FastAPI endpoints (auth, chat, projekti, emaili)
- ~/ai-agent/flutter_app/lib/ - Flutter source (screens, services, config)
- ~/ai-agent/flutter_app/web/ - Built Flutter web app (served by nginx)
- ~/ai-agent/docker-compose.yml - 3 services: backend, ollama, web

## Docker Commands
- docker compose up -d                    # Start all
- docker compose build backend && docker compose up -d backend  # Rebuild backend
- docker compose logs -f backend          # Backend logs
- docker compose restart backend          # Quick restart

## Database
- ai_agent schema: Projekti, Uporabniki, DelovniNalogi, Emaili, CakajočeAkcije, etc.
- dbo schema: LARGO ERP (Partnerji, Narocilo, Ponudba, Dobavnica, Kalkulacija, etc.)
- Admin login: admin / admin123

## ERP Tools (16 read + 5 write + 1 escalation)
- Read: search_partners, get_partner_details, list_projects, search_orders, search_quotes, get_emails, count_records, etc.
- Write (need confirmation): create_project, update_project, create_work_order, assign_email_to_project, etc.
- Escalation: ask_claude_for_script (Claude API writes SQL/Python when agent cant solve)

## Brand
- Colors: Navy #1A2744, Gold #B8963E
- Logo: Diamond/rhombus shape (CustomPainter in brand_theme.dart)
- Company: Luznar Electronics d.o.o., Hrastje 52g, SI-4000 Kranj

## Known Issues
- llama3.1:8b is small - occasional wrong tool arguments
- Flutter web needs rebuild + scp to flutter_app/web/ after changes
- .env not in git (contains secrets)
