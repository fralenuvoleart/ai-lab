# AI-LAB Workspace Structure

```
ai-lab/                                <--- Root Git Repo & VS Code Workspace
├── .vscode/                           <--- VS Code Workspace Configurations
│   ├── settings.json                  <--- Workspace settings (Docker, SSH, AI settings)
│   └── extensions.json                <--- Recommended extensions (Roo Code, Remote-SSH)
├── .rooignore                         <--- Prevents Roo Code from indexing heavy/sensitive files
├── .roomodes                          <--- Custom Roo Code Modes (e.g., DevOps, RAG Engineer)
├── .clinerules                        <--- Global rules & behavior constraints for Roo Code
├── .gitignore                         <--- Standard Git ignore rules
├── .env.example                       <--- Template for shared API keys (OpenAI, Anthropic, etc.)
├── Makefile                           <--- CLI shortcuts for Docker & deployment commands
│
├── infra/                             <--- SHARED INFRASTRUCTURE (Always On)
│   ├── docker-compose.infra.yml       <--- Reverse Proxy, Databases, Vector DBs
│   ├── caddy/                         <--- Auto-SSL Reverse Proxy configuration
│   ├── postgres/                      <--- Shared relational database storage
│   └── qdrant/                        <--- Shared vector DB storage for RAG projects
│
├── projects/                          <--- ISOLATED EXPERIMENTS & APPS
│   ├── _template/                     <--- Starter template for new experiments
│   │   ├── docker-compose.yml
│   │   ├── README.md
│   │   └── .env.example
│   ├── openclaw-agent/                <--- Experiment A: OpenClaw Daemon
│   │   ├── docker-compose.yml
│   │   ├── SOUL.md
│   │   └── MEMORY.md
│   └── multi-agent-crew/              <--- Experiment B: Python CrewAI Setup
│       ├── main.py
│       └── requirements.txt
│
├── shared/                            <--- REUSABLE ASSETS ACROSS EXPERIMENTS
│   ├── mcp-servers/                   <--- Custom MCP servers (Hetzner, Docker, etc.)
│   │   ├── hetzner-mcp/
│   │   └── docker-mcp/
│   ├── skills/                        <--- Reusable prompt templates & instructions
│   └── datasets/                      <--- Sample documents/eval datasets for RAG testing
│
└── scripts/                           <--- DEVOPS & MAINTENANCE
    ├── deploy.sh                      <--- Rsync/Deploy workspace to Hetzner VPS
    └── backup-db.sh                   <--- Database backup scripts
```

## Key Principles

- **`infra/`** — Shared always-on services. Do NOT modify when working on an isolated project unless explicitly asked.
- **`projects/`** — Each experiment is self-contained with its own `docker-compose.yml`. Scaffold new ones from `_template/`.
- **`shared/`** — Reusable across experiments: MCP servers, skills, datasets.
- **`scripts/`** — DevOps utilities. `deploy.sh` syncs to Hetzner VPS, `backup-db.sh` dumps PostgreSQL.
