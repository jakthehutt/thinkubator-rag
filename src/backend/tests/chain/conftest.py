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
    """Create a mocked RAG pipeline for testing with Supabase"""
    # Mock environment variables to avoid real API calls
    with patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_api_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_SERVICE_ROLE_KEY': 'test_key',
        'POSTGRES_URL_NON_POOLING': 'postgresql://test@localhost/test'
    }, clear=False):
        with patch('src.backend.chain.rag_pipeline.genai') as mock_genai:
            with patch('src.backend.chain.rag_pipeline.GoogleGenerativeAIEmbeddings') as mock_embeddings:
                with patch('src.backend.chain.rag_pipeline.SupabaseVectorStore') as mock_vector_store_class:
                    
                    # Mock the genai.configure call
                    mock_genai.configure = MagicMock()
                    
                    # Mock the generative model
                    mock_gen_model = MagicMock()
                    mock_genai.GenerativeModel.return_value = mock_gen_model
                    mock_gen_model.generate_content.return_value.text = "<chunk>Test chunk 1</chunk>\n<chunk>Test chunk 2</chunk>"
                    
                    # Mock GoogleGenerativeAIEmbeddings
                    mock_embedding_instance = MagicMock()
                    mock_embedding_instance.embed_query.return_value = [0.1, 0.2, 0.3] * 256  # 768-dim mock embedding
                    mock_embeddings.return_value = mock_embedding_instance
                    
                    # Mock SupabaseVectorStore - create instance first
                    mock_vector_store = MagicMock()
                    mock_vector_store_class.return_value = mock_vector_store
                    
                    # Mock vector store methods
                    mock_vector_store.add_documents.return_value = ["doc1", "doc2"]
                    mock_vector_store.similarity_search.return_value = [
                        type('MockDoc', (), {
                            'content': "Retrieved Chunk 1", 
                            'metadata': {"page_in_document": 1, "document_name": "test.pdf"},
                            'distance': 0.1
                        }),
                        type('MockDoc', (), {
                            'content': "Retrieved Chunk 2", 
                            'metadata': {"page_in_document": 2, "document_name": "test.pdf"},
                            'distance': 0.2
                        })
                    ]
                    mock_vector_store.get_collection_info.return_value = {
                        "table_name": "test_embeddings",
                        "embedding_dimension": 768,
                        "total_documents": 0
                    }
                    
                    # Import and create RAG pipeline with a test API key
                    from src.backend.chain.rag_pipeline import RAGPipeline
                    pipeline = RAGPipeline(api_key="test_api_key")
                    
                    yield pipeline, mock_gen_model, mock_vector_store
