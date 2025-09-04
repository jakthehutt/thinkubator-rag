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
        # Mock the generative model's response
        mock_gen_model_instance.generate_content.return_value.text = "Generated answer based on context."

        user_query = "What is discussed in these documents?"
        generated_answer = pipeline.generate_answer(user_query, top_k_chunks=3)

        # Assert that the generative model was called
        mock_gen_model_instance.generate_content.assert_called_once()
        
        # Get the call arguments to inspect the generated prompt
        called_prompt = mock_gen_model_instance.generate_content.call_args[0][0]

        # Assert that the system prompt is included
        # The pipeline.generation_system_prompt attribute should already be set by the fixture.
        assert pipeline.generation_system_prompt.strip() in called_prompt.strip()

        # Assert that document overview is included (new format)
        assert "DOCUMENT OVERVIEW: Summary of Doc1." in called_prompt

        # Assert that chunk contents are included with new numbered format
        assert "Source [1]: Doc1.pdf (Page ~1)" in called_prompt
        assert "Source [2]: Doc1.pdf (Page ~2)" in called_prompt
        assert "Source [3]: Doc2.pdf (Page ~3)" in called_prompt

        # Assert that the new format instructions are included
        assert "INSTRUCTIONS FOR CITATION:" in called_prompt
        assert "Use numbered citations [1], [2], etc. in your answer" in called_prompt

        # Assert that user query is included
        assert f"USER QUESTION: {user_query}" in called_prompt

        # Assert the final answer
        assert generated_answer == "Generated answer based on context."
