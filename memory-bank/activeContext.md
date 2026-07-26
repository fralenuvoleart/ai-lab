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
  - All infra containers running: Caddy (:80/:443), PostgreSQL (:5432, healthy), Qdrant (:6333/:6334)
  - SSH key `~/.ssh/id_ed25519` active for root access
  - HCLOUD_TOKEN stored in `.env`
