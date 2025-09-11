.PHONY: test-chunking test-storing test-retrieving test-generation test-e2e-rag test-supabase test-api test-all ingest-pdfs dev prod stop build logs test-docker clean-docker

# Backend tests
test-chunking:
	@bash make/test_chunking.sh

test-storing:
	@bash make/test_storing.sh

test-retrieving:
	@bash make/test_retrieving.sh

test-generation:
	@bash make/test_generation.sh

test-e2e-rag:
	@bash make/test_e2e_rag.sh

test-supabase:
	@bash make/test_supabase.sh

test-api:
	@bash make/test_api.sh

test-rag-pipeline:
	@bash make/test_rag_pipeline.sh

test-all:
	@bash make/test_all.sh

# Utilities
ingest-pdfs:
	@bash make/ingest_pdfs.sh

# === DOCKER COMMANDS ===

# Development environment
dev:
	@echo "🐳 Starting development environment..."
	docker compose up --build -d
	@echo "✅ Development environment running at:"
	@echo "   - Backend:  http://localhost:8001"
	@echo "   - Frontend: http://localhost:3001"
	@echo "   - Health:   http://localhost:8001/health"

# Production environment  
prod:
	@echo "🚀 Starting production environment..."
	docker compose -f docker-compose-prod.yml up --build -d
	@echo "✅ Production environment running"

# Stop all containers
stop:
	@echo "🛑 Stopping containers..."
	docker compose down
	docker compose -f docker-compose-prod.yml down

# Build containers without starting
build:
	@echo "🔨 Building containers..."
	docker compose build
	docker compose -f docker-compose-prod.yml build

# View logs
logs:
	docker compose logs -f

# Test Docker setup
test-docker:
	@bash make/test_docker.sh

# Test frontend
test-frontend:
	@bash make/test_frontend.sh

# Clean Docker environment
clean-docker:
	@echo "🧹 Cleaning Docker environment..."
	docker compose down -v
	docker system prune -f
	docker volume prune -f
