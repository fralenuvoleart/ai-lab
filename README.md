# AI-LAB

Mono-repo AI experimentation workspace with shared infrastructure and isolated projects.

## Quick Start

```bash
cp .env.example .env
# Edit .env with your API keys
make infra-up
```

## Structure

- `infra/` — Shared always-on services (Caddy, PostgreSQL, Qdrant)
- `projects/` — Isolated experiments, each with its own docker-compose.yml
- `shared/` — Reusable MCP servers, skills, datasets
- `scripts/` — DevOps utilities (deploy, backup)

See [`docs/WORKSPACE-STRUCTURE.md`](docs/WORKSPACE-STRUCTURE.md) for the full tree.

## Commands

| Command | Description |
|---------|-------------|
| `make infra-up` | Start shared infrastructure |
| `make infra-down` | Stop shared infrastructure |
| `make template-scaffold NAME=my-exp` | Scaffold a new experiment |
| `make deploy` | Deploy workspace to Hetzner VPS |
| `make backup-db` | Backup PostgreSQL databases |
