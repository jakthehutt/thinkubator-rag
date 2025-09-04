import sys
import pytest
from unittest.mock import MagicMock, patch, call
import os

# Mock external modules *before* any other imports that might depend on them.
# This ensures GEMINI_API_KEY is set in os.environ before RAGPipeline is imported and initializes.
with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_api_key"}):
    sys.modules['google.generativeai'] = MagicMock()
    sys.modules['chromadb'] = MagicMock()
    sys.modules['langchain_google_genai'] = MagicMock()
    # sys.modules['pypdf'] = MagicMock() # Removed as _extract_text_from_pdf will be patched

    from src.backend.chain.rag_pipeline import RAGPipeline

    # Read actual prompt contents for setting RAGPipeline attributes in the fixture
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_dir = os.path.abspath(os.path.join(current_file_dir, '..', '..', 'prompt'))

    with open(os.path.join(prompt_dir, "chunking_prompt.txt"), 'r') as f:
        mock_chunking_prompt_content = f.read().strip()
    with open(os.path.join(prompt_dir, "chunk_summary_prompt.txt"), 'r') as f:
        mock_chunk_summary_prompt_content = f.read().strip()
    with open(os.path.join(prompt_dir, "document_summary_prompt.txt"), 'r') as f:
        mock_document_summary_prompt_content = f.read().strip()
    with open(os.path.join(prompt_dir, "generation_system_prompt.txt"), 'r') as f:
        mock_generation_system_prompt_content = f.read().strip()

    # Define the side_effect for the mocked _load_prompt
    def mock_load_prompt_side_effect(file_path):
        if "chunking_prompt.txt" in file_path:
            return mock_chunking_prompt_content
        elif "chunk_summary_prompt.txt" in file_path:
            return mock_chunk_summary_prompt_content
        elif "document_summary_prompt.txt" in file_path:
            return mock_document_summary_prompt_content
        elif "generation_system_prompt.txt" in file_path:
            return mock_generation_system_prompt_content
        # Fallback for unexpected paths, though not expected if all are covered
        return "Mocked Default Prompt Content"
    
    # Patch _load_prompt at the module level to ensure it's mocked before RAGPipeline is instantiated
    patch.object(RAGPipeline, '_load_prompt', side_effect=mock_load_prompt_side_effect).start()


    @pytest.fixture
    def mock_rag_pipeline():
        with patch('rag_pipeline.genai.GenerativeModel') as mock_gen_model:
            with patch('rag_pipeline.chromadb.PersistentClient') as mock_chroma_client:
                with patch('rag_pipeline.GoogleGenerativeAIEmbeddings') as mock_embeddings:
                    
                    mock_gen_model_instance = MagicMock()
                    mock_gen_model.return_value = mock_gen_model_instance
                    # This specific mock is for when generate_content is called directly, e.g. for _chunk_text if not patched
                    mock_gen_model_instance.generate_content.return_value.text = "<chunk>Chunk 1</chunk>\n\n<chunk>Chunk 2</chunk>"

                    mock_embeddings_instance = MagicMock()
                    mock_embeddings.return_value = mock_embeddings_instance

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

                    # Instantiate RAGPipeline with dummy paths, then set prompt attributes directly
                    pipeline = RAGPipeline(
                        chroma_path="./test_chroma_db",
                        chunking_prompt_path="dummy_chunking_path",
                        chunk_summary_prompt_path="dummy_chunk_summary_path",
                        document_summary_prompt_path="dummy_document_summary_path",
                        generation_system_prompt_path="dummy_generation_system_prompt_path"
                    )
                    # Set the prompt attributes directly from the pre-read content
                    pipeline.chunking_prompt = mock_chunking_prompt_content
                    pipeline.chunk_summary_prompt = mock_chunk_summary_prompt_content
                    pipeline.document_summary_prompt = mock_document_summary_prompt_content
                    pipeline.generation_system_prompt = mock_generation_system_prompt_content

                    # Do not patch internal methods like _chunk_text, _summarize_chunk, _summarize_document or _extract_text_from_pdf here.
                    # These mocks should be handled by individual tests if needed, or by side_effect on mock_gen_model_instance.generate_content.
                    yield pipeline, mock_gen_model_instance, mock_collection_instance
