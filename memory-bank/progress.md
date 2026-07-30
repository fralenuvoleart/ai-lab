# Project Progress

## Completed

- [x] **2026-07-28**: Basic Memory MCP server deployed — `basic-memory` v0.22.1 via pipx, vault at `/data/vault/`, systemd service on port 8000, SSE transport, built-in semantic search (fastembed/bge-small-en-v1.5). Open WebUI configured to connect at `http://host.docker.internal:8000/mcp`.
- [x] **2026-07-27**: OpenSERP web search deployed — `karust/openserp:latest` container, `OPENSERP_BASE_URL` configured, DuckDuckGo verified working
- [x] **2026-07-27**: Open WebUI updated to v0.11.0 — pulled `ghcr.io/open-webui/open-webui:main`, recreated container on Hetzner
- [x] **2026-07-27**: Open WebUI Ollama fix deployed — `host.docker.internal` resolution, Ollama installed on VPS, `llama3.2:1b` + `gemma2:2b` pulled
- [x] **2026-07-26**: Workspace scaffolded — directory structure, VS Code config, custom Roo modes, shared infra, experiment templates, DevOps scripts, Makefile
- [x] **2026-07-26**: Hetzner VPS fully deployed — Docker installed, workspace rsync'd, all infra containers running (Caddy, PostgreSQL, Qdrant)
- [x] **2026-07-26**: Open WebUI scaffolded — `projects/open-webui/` with docker-compose, Caddy route, deploy.sh data exclusion
- [x] **2026-07-26**: pbservices.ge scraped — 150 clean .md pages (1.5 MB) to `shared/datasets/scraped/pbservices-en/`
- [x] **2026-07-26**: Crawl4AI content cleaner finalized — excluded_tags + excluded_selector config

- [x] **2026-07-30**: Workspace config migration complete — all server configs in git repo, secrets encrypted with git-crypt, vault + knowledge assets tracked, deploy scripts updated, old vault removed, zero regressions after service restarts.
- [x] **2026-07-30**: Data consolidation — Open WebUI data moved from `projects/open-webui/data/` to `/opt/ai-lab/data/open-webui/`, backup scripts updated, 1.4GB redundant data.old removed.
- [x] **2026-07-30**: Pipe agent debugged and fixed — XML parsing handles 3 tag formats, $ref schema resolution for tool parameters, system prompt injection, bot timeout 30s→120s, memory index rebuilt.
- [x] **2026-07-30**: Config naming conventions unified — `config/` and `secrets/` both grouped by service folder (basic-memory, mcp-tools, ollama, open-webui, searxng, telegram-bot). `config/systemd/` and `config/mcpo/` eliminated. Migration audit passed with 0 stale references.

## In Progress

_None_


## Upcoming

- First experiment development
- Custom MCP server development
