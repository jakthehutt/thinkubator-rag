import pytest
from unittest.mock import MagicMock, patch, call
import os
# from conftest import PROJECT_ROOT # No longer needed

def test_storing_chunks(mock_rag_pipeline):
    pipeline, mock_gen_model_instance, mock_collection_instance = mock_rag_pipeline

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
        with patch.object(pipeline, '_summarize_document', return_value="Two sentence summary of the document."):
            # Mock the responses for summarization and chunking
            mock_gen_model_instance.generate_content.side_effect = [
                MagicMock(text="<chunk>This is a meaningful section about document structure.</chunk>\n\n<chunk>This section discusses the content of page 2 and its relevance.</chunk>"),
                MagicMock(text="Summary of Chunk 1"),
                MagicMock(text="Summary of Chunk 2")
            ]

            document_name = "Test Document"
            general_meta = {"category": "test"}
            pipeline.ingest_pdf("dummy_path.pdf", document_name, general_metadata=general_meta)

            mock_collection_instance.add.assert_called_once()
            args, kwargs = mock_collection_instance.add.call_args

            assert "documents" in kwargs
            assert "metadatas" in kwargs
            assert "ids" in kwargs

            assert len(kwargs["documents"]) == 2
            assert kwargs["documents"][0] == "<chunk>This is a meaningful section about document structure.</chunk>"
            assert kwargs["documents"][1] == "<chunk>This section discusses the content of page 2 and its relevance.</chunk>"

            assert kwargs["metadatas"][0]["document_name"] == document_name
            assert kwargs["metadatas"][0]["summary_of_chunk"] == "Summary of Chunk 1"
            assert kwargs["metadatas"][0]["summary_of_document"] == "Two sentence summary of the document."
            # Check flattened metadata (now prefixed with meta_)
            assert kwargs["metadatas"][0]["meta_category"] == "test"
            assert kwargs["metadatas"][0]["page_in_document"] == 1
            assert kwargs["metadatas"][0]["page_approximation"] == "true"

            assert kwargs["ids"][0] == f"{document_name}_1_0"

            assert kwargs["metadatas"][1]["page_in_document"] == 2
            assert kwargs["ids"][1] == f"{document_name}_2_1"
