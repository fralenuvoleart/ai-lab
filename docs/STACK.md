# AI Lab Stack Reference

> Hetzner CX23 — 2 vCPU, 4 GB RAM, 40 GB SSD — Ubuntu 26.04 — Nuremberg

## Infrastructure (Docker)

| Service | Image | Port | RAM | Purpose |
|---------|-------|------|-----|---------|
| Caddy | `caddy:2-alpine` | 80, 443 | ~16 MB | Reverse proxy + auto-SSL |
| PostgreSQL | `pgvector/pgvector:pg17` | 5432 | ~24 MB | Shared DB (idle, future RAG) |
| Open WebUI | `ghcr.io/open-webui/open-webui:main` | 3000→8080 | ~670 MB | Chat interface |
| SearXNG | `searxng/searxng:latest` | 8888 | ~108 MB | Self-hosted metasearch |
| SearXNG Redis | `redis:7-alpine` | — | ~4 MB | Caching/rate limiting |

## Systemd Services

| Service | Command | Port | Purpose |
|---------|---------|------|---------|
| `basic-memory` | `mcpo → basic-memory mcp` | 8000 | Persistent memory (`.md` in `/data/vault/`) |
| `mcp-tools` | `mcpo → fetch + github + searxng` | 8001 | Web fetch + GitHub + SearXNG |
| `telegram-bot` | Python → Open WebUI API | — | Telegram ↔ AI chat bridge |

## Open WebUI Tool Servers

| Tool | URL | Active Functions |
|------|-----|-----------------|
| Basic Memory | `http://host.docker.internal:8000` | 10 (write_note, search_notes, edit_note, delete_note, build_context, list_directory, read_content, recent_activity, list_memory_projects, read_note) |
| GitHub | `http://host.docker.internal:8001/github` | 7 (search_repositories, get_file_contents, create_or_update_file, search_code, list_commits, list_issues, get_issue) |
| Fetch | `http://host.docker.internal:8001/fetch` | 1 (fetch) |
| SearXNG | `http://host.docker.internal:8001/searxng` | 1 (search_web) |

## Open WebUI Functions

| Function | Type | Purpose |
|----------|------|---------|
| Telegram Agent Pipe | Pipe (model: `telegram_agent_pipe`) | Server-side tool execution loop for API/Telegram. Auto-discovers tools from mcpo endpoints. Async, non-blocking. |

## Models

| Provider | Model | Type |
|----------|-------|------|
| OpenRouter | DeepSeek V4 Pro | Primary (chat + tools) |
| OpenRouter | Google Gemini Pro Latest | Secondary |
| Ollama (host) | Various | Local, on-demand |

## Telegram Bot

- **Systemd:** `telegram-bot.service`
- **Model:** `telegram_agent_pipe` (calls Pipe for tool execution)
- **Tool IDs:** Hardcoded in bot (18 tools across memory/github/fetch/searxng)
- **Prompt:** Inherited from `telegram-chat` model via API

## SearXNG — 13 Active Engines

duckduckgo, brave, qwant, startpage, mojeek, yahoo, bing news, google news, wikidata, presearch, mwmbl, tusksearch, wiby

Full list: [`docs/SEARXNG.md`](SEARXNG.md)

## Disk Layout

```
/data/vault/          — Basic Memory vault (Personal/ + Projects/)
/opt/ai-lab/          — Workspace (rsync'd from dev machine)
/opt/searxng/         — SearXNG docker-compose + config
/opt/repos/           — Reserved for git clones
/root/.basic-memory/  — basic-memory config + SQLite DB
/root/.mcpo-tools.json — mcpo multi-server config (fetch + github + searxng)
```

## Service Management

```bash
# Docker
docker ps
cd /opt/searxng && docker compose restart

# Systemd
systemctl status basic-memory mcp-tools telegram-bot
journalctl -u telegram-bot -f

# Backups
/opt/ai-lab/scripts/backup-full.sh
```

## Key Decisions

- **Qdrant removed** — redundant with basic-memory's semantic search
- **PostgreSQL kept idle** — 24 MB, available for future RAG
- **GitHub MCP over git MCP** — works via API, no local clones
- **mcpo/OpenAPI over native MCP** — avoids DeepSeek's DSML bug
- **Pipe for API tool execution** — Open WebUI API doesn't handle tools natively
- **SearXNG with Redis** — rate limiting for upstream engines
- **13 engines, no API keys** — free metasearch, datacenter IP limits some engines
- **Telegram bot calls Pipe** — 30-line bot, all logic in Pipe
- **Memory toggle OFF per-model** — prevents conflict with Open WebUI built-in memory
- **Tool lists trimmed** — avoids model context limits
