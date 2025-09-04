.PHONY: test-chunking test-storing test-retrieving test-generation ingest-pdfs

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

ingest-pdfs:
	@bash make/ingest_pdfs.sh

test-all:
	@bash make/test_all.sh

test-frontend:
	@bash make/test_frontend.sh

run-frontend:
	@python -m streamlit run src/frontend/app.py
