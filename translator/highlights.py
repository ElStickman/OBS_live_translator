from __future__ import annotations

from pathlib import Path


def load_highlight_terms(path: str) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    terms: list[str] = []
    seen: set[str] = set()
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        term = raw_line.strip()
        normalized = term.casefold()
        if not term or term.startswith("#") or normalized in seen:
            continue
        seen.add(normalized)
        terms.append(term)
    return terms
