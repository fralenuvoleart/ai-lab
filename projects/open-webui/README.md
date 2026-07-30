# Open WebUI — Self-hosted AI Chat Interface 

Open WebUI is a ChatGPT-like interface that connects to any OpenAI-compatible API (Groq, OpenRouter, local Ollama, etc.). No GPU required — it's purely a web proxy to external LLM providers.

## Quick Start

```bash
# 1. Configure
cp .env.example .env
# Generate a secret key:
openssl rand -hex 32  # paste into WEBUI_SECRET_KEY in .env

# 2. Launch
docker compose up -d

# 3. Access via SSH tunnel (local only)
ssh -L 3000:localhost:3000 hetzner-ailab
# Open http://localhost:3000 in your browser
```

## Admin Setup (First Run)

1. Start the container and access via SSH tunnel (see above)
2. Register your account — the **first user becomes Super Admin**
3. Go to Admin Panel → Settings → General → set `ENABLE_SIGNUP=false` in `.env`
4. Restart: `docker compose up -d`

## API Provider Setup

After admin login, go to **Admin Panel → Settings → Connections**:

| Provider | API URL | Key Field |
|---|---|---|
| Groq | `https://api.groq.com/openai/v1` | OpenAI API Key |
| OpenRouter | `https://openrouter.ai/api/v1` | OpenAI API Key |

Click **Verify** after adding each. Models appear in the top dropdown.

## Public Access (via Caddy)

Once you have a domain pointed to the server, add to [`infra/caddy/Caddyfile`](../../infra/caddy/Caddyfile):

```caddy
ai.yourdomain.com {
    reverse_proxy ailab-open-webui:8080
}
```

Then reload Caddy: `make proxy-reload` from the workspace root.

## Memory Server (Basic Memory via MCP)

Open WebUI connects to [`basic-memory`](https://github.com/basicmachines-co/basic-memory) — a local-first knowledge engine that stores memories as `.md` files on the VPS at `/opt/ai-lab/data/vault/`. Uses Open WebUI's **native MCP (Streamable HTTP)** integration — no adapters needed.

**Status**: Running as `basic-memory.service` (systemd), MCP on port `8000`.

### Connect in Open WebUI

1. Go to **Admin Panel → Settings → External Tools** (not Tools)
2. Click **+ Add**:
   - **Type**: `MCP (Streamable HTTP)`
   - **Name**: `Basic Memory`
   - **URL**: `http://host.docker.internal:8000/mcp`
3. Tools auto-discover — `write_note`, `search_notes`, `build_context`, `edit_note`, `delete_note`, `read_note`, `list_directory`, `move_note`, and more

### Enable Per-Model

1. **Admin Panel → Settings → Models** → edit your model
2. Toggle **Memory** to **OFF** (this is Open WebUI's built-in memory — conflicts with basic-memory)
3. Under **Tools**, enable **"Basic Memory"**
4. Save — now every chat with that model uses basic-memory exclusively

### Architecture

```
Open WebUI (Docker) ──MCP Streamable HTTP──▶ basic-memory (:8000)
                                                    │
                                     /opt/ai-lab/data/vault/
                                            ├── Personal/
                                            └── Projects/
```

### System Prompt for Auto-Memory

Add to your model's system prompt (**Admin → Settings → Models → edit model**):

> **Memory**: Use `write_note` to save facts and `search_notes` to retrieve them. Do NOT use `update_memory` or `read_memory_path` — those are a different system. Store personal info under the `Personal/` folder and project notes under `Projects/`. Before answering questions about the user, always check memory first with `search_notes`.

⚠️ Open WebUI has its own built-in memory (`update_memory`/`read_memory_path`) that the model may pick instead. The explicit tool names in the prompt prevent this conflict.

### Manual Vault Access

```bash
ssh hetzner-ailab
ls /opt/ai-lab/data/vault/Personal/   # Personal memories
ls /opt/ai-lab/data/vault/Projects/   # Project-specific notes
vim /opt/ai-lab/data/vault/Personal/preferences.md  # Edit directly
```

### Service Management

```bash
systemctl status basic-memory     # Check status
systemctl restart basic-memory    # Restart after config changes
journalctl -u basic-memory -f     # Tail logs
```

## Required Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `WEBUI_SECRET_KEY` | **YES** | JWT signing secret — must be set or auth breaks |
| `OPENAI_API_KEY` | No | Default API key for OpenAI-compatible providers |
| `TAVILY_API_KEY` | No | Web search API key (if web search enabled) |
| `RAG_OPENAI_API_KEY` | No | Embeddings API key (if RAG enabled) |

Generate a secret key: `openssl rand -hex 32`

## Secrets Management

- **Never commit `.env` to git** — it is in `.gitignore`
- **Rotate API keys regularly** — especially after sharing access or suspected exposure
- **`.env` contains multiple credentials** (OpenAI, Tavily, RAG, WebUI secret) — treat it as a high-value target
- For production, consider [Docker secrets](https://docs.docker.com/compose/how-tos/use-secrets/) instead of flat `.env` files

## Notes

- **Data**: All chats, users, and settings persist in `./data/` (excluded from rsync deploys — back up separately)
- **No GPU needed**: All inference happens on Groq/OpenRouter servers
- **Updates**: `docker compose pull && docker compose up -d`
- **SSH tunnel** is only needed for initial admin setup; after that, use the Caddy domain
