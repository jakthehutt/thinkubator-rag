import pytest
from unittest.mock import MagicMock, patch, call
import os

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
