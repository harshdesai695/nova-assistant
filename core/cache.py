import hashlib
import re
import time
from collections import OrderedDict
from typing import Any, Optional


class ResponseCache:
    def __init__(self, max_items: int = 256, ttl_seconds: int = 180):
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self._store: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def key_for(self, text: str, session_id: str = "") -> str:
        src = f"{session_id}:{self._normalize(text)}"
        return hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        item = self._store.get(key)
        if item is None:
            return None
        created_at, value = item
        if now - created_at > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)
        self._store.move_to_end(key)
        while len(self._store) > self.max_items:
            self._store.popitem(last=False)

    def stats(self) -> dict:
        return {"size": len(self._store), "max_items": self.max_items, "ttl_seconds": self.ttl_seconds}
