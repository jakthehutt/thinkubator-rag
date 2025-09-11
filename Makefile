.PHONY: test-chunking test-storing test-retrieving test-generation test-e2e-rag test-supabase test-api test-all ingest-pdfs setup-users test-users query-users migrate-user-sessions dev prod stop build logs test-docker clean-docker

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

# Setup users table with mock data
setup-users:
	@echo "👥 Setting up users table..."
	cd src/backend/database && python setup_users_table.py

# Test users table
test-users:
	@echo "🧪 Testing users table..."
	cd src/backend && python -m pytest tests/test_users_table.py -v

# Query and display users
query-users:
	@echo "👥 Displaying users table..."
	cd src/backend/database && python query_users.py

# Migrate user sessions
migrate-user-sessions:
	@echo "🔄 Running user sessions migration..."
	cd src/backend/database && python migrate_user_sessions.py

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

# === DEBUGGING COMMANDS ===

# Start debug environment
debug:
	@echo "🐛 Starting debug environment..."
	docker compose -f docker-compose-debug.yml up --build -d
	@echo "✅ Debug environment running at:"
	@echo "   - Backend:  http://localhost:8001 (Debug: 5679)"
	@echo "   - Frontend: http://localhost:3001 (Debug: 9229)"
	@echo "   - Health:   http://localhost:8001/health"
	@echo ""
	@echo "🔍 VS Code Debug Instructions:"
	@echo "   1. Set breakpoints in your code"
	@echo "   2. Press Ctrl+Shift+D (Run and Debug)"
	@echo "   3. Select '🐍 Debug RAG Backend' or '🔗 Debug Full Stack'"
	@echo "   4. Press F5 to start debugging"

# Stop debug environment
debug-stop:
	@echo "🛑 Stopping debug environment..."
	docker compose -f docker-compose-debug.yml down

# Debug logs
debug-logs:
	docker compose -f docker-compose-debug.yml logs -f

# Clean Docker environment
clean-docker:
	@echo "🧹 Cleaning Docker environment..."
	docker compose down -v
	docker system prune -f
	docker volume prune -f
