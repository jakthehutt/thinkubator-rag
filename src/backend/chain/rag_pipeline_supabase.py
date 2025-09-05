#!/usr/bin/env python3
"""
Updated RAG Pipeline using Supabase vector store instead of ChromaDB.
Maintains compatibility with existing interface while using Supabase for vector storage.
"""

import os
import pypdf
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging
import re
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.backend.chain.query_processor import QueryProcessorFactory, BaseQueryProcessor
from src.backend.chain.reranker import RerankerFactory, BaseReranker
from src.backend.vector_store.supabase_vector_store import SupabaseVectorStore

from src.backend.chain.config import (
    CHUNKING_PROMPT_PATH,
    CHUNK_SUMMARY_PROMPT_PATH,
    DOCUMENT_SUMMARY_PROMPT_PATH,
    GENERATION_SYSTEM_PROMPT_PATH,
    GEMINI_GENERATIVE_MODEL,
    GEMINI_EMBEDDING_MODEL,
    DEFAULT_TOP_K_CHUNKS
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RAGPipelineSupabase:
    """
    Supabase-powered RAG Pipeline with configurable query processing and reranking.
    
    Features:
    - Supabase vector storage with pgvector
    - Configurable query processors (basic, enhanced, advanced)
    - Configurable rerankers (none, hybrid)
    - Comprehensive PDF ingestion and chunking
    - Gemini-powered generation with numbered citations
    - Compatible interface with ChromaDB version for easy migration
    
    Usage:
        # Default setup (basic processing, no reranking)
        pipeline = RAGPipelineSupabase(api_key="your_key")
        
        # Enhanced processing with hybrid reranking
        pipeline = RAGPipelineSupabase(
            api_key="your_key",
            query_processor_version="enhanced",
            reranker_version="hybrid"
        )
    """
    
    def __init__(self,
                 api_key: str = None,
                 table_name: str = "document_embeddings",
                 embedding_dimension: int = 768,
                 chunking_prompt_path: str = CHUNKING_PROMPT_PATH,
                 chunk_summary_prompt_path: str = CHUNK_SUMMARY_PROMPT_PATH,
                 document_summary_prompt_path: str = DOCUMENT_SUMMARY_PROMPT_PATH,
                 generation_system_prompt_path: str = GENERATION_SYSTEM_PROMPT_PATH,
                 query_processor_version: str = "basic",
                 reranker_version: str = "none"):
        
        # --- Configure the Gemini API at runtime ---
        # Priority:
        # 1. API key passed directly to the constructor.
        # 2. API key from the environment variable.
        # 3. Fallback to Application Default Credentials (ADC).
        effective_api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if effective_api_key:
            genai.configure(api_key=effective_api_key)
            # Configure the embedding model with the API key
            self.langchain_embeddings = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=effective_api_key
            )
        else:
            # If no API key is found, we log a message and assume ADC is configured.
            logging.info("No direct API key or environment variable found. Falling back to Application Default Credentials.")
            self.langchain_embeddings = GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEDDING_MODEL)

        # Initialize Supabase vector store
        try:
            self.vector_store = SupabaseVectorStore(
                table_name=table_name,
                embedding_dimension=embedding_dimension
            )
            logging.info(f"Initialized Supabase vector store with table '{table_name}'")
        except Exception as e:
            logging.error(f"Failed to initialize Supabase vector store: {e}")
            raise

        self.generative_model = genai.GenerativeModel(GEMINI_GENERATIVE_MODEL)
        
        self.chunking_prompt = self._load_prompt(chunking_prompt_path)
        self.chunk_summary_prompt = self._load_prompt(chunk_summary_prompt_path)
        self.document_summary_prompt = self._load_prompt(document_summary_prompt_path)
        self.generation_system_prompt = self._load_prompt(generation_system_prompt_path)
        
        # --- Initialize Query Processor and Reranker ---
        try:
            self.query_processor = QueryProcessorFactory.create_processor(
                query_processor_version, 
                api_key=effective_api_key
            )
            self.reranker = RerankerFactory.create_reranker(reranker_version)
            
            logging.info(f"Initialized with {self.query_processor.get_version_info()['version']} query processor")
            logging.info(f"Initialized with {self.reranker.get_version_info()['version']} reranker")
            
        except Exception as e:
            logging.error(f"Error initializing query processor or reranker: {e}")
            # Fallback to basic versions
            self.query_processor = QueryProcessorFactory.create_processor("basic")
            self.reranker = RerankerFactory.create_reranker("none")
            logging.warning("Falling back to basic query processor and no reranker")

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the current pipeline configuration.
        
        Returns:
            Dict: Pipeline configuration and component information
        """
        vector_store_info = self.vector_store.get_collection_info()
        return {
            "vector_store": "Supabase with pgvector",
            "query_processor": self.query_processor.get_version_info(),
            "reranker": self.reranker.get_version_info(),
            "embedding_model": GEMINI_EMBEDDING_MODEL,
            "generative_model": GEMINI_GENERATIVE_MODEL,
            "table_info": vector_store_info
        }

    def _load_prompt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logging.error(f"Prompt file not found: {file_path}")
            raise

    def ingest_pdf(self, pdf_path: str, document_name: str, general_metadata: dict = None):
        """
        Ingest a PDF document into the Supabase vector store.
        
        Args:
            pdf_path: Path to the PDF file
            document_name: Name/identifier for the document
            general_metadata: Additional metadata to attach to all chunks
        """
        if general_metadata is None:
            general_metadata = {}

        try:
            full_document_text, page_texts_with_num = self._extract_text_from_pdf(pdf_path)
        except Exception as e:
            logging.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise

        try:
            document_summary = self._summarize_document(full_document_text)
        except Exception as e:
            logging.error(f"Error summarizing document {document_name}: {e}")
            raise

        try:
            chunks = self._chunk_text(full_document_text)
        except Exception as e:
            logging.error(f"Error chunking document {document_name}: {e}")
            raise

        # Prepare chunks for vector storage
        documents = []
        embeddings = []
        metadatas = []
        ids = []

        for chunk_idx, chunk_text in enumerate(chunks):
            try:
                chunk_summary = self._summarize_chunk(chunk_text)
            except Exception as e:
                logging.warning(f"Could not summarize chunk {chunk_idx} from {document_name}: {e}")
                chunk_summary = ""

            page_in_document = self._get_page_number_for_chunk(chunk_text, page_texts_with_num)

            # Create metadata
            metadata = {
                "document_name": document_name,
                "page_in_document": page_in_document,
                "page_approximation": True,  # Indicate page number is estimated
                "summary_of_chunk": chunk_summary if chunk_summary else "",
                "summary_of_document": document_summary if document_summary else "",
                "created_at": datetime.now().isoformat(),
            }
            
            # Add general_metadata fields with a prefix to avoid naming conflicts
            for key, value in general_metadata.items():
                if value is not None:
                    metadata[f"meta_{key}"] = str(value)
                else:
                    metadata[f"meta_{key}"] = ""

            # Generate embeddings for the chunk
            try:
                chunk_embedding = self.langchain_embeddings.embed_query(chunk_text)
            except Exception as e:
                logging.error(f"Error generating embedding for chunk {chunk_idx}: {e}")
                raise

            # Generate a unique ID for each chunk
            page_for_id = page_in_document if page_in_document is not None else 0
            chunk_id = f"{document_name}_{page_for_id}_{chunk_idx}"

            documents.append(chunk_text)
            embeddings.append(chunk_embedding)
            metadatas.append(metadata)
            ids.append(chunk_id)

        # Store all chunks in Supabase
        try:
            self.vector_store.add_documents(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logging.info(f"Successfully ingested {len(chunks)} chunks from {document_name}")
        except Exception as e:
            logging.error(f"Error storing chunks for {document_name} in Supabase: {e}")
            raise

    def _extract_text_from_pdf(self, pdf_path: str) -> tuple[str, list[tuple[int, str]]]:
        text = ""
        page_texts_with_num = []
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page_content = reader.pages[page_num].extract_text()
                text += page_content + "\n\n"
                page_texts_with_num.append((page_num + 1, page_content))
        return text, page_texts_with_num

    def _chunk_text(self, text: str) -> list[str]:
        prompt = self.chunking_prompt.format(text=text)
        try:
            response = self.generative_model.generate_content(prompt)
            # Use regex to find content between <chunk> and </chunk> tags
            chunks = re.findall(r'(<chunk>.*?</chunk>)', response.text, re.DOTALL)
            if not chunks:
                logging.warning("No chunks found using the specified tags. Returning raw split by newline.")
                return response.text.split("\n\n") # Fallback
            return chunks
        except Exception as e:
            logging.error(f"Error during text chunking with Gemini: {e}")
            raise

    def _summarize_chunk(self, chunk_text: str) -> str:
        prompt = self.chunk_summary_prompt.format(chunk_text=chunk_text)
        try:
            response = self.generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error summarizing chunk with Gemini: {e}")
            raise

    def _summarize_document(self, document_text: str) -> str:
        prompt = self.document_summary_prompt.format(document_text=document_text)
        try:
            response = self.generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error summarizing document with Gemini: {e}")
            raise

    def _get_page_number_for_chunk(self, chunk_text: str, page_texts_with_num: list[tuple[int, str]]) -> int:
        """
        Determines the most likely page number for a given chunk using improved heuristics.
        Returns the page number with a note that it's an approximation.
        """
        # Remove chunk tags and clean text
        cleaned_chunk_text = chunk_text.replace("<chunk>", "").replace("</chunk>", "").strip()
        
        # If chunk is very short, return first page as fallback
        if len(cleaned_chunk_text) < 50:
            return 1
        
        # Extract a meaningful sample from the beginning of the chunk for matching
        chunk_sample = cleaned_chunk_text[:200].strip()
        
        best_match_page = 1
        best_match_score = 0
        
        for page_num, page_content in page_texts_with_num:
            # Calculate overlap score
            if chunk_sample in page_content:
                # Direct match - highest score
                return page_num
            
            # Calculate word overlap for fuzzy matching
            chunk_words = set(chunk_sample.lower().split())
            page_words = set(page_content.lower().split())
            
            if chunk_words and page_words:
                overlap = len(chunk_words.intersection(page_words))
                overlap_ratio = overlap / len(chunk_words)
                
                if overlap_ratio > best_match_score:
                    best_match_score = overlap_ratio
                    best_match_page = page_num
        
        return best_match_page

    def _pre_query_transformation(self, query: str) -> str:
        """
        Apply query preprocessing using the configured processor.
        
        Args:
            query (str): Raw user query
            
        Returns:
            str: Processed query optimized for retrieval
        """
        try:
            processed_query = self.query_processor.process_query(query)
            logging.debug(f"Query preprocessing: '{query}' → '{processed_query}'")
            return processed_query
        except Exception as e:
            logging.error(f"Error in query preprocessing: {e}")
            # Fallback to original query
            return query

    def _rerank_chunks(self, query: str, supabase_results: list) -> list[dict]:
        """
        Apply reranking using the configured reranker.
        Convert Supabase results to ChromaDB-like format for reranking compatibility.
        
        Args:
            query (str): Original user query for relevance scoring
            supabase_results (list): Results from Supabase vector store
            
        Returns:
            List[dict]: Reranked chunks with enhanced relevance scores
        """
        try:
            # Convert Supabase results to ChromaDB-like format for reranker compatibility
            chroma_like_results = {
                'documents': [[doc.content for doc in supabase_results]],
                'metadatas': [[doc.metadata for doc in supabase_results]],
                'distances': [[doc.distance for doc in supabase_results]]
            }
            
            reranked_chunks = self.reranker.rerank(query, chroma_like_results)
            logging.debug(f"Reranking applied: {len(reranked_chunks)} chunks processed")
            return reranked_chunks
            
        except Exception as e:
            logging.error(f"Error in reranking: {e}")
            # Fallback to simple formatting
            fallback_chunks = []
            for doc in supabase_results:
                fallback_chunks.append({
                    "document": doc.content,
                    "metadata": doc.metadata,
                    "distance": doc.distance
                })
            return fallback_chunks

    def retrieve(self, query: str, n_results: int = DEFAULT_TOP_K_CHUNKS) -> list[dict]:
        """
        Retrieve relevant chunks for a query using Supabase vector store.
        
        Args:
            query: User query
            n_results: Number of chunks to retrieve
            
        Returns:
            List of chunk information dictionaries
        """
        try:
            # Apply query transformation
            transformed_query = self._pre_query_transformation(query)
            
            # Generate embedding for the query
            query_embedding = self.langchain_embeddings.embed_query(transformed_query)
            
            # Perform similarity search in Supabase
            supabase_results = self.vector_store.similarity_search(
                query_embedding=query_embedding,
                k=n_results
            )
            
            # Apply reranking
            reranked_chunks = self._rerank_chunks(query, supabase_results)
            
            return reranked_chunks
            
        except Exception as e:
            logging.error(f"Error during retrieval for query \"{query}\": {e}")
            raise

    def generate_answer(self, user_query: str, top_k_chunks: int = DEFAULT_TOP_K_CHUNKS) -> str:
        """
        Generate an answer to a user query using retrieved chunks.
        
        Args:
            user_query: The user's question
            top_k_chunks: Number of top chunks to use for generation
            
        Returns:
            Generated answer with citations
        """
        try:
            retrieved_chunks_info = self.retrieve(user_query, n_results=top_k_chunks)

            if not retrieved_chunks_info:
                return "I do not have enough information to answer your question. No relevant documents were found."

            # Build numbered source list and context
            numbered_sources = []
            context_chunks = []
            document_summary = "No document summary available."

            for i, chunk_info in enumerate(retrieved_chunks_info, 1):
                doc_content = chunk_info["document"]
                meta = chunk_info["metadata"]

                doc_name = meta.get("document_name", "Unknown Document")
                page_num = meta.get("page_in_document", 1)
                is_approximation = meta.get("page_approximation", True)
                
                # Format page number with approximation indicator
                page_display = f"~{page_num}" if is_approximation else str(page_num)
                
                source_ref = f"[{i}] {doc_name} (Page {page_display})"
                numbered_sources.append(source_ref)

                # Add numbered reference to content
                context_chunks.append(f"Source [{i}]: {doc_name} (Page {page_display})\nContent:\n\"\"\"\n{doc_content}\n\"\"\"\n")

                if i == 1 and "summary_of_document" in meta:
                    document_summary = meta["summary_of_document"]

            context_string = "\n\n".join(context_chunks)
            sources_list = "\n".join(numbered_sources)

            full_prompt = f"""{self.generation_system_prompt}

DOCUMENT OVERVIEW: {document_summary}

AVAILABLE INFORMATION:
{context_string}

INSTRUCTIONS FOR CITATION:
- Use numbered citations [1], [2], etc. in your answer
- End your response with a "Sources:" section listing the numbered references
- Remember that page numbers are approximations (marked with ~)

USER QUESTION: {user_query}

ANSWER:"""

            response = self.generative_model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            logging.error(f"Error generating answer for query \"{user_query}\": {e}")
            raise
