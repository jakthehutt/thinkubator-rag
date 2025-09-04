import os
# import sys # Removed, relying on proper package installation and environment setup
import logging
# from dotenv import load_dotenv # Removed, as config.py handles this

# Configure logging for the ingestion script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file # Removed, as config.py handles this
# load_dotenv()

# Adjust the path to import RAGPipeline correctly
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
