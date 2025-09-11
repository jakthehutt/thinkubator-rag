import pytest
from unittest.mock import MagicMock, patch, call
import os
# from conftest import PROJECT_ROOT # No longer needed

def test_generate_answer(mock_rag_pipeline):
    pipeline, mock_gen_model_instance, _ = mock_rag_pipeline

    # Mock the retrieve method to return specific chunks and metadata
    mock_retrieved_chunks_info = [
        {
            "document": "<chunk>This is a meaningful section about document structure from Doc1.</chunk>",
            "metadata": {
                "document_name": "Doc1.pdf",
                "page_in_document": 1,
                "summary_of_document": "Summary of Doc1."
            },
            "distance": 0.1
        },
        {
            "document": "<chunk>This section discusses the content of page 2 and its relevance from Doc1.</chunk>",
            "metadata": {
                "document_name": "Doc1.pdf",
                "page_in_document": 2,
                "summary_of_document": "Summary of Doc1."
            },
            "distance": 0.2
        },
        {
            "document": "<chunk>Content from another relevant document, Doc2.</chunk>",
            "metadata": {
                "document_name": "Doc2.pdf",
                "page_in_document": 3,
                "summary_of_document": "Summary of Doc2."
            },
            "distance": 0.3
        }
    ]

    with patch.object(pipeline, 'retrieve', return_value=mock_retrieved_chunks_info):
        # Mock the GenerativeModel constructor to return our mock and capture its arguments
        with patch('src.backend.chain.rag_pipeline.genai.GenerativeModel', return_value=mock_gen_model_instance) as mock_model_constructor:
            # Mock the generative model's response  
            mock_gen_model_instance.generate_content.return_value.text = "Generated answer based on context."

            user_query = "What is discussed in these documents?"
            generated_answer = pipeline.generate_answer(user_query, top_k_chunks=3)

            # Assert that GenerativeModel was called with proper system instruction
            mock_model_constructor.assert_called_once()
            call_args = mock_model_constructor.call_args
            
            # Check that system_instruction was passed and contains expected elements
            assert 'system_instruction' in call_args.kwargs
            system_instruction = call_args.kwargs['system_instruction']
            
            # Verify system instruction contains key elements (but NOT the user query)
            assert "You are an expert AI assistant working for thinkubator.earth" in system_instruction
            assert "DOCUMENT OVERVIEW: Summary of Doc1." in system_instruction
            assert "Source [1]: Doc1.pdf (Page ~1)" in system_instruction
            assert "INSTRUCTIONS FOR CITATION:" in system_instruction
            assert user_query not in system_instruction  # User query should NOT be in system instruction

            # Assert that the generative model was called with the user query directly
            mock_gen_model_instance.generate_content.assert_called_once_with(user_query)
            
            # Assert the final answer
            assert generated_answer == "Generated answer based on context."
