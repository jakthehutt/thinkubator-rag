import os
import pypdf
import google.generativeai as genai
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction # This will be replaced with Gemini embedding

class RAGPipeline:
    def __init__(self, 
                 chroma_path: str = "./data/processed/chroma_db",
                 chunking_prompt_path: str = "./src/backend/prompt/chunking_prompt.txt",
                 chunk_summary_prompt_path: str = "./src/backend/prompt/chunk_summary_prompt.txt",
                 document_summary_prompt_path: str = "./src/backend/prompt/document_summary_prompt.txt"):
        
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.generative_model = genai.GenerativeModel("gemini-pro")
        
        # Create or get the collection with the custom embedding function
        self.collection = self.chroma_client.get_or_create_collection(
            name="rag_chunks",
            embedding_function=self.embedding_model # Use the Gemini embedding model
        )
        
        self.chunking_prompt = self._load_prompt(chunking_prompt_path)
        self.chunk_summary_prompt = self._load_prompt(chunk_summary_prompt_path)
        self.document_summary_prompt = self._load_prompt(document_summary_prompt_path)

    def _load_prompt(self, file_path: str) -> str:
        with open(file_path, 'r') as f:
            return f.read().strip()

    def ingest_pdf(self, pdf_path: str, document_name: str, general_metadata: dict = None):
        if general_metadata is None:
            general_metadata = {}

        full_document_text, page_texts_with_num = self._extract_text_from_pdf(pdf_path)

        document_summary = self._summarize_document(full_document_text)

        chunks = self._chunk_text(full_document_text)

        chunks_to_store = [] # List of (chunk_text, metadata, id)

        for chunk_idx, chunk_text in enumerate(chunks):
            chunk_summary = self._summarize_chunk(chunk_text)
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
        
        self._store_chunks_in_chroma(chunks_to_store)

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

    def _chunk_text(self, text: str) -> list[str]:
        prompt = self.chunking_prompt.format(text=text)
        response = self.generative_model.generate_content(prompt)
        return response.text.split("\n\n")

    def _summarize_chunk(self, chunk_text: str) -> str:
        prompt = self.chunk_summary_prompt.format(chunk_text=chunk_text)
        response = self.generative_model.generate_content(prompt)
        return response.text

    def _summarize_document(self, document_text: str) -> str:
        prompt = self.document_summary_prompt.format(document_text=document_text)
        response = self.generative_model.generate_content(prompt)
        return response.text

    def _store_chunks_in_chroma(self, chunks_with_metadata: list[tuple[str, dict, str]]):
        documents = [item[0] for item in chunks_with_metadata]
        metadatas = [item[1] for item in chunks_with_metadata]
        ids = [item[2] for item in chunks_with_metadata]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Stored {len(documents)} chunks in ChromaDB.")

    def _query_database(self, query_texts: list[str], n_results: int = 5) -> dict:
        """Retrieves the most relevant chunks from ChromaDB based on the query."""
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        return results

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
        
        # In a simple case, ChromaDB already returns sorted by distance, so we just return.
        # For more complex reranking, custom sorting logic would go here.
        return reranked_chunks

    def retrieve(self, query: str, n_results: int = 5) -> list[dict]:
        """Main method to retrieve, pre-process, and rerank document chunks."""
        transformed_query = self._pre_query_transformation(query)
        retrieved_results = self._query_database([transformed_query], n_results)
        reranked_chunks = self._rerank_chunks(query, retrieved_results)
        return reranked_chunks
