.PHONY: test-chunking test-storing test-retrieving

test-chunking:
	@bash make/test_chunking.sh

test-storing:
	@bash make/test_storing.sh

test-retrieving:
	@bash make/test_retrieving.sh
