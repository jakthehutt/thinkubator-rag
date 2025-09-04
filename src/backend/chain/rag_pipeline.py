import os
import pypdf
import google.generativeai as genai
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging
import re
from typing import List, Optional, Dict, Any

from src.backend.chain.query_processor import QueryProcessorFactory, BaseQueryProcessor
from src.backend.chain.reranker import RerankerFactory, BaseReranker

from src.backend.chain.config import (
    CHROMA_DB_PATH,
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

class ChromaEmbeddingWrapper:
    """Wrapper to make LangChain embeddings compatible with ChromaDB"""
    
    def __init__(self, langchain_embeddings):
        self.embeddings = langchain_embeddings
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """ChromaDB expects this signature"""
        return self.embeddings.embed_documents(input)
    
    def name(self) -> str:
        """ChromaDB expects this method"""
        return "google_generative_ai_embeddings"

class RAGPipeline:
    """
    Modular RAG Pipeline with configurable query processing and reranking.
    
    Features:
    - Configurable query processors (basic, enhanced, advanced)
    - Configurable rerankers (none, hybrid)
    - Comprehensive PDF ingestion and chunking
    - ChromaDB vector storage with metadata
    - Gemini-powered generation with numbered citations
    
    Usage:
        # Default setup (basic processing, no reranking)
        pipeline = RAGPipeline(api_key="your_key")
        
        # Enhanced processing with hybrid reranking
        pipeline = RAGPipeline(
            api_key="your_key",
            query_processor_version="enhanced",
            reranker_version="hybrid"
        )
    """
    
    def __init__(self,
                 api_key: str = None,
                 chroma_path: str = CHROMA_DB_PATH,
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
            # Also configure the embedding model with the API key
            langchain_embeddings = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=effective_api_key
            )
            self.embedding_model = ChromaEmbeddingWrapper(langchain_embeddings)
        else:
            # If no API key is found, we log a message and assume ADC is configured.
            logging.info("No direct API key or environment variable found. Falling back to Application Default Credentials.")
            langchain_embeddings = GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEDDING_MODEL)
            self.embedding_model = ChromaEmbeddingWrapper(langchain_embeddings)

        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.generative_model = genai.GenerativeModel(GEMINI_GENERATIVE_MODEL)
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="rag_chunks",
            embedding_function=self.embedding_model # Use the wrapped embedding model
        )
        
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
        return {
            "query_processor": self.query_processor.get_version_info(),
            "reranker": self.reranker.get_version_info(),
            "embedding_model": GEMINI_EMBEDDING_MODEL,
            "generative_model": GEMINI_GENERATIVE_MODEL,
            "chroma_collection": "rag_chunks"
        }

    def _load_prompt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logging.error(f"Prompt file not found: {file_path}")
            raise

    def ingest_pdf(self, pdf_path: str, document_name: str, general_metadata: dict = None):
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

        chunks_to_store = [] # List of (chunk_text, metadata, id)

        for chunk_idx, chunk_text in enumerate(chunks):
            try:
                chunk_summary = self._summarize_chunk(chunk_text)
            except Exception as e:
                logging.warning(f"Could not summarize chunk {chunk_idx} from {document_name}: {e}")
                chunk_summary = ""

            page_in_document = self._get_page_number_for_chunk(chunk_text, page_texts_with_num)

            # Flatten general_metadata and ensure all values are ChromaDB compatible
            metadata = {
                "document_name": str(document_name),
                "page_in_document": int(page_in_document),
                "page_approximation": "true",  # Indicate page number is estimated
                "summary_of_chunk": str(chunk_summary) if chunk_summary else "",
                "summary_of_document": str(document_summary) if document_summary else "",
            }
            
            # Add general_metadata fields with a prefix to avoid naming conflicts
            for key, value in general_metadata.items():
                # Convert all values to strings and handle None values
                if value is not None:
                    metadata[f"meta_{key}"] = str(value)
                else:
                    metadata[f"meta_{key}"] = ""
            # Generate a unique ID for each chunk. For updates, this ID will be crucial.
            page_for_id = page_in_document if page_in_document is not None else 0
            chunk_id = f"{document_name}_{page_for_id}_{chunk_idx}"
            chunks_to_store.append((chunk_text, metadata, chunk_id))
        
        try:
            self._store_chunks_in_chroma(chunks_to_store)
        except Exception as e:
            logging.error(f"Error storing chunks for {document_name} in ChromaDB: {e}")
            raise

    def _extract_text_from_pdf(self, pdf_path: str) -> tuple[str, list[tuple[int, str]]]:
        text = ""
        page_texts_with_num = []
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page_content = reader.pages[page_num].extract_text()
                text += page_content + "\n\n"
                page_texts_with_num.append((page_num + 1, page_content)) # Store (page_number, text)
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
        # Use first 200 characters as they're most likely to be unique
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
        
        # Return best match (will be marked as approximation in metadata)
        return best_match_page

    def _store_chunks_in_chroma(self, chunks_with_metadata: list[tuple[str, dict, str]]):
        documents = [item[0] for item in chunks_with_metadata]
        metadatas = [item[1] for item in chunks_with_metadata]
        ids = [item[2] for item in chunks_with_metadata]

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logging.info(f"Stored {len(documents)} chunks in ChromaDB.")
        except Exception as e:
            logging.error(f"Failed to add chunks to ChromaDB: {e}")
            raise

    def _query_database(self, query_texts: list[str], n_results: int = DEFAULT_TOP_K_CHUNKS) -> dict:
        """Retrieves the most relevant chunks from ChromaDB based on the query."""
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            return results
        except Exception as e:
            logging.error(f"Error querying ChromaDB: {e}")
            raise

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

    def _rerank_chunks(self, query: str, retrieved_results: dict) -> list[dict]:
        """
        Apply reranking using the configured reranker.
        
        Args:
            query (str): Original user query for relevance scoring
            retrieved_results (dict): Raw results from ChromaDB
            
        Returns:
            List[dict]: Reranked chunks with enhanced relevance scores
        """
        try:
            reranked_chunks = self.reranker.rerank(query, retrieved_results)
            logging.debug(f"Reranking applied: {len(reranked_chunks)} chunks processed")
            return reranked_chunks
        except Exception as e:
            logging.error(f"Error in reranking: {e}")
            # Fallback to simple formatting
            fallback_chunks = []
            documents = retrieved_results.get('documents', [[]])[0]
            metadatas = retrieved_results.get('metadatas', [[]])[0]
            distances = retrieved_results.get('distances', [[]])[0]

            for doc, meta, dist in zip(documents, metadatas, distances):
                fallback_chunks.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist
                })
            return fallback_chunks

    def retrieve(self, query: str, n_results: int = DEFAULT_TOP_K_CHUNKS) -> list[dict]:
        try:
            transformed_query = self._pre_query_transformation(query)
            retrieved_results = self._query_database([transformed_query], n_results)
            reranked_chunks = self._rerank_chunks(query, retrieved_results)
            return reranked_chunks
        except Exception as e:
            logging.error(f"Error during retrieval for query \"{query}\": {e}")
            raise

    def generate_answer(self, user_query: str, top_k_chunks: int = DEFAULT_TOP_K_CHUNKS) -> str:
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
                is_approximation = meta.get("page_approximation", "true") == "true"
                
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
