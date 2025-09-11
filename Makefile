.PHONY: test-chunking test-storing test-retrieving test-generation test-e2e-rag test-supabase test-api test-all ingest-pdfs

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
