.PHONY: test-chunking test-storing test-retrieving test-generation ingest-pdfs test-frontend-vercel test-frontend-api test-frontend-e2e test-frontend-components test-frontend-coverage

# Backend tests
test-chunking:
	@bash make/test_chunking.sh

test-storing:
	@bash make/test_storing.sh

test-retrieving:
	@bash make/test_retrieving.sh

test-generation:
	@bash make/test_generation.sh

test-e2e:
	@bash make/test_e2e.sh

test-supabase:
	@bash make/test_supabase.sh

test-api:
	@bash make/test_api.sh

test-all:
	@bash make/test_all.sh

# Frontend tests (Vercel dev)
test-frontend-vercel:
	@bash make/test_frontend_vercel.sh

test-frontend-api:
	@bash make/test_frontend_api.sh

test-frontend-e2e:
	@bash make/test_frontend_e2e.sh

test-frontend-components:
	@bash make/test_frontend_components.sh

test-frontend-coverage:
	@bash make/test_frontend_coverage.sh

# Legacy frontend test (keep for compatibility)
test-frontend:
	@bash make/test_frontend.sh

# Utilities
ingest-pdfs:
	@bash make/ingest_pdfs.sh

run-frontend:
	@cd src/frontend && npm run dev
