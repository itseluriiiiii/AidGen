# backend/services/resource_service.py
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "offline_data"
SHELTER_FILE = DATA_DIR / "shelters.json"

def get_all_resources():
    if not SHELTER_FILE.exists():
        return []
    return json.loads(SHELTER_FILE.read_text(encoding="utf-8"))

def find_resources_by_keyword(keyword: str, limit: int = 5):
    keyword = (keyword or "").lower()
    results = []
    for r in get_all_resources():
        text = " ".join([str(v).lower() for v in r.values() if v])
        if keyword in text:
            results.append(r)
        if len(results) >= limit:
            break
    return results
