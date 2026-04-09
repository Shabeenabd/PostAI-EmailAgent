"""
Simple JSON-backed draft store.
"""
import json
from pathlib import Path
from typing import Any, Optional

class DraftStore:
    """Persists email drafts to a local JSON file."""
 
    def __init__(self, path: str = "logs/drafts.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")
    
    def _read(self) -> dict:
        return json.loads(self.path.read_text())
 
    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2))
    
    def save(self, draft_id: str, draft: dict) -> None:
        data = self._read()
        data[draft_id] = draft
        self._write(data)

    def load(self, draft_id: str) -> Optional[dict]:
        return self._read().get(draft_id)
 
    def list_all(self) -> list[dict]:
        return list(self._read().values())
 
    def delete(self, draft_id: str) -> bool:
        data = self._read()
        if draft_id in data:
            del data[draft_id]
            self._write(data)
            return True
        return False    
