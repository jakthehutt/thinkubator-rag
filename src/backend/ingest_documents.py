import os
import sys
from dotenv import load_dotenv
import logging
# from dotenv import load_dotenv # Removed, as config.py handles this

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
    # The RAGPipeline constructor handles GEMINI_API_KEY check and genai.configure(api_key=...) internally
    pipeline = RAGPipeline(chroma_path=chroma_db_path)
    
    # Ensure the ChromaDB directory exists
    os.makedirs(chroma_db_path, exist_ok=True)

    # Ensure the PDF directory exists
    if not os.path.exists(pdf_directory):
        logging.error(f"PDF directory not found: {pdf_directory}")
        raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")

    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):  # Process only PDF files
            pdf_path = os.path.join(pdf_directory, filename)
            document_name = filename.replace(".pdf", "") # Use filename as document name
            logging.info(f"Ingesting {document_name} from {pdf_path}...")
            
            try:
                # General metadata can be extended here if needed
                pipeline.ingest_pdf(pdf_path, document_name, general_metadata={"source_directory": pdf_directory})
                logging.info(f"Successfully ingested {document_name}.")
            except Exception as e:
                logging.error(f"Error ingesting {document_name}: {e}")

if __name__ == "__main__":
    ingest_all_pdfs()
