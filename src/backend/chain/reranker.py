"""
Reranking Module for RAG Pipeline

This module provides different reranking strategies to improve the relevance of retrieved chunks:
1. NoReranker: Uses ChromaDB's default vector similarity ranking
2. HybridReranker: Combines vector similarity with metadata-based scoring

Each reranker can be used with any query processor for flexible combinations.
"""

import logging
import re
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime


class BaseReranker(ABC):
    """Abstract base class for rerankers"""
    
    @abstractmethod
    def rerank(self, query: str, retrieved_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rerank the retrieved results based on the query"""
        pass
    
    @abstractmethod
    def get_version_info(self) -> Dict[str, str]:
        """Return information about this reranker version"""
        pass


class NoReranker(BaseReranker):
    """
    Version 1: No Reranking
    
    Simply formats Supabase vector store results without additional reranking.
    Uses the vector similarity scores from pgvector directly.
    
    Pros: Fast, simple, relies on high-quality embeddings
    Cons: May miss important contextual relevance signals
    """
    
    def __init__(self):
        logging.info("NoReranker initialized - using Supabase vector similarity only")
    
    def rerank(self, query: str, retrieved_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format Supabase vector store results without reranking.
        
        Args:
            query (str): User query (not used in this version)
            retrieved_results (dict): Raw results from Supabase vector store
            
        Returns:
            List[Dict]: Formatted results in original order
        """
        reranked_chunks = []
        documents = retrieved_results.get('documents', [[]])[0]
        metadatas = retrieved_results.get('metadatas', [[]])[0]
        distances = retrieved_results.get('distances', [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            reranked_chunks.append({
                "document": doc,
                "metadata": meta,
                "distance": dist,
                "rerank_score": 1.0 - dist  # Convert distance to similarity score
            })
        
        logging.debug(f"NoReranker: Formatted {len(reranked_chunks)} results")
        return reranked_chunks
    
    def get_version_info(self) -> Dict[str, str]:
        return {
            "version": "1.0 - No Reranking",
            "features": "Direct Supabase vector similarity",
            "overhead": "None (~0ms)",
            "use_case": "Fast retrieval with high-quality embeddings"
        }


class HybridReranker(BaseReranker):
    """
    Version 2: Hybrid Reranking
    
    Combines vector similarity with metadata-based scoring:
    - Document recency bonus
    - Chunk position importance
    - Keyword overlap scoring
    - Document type prioritization
    
    Provides better contextual relevance than pure vector similarity.
    """
    
    def __init__(self):
        # Document importance weights (can be tuned based on domain knowledge)
        self.doc_type_weights = {
            'report': 1.2,  # Reports are often more comprehensive
            'summary': 1.1,  # Summaries are concise and relevant
            'analysis': 1.15,  # Analysis documents often have insights
            'default': 1.0
        }
        
        # Year-based recency scoring (more recent = higher score)
        self.base_year = 2020  # Baseline year for recency calculation
        
        logging.info("HybridReranker initialized")
    
    def _calculate_recency_score(self, document_name: str) -> float:
        """
        Calculate recency bonus based on document year.
        Assumes document names contain years (e.g., "Report 2024", "cgr25")
        """
        # Extract year from document name
        year_matches = re.findall(r'\b(20\d{2}|2[1-9])\b', document_name)
        
        if year_matches:
            try:
                doc_year = int(year_matches[-1])  # Use the last year found
                if doc_year < 50:  # Handle 2-digit years like "25" for 2025
                    doc_year += 2000
                
                # Calculate recency bonus (max 1.2x for very recent docs)
                years_diff = doc_year - self.base_year
                recency_bonus = 1.0 + min(years_diff * 0.05, 0.2)  # Max 20% bonus
                return recency_bonus
            except ValueError:
                pass
        
        return 1.0  # No bonus if year not found
    
    def _calculate_keyword_overlap(self, query: str, chunk_content: str) -> float:
        """
        Calculate keyword overlap score between query and chunk.
        Uses TF-like scoring for important terms.
        """
        query_words = set(query.lower().split())
        chunk_words = chunk_content.lower().split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        query_words = query_words - stop_words
        
        if not query_words:
            return 1.0
        
        # Count keyword occurrences
        overlap_score = 0
        for word in query_words:
            count = chunk_words.count(word)
            if count > 0:
                # TF-like scoring: log(1 + count)
                overlap_score += min(count * 0.1, 0.3)  # Cap per word contribution
        
        # Normalize by query length
        return 1.0 + (overlap_score / len(query_words))
    
    def _get_document_type_weight(self, document_name: str) -> float:
        """Determine document type and return appropriate weight"""
        doc_name_lower = document_name.lower()
        
        for doc_type, weight in self.doc_type_weights.items():
            if doc_type in doc_name_lower:
                return weight
        
        return self.doc_type_weights['default']
    
    def rerank(self, query: str, retrieved_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply hybrid reranking combining multiple relevance signals.
        
        Args:
            query (str): User query for keyword overlap calculation
            retrieved_results (dict): Raw results from ChromaDB
            
        Returns:
            List[Dict]: Reranked results with hybrid scores
        """
        scored_chunks = []
        documents = retrieved_results.get('documents', [[]])[0]
        metadatas = retrieved_results.get('metadatas', [[]])[0]
        distances = retrieved_results.get('distances', [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # Base similarity score (convert distance to similarity)
            base_score = 1.0 - dist
            
            # Calculate enhancement factors
            doc_name = meta.get("document_name", "")
            recency_bonus = self._calculate_recency_score(doc_name)
            keyword_bonus = self._calculate_keyword_overlap(query, doc)
            doc_type_weight = self._get_document_type_weight(doc_name)
            
            # Combine scores
            final_score = base_score * recency_bonus * keyword_bonus * doc_type_weight
            
            chunk_data = {
                "document": doc,
                "metadata": meta,
                "distance": dist,
                "rerank_score": final_score,
                "score_breakdown": {
                    "base_similarity": base_score,
                    "recency_bonus": recency_bonus,
                    "keyword_bonus": keyword_bonus,
                    "doc_type_weight": doc_type_weight
                }
            }
            scored_chunks.append(chunk_data)
        
        # Sort by final score (descending)
        reranked = sorted(scored_chunks, key=lambda x: x["rerank_score"], reverse=True)
        
        logging.debug(f"HybridReranker: Reranked {len(reranked)} chunks")
        return reranked
    
    def get_version_info(self) -> Dict[str, str]:
        return {
            "version": "2.0 - Hybrid",
            "features": "Vector similarity + recency + keyword overlap + document type weighting",
            "overhead": "Low (~10ms)",
            "use_case": "Improved relevance with multiple ranking signals"
        }


class RerankerFactory:
    """Factory class to create rerankers"""
    
    @staticmethod
    def create_reranker(version: str) -> BaseReranker:
        """
        Create a reranker of the specified version.
        
        Args:
            version (str): "none" or "hybrid"
            
        Returns:
            BaseReranker: The requested reranker instance
        """
        version = version.lower()
        
        if version == "none":
            return NoReranker()
        elif version == "hybrid":
            return HybridReranker()
        else:
            raise ValueError(f"Unknown reranker version: {version}. Use 'none' or 'hybrid'")
    
    @staticmethod
    def list_versions() -> Dict[str, Dict[str, str]]:
        """List all available reranker versions"""
        return {
            "none": NoReranker().get_version_info(),
            "hybrid": HybridReranker().get_version_info()
        }


# Example usage
if __name__ == "__main__":
    # Test reranking
    test_query = "What is the circularity gap in 2024?"
    
    # Mock retrieved results
    mock_results = {
        'documents': [["Chunk about 2024 circularity", "Chunk about 2020 data", "Chunk about methodology"]],
        'metadatas': [[
            {"document_name": "cgr24", "page_in_document": 5},
            {"document_name": "cgr20", "page_in_document": 10}, 
            {"document_name": "methodology_guide", "page_in_document": 2}
        ]],
        'distances': [[0.1, 0.3, 0.2]]
    }
    
    print("=== Reranking Comparison ===")
    print(f"Query: {test_query}\n")
    
    # Test no reranking
    no_reranker = NoReranker()
    no_rerank_results = no_reranker.rerank(test_query, mock_results)
    print("No Reranking:")
    for i, result in enumerate(no_rerank_results):
        print(f"  {i+1}. {result['metadata']['document_name']} (score: {result['rerank_score']:.3f})")
    
    print()
    
    # Test hybrid reranking
    hybrid_reranker = HybridReranker()
    hybrid_results = hybrid_reranker.rerank(test_query, mock_results)
    print("Hybrid Reranking:")
    for i, result in enumerate(hybrid_results):
        print(f"  {i+1}. {result['metadata']['document_name']} (score: {result['rerank_score']:.3f})")
        breakdown = result['score_breakdown']
        print(f"      Base: {breakdown['base_similarity']:.3f}, Recency: {breakdown['recency_bonus']:.3f}, Keywords: {breakdown['keyword_bonus']:.3f}")
