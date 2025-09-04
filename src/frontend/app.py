import streamlit as st
import os
import sys
from dotenv import load_dotenv

# --- Robustly find and load the .env file ---
# This script is in src/frontend/app.py
# The project root is two levels up from this script's directory.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    # This will be visible in the Streamlit UI if the .env file is missing
    print(f"Warning: .env file not found at {dotenv_path}")

# Adjust the path to import RAGPipeline correctly
# Add the project root to the path, so 'from src...' works.
sys.path.insert(0, project_root)

from src.backend.chain.rag_pipeline import RAGPipeline
from src.backend.chain.config import GEMINI_API_KEY

def main():
    st.set_page_config(page_title="Thinkubator RAG Pipeline Explorer", layout="wide")

    st.title("Thinkubator RAG Pipeline Explorer")
    st.markdown("""
        This application allows you to test and visualize the different components of the RAG (Retrieval-Augmented Generation) pipeline.
        Enter a query below to see the retrieved chunks, the generated system prompt, and the final answer from the LLM.
    """)

    # Check for GEMINI_API_KEY
    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY environment variable not set. Please set it in your .env file at the project root.")
        st.stop()

    # Instantiate the RAGPipeline
    # This might take a moment as it loads the embedding model
    with st.spinner("Initializing RAG Pipeline..."):
        try:
            pipeline = RAGPipeline()
            st.session_state.pipeline = pipeline
            st.success("RAG Pipeline initialized successfully.")
        except Exception as e:
            st.error(f"Error initializing RAG Pipeline: {e}")
            st.stop()
    
    # User input
    user_query = st.text_input("Enter your query:", "What is the circularity gap?")

    if st.button("Generate Answer"):
        if 'pipeline' in st.session_state and user_query:
            pipeline = st.session_state.pipeline
            
            with st.spinner("Retrieving chunks from ChromaDB..."):
                try:
                    retrieved_chunks_info = pipeline.retrieve(user_query, n_results=5)
                except Exception as e:
                    st.error(f"Error retrieving chunks: {e}")
                    retrieved_chunks_info = []

            st.header("1. Retrieved Chunks and Metadata")
            if retrieved_chunks_info:
                with st.expander("View Retrieved Chunks", expanded=True):
                    for i, chunk_info in enumerate(retrieved_chunks_info):
                        st.subheader(f"Chunk {i+1}")
                        st.text(f"Source: {chunk_info['metadata'].get('document_name', 'N/A')} (Page: {chunk_info['metadata'].get('page_in_document', 'N/A')})")
                        st.text(f"Distance: {chunk_info['distance']:.4f}")
                        st.text_area("Chunk Content", chunk_info['document'], height=200, key=f"chunk_{i}")
                        st.json(chunk_info['metadata'])
            else:
                st.warning("No chunks were retrieved for this query.")

            with st.spinner("Generating system prompt and final answer..."):
                try:
                    # Construct the full prompt (similar to generate_answer logic)
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

                    full_prompt = f"{pipeline.generation_system_prompt}\n\nDocument Summary: {document_summary}\n\nRetrieved Information:\n{context_string}\n\nSources: {sources_string}\n\nUser Request: {user_query}\n\nAnswer:"
                    
                    st.header("2. System Prompt")
                    with st.expander("View Full System Prompt"):
                        st.text_area("Full Prompt Sent to LLM", full_prompt, height=400)

                    # Generate the final answer
                    generated_answer = pipeline.generate_answer(user_query, top_k_chunks=5)
                    
                    st.header("3. Final Generated Answer")
                    st.markdown(generated_answer)

                except Exception as e:
                    st.error(f"Error generating answer: {e}")

        elif not user_query:
            st.warning("Please enter a query.")

if __name__ == "__main__":
    main()
