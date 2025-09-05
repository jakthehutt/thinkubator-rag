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

    env_api_key = os.environ.get("GEMINI_API_KEY")
    if not env_api_key:
        st.error("GEMINI_API_KEY not found in .env file. Please set it to proceed.")
        st.stop()

    if 'rag_pipeline' not in st.session_state or st.session_state.get('api_key') != env_api_key:
        with st.spinner("Initializing RAG Pipeline..."):
            try:
                pipeline = RAGPipeline(api_key=env_api_key)
                st.session_state.rag_pipeline = pipeline
                st.session_state.api_key = env_api_key
                st.sidebar.success("Pipeline Initialized!")
            except Exception as e:
                st.error(f"Error initializing RAG Pipeline: {e}")
                st.stop()
    
    st.markdown("""
    This application allows you to test and visualize the different components of the RAG (Retrieval-Augmented Generation) pipeline. 
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
