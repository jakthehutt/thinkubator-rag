import os

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROMPT_DIR = os.path.join(BASE_DIR, "prompt")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "..", "..", "data", "processed", "chroma_db")

CHUNKING_PROMPT_PATH = os.path.join(PROMPT_DIR, "chunking_prompt.txt")
CHUNK_SUMMARY_PROMPT_PATH = os.path.join(PROMPT_DIR, "chunk_summary_prompt.txt")
DOCUMENT_SUMMARY_PROMPT_PATH = os.path.join(PROMPT_DIR, "document_summary_prompt.txt")
GENERATION_SYSTEM_PROMPT_PATH = os.path.join(PROMPT_DIR, "generation_system_prompt.txt")

# --- Gemini Models ---
GEMINI_GENERATIVE_MODEL = "gemini-pro"
GEMINI_EMBEDDING_MODEL = "models/embedding-001"

# --- Other Config ---
DEFAULT_TOP_K_CHUNKS = 5

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
