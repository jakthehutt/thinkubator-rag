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
# from src.backend.chain.config import GEMINI_API_KEY # No longer needed, handled in pipeline

def main():
    st.set_page_config(page_title="Thinkubator RAG Pipeline Explorer", layout="wide")

    st.title("Thinkubator RAG Pipeline Explorer")

    # --- API Key Input in Sidebar ---
    st.sidebar.header("Configuration")
    api_key_input = st.sidebar.text_input(
        "Enter your Gemini API Key", 
        type="password",
        help="Get your key from Google AI Studio. The app will use this key to initialize the pipeline."
    )

    # --- Pipeline Initialization ---
    # The pipeline is now initialized only after a key is provided.
    if api_key_input:
        if 'rag_pipeline' not in st.session_state or st.session_state.api_key != api_key_input:
            with st.spinner("Initializing RAG Pipeline with new API Key..."):
                try:
                    # Pass the key directly to the pipeline
                    pipeline = RAGPipeline(api_key=api_key_input)
                    st.session_state.rag_pipeline = pipeline
                    st.session_state.api_key = api_key_input # Store the key to detect changes
                    st.sidebar.success("Pipeline Initialized!")
                except Exception as e:
                    st.error(f"Error initializing RAG Pipeline: {e}")
                    st.stop()
    
    # --- Main App Body ---
    st.markdown("""
    This application allows you to test and visualize the different components of the RAG (Retrieval-Augmented Generation) pipeline. 
    
    **Enter your Gemini API Key in the sidebar to begin.**
    """)

    # Only show the query interface if the pipeline is ready
    if 'rag_pipeline' in st.session_state:
        st.subheader("Query the RAG Pipeline")
        user_query = st.text_input("Enter your query:", "What is the circularity gap?")

        if st.button("Generate Answer"):
            if user_query:
                pipeline = st.session_state.rag_pipeline
                
                with st.spinner("Retrieving chunks, generating prompt, and getting answer..."):
                    try:
                        # ... (rest of the code for displaying results remains the same) ...
                        retrieved_chunks = pipeline.retrieve(user_query)
                        answer = pipeline.generate_answer(user_query)

                        st.divider()
                        st.header("Final Answer")
                        st.markdown(answer)

                        st.divider()
                        st.header("Retrieved Chunks and Metadata")
                        st.write("These are the top chunks retrieved from the database that were used to generate the answer.")
                        for i, chunk_info in enumerate(retrieved_chunks):
                            with st.expander(f"Chunk {i+1} (Source: {chunk_info['metadata'].get('document_name', 'N/A')}, Page: {chunk_info['metadata'].get('page_in_document', 'N/A')})"):
                                st.text(chunk_info['document'])
                                st.json(chunk_info['metadata'])

                    except Exception as e:
                        st.error(f"An error occurred during generation: {e}")

if __name__ == "__main__":
    main()
