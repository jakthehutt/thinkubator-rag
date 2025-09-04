import os
import sys
import json
from dotenv import load_dotenv
import logging
from datetime import datetime

# --- Robustly find and load the .env file ---
# This script is in src/backend/ingest_documents.py
# The project root is two levels up from this script's directory.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    logging.warning(f".env file not found at {dotenv_path}. The script might fail if GEMINI_API_KEY is not set.")

# Adjust the path to import RAGPipeline correctly
# Add the project root to the path, so 'from src...' works.
sys.path.insert(0, project_root)

# Configure logging for the ingestion script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the project root to the Python path
# This is necessary for the script to find the backend modules
# Get the directory of the current script: /path/to/project_root/src/backend
# script_dir = os.path.dirname(os.path.abspath(__file__)) # Removed
# Go up two levels to reach the project root: /path/to/project_root
# project_root = os.path.abspath(os.path.join(script_dir, '..', '..')) # Removed
# sys.path.insert(0, project_root) # Removed

# Rely on direct import now that package structure should be resolvable by python path
from src.backend.chain.rag_pipeline import RAGPipeline
from src.backend.chain.config import (
    CHROMA_DB_PATH,
)

def ingest_all_pdfs(pdf_directory: str = "./data/pdfs", chroma_db_path: str = CHROMA_DB_PATH):
    """
    Ingest all PDFs from the specified directory using the RAGPipeline class.
    The RAGPipeline.ingest_pdf method already handles all the processing.
    """
    logging.info("Initializing RAG Pipeline...")
    
    # Get the API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment. Please check your .env file.")
        raise ValueError("GEMINI_API_KEY is required for ingestion.")
    
    logging.info("API key found, initializing pipeline...")
    pipeline = RAGPipeline(api_key=api_key, chroma_path=chroma_db_path)
    
    # Ensure directories exist
    os.makedirs(chroma_db_path, exist_ok=True)
    if not os.path.exists(pdf_directory):
        logging.error(f"PDF directory not found: {pdf_directory}")
        raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")

    # Get list of PDF files
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]
    total_files = len(pdf_files)
    
    logging.info(f"Found {total_files} PDF files to process")
    
    successful = 0
    failed = 0
    
    for i, filename in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_directory, filename)
        document_name = filename.replace(".pdf", "")
        
        logging.info(f"[{i}/{total_files}] Processing: {document_name}")
        
        try:
            # Use the RAGPipeline's built-in ingest_pdf method
            # It handles: extraction, chunking, summarization, and ChromaDB storage
            general_metadata = {
                "source_file": filename,
                "source_directory": pdf_directory,
                "processed_at": datetime.now().isoformat()
            }
            
            pipeline.ingest_pdf(pdf_path, document_name, general_metadata=general_metadata)
            successful += 1
            logging.info(f"✅ Successfully processed: {document_name}")
            
        except Exception as e:
            failed += 1
            logging.error(f"❌ Failed to process {document_name}: {e}")
    
    # Final summary
    logging.info(f"""
    📊 INGESTION SUMMARY:
    ✅ Successful: {successful}/{total_files}
    ❌ Failed: {failed}/{total_files}
    
    The ChromaDB now contains chunks from {successful} documents.
    You can now query the RAG pipeline!
    """)

if __name__ == "__main__":
    ingest_all_pdfs()
