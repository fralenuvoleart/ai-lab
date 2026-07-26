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

## Notes

- **Data**: All chats, users, and settings persist in `./data/` (excluded from rsync deploys — back up separately)
- **No GPU needed**: All inference happens on Groq/OpenRouter servers
- **Updates**: `docker compose pull && docker compose up -d`
- **SSH tunnel** is only needed for initial admin setup; after that, use the Caddy domain
