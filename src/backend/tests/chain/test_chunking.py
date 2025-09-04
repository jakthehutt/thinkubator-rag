import pytest
from unittest.mock import MagicMock, patch, call
import os

def test_chunking_document(mock_rag_pipeline):
    pipeline, mock_gen_model_instance, _ = mock_rag_pipeline

    # The actual text that would be extracted from the mock_pdf_file
    extracted_text = (
        "This is page 1 of the document. This is some more text on page 1. "
        "This is a meaningful section about document structure.\n\n"
        "This is page 2. More content here. This section discusses the content of page 2 and its relevance. "
        "This is the end of the document.\n\n"
    )
    page_texts_with_num = [
        (1, "This is page 1 of the document. This is some more text on page 1. This is a meaningful section about document structure."),
        (2, "This is page 2. More content here. This section discusses the content of page 2 and its relevance. This is the end of the document.")
    ]

    with patch.object(pipeline, '_extract_text_from_pdf', return_value=(extracted_text, page_texts_with_num)):
        # Mock the responses for document summarization and chunking/summaries
        mock_gen_model_instance.generate_content.side_effect = [
            MagicMock(text="Two sentence summary of the document."), # For document summary
            MagicMock(text="<chunk>This is a meaningful section about document structure.</chunk>\n\n<chunk>This section discusses the content of page 2 and its relevance.</chunk>"), # For chunking
            MagicMock(text="Summary of Chunk 1"), # For chunk 1 summary
            MagicMock(text="Summary of Chunk 2")  # For chunk 2 summary
        ]

        document_name = "Test Document"
        pipeline.ingest_pdf("dummy_path.pdf", document_name)

        # Assert that chunking was called with the correct prompt
        # Read the actual prompt from the file to ensure consistency
        with open("./src/backend/prompt/chunking_prompt.txt", 'r') as f:
            chunking_prompt_template = f.read()
        
        expected_chunking_prompt_call = chunking_prompt_template.format(text=extracted_text)

        call_args_list = [call.args[0] for call in mock_gen_model_instance.generate_content.call_args_list]
        
        # Find the call corresponding to the chunking prompt
        chunking_call_found = False
        for arg in call_args_list:
            # Strip any leading/trailing whitespace to avoid issues with newlines/spaces
            if arg.strip() == expected_chunking_prompt_call.strip():
                chunking_call_found = True
                break
        assert chunking_call_found, "Chunking prompt was not called correctly"
