# Workspace Config & Data Migration Plan

> **Goal**: Move all server configuration files, secrets (encrypted), the basic-memory vault, and critical knowledge assets into the workspace repository for version control, audit trail, backup, and local editability — with zero downtime.

---

## 1. Current State Inventory

### 1.1 Config files outside workspace (server-only)

| File | Server Path | Content | Has Secrets? |
|---|---|---|---|
| `docker-compose.yml` | `/opt/searxng/` | SearXNG + Redis containers | No |
| `settings.yml` | `/opt/searxng/` | 27 engines, keep_only, categories | No |
| `limiter.toml` | `/opt/searxng/` | Bot detection header check | No |
| `mcp_server.py` | `/opt/searxng/` | SearXNG MCP stdin/stdout wrapper | No |
| `mcpo-tools.json` | `/root/` | Fetch + GitHub + SearXNG MCP config | **Yes** — `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `basic-memory.service` | `/etc/systemd/system/` | systemd unit for memory MCP (port 8000) | No |
| `mcp-tools.service` | `/etc/systemd/system/` | systemd unit for mcpo (port 8001) | **Yes** — `GITHUB_PERSONAL_ACCESS_TOKEN` in env |
| `telegram-bot.service` | `/etc/systemd/system/` | systemd unit for Telegram bridge | **Yes** — `TELEGRAM_BOT_TOKEN` + `OWUI_API_KEY` |
| `ollama.service` | `/etc/systemd/system/` | systemd unit for Ollama LLM server | No |
| `.env` (open-webui) | `/opt/ai-lab/projects/open-webui/` | Open WebUI environment | **Yes** — `WEBUI_SECRET_KEY`, API keys |
| `config.json` (basic-memory) | `/root/.basic-memory/` | Vault path, embedding model, search params | Minor — `cloud_client_id` (public identifier) |
| `.bmignore` (basic-memory) | `/root/.basic-memory/` | Gitignore-style patterns for vault sync | No |

### 1.2 Knowledge assets (data worth preserving)

| Data | Server Path | Size | Content | Priority |
|---|---|---|---|---|
| basic-memory vault | `/data/vault/` | 28 KB | 3 `.md` files: `Faith.md`, `News Coverage Preferences.md`, `User Profile.md` | 🔴 Source of truth |
| Open WebUI database | `/opt/ai-lab/projects/open-webui/data/webui.db` | 9.4 MB | 78 chats, 281 messages, 2 knowledge bases (PBS), 393 config entries | 🔴 Irreplaceable |
| Knowledge base uploads | `/opt/ai-lab/projects/open-webui/data/uploads/` | 3.2 MB | ~150 scraped `.md` files — Georgia business, visas, universities, real estate | 🔴 Raw source for RAG KBs |
| Vector embeddings | `/opt/ai-lab/projects/open-webui/data/vector_db/` | 333 MB | 299 embedding directories | ⚫ Excluded — regeneratable from uploads |
| Ollama models | Ollama data dir | ~3 GB | `gemma2:2b` (1.6 GB), `llama3.2:1b` (1.3 GB) | ⚫ Excluded — binary, documented via manifest |

### 1.3 Already in workspace (reference)

| File | Workspace Path | Server Path |
|---|---|---|
| Infrastructure compose | `infra/docker-compose.infra.yml` | `/opt/ai-lab/infra/` |
| Caddy config | `infra/caddy/Caddyfile` | `/opt/ai-lab/infra/caddy/` |
| Open WebUI compose | `projects/open-webui/docker-compose.yml` | `/opt/ai-lab/projects/open-webui/` |
| Open WebUI env template | `projects/open-webui/.env.example` | (template only) |
| Telegram bot code | `projects/telegram-bot/bot.py` | `/opt/ai-lab/projects/telegram-bot/` |
| Pipe agent code | `projects/telegram-bot/pipe-agent.py` | (manually copied to Open WebUI) |
| SearXNG MCP code | `projects/telegram-bot/searxng-mcp.py` | (development copy) |
| Deploy script | `scripts/deploy.sh` | `/opt/ai-lab/scripts/` |
| Backup scripts | `scripts/backup-*.sh` | `/opt/ai-lab/scripts/` |

### 1.4 Active services (server)

| Service | Type | Runs | Restart method |
|---|---|---|---|
| `basic-memory` | systemd | mcpo port 8000 → basic-memory MCP | `systemctl restart basic-memory` |
| `mcp-tools` | systemd | mcpo port 8001 → fetch + github + searxng | `systemctl restart mcp-tools` |
| `telegram-bot` | systemd | Python bot.py (polling) | `systemctl restart telegram-bot` |
| `ollama` | systemd | Ollama LLM serve (gemma2:2b, llama3.2:1b) | `systemctl restart ollama` |
| `searxng` | Docker | SearXNG container | `docker compose restart` |
| `searxng-redis` | Docker | Redis for SearXNG | `docker compose restart` |
| `ailab-open-webui` | Docker | Open WebUI container | `docker compose restart` |
| `ailab-caddy` | Docker | Reverse proxy | `docker compose restart` |
| `ailab-postgres` | Docker | PostgreSQL/pgvector | `docker compose restart` |

---

## 2. Target Workspace Structure

```
AI-LAB/
├── secrets/                              # NEW: git-crypt encrypted — REAL tokens
│   ├── .gitattributes                     # * filter=git-crypt diff=git-crypt (with !filter !diff for .gitattributes itself)
│   ├── mcpo-tools.json                   # real GITHUB_PAT
│   ├── mcp-tools.service                 # real GITHUB_PAT in Environment=
│   ├── telegram-bot.service              # real TELEGRAM_BOT_TOKEN + OWUI_API_KEY
│   ├── open-webui.env                    # real WEBUI_SECRET_KEY + API keys
│   └── basic-memory-config.json          # real cloud_client_id
├── config/                               # NEW: UNencrypted configs + .example templates
│   ├── README.md                         # How to deploy configs
│   ├── searxng/
│   │   ├── docker-compose.yml            # from /opt/searxng/ — tracked (no secrets)
│   │   ├── settings.yml                  # from /opt/searxng/ — tracked (no secrets)
│   │   ├── limiter.toml                  # from /opt/searxng/ — tracked (no secrets)
│   │   └── mcp_server.py                 # from /opt/searxng/ — tracked (no secrets)
│   ├── mcpo/
│   │   └── mcpo-tools.json.example       # template: YOUR_GITHUB_PAT placeholder
│   ├── systemd/
│   │   ├── basic-memory.service          # from /etc/systemd/system/ — tracked (no secrets)
│   │   ├── ollama.service                # from /etc/systemd/system/ — tracked (no secrets)
│   │   ├── mcp-tools.service.example     # template: YOUR_GITHUB_PAT placeholder
│   │   └── telegram-bot.service.example  # template: YOUR_TELEGRAM_BOT_TOKEN placeholder
│   ├── basic-memory/
│   │   ├── config.json.example           # template: YOUR_CLOUD_CLIENT_ID placeholder
│   │   └── .bmignore                     # from /root/.basic-memory/ — tracked (no secrets)
│   ├── ollama/
│   │   └── models.txt                    # manifest: gemma2:2b, llama3.2:1b
│   └── open-webui/
│       └── .env.example                  # template: placeholder values
├── data/
│   └── vault/                            # NEW: basic-memory vault (tracked in git)
│       ├── Personal/                     # Faith.md, News Coverage Preferences.md, User Profile.md
│       └── Projects/                     # (empty, ready for project notes)
├── docs/
├── infra/
├── memory-bank/
├── plans/
├── projects/
│   └── open-webui/
│       └── data/                         # already in workspace, tracked assets:
│           ├── webui.db                  # chat history + KBs + configs (9.4 MB)
│           └── uploads/                  # ~150 RAG source .md files (3.2 MB)
├── scripts/
│   ├── deploy.sh                         # UPDATED: pull-only data, push-only configs
│   ├── deploy-config.sh                  # NEW: copies from secrets/ + config/ to server
│   └── ...
└── shared/
```

---

## 3. Secrets Strategy: git-crypt

### 3.1 Principle

**Real secrets are stored in the repo, encrypted with `git-crypt`.** On your local machine, files in `secrets/` are plaintext — you read and edit them normally. On the remote (and in git objects), they are AES-256-CTR encrypted binary. Anyone without your GPG key sees garbage. No `.example` templates needed for backup — the real files are there, just encrypted.

### 3.2 How git-crypt works

```
LOCAL (unlocked)              GIT OBJECTS / REMOTE
─────────────────              ────────────────────
secrets/.env                   secrets/.env
  WEBUI_SECRET_KEY=abc123...     → git push →  ��x��9�zݰ��F�_�...
  (plaintext)                                  (AES-256-CTR ciphertext)

                                ← git pull ←  (auto-decrypted on the fly)
```

- `git-crypt init` — generates a symmetric key, stores in `.git/git-crypt/keys/`
- `git-crypt add-gpg-user <keyid>` — encrypts the symmetric key with your GPG public key
- `.gitattributes` — marks which files to encrypt: `secrets/** filter=git-crypt diff=git-crypt`
- `git-crypt unlock` — on a new machine, decrypts the symmetric key using your GPG private key (one-time)
- `git-crypt lock` — removes the key locally; files become unreadable until `unlock` again

### 3.3 Secrets inventory

| Real File (encrypted) | Server Destination | Contents |
|---|---|---|
| `secrets/mcpo-tools.json` | `/root/.mcpo-tools.json` | Real `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `secrets/mcp-tools.service` | `/etc/systemd/system/mcp-tools.service` | Real `GITHUB_PERSONAL_ACCESS_TOKEN` in env |
| `secrets/telegram-bot.service` | `/etc/systemd/system/telegram-bot.service` | Real `TELEGRAM_BOT_TOKEN` + `OWUI_API_KEY` |
| `secrets/open-webui.env` | `/opt/ai-lab/projects/open-webui/.env` | Real `WEBUI_SECRET_KEY` + API keys |
| `secrets/basic-memory-config.json` | `/root/.basic-memory/config.json` | Real `cloud_client_id` |

### 3.4 Config files tracked as-is (no secrets)

| File | Reason |
|---|---|
| `config/searxng/*` | No secrets — settings, compose, limiter, mcp_server.py |
| `config/systemd/basic-memory.service` | Clean systemd unit, no tokens |
| `config/systemd/ollama.service` | Clean systemd unit, no tokens |
| `config/basic-memory/.bmignore` | Gitignore patterns only |
| `config/ollama/models.txt` | Model name manifest only |

### 3.5 `.gitignore` — only runtime/regeneratable exclusions

```gitignore
# === Runtime / regeneratable data ===
projects/open-webui/data/vector_db/       # 333 MB embeddings — regeneratable from uploads/
projects/open-webui/data/cache/           # embedding, whisper, audio caches
projects/open-webui/data/webui.db-shm     # SQLite WAL shared memory
projects/open-webui/data/webui.db-wal     # SQLite WAL journal

# === Git-crypt internal ===
.git/git-crypt/keys/default.key           # symmetric key backup (git-crypt manages this)
```

> **Tracked in git:** `secrets/` (encrypted), `config/` (plaintext templates + clean configs), `data/vault/` (memories), `projects/open-webui/data/webui.db`, `projects/open-webui/data/uploads/`.

---

## 4. Deploy & Backup: Sync Directions

### 4.1 Direction map

```
┌──────────────────────────────────────────────────┐
│                    deploy.sh                       │
│                                                    │
│  STEP 1: PULL (server → local)                    │
│  ┌──────────────────────────────────────────┐     │
│  │  data/vault/          rsync -avzu  ←──┐  │     │
│  │  webui.db             rsync -avzu  ←──┤  │     │
│  │  uploads/             rsync -avzu  ←──┤  │     │
│  └──────────────────────────────────────────┘     │
│             BACKUP DIRECTION                       │
│             Never pushed back to server            │
│                                                    │
│  STEP 2: PUSH (local → server)                    │
│  ┌──────────────────────────────────────────┐     │
│  │  config/              rsync -avz  ───→┐  │     │
│  │  scripts/             rsync -avz  ───→┤  │     │
│  │  projects/ (code)     rsync -avz  ───→┤  │     │
│  │  docs/                rsync -avz  ───→┤  │     │
│  │  memory-bank/         rsync -avz  ───→┤  │     │
│  │  --exclude data/      (never pushed)   │     │
│  │  --exclude secrets/   (never pushed)   │     │
│  └──────────────────────────────────────────┘     │
│             DEPLOY DIRECTION                       │
│             Only code + clean configs              │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│                deploy-config.sh                    │
│                                                    │
│  STEP 3: SECRETS + SYSTEMD (local → server)       │
│  ┌──────────────────────────────────────────┐     │
│  │  secrets/ → /root/, /etc/systemd/, etc.  │     │
│  │  config/systemd/ → /etc/systemd/system/  │     │
│  │  (real service files, no rsync)          │     │
│  └──────────────────────────────────────────┘     │
│             Manual or post-deploy                  │
│             Only when secrets/systemd change       │
└──────────────────────────────────────────────────┘
```

### 4.2 Overwrite safeties

| Direction | Command | Safeties |
|---|---|---|
| Server → local (pull) | `rsync -avzu` | `-u` = skip if local file is newer. Prevents server overwriting your local edits. `-z` = compress during transfer. No `--delete` — server never deletes local files. |
| Local → server (push) | `rsync -avz --delete` + `--exclude` | `--exclude=data/vault/`, `--exclude=projects/open-webui/data/`, `--exclude=secrets/` — data and secrets are NEVER pushed. `--delete` removes server files that were deleted locally (keeps workspace as source of truth for code). |
| Secrets deploy | `scp` individual files | Manual, explicit. No bulk rsync — each secret file is copied individually to its exact destination. No accidental overwrites. |

### 4.3 Why this separation matters

- **`webui.db` is server-owned**: Open WebUI writes to it constantly. If `deploy.sh` pushed it, every deploy would overwrite live chat history with a stale copy from whenever you last pulled. By excluding it from push, the server's live database is never touched by deploys.
- **`secrets/` is never pushed by rsync**: The `--exclude=secrets/` on push ensures encrypted secrets never end up on the server filesystem at `/opt/ai-lab/secrets/`. They only go to their intended destinations via `deploy-config.sh`.
- **Vault is pull-only**: AI writes to vault on the server. Your local edits (via git) get pulled into the server via the push... wait, no — vault is excluded from push. So local vault edits would need a separate mechanism. But the pull-before-push pattern ensures you always have the latest server state before making local edits. And your local vault edits get committed and pushed to git — the server doesn't need them pushed via rsync because basic-memory writes directly to `/opt/ai-lab/data/vault/`.

> **Correction**: `data/vault/` is excluded from push rsync. Vault sync is **server → local only** (backup). Local vault edits go to git for version control; the server's live vault at `/opt/ai-lab/data/vault/` is the authoritative source. If you want to push local vault edits to the server, use `git pull` on the server or a separate rsync. This avoids the race condition where basic-memory writes a note and your push overwrites it.

---

## 5. Implementation Steps

### Phase 0: Pre-Flight Verification (server, read-only)

**Step 0.1** — Verify basic-memory `--path` flag exists
```bash
ssh root@167.233.42.140 'basic-memory mcp --help | grep -i vault'
```
If the flag doesn't exist, use the symlink fallback: `ln -s /opt/ai-lab/data/vault /data/vault` (skip systemd edit in Phase 2).

**Step 0.2** — Run pre-migration smoke tests (baseline)
Run all tests from Section 6.1 and record results.

**Step 0.3** — Verify GPG key available locally
```bash
gpg --list-secret-keys  # confirm your GPG key exists
```

---

### Phase 1: Workspace Setup (local, no server impact)

**Step 1.1** — Create directory structure
```bash
mkdir -p config/{searxng,mcpo,systemd,basic-memory,ollama,open-webui}
mkdir -p data/vault/{Personal,Projects}
mkdir -p projects/open-webui/data/uploads
mkdir -p secrets
```

**Step 1.2** — Initialize git-crypt
```bash
git-crypt init
git-crypt add-gpg-user $(gpg --list-secret-keys --keyid-format LONG | grep sec | awk '{print $2}' | cut -d'/' -f2)
cat > secrets/.gitattributes << 'EOF'
* filter=git-crypt diff=git-crypt
EOF
```

**Step 1.3** — Pull clean configs from server (no secrets)
```bash
# SearXNG
scp root@167.233.42.140:/opt/searxng/docker-compose.yml config/searxng/
scp root@167.233.42.140:/opt/searxng/settings.yml config/searxng/
scp root@167.233.42.140:/opt/searxng/limiter.toml config/searxng/
scp root@167.233.42.140:/opt/searxng/mcp_server.py config/searxng/

# systemd units (clean, no secrets)
scp root@167.233.42.140:/etc/systemd/system/basic-memory.service config/systemd/
scp root@167.233.42.140:/etc/systemd/system/ollama.service config/systemd/

# basic-memory config
scp root@167.233.42.140:/root/.basic-memory/.bmignore config/basic-memory/
```

**Step 1.4** — Pull real secrets into `secrets/` (encrypted on next commit)
```bash
scp root@167.233.42.140:/root/.mcpo-tools.json secrets/
scp root@167.233.42.140:/etc/systemd/system/mcp-tools.service secrets/
scp root@167.233.42.140:/etc/systemd/system/telegram-bot.service secrets/
scp root@167.233.42.140:/opt/ai-lab/projects/open-webui/.env secrets/open-webui.env
scp root@167.233.42.140:/root/.basic-memory/config.json secrets/basic-memory-config.json
```

**Step 1.5** — Create `.example` templates (documentation, readable without GPG key)
```bash
# mcpo
sed 's/github_pat_[A-Za-z0-9]*/YOUR_GITHUB_PAT/g' secrets/mcpo-tools.json > config/mcpo/mcpo-tools.json.example

# systemd
sed 's/github_pat_[A-Za-z0-9]*/YOUR_GITHUB_PAT/g' secrets/mcp-tools.service > config/systemd/mcp-tools.service.example
sed 's/8716439271:[A-Za-z0-9_-]*/YOUR_TELEGRAM_BOT_TOKEN/g; s/sk-[A-Za-z0-9]*/YOUR_OWUI_API_KEY/g' secrets/telegram-bot.service > config/systemd/telegram-bot.service.example

# open-webui
sed 's/WEBUI_SECRET_KEY=.*/WEBUI_SECRET_KEY=YOUR_WEBUI_SECRET_KEY/' secrets/open-webui.env > config/open-webui/.env.example

# basic-memory
sed 's/client_[A-Za-z0-9]*/YOUR_CLOUD_CLIENT_ID/g' secrets/basic-memory-config.json > config/basic-memory/config.json.example
```

**Step 1.6** — Create Ollama model manifest
```bash
cat > config/ollama/models.txt << 'EOF'
gemma2:2b
llama3.2:1b
EOF
```

**Step 1.7** — Pull knowledge assets
```bash
# Vault memories
rsync -avz root@167.233.42.140:/data/vault/ data/vault/

# Open WebUI chat history & configs
scp root@167.233.42.140:/opt/ai-lab/projects/open-webui/data/webui.db projects/open-webui/data/

# Knowledge base source documents
rsync -avz root@167.233.42.140:/opt/ai-lab/projects/open-webui/data/uploads/ projects/open-webui/data/uploads/
```

**Step 1.8** — Update `.gitignore` with rules from Section 3.5

---

### Phase 2: Server Migration

**Step 2.1** — Backup originals
```bash
ssh root@167.233.42.140
cp -a /opt/searxng /opt/searxng.bak.$(date +%Y%m%d)
cp /etc/systemd/system/basic-memory.service /etc/systemd/system/basic-memory.service.bak
cp /etc/systemd/system/ollama.service /etc/systemd/system/ollama.service.bak
cp /root/.mcpo-tools.json /root/.mcpo-tools.json.bak
cp /etc/systemd/system/mcp-tools.service /etc/systemd/system/mcp-tools.service.bak
cp /etc/systemd/system/telegram-bot.service /etc/systemd/system/telegram-bot.service.bak
```

**Step 2.2** — Create symlinks for SearXNG config
```bash
ln -sf /opt/ai-lab/config/searxng/settings.yml /opt/searxng/settings.yml
ln -sf /opt/ai-lab/config/searxng/limiter.toml /opt/searxng/limiter.toml
# docker-compose.yml + mcp_server.py: real files (symlinks break Docker/mcpo)
# Deployed as real copies by deploy.sh
```

**Step 2.3** — Update mcpo config path
```bash
# Edit /root/.mcpo-tools.json:
#   "args": ["/opt/searxng/mcp_server.py"]
# → "args": ["/opt/ai-lab/config/searxng/mcp_server.py"]
```

**Step 2.4** — Update basic-memory for new vault path
```bash
# Option A (if --path confirmed in Step 0.1):
# Edit /etc/systemd/system/basic-memory.service, add to ExecStart:
#   --path /opt/ai-lab/data/vault

# Option B (fallback if flag doesn't exist):
# ln -s /opt/ai-lab/data/vault /data/vault

# Update /root/.basic-memory/config.json:
#   "path": "/data/vault"  →  "path": "/opt/ai-lab/data/vault"
systemctl daemon-reload
```

**Step 2.5** — Migrate vault data
```bash
cp -a /data/vault/* /opt/ai-lab/data/vault/
# Verify counts match
find /data/vault -name '*.md' | wc -l
find /opt/ai-lab/data/vault -name '*.md' | wc -l
```

---

### Phase 3: Restart Services (ordered by dependency)

**Step 3.1** — Restart basic-memory (new vault path)
```bash
systemctl restart basic-memory
# Verify: systemctl is-active basic-memory
# Verify: curl http://127.0.0.1:8000/openapi.json returns 200
```

**Step 3.2** — Restart mcp-tools (new mcp_server.py path)
```bash
systemctl restart mcp-tools
# Verify: systemctl is-active mcp-tools
# Verify: curl http://127.0.0.1:8001/searxng/openapi.json returns 200
```

**Step 3.3** — Restart SearXNG (new settings symlink)
```bash
cd /opt/searxng && docker compose restart searxng
# Verify: curl http://127.0.0.1:8888/search?q=test&format=json returns results
```

**Step 3.4** — Verify Telegram bot (auto-reconnect via polling)
```bash
systemctl is-active telegram-bot
# Test: send message to Telegram bot, verify response
```

**Step 3.5** — Verify Ollama (unchanged)
```bash
systemctl is-active ollama && ollama list
```

---

### Phase 4: Deploy Script Updates

**Step 4.1** — Update `scripts/deploy.sh` with separated pull/push directions
```bash
#!/usr/bin/env bash
# deploy.sh — Sync workspace to server
# Pull: data FROM server (backup). Push: code + configs TO server (deploy).

set -euo pipefail
TARGET="${1:-${DEPLOY_HOST:-}}"
REMOTE_PATH="${DEPLOY_PATH:-/opt/ai-lab}"
REMOTE_USER="${DEPLOY_USER:-root}"

echo "=== STEP 1: Pull knowledge assets FROM server (backup) ==="
rsync -avzu ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/data/vault/ ./data/vault/
rsync -avzu ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/projects/open-webui/data/webui.db ./projects/open-webui/data/
rsync -avzu ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/projects/open-webui/data/uploads/ ./projects/open-webui/data/uploads/

echo "=== STEP 2: Push code + configs TO server (deploy) ==="
rsync -avz --delete \
    --exclude='.git/' \
    --exclude='.anchr/' \
    --exclude='secrets/' \
    --exclude='data/vault/' \
    --exclude='projects/open-webui/data/' \
    --exclude='infra/postgres/' \
    --exclude='infra/qdrant/' \
    --exclude='*.db' \
    --exclude='*.db-shm' \
    --exclude='*.db-wal' \
    ./ ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/

echo "=== Deploy complete. ==="
echo "Run ./scripts/deploy-config.sh if configs or secrets changed."
```

**Step 4.2** — Create `scripts/deploy-config.sh`
```bash
#!/usr/bin/env bash
# deploy-config.sh — Install configs + secrets to server locations
# Run AFTER deploy.sh, only when configs or secrets changed.

set -euo pipefail
TARGET="${1:-${DEPLOY_HOST:-}}"
REMOTE_PATH="${DEPLOY_PATH:-/opt/ai-lab}"

echo "=== Deploying configs to ${TARGET} ==="

# SearXNG — real files (not symlinks)
scp config/searxng/docker-compose.yml root@${TARGET}:/opt/searxng/
scp config/searxng/mcp_server.py root@${TARGET}:/opt/searxng/

# Systemd — clean units
scp config/systemd/basic-memory.service root@${TARGET}:/etc/systemd/system/
scp config/systemd/ollama.service root@${TARGET}:/etc/systemd/system/

# Secrets — to their actual server locations
scp secrets/mcpo-tools.json root@${TARGET}:/root/.mcpo-tools.json
scp secrets/mcp-tools.service root@${TARGET}:/etc/systemd/system/
scp secrets/telegram-bot.service root@${TARGET}:/etc/systemd/system/
scp secrets/open-webui.env root@${TARGET}:${REMOTE_PATH}/projects/open-webui/.env
scp secrets/basic-memory-config.json root@${TARGET}:/root/.basic-memory/config.json

# Reload and restart
ssh root@${TARGET} << 'ENDSSH'
systemctl daemon-reload
systemctl restart basic-memory
systemctl restart mcp-tools
cd /opt/searxng && docker compose restart searxng
echo "Config deployment complete."
ENDSSH
```

> **When to run `deploy-config.sh`**: Only when `config/` or `secrets/` files changed. Normal code-only deploys just need `deploy.sh`.

---

## 6. Testing Strategy

### 6.1 Pre-migration smoke tests (baseline)

| Test | Command | Expected |
|---|---|---|
| basic-memory health | `curl -s http://127.0.0.1:8000/openapi.json` | HTTP 200 |
| mcp-tools health | `curl -s http://127.0.0.1:8001/searxng/openapi.json` | HTTP 200 |
| mcp-tools github | `curl -s http://127.0.0.1:8001/github/openapi.json` | HTTP 200 |
| SearXNG search | `curl -s "http://127.0.0.1:8888/search?q=test&format=json"` | results > 0 |
| SearXNG config | `curl -s http://127.0.0.1:8888/config` | 27 engines |
| Telegram bot | Send test message | Reply received |
| Vault access | `ls /data/vault/Personal/` | .md files present |
| Ollama | `ollama list` | gemma2:2b, llama3.2:1b |
| Open WebUI | `docker ps \| grep ailab-open-webui` | Up and healthy |

### 6.2 Post-migration verification

Run all 6.1 tests after Phase 3. All must return identical results.

### 6.3 Knowledge asset integrity

```bash
# WebUI DB row counts
ssh root@167.233.42.140 'docker exec ailab-open-webui python3 -c "
import sqlite3; c=sqlite3.connect(\"/app/backend/data/webui.db\")
print(\"chats:\", c.execute(\"SELECT COUNT(*) FROM chat\").fetchone()[0])
print(\"messages:\", c.execute(\"SELECT COUNT(*) FROM chat_message\").fetchone()[0])
"'

# Uploads file count + vault file count
find projects/open-webui/data/uploads/ -type f | wc -l
find data/vault -name '*.md' | wc -l

# Spot-check vault file
diff <(ssh root@167.233.42.140 'cat /opt/ai-lab/data/vault/Personal/User\ Profile.md') data/vault/Personal/User\ Profile.md
```

### 6.4 Memory write test (end-to-end)

Write a test note via basic-memory, verify it appears in `/opt/ai-lab/data/vault/`.

### 6.5 Deploy round-trip test

1. Edit `config/searxng/settings.yml` locally
2. Run `deploy.sh` → verify SearXNG picks up change
3. Verify `webui.db` was NOT overwritten (check chat count unchanged)
4. Edit a vault `.md` locally
5. Commit to git → verify the tracked `.md` appears in repo

---

## 7. Edge Cases & Risk Mitigations

### 7.1 basic-memory vault path change

**Risk**: `--path` flag may not exist.
**Mitigation**: Pre-flight verified in Step 0.1. Fallback: symlink `ln -s /opt/ai-lab/data/vault /data/vault`. Also update `config.json` `projects.main.path`.

### 7.2 basic-memory dual-source vault path

**Risk**: Vault path in both systemd unit (`--path`) and `config.json` (`projects.main.path`). Changing only one causes inconsistency.
**Mitigation**: Step 2.4 updates both. Verify via basic-memory logs after restart.

### 7.3 Symlinked Docker files

**Risk**: Docker Compose may not follow symlinks for volume mounts.
**Mitigation**: `settings.yml` and `limiter.toml` are symlinked (safe — mounted as individual files `:ro`). `docker-compose.yml` and `mcp_server.py` stay as real files deployed by `deploy.sh`/`deploy-config.sh`.

### 7.4 mcpo config caching

**Risk**: mcpo caches config, doesn't pick up new `mcp_server.py` path.
**Mitigation**: `systemctl restart mcp-tools` forces full reload. Verified by `/searxng/openapi.json`.

### 7.5 webui.db overwrite during deploy

**Risk**: `deploy.sh` push overwrites live `webui.db` with stale local copy.
**Mitigation**: `webui.db` excluded from push via `--exclude='projects/open-webui/data/'`. Push is code+configs only. Data is pull-only (backup direction).

### 7.6 webui.db partial read during copy

**Risk**: Copying `webui.db` while Open WebUI writes to it.
**Mitigation**: SQLite WAL mode — reads are consistent even during writes. The `-shm` and `-wal` files excluded from sync. At 9.4 MB, copy is near-instantaneous.

### 7.7 Vault sync: server is authoritative

**Risk**: Vault edited locally and on server simultaneously.
**Mitigation**: Vault is **server → local only** (pull for backup). The server's vault at `/opt/ai-lab/data/vault/` is authoritative — basic-memory writes there directly. Local edits go to git for version history; server is never overwritten by deploy push.

### 7.8 Secrets exposure in git history

**Risk**: Real secrets committed before git-crypt setup.
**Mitigation**: `secrets/` directory is git-crypt encrypted from the first commit. `.gitignore` ensures unencrypted secrets files can't be accidentally added outside `secrets/`. Pre-commit hook scans for token patterns.

### 7.9 GPG key loss

**Risk**: Lose GPG private key → can't decrypt `secrets/`.
**Mitigation**: Export GPG key backup. `git-crypt export-key` exports the symmetric key as a raw file (store offline). Multiple GPG keys can be added with `git-crypt add-gpg-user`.

---

## 8. Rollback Plan

### 8.1 Instant rollback (per service)

```bash
# basic-memory: revert vault path
cp /etc/systemd/system/basic-memory.service.bak /etc/systemd/system/basic-memory.service
# Revert config.json path back to /data/vault
systemctl daemon-reload && systemctl restart basic-memory

# mcp-tools: revert mcp_server.py path in /root/.mcpo-tools.json
cp /root/.mcpo-tools.json.bak /root/.mcpo-tools.json
systemctl restart mcp-tools

# SearXNG: restore from backup
cp /opt/searxng.bak.*/docker-compose.yml /opt/searxng/
cp /opt/searxng.bak.*/settings.yml /opt/searxng/
cp /opt/searxng.bak.*/limiter.toml /opt/searxng/
cd /opt/searxng && docker compose restart searxng
```

### 8.2 Full rollback

Restore `/opt/searxng/` from `.bak` directory. Revert all systemd units and mcpo config from `.bak` copies. Restart all services. Original vault at `/data/vault/` is untouched (copy, not move).

---

## 9. Dependencies Between Steps

```
Phase 0 (pre-flight) — read-only verification
    ↓
Phase 1 (local setup) — git-crypt init, pull files, create templates
    ↓
Phase 2 (server prep) — backups, symlinks, path updates
    ↓
Phase 3 (restart) — ordered:
    basic-memory → mcp-tools → SearXNG → Telegram (indep.), Ollama (indep.)
    ↓
Phase 4 (scripts) — deploy.sh (pull data + push code), deploy-config.sh (secrets + systemd)
```

---

## 10. Acceptance Criteria

- [ ] Step 0.1: `--path` flag confirmed or symlink fallback selected
- [ ] `git-crypt` initialized and `secrets/` encrypts correctly (verify: `git-crypt status`)
- [ ] All 5 real secret files in `secrets/` with correct content
- [ ] All `.example` templates in `config/` with placeholders (readable without GPG)
- [ ] 9 clean config files tracked in `config/` (SearXNG x4, systemd x2, basic-memory x1, ollama x1, open-webui x1)
- [ ] `data/vault/` contains 3 vault `.md` files synced from server
- [ ] `projects/open-webui/data/webui.db` synced (chats + messages row counts verified)
- [ ] `projects/open-webui/data/uploads/` contains ~150 source `.md` files
- [ ] All 6.1 smoke tests pass after migration
- [ ] Memory write test passes (new note → appears in `/opt/ai-lab/data/vault/`)
- [ ] `deploy.sh` pulls data correctly and does NOT push `webui.db` or vault back
- [ ] `deploy-config.sh` deploys secrets + configs to correct server locations
- [ ] All 27 SearXNG engines still loaded
- [ ] Telegram bot still functional
- [ ] Ollama still serving both models
- [ ] Zero unencrypted secrets committed (verify: `git diff --cached` + `git-crypt status`)
