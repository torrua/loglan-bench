"""Configuration settings for Loglan Bench."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"
RAW_RESULTS_DIR = RESULTS_DIR / "raw"

# Load .env file from project root or parent directories
load_dotenv(PROJECT_ROOT / ".env")

# Database configuration
DEFAULT_DB_PATH = DATA_DIR / "export.db"
DB_PATH = Path(os.getenv("LOGLAN_DB_PATH", str(DEFAULT_DB_PATH)))

# Model & Provider Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma-3-27b-it")
FALLBACK_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# RAG Hyperparameters
DEFAULT_TOP_WORDS = 5
DEFAULT_TOP_DOCS = 3
CHUNK_SIZE_WORDS = 450
CHUNK_OVERLAP_WORDS = 50

# Ensure essential directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
