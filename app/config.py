import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
DEFAULT_MODEL: str = "gemini-3.1-pro-preview"
PORT: int = int(os.environ.get("PORT", "8001"))
DATA_DIR: str = os.environ.get("DATA_DIR", "/app/data")
