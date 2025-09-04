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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'chain')))
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
