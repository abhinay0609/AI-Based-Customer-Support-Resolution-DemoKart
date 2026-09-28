from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / os.getenv("DATA_DIR", "data")
# Operational CSVs and the runtime SQLite database live together by default.
# This avoids creating an empty data/operational directory that shadows the CSVs.
OPERATIONAL_DATA_PATH = PROJECT_ROOT / os.getenv("OPERATIONAL_DATA_PATH", "data")
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / os.getenv("KNOWLEDGE_BASE_PATH", "data/knowledge_base")
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")
VECTORSTORE_PATH = PROJECT_ROOT / os.getenv("VECTORSTORE_PATH", "vectorstore")
VECTOR_DB_DIR = PROJECT_ROOT / os.getenv("VECTOR_DB_DIR", "vector_db")
LOG_PATH = PROJECT_ROOT / os.getenv("LOG_PATH", "logs")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
UNDERSTANDING_THRESHOLD = float(os.getenv("UNDERSTANDING_THRESHOLD", "0.75"))
RESOLUTION_THRESHOLD = float(os.getenv("RESOLUTION_THRESHOLD", "0.80"))

for directory in (DATA_DIR, KNOWLEDGE_BASE_PATH, KNOWLEDGE_BASE_DIR, VECTORSTORE_PATH, VECTOR_DB_DIR, LOG_PATH):
    directory.mkdir(parents=True, exist_ok=True)
