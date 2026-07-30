# Active Context

## Current Focus

AI-LAB deployed on Hetzner VPS with shared infrastructure running (Caddy, PostgreSQL/pgvector, Qdrant). Ready for experiment development.

## Recent Changes

- **2026-07-26**: Workspace initialized from scratch:
  - Created full directory structure (`infra/`, `projects/`, `shared/`, `scripts/`)
  - Configured VS Code workspace (settings, extensions, custom Roo Code modes)
  - Set up shared infrastructure docker-compose (Caddy + PostgreSQL + Qdrant)
  - Scaffolded experiment templates (`_template/`, `openclaw-agent/`, `multi-agent-crew/`)
  - Added DevOps scripts (`deploy.sh`, `backup-db.sh`) and `Makefile`
  - Documented workspace structure in `docs/WORKSPACE-STRUCTURE.md`
- **2026-07-26**: Open WebUI scaffolded under `projects/open-webui/`:
  - docker-compose.yml binds to 127.0.0.1:3000 (SSH tunnel for admin setup)
  - Caddy route added (commented, uncomment with domain)
  - deploy.sh updated to exclude `projects/*/data/`
- **2026-07-26**: Hetzner server fully deployed:
  - Server: **AI-LAB** — `167.233.42.140` (CX23, 2 vCPU, 4 GB RAM, 40 GB, Ubuntu 26.04, Nuremberg)
  - Docker 29.6.2 installed with compose plugin
  - Workspace rsync'd to `/opt/ai-lab`
  - All infra containers running: Caddy (:80/:443), PostgreSQL (:5432, healthy)
  - SSH key `~/.ssh/id_ed25519` active for root access
  - HCLOUD_TOKEN stored in `.env`
- **2026-07-27**: Fixed Open WebUI Ollama connection:
  - Added `extra_hosts: host.docker.internal:host-gateway` to docker-compose (Linux doesn't resolve this DNS name by default)
  - Added commented-out Ollama container service as alternative to host-installed Ollama
  - Added `WHISPER_LANG=en` env var to force English STT (Whisper base model misdetected as Spanish)
- **2026-07-27**: Open WebUI updated to v0.11.0 — pulled latest `ghcr.io/open-webui/open-webui:main` (digest `6a773e5`) and recreated container on Hetzner
- **2026-07-27**: OpenSERP web search deployed — `karust/openserp:latest` container added to docker-compose, `OPENSERP_BASE_URL` env var configured. DuckDuckGo works; Google may CAPTCHA-block datacenter IPs. 6 engines available, no API keys needed.
- **2026-07-28**: Basic Memory MCP server deployed for Open WebUI:
  - Installed `basic-memory` v0.22.1 via pipx (Python 3.14.4)
  - Architecture: Open WebUI → MCP Streamable HTTP → basic-memory (direct, no adapters)
  - Vault directory: `/data/vault/` (Personal/ + Projects/ subdirectories)
  - Runs as `basic-memory.service` (systemd), MCP on port `8000`
  - Built-in semantic search: fastembed + bge-small-en-v1.5, SQLite backend
  - 23 MCP tools: write_note, search_notes, build_context, edit_note, delete_note, read_note, list_directory, move_note, etc.
  - Open WebUI config: Admin → External Tools → MCP (Streamable HTTP) → `http://host.docker.internal:8000/mcp`
  - 157 MB RAM usage, auto-restarts on failure
- **2026-07-28/29**: Major infrastructure expansion:
  - **Telegram bot** deployed (`telegram-bot.service`) — bridges Telegram ↔ Open WebUI via API
  - **Pipe agent** (`telegram_agent_pipe`) — async Open WebUI Pipe that auto-discovers tools from mcpo endpoints and handles tool execution loop server-side. Enables tool use via API/Telegram.
  - **GitHub MCP** installed (Node.js + `@modelcontextprotocol/server-github`) — 7 tools via mcpo on port 8001/github
  - **Fetch MCP** installed (`mcp-server-fetch`) — 1 tool via mcpo on port 8001/fetch
  - **SearXNG** deployed (Docker + Redis, port 8888) — self-hosted metasearch with 13 free engines (duckduckgo, brave, qwant, startpage, mojeek, yahoo, bing_news, google_news, wikidata, presearch, mwmbl, tusksearch, wiby)
  - **SearXNG MCP** — custom Python MCP server wrapping SearXNG JSON API, exposed via mcpo, auto-discovered by Pipe
  - **Qdrant removed** — redundant
  - **API key** enabled via `USER_PERMISSIONS_FEATURES_API_KEYS=true`
  - **Full backup script** (`scripts/backup-full.sh`) — tars vault, webui.db, configs
  - **STACK.md** and **SEARXNG.md** docs updated
  - Architecture: Telegram → bot → Pipe → model + tools (memory, github, fetch, searxng). Web UI uses native tool handling. Two independent paths.
  - RAM: 2.4GB used, 1.4GB free. 13 engines active.
- **2026-07-30**: Config consolidation and fixes:
  - Data consolidated: `projects/open-webui/data/` → `/opt/ai-lab/data/open-webui/`
  - Config convention: `config/` and `secrets/` grouped by service (basic-memory, mcp-tools, ollama, open-webui, searxng, telegram-bot)
  - Pipe agent XML parsing: 3 regex patterns handle all model output formats (nested, self-closing, bare opening)
  - Tool parameter schemas resolved via `$ref` in OpenAPI specs — no hardcoded params needed
  - Bot timeout increased 30s → 120s for multi-tool execution
  - Memory index rebuilt after workspace migration caused empty DB
- **2026-07-30**: Workspace config migration complete:
  - All server configs migrated to `config/` in git repo (SearXNG, systemd, basic-memory, ollama)
  - Real secrets encrypted with git-crypt in `secrets/` (GPG key: 91EA0175D20A372B)
  - Vault moved from `/data/vault/` → `/opt/ai-lab/data/vault/` (tracked in git)
  - Knowledge assets backed up: `webui.db` (9.4MB) + `uploads/` (~150 .md, 3.2MB)
  - Deploy scripts updated: `deploy.sh` pulls data from server (backup), pushes code (deploy)
  - `deploy-config.sh` created for secrets + systemd unit deployment
  - Old vault `/data/vault/` removed, npm cache cleaned
  - All 5 services healthy after migration, zero regressions
- **2026-07-30**: RSS Reader MCP installed:
  - `rss-reader-mcp` v1.0.8 npm package added to mcpo on port 8001
  - 2 tools exposed: `fetch_feed_entries` (RSS/Atom parsing) + `fetch_article_content` (full article → Markdown)
  - Added as 4th MCP server in `/root/.mcpo-tools.json` alongside fetch, github, searxng
  - Endpoint: `http://host.docker.internal:8001/rss-reader`
  - Verified: Hacker News feed returns live articles
