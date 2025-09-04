.PHONY: test-chunking test-storing test-retrieving test-generation ingest-pdfs

test-chunking:
	@bash make/test_chunking.sh

test-storing:
	@bash make/test_storing.sh

test-retrieving:
	@bash make/test_retrieving.sh

test-generation:
	@bash make/test_generation.sh

ingest-pdfs:
	@python src/backend/ingest_documents.py

test-e2e:
	@bash make/test_e2e_rag.sh

test-all:
	@bash make/test_all.sh
