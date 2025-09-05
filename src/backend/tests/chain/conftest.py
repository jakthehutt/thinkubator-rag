import sys
import pytest
from unittest.mock import MagicMock, patch
import os

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
sys.path.insert(0, project_root)

@pytest.fixture
def mock_rag_pipeline():
    """Create a mocked RAG pipeline for testing"""
    with patch('src.backend.chain.rag_pipeline.genai') as mock_genai:
        with patch('src.backend.chain.rag_pipeline.chromadb') as mock_chromadb:
            with patch('src.backend.chain.rag_pipeline.GoogleGenerativeAIEmbeddings') as mock_embeddings:
                
                # Mock the generative model
                mock_gen_model = MagicMock()
                mock_genai.GenerativeModel.return_value = mock_gen_model
                mock_gen_model.generate_content.return_value.text = "<chunk>Test chunk 1</chunk>\n<chunk>Test chunk 2</chunk>"
                
                # Mock ChromaDB
                mock_client = MagicMock()
                mock_chromadb.PersistentClient.return_value = mock_client
                mock_collection = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_collection
                
                # Set up the query mock return value
                mock_collection.query.return_value = {
                    'documents': [["Retrieved Chunk 1", "Retrieved Chunk 2"]],
                    'metadatas': [[{"page_in_document": 1}, {"page_in_document": 2}]],
                    'distances': [[0.1, 0.2]]
                }
                
                # Mock embeddings
                mock_embedding_instance = MagicMock()
                mock_embeddings.return_value = mock_embedding_instance
                
                # Import and create RAG pipeline with a test API key
                from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase
                pipeline = RAGPipelineSupabase(api_key="test_api_key")
                
                yield pipeline, mock_gen_model, mock_collection
