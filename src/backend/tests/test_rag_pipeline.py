import sys
import pytest
from unittest.mock import MagicMock, patch, call
import os

# Mock the genai, chromadb, and langchain_google_genai imports at the module level BEFORE importing RAGPipeline
sys.modules['google.generativeai'] = MagicMock()
sys.modules['chromadb'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['pypdf'] = MagicMock() # Also mock pypdf

# Adjust the path to import RAGPipeline correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'chain')))
from rag_pipeline import RAGPipeline

@pytest.fixture
def mock_rag_pipeline():
    with patch('rag_pipeline.genai.GenerativeModel') as mock_gen_model:
        with patch('rag_pipeline.chromadb.PersistentClient') as mock_chroma_client:
            with patch('rag_pipeline.GoogleGenerativeAIEmbeddings') as mock_embeddings:
                
                # Mock the generative model for content generation (chunking, summarization)
                mock_gen_model_instance = MagicMock()
                mock_gen_model.return_value = mock_gen_model_instance
                mock_gen_model_instance.generate_content.return_value.text = "<chunk>Chunk 1</chunk>\n\n<chunk>Chunk 2</chunk>"

                # Mock the embedding model
                mock_embeddings_instance = MagicMock()
                mock_embeddings.return_value = mock_embeddings_instance

                # Mock ChromaDB client and collection
                mock_client_instance = MagicMock()
                mock_chroma_client.return_value = mock_client_instance
                mock_collection_instance = MagicMock()
                mock_client_instance.get_or_create_collection.return_value = mock_collection_instance
                mock_collection_instance.add.return_value = None # No return for add
                mock_collection_instance.query.return_value = {
                    'documents': [["Retrieved Chunk 1", "Retrieved Chunk 2"]],
                    'metadatas': [[{"page_in_document": 1}, {"page_in_document": 2}]],
                    'distances': [[0.1, 0.2]]
                }

                pipeline = RAGPipeline(
                    chroma_path="./test_chroma_db",
                    chunking_prompt_path="./src/backend/prompt/chunking_prompt.txt",
                    chunk_summary_prompt_path="./src/backend/prompt/chunk_summary_prompt.txt",
                    document_summary_prompt_path="./src/backend/prompt/document_summary_prompt.txt"
                )
                yield pipeline, mock_gen_model_instance, mock_collection_instance


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
        # Mock the responses for summarization and chunking
        mock_gen_model_instance.generate_content.side_effect = [
            MagicMock(text="Two sentence summary of the document."),
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
        assert kwargs["metadatas"][0]["general_metadata"] == general_meta
        assert kwargs["metadatas"][0]["page_in_document"] == 1  # Now should correctly derive page 1

        assert kwargs["ids"][0] == f"{document_name}_1_0"

        assert kwargs["metadatas"][1]["page_in_document"] == 2 # Now should correctly derive page 2
        assert kwargs["ids"][1] == f"{document_name}_2_1"

def test_retrieving_chunks(mock_rag_pipeline):
    pipeline, _, mock_collection_instance = mock_rag_pipeline

    query = "What is the document about?"
    retrieved_chunks = pipeline.retrieve(query)

    mock_collection_instance.query.assert_called_once_with(
        query_texts=[query], # The pre-query transformation is a passthrough for now
        n_results=5,
        include=['documents', 'metadatas', 'distances']
    )

    assert len(retrieved_chunks) == 2
    assert retrieved_chunks[0]["document"] == "Retrieved Chunk 1"
    assert retrieved_chunks[0]["metadata"] == {"page_in_document": 1}
    assert retrieved_chunks[0]["distance"] == 0.1

    assert retrieved_chunks[1]["document"] == "Retrieved Chunk 2"
    assert retrieved_chunks[1]["metadata"] == {"page_in_document": 2}
    assert retrieved_chunks[1]["distance"] == 0.2
