#!/usr/bin/env python3
"""
Tests for SupabaseVectorStore implementation.
"""

import pytest
import os
import sys
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.backend.vector_store.supabase_vector_store import SupabaseVectorStore, VectorDocument

# Load environment variables
load_dotenv(dotenv_path=project_root / '.env')

class TestSupabaseVectorStore:
    """Test suite for SupabaseVectorStore."""
    
    @pytest.fixture(scope="class")
    def vector_store(self):
        """Create SupabaseVectorStore instance for testing."""
        # Use a test table to avoid interfering with production data
        return SupabaseVectorStore(
            table_name="test_embeddings",
            embedding_dimension=3  # Small dimension for testing
        )
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            "The circular economy is a sustainable approach to resource management.",
            "Recycling helps reduce waste and environmental impact.",
            "Renewable energy sources include solar, wind, and hydro power."
        ]
    
    @pytest.fixture
    def sample_embeddings(self):
        """Sample embeddings for testing (3D for simplicity)."""
        return [
            [1.0, 0.5, 0.2],
            [0.8, 1.0, 0.1],
            [0.3, 0.4, 1.0]
        ]
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return [
            {"source": "document1.pdf", "page": 1, "topic": "circular_economy"},
            {"source": "document2.pdf", "page": 2, "topic": "recycling"},
            {"source": "document3.pdf", "page": 3, "topic": "renewable_energy"}
        ]
    
    def test_vector_store_initialization(self, vector_store):
        """Test that vector store initializes correctly."""
        assert vector_store is not None
        assert vector_store.table_name == "test_embeddings"
        assert vector_store.embedding_dimension == 3
        assert vector_store.client is not None
    
    def test_database_setup(self, vector_store):
        """Test that database is set up correctly."""
        # This test implicitly runs during vector_store initialization
        # If we get here without exceptions, setup worked
        assert True
    
    def test_get_collection_info(self, vector_store):
        """Test getting collection information."""
        info = vector_store.get_collection_info()
        
        assert "table_name" in info
        assert "embedding_dimension" in info
        assert "total_documents" in info
        assert info["table_name"] == "test_embeddings"
        assert info["embedding_dimension"] == 3
        assert isinstance(info["total_documents"], int)
    
    def test_add_documents_basic(self, vector_store, sample_documents, sample_embeddings):
        """Test adding documents without metadata or IDs."""
        # Clear the collection first
        vector_store.clear_collection()
        
        ids = vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings
        )
        
        assert len(ids) == len(sample_documents)
        assert all(isinstance(doc_id, str) for doc_id in ids)
        
        # Verify documents were added
        info = vector_store.get_collection_info()
        assert info["total_documents"] == len(sample_documents)
    
    def test_add_documents_with_metadata(self, vector_store, sample_documents, 
                                       sample_embeddings, sample_metadata):
        """Test adding documents with metadata."""
        # Clear the collection first
        vector_store.clear_collection()
        
        ids = vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings,
            metadatas=sample_metadata
        )
        
        assert len(ids) == len(sample_documents)
        
        # Verify we can retrieve a document and its metadata
        doc = vector_store.get_document_by_id(ids[0])
        assert doc is not None
        assert doc.content == sample_documents[0]
        assert doc.metadata == sample_metadata[0]
    
    def test_add_documents_with_custom_ids(self, vector_store, sample_documents, 
                                         sample_embeddings):
        """Test adding documents with custom IDs."""
        # Clear the collection first
        vector_store.clear_collection()
        
        custom_ids = ["custom_1", "custom_2", "custom_3"]
        
        returned_ids = vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings,
            ids=custom_ids
        )
        
        assert returned_ids == custom_ids
        
        # Verify we can retrieve by custom ID
        doc = vector_store.get_document_by_id("custom_1")
        assert doc is not None
        assert doc.id == "custom_1"
        assert doc.content == sample_documents[0]
    
    def test_similarity_search_basic(self, vector_store, sample_documents, 
                                   sample_embeddings):
        """Test basic similarity search."""
        # Clear and populate the collection
        vector_store.clear_collection()
        vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings
        )
        
        # Search with the same embedding as first document (should return it first)
        query_embedding = [1.0, 0.5, 0.2]
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=2
        )
        
        assert len(results) <= 2
        assert all(isinstance(result, VectorDocument) for result in results)
        assert all(result.distance is not None for result in results)
        
        # Results should be sorted by distance (closest first)
        if len(results) > 1:
            assert results[0].distance <= results[1].distance
        
        # First result should be exact match (distance ~0)
        assert results[0].distance < 0.01  # Very small distance due to exact match
    
    def test_similarity_search_with_filters(self, vector_store, sample_documents, 
                                          sample_embeddings, sample_metadata):
        """Test similarity search with metadata filters."""
        # Clear and populate the collection with metadata
        vector_store.clear_collection()
        vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings,
            metadatas=sample_metadata
        )
        
        # Search with metadata filter
        query_embedding = [0.5, 0.5, 0.5]
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=10,
            filter_metadata={"topic": "recycling"}
        )
        
        # Should only return documents with matching metadata
        assert len(results) == 1
        assert results[0].metadata["topic"] == "recycling"
        assert "recycling" in results[0].content.lower()
    
    def test_get_document_by_id(self, vector_store, sample_documents, sample_embeddings):
        """Test retrieving document by ID."""
        # Clear and populate the collection
        vector_store.clear_collection()
        ids = vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings
        )
        
        # Get a document by ID
        doc = vector_store.get_document_by_id(ids[0])
        
        assert doc is not None
        assert doc.id == ids[0]
        assert doc.content == sample_documents[0]
        assert len(doc.embedding) == 3
        
        # Try with non-existent ID
        non_existent = vector_store.get_document_by_id("non_existent_id")
        assert non_existent is None
    
    def test_delete_documents(self, vector_store, sample_documents, sample_embeddings):
        """Test deleting documents."""
        # Clear and populate the collection
        vector_store.clear_collection()
        ids = vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings
        )
        
        # Delete first two documents
        deleted_count = vector_store.delete_documents(ids[:2])
        assert deleted_count == 2
        
        # Verify documents are gone
        assert vector_store.get_document_by_id(ids[0]) is None
        assert vector_store.get_document_by_id(ids[1]) is None
        assert vector_store.get_document_by_id(ids[2]) is not None
        
        # Verify collection count
        info = vector_store.get_collection_info()
        assert info["total_documents"] == 1
    
    def test_clear_collection(self, vector_store, sample_documents, sample_embeddings):
        """Test clearing the collection."""
        # Add documents
        vector_store.add_documents(
            documents=sample_documents,
            embeddings=sample_embeddings
        )
        
        # Verify documents exist
        info = vector_store.get_collection_info()
        assert info["total_documents"] > 0
        
        # Clear collection
        vector_store.clear_collection()
        
        # Verify collection is empty
        info = vector_store.get_collection_info()
        assert info["total_documents"] == 0
    
    def test_embedding_dimension_validation(self, vector_store):
        """Test that embedding dimension is validated."""
        # Try to add document with wrong embedding dimension
        with pytest.raises(ValueError, match="Embedding dimension mismatch"):
            vector_store.add_documents(
                documents=["test document"],
                embeddings=[[1.0, 2.0]]  # Wrong dimension (should be 3)
            )
        
        # Try similarity search with wrong dimension
        with pytest.raises(ValueError, match="Query embedding dimension mismatch"):
            vector_store.similarity_search(
                query_embedding=[1.0, 2.0]  # Wrong dimension (should be 3)
            )
    
    def test_input_validation(self, vector_store):
        """Test input validation for add_documents."""
        # Mismatched documents and embeddings
        with pytest.raises(ValueError, match="Number of documents and embeddings must match"):
            vector_store.add_documents(
                documents=["doc1", "doc2"],
                embeddings=[[1.0, 2.0, 3.0]]
            )
        
        # Mismatched documents and metadata
        with pytest.raises(ValueError, match="Number of metadatas must match"):
            vector_store.add_documents(
                documents=["doc1", "doc2"],
                embeddings=[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                metadatas=[{"key": "value"}]
            )
        
        # Mismatched documents and IDs
        with pytest.raises(ValueError, match="Number of IDs must match"):
            vector_store.add_documents(
                documents=["doc1", "doc2"],
                embeddings=[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                ids=["id1"]
            )


@pytest.mark.integration
class TestSupabaseVectorStoreIntegration:
    """Integration tests that require full Supabase setup."""
    
    def test_environment_setup(self):
        """Test that all required environment variables are set."""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "POSTGRES_URL_NON_POOLING"
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Environment variable {var} is not set"
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from adding documents to similarity search."""
        vector_store = SupabaseVectorStore(
            table_name="test_e2e_embeddings",
            embedding_dimension=5
        )
        
        try:
            # Clear any existing data
            vector_store.clear_collection()
            
            # Add sample documents
            documents = [
                "Artificial intelligence is transforming industries.",
                "Machine learning algorithms process large datasets.",
                "Natural language processing enables text understanding.",
                "Computer vision recognizes patterns in images.",
                "Deep learning models require substantial computation."
            ]
            
            embeddings = [
                [0.1, 0.2, 0.3, 0.4, 0.5],
                [0.2, 0.3, 0.4, 0.5, 0.6],
                [0.3, 0.4, 0.5, 0.6, 0.7],
                [0.4, 0.5, 0.6, 0.7, 0.8],
                [0.5, 0.6, 0.7, 0.8, 0.9]
            ]
            
            metadata = [
                {"category": "ai", "complexity": "high"},
                {"category": "ml", "complexity": "medium"},
                {"category": "nlp", "complexity": "high"},
                {"category": "cv", "complexity": "medium"},
                {"category": "dl", "complexity": "very_high"}
            ]
            
            # Add documents
            ids = vector_store.add_documents(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata
            )
            
            assert len(ids) == len(documents)
            
            # Perform similarity search
            query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55]
            results = vector_store.similarity_search(
                query_embedding=query_embedding,
                k=3
            )
            
            assert len(results) <= 3
            assert all(isinstance(result, VectorDocument) for result in results)
            
            # Test filtered search
            filtered_results = vector_store.similarity_search(
                query_embedding=query_embedding,
                k=10,
                filter_metadata={"complexity": "high"}
            )
            
            assert len(filtered_results) == 2  # Should match 2 documents
            assert all(result.metadata["complexity"] == "high" for result in filtered_results)
            
            # Test document retrieval
            doc = vector_store.get_document_by_id(ids[0])
            assert doc is not None
            assert doc.content == documents[0]
            
        finally:
            # Clean up
            vector_store.clear_collection()


if __name__ == "__main__":
    """Run tests directly if script is executed."""
    print("Running Supabase Vector Store tests...")
    print("=" * 60)
    
    # Run tests
    exit_code = pytest.main([__file__, "-v"])
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ All Supabase Vector Store tests passed!")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Please check the implementation.")
    
    sys.exit(exit_code)
