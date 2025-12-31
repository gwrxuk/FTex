# FTex Decision Intelligence Platform
# Makefile for common operations

.PHONY: help build up down logs clean test dev prod spark-submit

# Default target
help:
	@echo "FTex Decision Intelligence Platform"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build       Build all Docker images"
	@echo "  up          Start all services"
	@echo "  down        Stop all services"
	@echo "  dev         Start development environment"
	@echo "  prod        Start production environment"
	@echo "  logs        View logs from all services"
	@echo "  clean       Remove all containers and volumes"
	@echo "  test        Run tests"
	@echo "  spark-submit Submit a Spark job"
	@echo "  shell-backend Enter backend container shell"
	@echo "  shell-db    Enter PostgreSQL container"
	@echo ""

# Build all images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d
	@echo ""
	@echo "FTex Platform is starting..."
	@echo ""
	@echo "Services:"
	@echo "  Frontend:           http://localhost:3000"
	@echo "  Backend API:        http://localhost:8000"
	@echo "  API Documentation:  http://localhost:8000/docs"
	@echo "  Spark Master UI:    http://localhost:8080"
	@echo "  OpenSearch:         http://localhost:9200"
	@echo "  OpenSearch Dashboard: http://localhost:5601"
	@echo "  Neo4j Browser:      http://localhost:7474"
	@echo ""

# Stop all services
down:
	docker-compose down

# Development mode with hot reload
dev:
	docker-compose -f docker-compose.yml up -d postgres redis opensearch neo4j kafka zookeeper
	@echo "Infrastructure services started. Run frontend and backend locally for development."

# Production mode
prod:
	docker-compose -f docker-compose.yml up -d

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-%:
	docker-compose logs -f $*

# Clean up everything
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Run tests
test:
	docker-compose exec backend pytest -v

# Submit Spark job
spark-submit:
	@if [ -z "$(JOB)" ]; then \
		echo "Usage: make spark-submit JOB=entity_resolution.py"; \
	else \
		docker-compose exec spark-master spark-submit \
			--master spark://spark-master:7077 \
			/opt/spark/jobs/$(JOB); \
	fi

# Enter backend shell
shell-backend:
	docker-compose exec backend /bin/bash

# Enter database shell
shell-db:
	docker-compose exec postgres psql -U ftex -d ftex_db

# Enter Redis CLI
shell-redis:
	docker-compose exec redis redis-cli

# Restart specific service
restart-%:
	docker-compose restart $*

# Check service health
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend not responding"
	@echo ""
	@curl -s http://localhost:9200/_cluster/health | jq . || echo "OpenSearch not responding"

# Initialize database
init-db:
	docker-compose exec postgres psql -U ftex -d ftex_db -f /docker-entrypoint-initdb.d/init-db.sql

# Backup database
backup-db:
	docker-compose exec postgres pg_dump -U ftex ftex_db > backups/ftex_backup_$$(date +%Y%m%d_%H%M%S).sql

# Scale Spark workers
scale-spark:
	@if [ -z "$(N)" ]; then \
		echo "Usage: make scale-spark N=4"; \
	else \
		docker-compose up -d --scale spark-worker-1=$(N); \
	fi

