from __future__ import annotations

from pathlib import Path
import re


DEFAULT_HIGHLIGHT_COLOR = "#ffd400"
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_highlight_config(path: str) -> tuple[list[str], dict[str, str]]:
    """Load terms and colors; plain legacy lines keep the default yellow."""
    file_path = Path(path)
    if not file_path.exists():
        file_path.touch(exist_ok=True)

    terms: list[str] = []
    colors: dict[str, str] = {}
    seen: set[str] = set()
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        term, separator, raw_color = line.partition("\t")
        term = term.strip()
        normalized = term.casefold()
        if not term or normalized in seen:
            continue
        color = raw_color.strip().lower() if separator else DEFAULT_HIGHLIGHT_COLOR
        if not COLOR_PATTERN.fullmatch(color):
            color = DEFAULT_HIGHLIGHT_COLOR
        seen.add(normalized)
        terms.append(term)
        colors[normalized] = color
    return terms, colors


def load_highlight_terms(path: str) -> list[str]:
    return load_highlight_config(path)[0]
