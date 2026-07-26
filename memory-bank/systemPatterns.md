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
| **Secret management** | Reference `.env` files; use `${VAR_NAME}` in docker-compose; never hardcode keys. |
| **Docker compose v2** | Always use `docker compose` (plugin), not `docker-compose` (v1). |
| **Shell safety** | Every `.sh` script starts with `set -euo pipefail`. |

---

*This file describes durable architectural rules, not a changelog. When a pattern changes, update the entry in place.*
