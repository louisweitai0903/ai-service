import json
import os
from datetime import datetime, timezone
from typing import Optional
from app.config import DATA_DIR

RESUME_FILE = os.path.join(DATA_DIR, "resume.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_resume(filename: str, ai_result: dict) -> dict:
    _ensure_dir()
    data = {
        "filename": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        **ai_result,
    }
    with open(RESUME_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return data


def load_resume() -> Optional[dict]:
    if not os.path.exists(RESUME_FILE):
        return None
    with open(RESUME_FILE, "r") as f:
        return json.load(f)


def clear_resume() -> bool:
    if os.path.exists(RESUME_FILE):
        os.remove(RESUME_FILE)
        return True
    return False


def resume_exists() -> bool:
    return os.path.exists(RESUME_FILE)
