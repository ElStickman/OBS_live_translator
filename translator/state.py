from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass


@dataclass
class Caption:
    text: str = ""
    source_language: str = ""
    created_at: float = 0.0
    expires_at: float = 0.0
    sequence: int = 0


class CaptionStore:
    def __init__(self) -> None:
        self._caption = Caption()
        self._lock = threading.Lock()

    def publish(self, text: str, source_language: str, lifetime: float) -> None:
        now = time.time()
        with self._lock:
            self._caption = Caption(
                text=text.strip(),
                source_language=source_language,
                created_at=now,
                expires_at=now + lifetime,
                sequence=self._caption.sequence + 1,
            )

    def snapshot(self) -> dict[str, str | float | int | bool]:
        now = time.time()
        with self._lock:
            result = asdict(self._caption)
        result["visible"] = bool(result["text"] and result["expires_at"] > now)
        return result
