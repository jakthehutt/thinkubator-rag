import os
import pypdf
import google.generativeai as genai
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging
import re
from typing import List

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
    def __init__(self,
                 api_key: str = None,
                 chroma_path: str = CHROMA_DB_PATH,
                 chunking_prompt_path: str = CHUNKING_PROMPT_PATH,
                 chunk_summary_prompt_path: str = CHUNK_SUMMARY_PROMPT_PATH,
                 document_summary_prompt_path: str = DOCUMENT_SUMMARY_PROMPT_PATH,
                 generation_system_prompt_path: str = GENERATION_SYSTEM_PROMPT_PATH):
        
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

            metadata = {
                "document_name": document_name,
                "page_in_document": page_in_document,
                "summary_of_chunk": chunk_summary,
                "summary_of_document": document_summary,
                "general_metadata": general_metadata.copy() # Ensure a copy to avoid mutation
            }
            # Generate a unique ID for each chunk. For updates, this ID will be crucial.
            chunk_id = f"{document_name}_{page_in_document}_{chunk_idx}"
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

    def _get_page_number_for_chunk(self, chunk_text: str, page_texts_with_num: list[tuple[int, str]]) -> int | None:
        """Heuristically determines the primary page number for a given chunk.
        This is a simple heuristic and might not be accurate for chunks spanning multiple pages
        or very short, common phrases.
        """
        # Remove chunk tags before searching in page content
        cleaned_chunk_text = chunk_text.replace("<chunk>", "").replace("</chunk>", "").strip()

        for page_num, page_content in page_texts_with_num:
            if cleaned_chunk_text in page_content.strip():
                return page_num
        return None

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
        """Placeholder for pre-query transformation (e.g., query rewriting, expansion).
        
        Suggestions for advanced implementations:
        - Use an LLM to rewrite the query for better retrieval.
        - Expand the query with synonyms or related terms.
        - Decompose complex queries into simpler sub-queries.
        """
        return query

    def _rerank_chunks(self, query: str, retrieved_results: dict) -> list[dict]:
        """A simple reranking algorithm based on the distance from ChromaDB.
        The results are already sorted by distance by ChromaDB, so this method primarily
        formats the output and serves as a placeholder for more complex reranking.
        
        Suggestions for advanced implementations:
        - Implement a more sophisticated reranking model (e.g., a cross-encoder).
        - Use hybrid search results (keyword + vector) for reranking.
        - Incorporate metadata (e.g., document importance, recency) into the reranking score.
        """
        reranked_chunks = []
        documents = retrieved_results.get('documents', [[]])[0]
        metadatas = retrieved_results.get('metadatas', [[]])[0]
        distances = retrieved_results.get('distances', [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            reranked_chunks.append({
                "document": doc,
                "metadata": meta,
                "distance": dist
            })
        
        return reranked_chunks

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

            context_chunks = []
            source_references = set()
            document_summary = "No document summary available."

            for i, chunk_info in enumerate(retrieved_chunks_info):
                doc_content = chunk_info["document"]
                meta = chunk_info["metadata"]
                
                doc_name = meta.get("document_name", "Unknown Document")
                page_num = meta.get("page_in_document", "Unknown Page")
                source_ref = f"{doc_name} (Page: {page_num})"
                source_references.add(source_ref)

                context_chunks.append(f"Content from {source_ref}:\n\"\"\"\n{doc_content}\n\"\"\"\n")
                
                if i == 0 and "summary_of_document" in meta:
                    document_summary = meta["summary_of_document"]
            
            context_string = "\n\n".join(context_chunks)
            sources_string = "; ".join(sorted(list(source_references)))

            full_prompt = f"""{self.generation_system_prompt}\n\nDocument Summary: {document_summary}\n\nRetrieved Information:\n{context_string}\n\nSources: {sources_string}\n\nUser Request: {user_query}\n\nAnswer:"""

            response = self.generative_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error generating answer for query \"{user_query}\": {e}")
            raise
