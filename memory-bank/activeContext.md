# Active Context

## Current Focus

AI-LAB workspace initialization — mono-repo scaffolded with shared infrastructure (Caddy, PostgreSQL/pgvector, Qdrant), experiment templates, and DevOps tooling.

## Recent Changes

- **2026-07-26**: Workspace initialized from scratch:
  - Created full directory structure (`infra/`, `projects/`, `shared/`, `scripts/`)
  - Configured VS Code workspace (settings, extensions, custom Roo Code modes)
  - Set up shared infrastructure docker-compose (Caddy + PostgreSQL + Qdrant)
  - Scaffolded experiment templates (`_template/`, `openclaw-agent/`, `multi-agent-crew/`)
  - Added DevOps scripts (`deploy.sh`, `backup-db.sh`) and `Makefile`
  - Documented workspace structure in `docs/WORKSPACE-STRUCTURE.md`
