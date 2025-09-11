import pytest
import os
from src.backend.chain.rag_pipeline import RAGPipeline

@pytest.mark.e2e
def test_e2e_rag_pipeline():
    """
    End-to-end test for the RAG pipeline.
    This test assumes the Supabase vector store has been populated by running the ingest_documents.py script.
    It makes a live call to the Gemini API for generation.
    """
    # Ensure GEMINI_API_KEY is set in the environment for the live API call
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        pytest.skip("GEMINI_API_KEY environment variable not set. Skipping E2E test.")

    # Instantiate the RAGPipeline with Supabase vector store
    # It will use the default configuration for Supabase
    pipeline = RAGPipeline()

    # A sample query that should retrieve relevant information from the ingested documents
    # (The query may need to be adjusted based on the content of your PDFs)
    user_query = "What is the circularity gap?"

    # Generate an answer using the RAG pipeline
    generated_answer = pipeline.generate_answer(user_query, top_k_chunks=5)

    # Assert that the generated answer is not empty and contains expected keywords
    assert generated_answer is not None
    assert isinstance(generated_answer, str)
    assert len(generated_answer) > 0
    # Add more specific assertions based on the expected output from your documents
    # For example, if you expect the answer to mention "economy" or "circular":
    assert "economy" in generated_answer.lower()
    assert "circular" in generated_answer.lower()
    # You could also assert that a source is referenced, though the exact source might vary
    assert "cgr" in generated_answer.lower() or "report" in generated_answer.lower()
