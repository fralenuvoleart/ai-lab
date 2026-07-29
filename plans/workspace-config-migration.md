# Workspace Config Migration Plan

> **Goal**: Move all configuration files and the basic-memory vault into the workspace repository for version control, audit trail, and local editability — while preserving secrets safety and zero downtime.

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
| `.env` | `/opt/ai-lab/projects/open-webui/` | Open WebUI environment | **Yes** — `WEBUI_SECRET_KEY`, RAG keys |

### 1.2 Runtime data outside workspace

| Data | Server Path | Size | Notes |
|---|---|---|---|
| basic-memory vault | `/data/vault/` | `.md` files (Personal/ + Projects/) | AI-generated notes, user wants editable local copy |

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
| `searxng` | Docker | SearXNG container | `docker compose restart` |
| `searxng-redis` | Docker | Redis for SearXNG | `docker compose restart` |
| `ailab-open-webui` | Docker | Open WebUI container | `docker compose restart` |
| `ailab-caddy` | Docker | Reverse proxy | `docker compose restart` |
| `ailab-postgres` | Docker | PostgreSQL/pgvector | `docker compose restart` |
| `ollama` | systemd | Ollama models | `systemctl restart ollama` |

---

## 2. Target Workspace Structure

```
AI-LAB/
├── config/                          # NEW: all server configs
│   ├── README.md                    # How to deploy configs
│   ├── searxng/
│   │   ├── docker-compose.yml       # from /opt/searxng/
│   │   ├── settings.yml             # from /opt/searxng/
│   │   ├── limiter.toml             # from /opt/searxng/
│   │   └── mcp_server.py            # from /opt/searxng/
│   ├── mcpo/
│   │   └── mcpo-tools.json.example  # template (no real tokens)
│   ├── systemd/
│   │   ├── basic-memory.service     # from /etc/systemd/system/
│   │   ├── mcp-tools.service.example # template (no tokens)
│   │   └── telegram-bot.service.example # template (no tokens)
│   └── open-webui/
│       └── .env.example             # already exists, verify match
├── data/
│   └── vault/                       # NEW: basic-memory vault
│       ├── .gitkeep
│       ├── Personal/
│       └── Projects/
├── docs/
├── infra/
├── memory-bank/
├── plans/
├── projects/
├── scripts/
│   ├── deploy.sh                    # UPDATED: bidirectional sync
│   ├── deploy-config.sh             # NEW: post-deploy config installer
│   └── ...
└── shared/
```

---

## 3. Secret Handling Strategy

### 3.1 Principle

**No real secrets in git — ever.** Files with secrets become `.example` templates. Actual secrets are deployed separately via environment variables or a server-local file outside the workspace.

### 3.2 Files requiring sanitization

| File | Secrets | Template Name | Real Values Location |
|---|---|---|---|
| `mcpo-tools.json` | `GITHUB_PERSONAL_ACCESS_TOKEN` | `mcpo-tools.json.example` | `/root/.mcpo-tools.json` (unchanged on server) |
| `mcp-tools.service` | `GITHUB_PERSONAL_ACCESS_TOKEN` env | `mcp-tools.service.example` | `/etc/systemd/system/mcp-tools.service` (unchanged) |
| `telegram-bot.service` | `TELEGRAM_BOT_TOKEN`, `OWUI_API_KEY` | `telegram-bot.service.example` | `/etc/systemd/system/telegram-bot.service` (unchanged) |
| `.env` (open-webui) | `WEBUI_SECRET_KEY`, API keys | `.env.example` (exists) | `/opt/ai-lab/projects/open-webui/.env` (unchanged) |

### 3.3 .gitignore additions

```
# Secrets — never commit real values
config/mcpo/mcpo-tools.json          # if real file exists, exclude it
!config/mcpo/mcpo-tools.json.example # but allow template
config/systemd/*.service             # exclude real service files
!config/systemd/*.service.example    # but allow templates
config/open-webui/.env               # exclude real .env
!config/open-webui/.env.example      # but allow template
```

---

## 4. Implementation Steps (ordered, with dependencies)

### Phase 1: Workspace Setup (local, no server impact)

**Step 1.1** — Create directory structure
```
mkdir -p config/{searxng,mcpo,systemd,open-webui}
mkdir -p data/vault/{Personal,Projects}
```

**Step 1.2** — Copy clean configs from server (SSH pull)
```bash
scp root@167.233.42.140:/opt/searxng/docker-compose.yml config/searxng/
scp root@167.233.42.140:/opt/searxng/settings.yml config/searxng/
scp root@167.233.42.140:/opt/searxng/limiter.toml config/searxng/
scp root@167.233.42.140:/opt/searxng/mcp_server.py config/searxng/
```

**Step 1.3** — Create sanitized templates
```bash
# mcpo config — replace real token with placeholder
scp root@167.233.42.140:/root/.mcpo-tools.json config/mcpo/mcpo-tools.json.example
# Manually replace GITHUB_PERSONAL_ACCESS_TOKEN value with "YOUR_GITHUB_PAT"

# systemd units — replace env values with placeholders
scp root@167.233.42.140:/etc/systemd/system/basic-memory.service config/systemd/
scp root@167.233.42.140:/etc/systemd/system/mcp-tools.service config/systemd/mcp-tools.service.example
scp root@167.233.42.140:/etc/systemd/system/telegram-bot.service config/systemd/telegram-bot.service.example
# Manually replace tokens with "YOUR_TELEGRAM_BOT_TOKEN" etc.
```

**Step 1.4** — Pull existing vault data
```bash
rsync -avz root@167.233.42.140:/data/vault/ data/vault/
```

**Step 1.5** — Update `.gitignore`

### Phase 2: Server Migration (with service restarts)

**Step 2.1** — Create symlinks for SearXNG config (no restart needed yet)
```bash
ssh root@167.233.42.140
# Backup originals
cp -a /opt/searxng /opt/searxng.bak.$(date +%Y%m%d)
# Symlink from workspace to /opt/searxng
ln -sf /opt/ai-lab/config/searxng/settings.yml /opt/searxng/settings.yml
ln -sf /opt/ai-lab/config/searxng/docker-compose.yml /opt/searxng/docker-compose.yml
ln -sf /opt/ai-lab/config/searxng/limiter.toml /opt/searxng/limiter.toml
# mcp_server.py needs to be a real file (not symlink) for mcpo
cp /opt/ai-lab/config/searxng/mcp_server.py /opt/searxng/mcp_server.py
```

**Step 2.2** — Update mcpo config path (no restart yet)
```bash
# Update mcp-tools.service to point mcp_server.py to new location
# Change: /opt/searxng/mcp_server.py → /opt/ai-lab/config/searxng/mcp_server.py
# But keep /root/.mcpo-tools.json as-is (contains real token)
# Only update the path in the JSON config (not the template)
```

**Step 2.3** — Update basic-memory vault path
```bash
# Edit /etc/systemd/system/basic-memory.service
# Add: --vault-path /opt/ai-lab/data/vault
# Full line becomes:
# ExecStart=/root/.local/bin/mcpo --port 8000 --name "Basic Memory" -- /root/.local/bin/basic-memory mcp --vault-path /opt/ai-lab/data/vault
systemctl daemon-reload
```

**Step 2.4** — Migrate existing vault data
```bash
# Copy existing vault to new location
cp -a /data/vault/* /opt/ai-lab/data/vault/
# Verify file count matches
find /data/vault -name '*.md' | wc -l
find /opt/ai-lab/data/vault -name '*.md' | wc -l
```

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

**Step 3.4** — Verify Telegram bot (should auto-reconnect, polling model)
```bash
systemctl is-active telegram-bot
# Test: send message to Telegram bot, verify response
```

### Phase 4: Deploy Script Updates

**Step 4.1** — Add bidirectional vault sync to `deploy.sh`
```bash
# BEFORE the push: pull current memories from server
echo "Pulling current memories from server..."
rsync -avz ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/data/vault/ ./data/vault/

# THEN the existing push (unchanged)
rsync -avz --delete ... ./ ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/
```

**Step 4.2** — Create `scripts/deploy-config.sh` for post-deploy config installation
```bash
#!/usr/bin/env bash
# deploy-config.sh — Install configs from workspace to server locations
# Run AFTER deploy.sh has synced files to /opt/ai-lab/

set -euo pipefail
TARGET="${1:-${DEPLOY_HOST:-}}"
REMOTE_PATH="${DEPLOY_PATH:-/opt/ai-lab}"

ssh root@${TARGET} << 'ENDSSH'
# Restore systemd units (if changed)
cp /opt/ai-lab/config/systemd/basic-memory.service /etc/systemd/system/
systemctl daemon-reload

# Restart services that need it
systemctl restart basic-memory
systemctl restart mcp-tools
cd /opt/searxng && docker compose restart searxng

echo "Config deployment complete."
ENDSSH
```

**Step 4.3** — Update deploy.sh exclusions
```bash
# Remove any exclusion that would block config/ or data/vault/
# Current exclusions are safe — config/ and data/ are new directories
# Verify: data/vault/ is NOT under projects/*/data/ (different path)
```

---

## 5. Testing Strategy

### 5.1 Pre-migration smoke tests (baseline)

| Test | Command | Expected |
|---|---|---|
| basic-memory health | `curl -s http://127.0.0.1:8000/openapi.json` | HTTP 200, paths present |
| mcp-tools health | `curl -s http://127.0.0.1:8001/searxng/openapi.json` | HTTP 200, 1 path |
| mcp-tools github | `curl -s http://127.0.0.1:8001/github/openapi.json` | HTTP 200, 26 paths |
| SearXNG search | `curl -s "http://127.0.0.1:8888/search?q=test&format=json"` | results > 0 |
| SearXNG config | `curl -s http://127.0.0.1:8888/config` | 27 engines |
| Telegram bot | Send test message | Reply received |
| Vault access | `ls /data/vault/Personal/` | .md files present |

### 5.2 Post-migration verification (exact same tests)

Run all 5.1 tests after Phase 3. All must return identical results.

### 5.3 Vault integrity check

```bash
# File count before and after
find /data/vault -name '*.md' | wc -l  # before
find /opt/ai-lab/data/vault -name '*.md' | wc -l  # after — must match

# Spot-check: diff a few files
diff /data/vault/Personal/some-file.md /opt/ai-lab/data/vault/Personal/some-file.md
```

### 5.4 Memory write test (end-to-end)

After migration, write a test note via basic-memory and verify it appears in `/opt/ai-lab/data/vault/`.

### 5.5 Deploy round-trip test

1. Make a change to `config/searxng/settings.yml` locally
2. Run `deploy.sh`
3. Verify SearXNG picks up the change (check `/config` endpoint)
4. Edit a vault .md file locally
5. Run `deploy.sh`
6. Verify change appears on server

---

## 6. Edge Cases & Risk Mitigations

### 6.1 basic-memory vault path change

**Risk**: basic-memory doesn't support `--vault-path` or uses a different flag.
**Mitigation**: Check `basic-memory mcp --help` before implementing. Fallback: use a symlink `ln -s /opt/ai-lab/data/vault /data/vault` instead (zero config change).

### 6.2 Symlinked docker-compose files

**Risk**: Docker Compose may not follow symlinks for volume mounts.
**Mitigation**: The compose file uses `./settings.yml` (relative). If the compose file itself is a symlink, `./` resolves to the symlink's directory. Alternative: keep compose file as a real file, symlink only settings.yml.

### 6.3 mcpo config hot-reload

**Risk**: mcpo may cache the config and not pick up changed mcp_server.py path.
**Mitigation**: `systemctl restart mcp-tools` forces full reload. Verified by checking `/searxng/openapi.json`.

### 6.4 Telegram bot token exposure

**Risk**: Service file templates accidentally committed with real tokens.
**Mitigation**: Manual review of `.example` files before commit. Add pre-commit hook to scan for token patterns.

### 6.5 Vault sync conflicts

**Risk**: Vault modified on both server and local simultaneously.
**Mitigation**: `deploy.sh` does `rsync -avz` (not `--delete`) for vault pull — merges, doesn't delete. The push uses `--delete` but only for the workspace tree. Vault is synced server→local before push, so local always has latest before any edits.

### 6.6 Service restart order

**Risk**: basic-memory restart while Open WebUI is using it.
**Mitigation**: MCP is stateless per-request. Open WebUI reconnects on next tool call. No data loss. Acceptable brief interruption.

### 6.7 PostgreSQL volume data

**Risk**: infra data directories excluded from deploy but not tracked elsewhere.
**Mitigation**: Already handled by `scripts/backup-db.sh`. Not in scope of this migration.

---

## 7. Rollback Plan

If any service fails after migration:

### 7.1 Instant rollback (per service)

```bash
# basic-memory: revert to original vault path
sed -i 's|--vault-path /opt/ai-lab/data/vault||' /etc/systemd/system/basic-memory.service
systemctl daemon-reload && systemctl restart basic-memory

# mcp-tools: revert mcp_server.py path in /root/.mcpo-tools.json
# (manually edit JSON back to /opt/searxng/mcp_server.py)
systemctl restart mcp-tools

# SearXNG: restore original files from backup
cp /opt/searxng.bak.*/settings.yml /opt/searxng/
cd /opt/searxng && docker compose restart searxng
```

### 7.2 Full rollback

Restore `/opt/searxng/` from `.bak` directory. Revert all systemd units from backup. Restart all services. Original vault at `/data/vault/` is untouched (we copy, not move).

---

## 8. Files to Exclude from Git (`.gitignore` additions)

```gitignore
# Secrets — never commit real values
config/mcpo/mcpo-tools.json
!config/mcpo/mcpo-tools.json.example
config/systemd/basic-memory.service
config/systemd/mcp-tools.service
config/systemd/telegram-bot.service
!config/systemd/*.service.example
config/open-webui/.env
!config/open-webui/.env.example

# Vault data — large, evolving AI-generated content
data/vault/Personal/
data/vault/Projects/
# But keep .gitkeep
!data/vault/Personal/.gitkeep
!data/vault/Projects/.gitkeep
```

Note: If the user wants vault in git, remove the `data/vault/Personal/` and `data/vault/Projects/` exclusions. This is the user's explicit request — "editable local copy in repo of the memories."

---

## 9. Dependencies Between Steps

```
Phase 1 (local) — no dependencies, can do anytime
    ↓
Phase 2 (server prep) — depends on Phase 1 files being deployed
    ↓
Phase 3 (restart) — depends on Phase 2 completion, ORDERED:
    basic-memory → mcp-tools → SearXNG → Telegram (independent)
    ↓
Phase 4 (scripts) — depends on Phase 3 successful verification
```

---

## 10. Acceptance Criteria

- [ ] All 8 config files exist in `config/` directory
- [ ] All secret-containing files have `.example` templates
- [ ] `data/vault/` contains current vault content synced from server
- [ ] All 5.1 smoke tests pass after migration
- [ ] Memory write test passes (new note → appears in workspace vault)
- [ ] `deploy.sh` successfully pulls vault and pushes configs
- [ ] All 27 SearXNG engines still loaded and returning results
- [ ] Telegram bot still functional
- [ ] Zero secrets committed to git (verify with `git diff --cached`)
