# System Patterns

## 🛠️ Developer Working Method
- **Standard:** Modular, elegant, performant.
- **Verification:** Trace every claim through the full call chain before asserting a pattern is followed — use `search_files`/grep, never assume from a function name or comment alone.
- **Zero Regression Policy:** Check this file before every file write to ensure changes don't violate an established architectural invariant.

---

## 🏗️ Workspace Architecture

| Rule | Detail |
|------|--------|
| **infra/ isolation** | Do NOT modify `infra/` when working on an isolated `projects/` experiment unless explicitly asked. |
| **Project scaffolding** | New experiments MUST be copied from `projects/_template/`. |
| **Secret management** | Real secrets in `secrets/` (git-crypt encrypted), templates in `config/`. Deploy via `scripts/deploy-config.sh`. |
| **Config convention** | `config/` and `secrets/` grouped by service folder (basic-memory, mcp-tools, ollama, open-webui, searxng, telegram-bot). One folder per service. |
| **Data layout** | All persistent data under `/opt/ai-lab/data/`: `open-webui/` (webui.db, uploads), `vault/` (basic-memory notes). |
| **Docker compose v2** | Always use `docker compose` (plugin), not `docker-compose` (v1). |
| **Shell safety** | Every `.sh` script starts with `set -euo pipefail`. |

---

*This file describes durable architectural rules, not a changelog. When a pattern changes, update the entry in place.*
