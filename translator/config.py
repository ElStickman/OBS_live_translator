from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    model: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"
    input_device: str | int | None = None
    sample_rate: int = 16000
    block_ms: int = 100
    silence_ms: int = 450
    min_speech_ms: int = 250
    max_phrase_ms: int = 12000
    speech_threshold: float = 0.012
    caption_seconds: float = 8
    highlight_terms_file: str = "highlight_terms.txt"
    host: str = "127.0.0.1"
    port: int = 8765

    def __post_init__(self) -> None:
        positive_integers = {
            "sample_rate": self.sample_rate,
            "block_ms": self.block_ms,
            "silence_ms": self.silence_ms,
            "min_speech_ms": self.min_speech_ms,
            "max_phrase_ms": self.max_phrase_ms,
        }
        for name, value in positive_integers.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.max_phrase_ms < self.min_speech_ms:
            raise ValueError("max_phrase_ms must be greater than or equal to min_speech_ms")
        if (
            not isinstance(self.speech_threshold, (int, float))
            or isinstance(self.speech_threshold, bool)
            or not 0 < self.speech_threshold <= 1
        ):
            raise ValueError("speech_threshold must be between 0 and 1")
        if (
            not isinstance(self.caption_seconds, (int, float))
            or isinstance(self.caption_seconds, bool)
            or self.caption_seconds <= 0
        ):
            raise ValueError("caption_seconds must be greater than zero")
        if not isinstance(self.port, int) or isinstance(self.port, bool) or not 1 <= self.port <= 65535:
            raise ValueError("port must be an integer between 1 and 65535")

    @classmethod
    def from_file(cls, path: str = "config.json") -> "Settings":
        config_path = Path(path)
        try:
            values = json.loads(config_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Configuration file not found: {config_path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in {config_path}: {error}") from error

        if not isinstance(values, dict):
            raise ValueError(f"Configuration in {config_path} must be a JSON object")
        allowed = {field.name for field in fields(cls)}
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ValueError(f"Unknown configuration keys: {', '.join(unknown)}")
        return cls(**values)

    def normalized_input_device(self) -> str | int | None:
        if isinstance(self.input_device, str) and self.input_device.isdigit():
            return int(self.input_device)
        return self.input_device
