# AI Lab Stack Reference

> Hetzner CX23 — 2 vCPU, 4 GB RAM, 40 GB SSD — Ubuntu 26.04 — Nuremberg

## Infrastructure (Docker)

| Service | Image | Port | RAM | Purpose |
|---------|-------|------|-----|---------|
| Caddy | `caddy:2-alpine` | 80, 443 | ~18 MB | Reverse proxy + auto-SSL |
| PostgreSQL | `pgvector/pgvector:pg17` | 5432 | ~24 MB | Shared DB (idle, future RAG) |
| Open WebUI | `ghcr.io/open-webui/open-webui:main` | 3000→8080 | ~890 MB | Chat interface |

## MCP Servers (systemd)

| Service | Command | Port | Tools | Purpose |
|---------|---------|------|-------|---------|
| `basic-memory` | `mcpo → basic-memory mcp` | 8000 | 10 | Persistent memory (`.md` files in `/data/vault/`) |
| `mcp-tools` | `mcpo → fetch + github` | 8001 | 8 | Web fetch + GitHub API |

## Open WebUI Tool Servers

| Tool | URL | Tools | Filter List |
|------|-----|-------|-------------|
| Basic Memory | `http://host.docker.internal:8000` | 10 | `tool_write_note_post, tool_read_note_post, tool_edit_note_post, tool_delete_note_post, tool_search_notes_post, tool_build_context_post, tool_list_directory_post, tool_read_content_post, tool_recent_activity_post, tool_list_memory_projects_post` |
| GitHub | `http://host.docker.internal:8001/github` | 7 | `tool_search_repositories_post, tool_get_file_contents_post, tool_create_or_update_file_post, tool_search_code_post, tool_list_commits_post, tool_list_issues_post, tool_get_issue_post` |
| Fetch | `http://host.docker.internal:8001/fetch` | 1 | `tool_fetch_post` |

## Models

| Provider | Model | Type |
|----------|-------|------|
| OpenRouter | DeepSeek V4 Pro | Primary (chat + tools) |
| OpenRouter | Google Gemini Pro Latest | Secondary |
| Ollama (host) | Various | Local, on-demand |

## Disk Layout

```
/data/vault/          — Basic Memory vault (Personal/ + Projects/)
/opt/ai-lab/          — Workspace (rsync'd from dev machine)
/opt/repos/           — Reserved for git clones (unused)
/root/.basic-memory/  — basic-memory config + SQLite DB
/root/.mcpo-tools.json — mcpo multi-server config
```

## Services

```bash
systemctl status basic-memory   # Memory MCP (mcpo on :8000)
systemctl status mcp-tools      # Fetch + GitHub MCP (mcpo on :8001)
```

## Key Decisions

- **Qdrant removed** — redundant with basic-memory's built-in semantic search
- **PostgreSQL kept idle** — 24 MB, available for future RAG projects
- **GitHub MCP over git MCP** — works via API, no local clones needed
- **mcpo/OpenAPI over native MCP** — avoids DeepSeek's DSML function calling bug
- **Tool lists trimmed** — 18 total tools avoid model context limits
- **Memory toggle OFF per-model** — prevents conflict with Open WebUI's built-in memory
