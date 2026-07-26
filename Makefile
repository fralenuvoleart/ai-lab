.PHONY: up down restart logs ps clean help \
        infra-up infra-down infra-logs \
        proxy-reload \
        template-scaffold \
        deploy backup-db restore-db

# Default target
help:
	@echo "AI-LAB Makefile Commands"
	@echo "========================="
	@echo ""
	@echo "Infrastructure:"
	@echo "  make infra-up       Start shared infrastructure (Caddy, Postgres, Qdrant)"
	@echo "  make infra-down     Stop shared infrastructure"
	@echo "  make infra-logs     Tail shared infrastructure logs"
	@echo "  make proxy-reload   Reload Caddy configuration"
	@echo ""
	@echo "Experiments:"
	@echo "  make template-scaffold NAME=my-experiment   Scaffold a new experiment"
	@echo ""
	@echo "DevOps:"
	@echo "  make deploy         Deploy workspace to remote VPS"
	@echo "  make backup-db      Backup PostgreSQL databases"
	@echo "  make restore-db     Restore PostgreSQL from latest backup"
	@echo "  make clean          Stop all containers and remove volumes (DANGER)"

# ==============================================================================
# Infrastructure
# ==============================================================================

infra-up:
	@echo "Starting shared infrastructure..."
	docker compose -f infra/docker-compose.infra.yml up -d
	@echo "Infrastructure started. Caddy: :80/:443, Postgres: :5432, Qdrant: :6333"

infra-down:
	@echo "Stopping shared infrastructure..."
	docker compose -f infra/docker-compose.infra.yml down

infra-logs:
	docker compose -f infra/docker-compose.infra.yml logs -f --tail=100

proxy-reload:
	@echo "Reloading Caddy configuration..."
	docker compose -f infra/docker-compose.infra.yml exec -w /etc/caddy caddy caddy reload --config /etc/caddy/Caddyfile

# ==============================================================================
# Experiments
# ==============================================================================

template-scaffold:
	@if [ -z "$(NAME)" ]; then \
		echo "Usage: make template-scaffold NAME=my-experiment"; \
		exit 1; \
	fi
	@echo "Scaffolding new experiment: projects/$(NAME)..."
	cp -r projects/_template projects/$(NAME)
	@echo "Done. Edit projects/$(NAME)/docker-compose.yml to configure."

# ==============================================================================
# DevOps
# ==============================================================================

deploy:
	@echo "Deploying workspace to remote VPS..."
	bash scripts/deploy.sh

backup-db:
	@echo "Backing up databases..."
	bash scripts/backup-db.sh

restore-db:
	@echo "Restoring databases from latest backup..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "Usage: make restore-db BACKUP_FILE=path/to/backup.sql.gz"; \
		exit 1; \
	fi
	gunzip -c $(BACKUP_FILE) | docker compose -f infra/docker-compose.infra.yml exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)
	@echo "Restore complete."

clean:
	@echo "WARNING: This will stop all containers and remove volumes."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f infra/docker-compose.infra.yml down -v; \
		echo "Cleaned."; \
	else \
		echo "Cancelled."; \
	fi
