import os
# from dotenv import load_dotenv
import logging

# load_dotenv() # This will be handled by the application entry points

# --- Paths ---
# BASE_DIR should be the project root
# This file is at src/backend/chain/config.py
# So, to get to the project root, we go up three levels.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

PROMPT_DIR = os.path.join(PROJECT_ROOT, "src", "backend", "prompt")
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "chroma_db")

CHUNKING_PROMPT_PATH = os.path.join(PROMPT_DIR, "chunking_prompt.txt")
CHUNK_SUMMARY_PROMPT_PATH = os.path.join(PROMPT_DIR, "chunk_summary_prompt.txt")
DOCUMENT_SUMMARY_PROMPT_PATH = os.path.join(PROMPT_DIR, "document_summary_prompt.txt")
GENERATION_SYSTEM_PROMPT_PATH = os.path.join(PROMPT_DIR, "generation_system_prompt.txt")

# --- Gemini Models ---
GEMINI_GENERATIVE_MODEL = "gemini-pro"
GEMINI_EMBEDDING_MODEL = "models/embedding-001"

# --- Other Config ---
DEFAULT_TOP_K_CHUNKS = 5

# --- API KEYS ---
# The API key is now fetched directly in the RAGPipeline class for robustness.
# GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
