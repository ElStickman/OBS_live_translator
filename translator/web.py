from __future__ import annotations

import json
import re
from pathlib import Path
from collections.abc import Callable

from flask import Flask, jsonify, request, send_from_directory

from .devices import list_audio_sources
from .state import CaptionStore


def create_app(
    captions: CaptionStore,
    highlight_terms: list[str] | None = None,
    selection_path: str = "audio_selection.json",
    highlight_terms_path: str = "highlight_terms.txt",
    highlight_colors: dict[str, str] | None = None,
    language_options: dict[str, str] | None = None,
    on_audio_selected: Callable[[], None] | None = None,
) -> Flask:
    static_dir = Path(__file__).with_name("static")
    app = Flask(__name__, static_folder=None)

    @app.after_request
    def disable_browser_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/")
    def overlay():
        return send_from_directory(static_dir, "overlay.html")

    @app.get("/settings")
    def settings_page():
        return send_from_directory(static_dir, "settings.html")

    @app.get("/api/caption")
    def caption():
        result = captions.snapshot()
        result["highlight_terms"] = highlight_terms or []
        result["highlights"] = [
            {
                "term": term,
                "color": (highlight_colors or {}).get(term.casefold(), "#ffd400"),
            }
            for term in (highlight_terms or [])
        ]
        return jsonify(result)

    @app.get("/api/audio-sources")
    def audio_sources():
        return jsonify([source.as_dict() for source in list_audio_sources()])

    def save_local_settings(changes: dict[str, object]) -> None:
        path = Path(selection_path)
        try:
            values = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (json.JSONDecodeError, OSError):
            values = {}
        values.update(changes)
        path.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")

    @app.get("/api/language-mode")
    def get_language_mode():
        return jsonify({"mode": (language_options or {}).get("mode", "english_spanish")})

    @app.put("/api/language-mode")
    def update_language_mode():
        mode = (request.get_json(silent=True) or {}).get("mode")
        if mode not in {"all", "english_spanish"}:
            return jsonify({"error": "Invalid language mode"}), 400
        save_local_settings({"language_mode": mode})
        if language_options is not None:
            language_options["mode"] = mode
        return jsonify({"ok": True, "mode": mode})

    @app.get("/api/highlight-terms")
    def get_highlight_terms():
        return jsonify({
            "terms": [
                {
                    "term": term,
                    "color": (highlight_colors or {}).get(term.casefold(), "#ffd400"),
                }
                for term in (highlight_terms or [])
            ]
        })

    @app.put("/api/highlight-terms")
    def update_highlight_terms():
        payload = request.get_json(silent=True) or {}
        raw_terms = payload.get("terms")
        if not isinstance(raw_terms, list):
            return jsonify({"error": "Terms must be a list"}), 400

        terms: list[str] = []
        colors: dict[str, str] = {}
        seen: set[str] = set()
        for item in raw_terms:
            if isinstance(item, str):
                raw_term, raw_color = item, "#ffd400"
            elif isinstance(item, dict):
                raw_term, raw_color = item.get("term"), item.get("color", "#ffd400")
            else:
                return jsonify({"error": "Each term must be text or a term/color object"}), 400
            if not isinstance(raw_term, str) or not isinstance(raw_color, str):
                return jsonify({"error": "Invalid term or color"}), 400
            term = raw_term.strip()
            color = raw_color.strip().lower()
            normalized = term.casefold()
            if not term or term.startswith("#") or normalized in seen:
                continue
            if "\t" in term or "\n" in term or "\r" in term:
                return jsonify({"error": "Terms cannot contain tabs or line breaks"}), 400
            if len(term) > 100:
                return jsonify({"error": "Each term must be 100 characters or fewer"}), 400
            if re.fullmatch(r"#[0-9a-f]{6}", color) is None:
                return jsonify({"error": f"Invalid color for {term}"}), 400
            seen.add(normalized)
            terms.append(term)
            colors[normalized] = color
        if len(terms) > 500:
            return jsonify({"error": "A maximum of 500 terms is supported"}), 400

        Path(highlight_terms_path).write_text(
            "".join(
                f"{term}\n" if colors[term.casefold()] == "#ffd400"
                else f"{term}\t{colors[term.casefold()]}\n"
                for term in terms
            ),
            encoding="utf-8",
        )
        if highlight_terms is not None:
            highlight_terms[:] = terms
        if highlight_colors is not None:
            highlight_colors.clear()
            highlight_colors.update(colors)
        result = [
            {"term": term, "color": colors[term.casefold()]} for term in terms
        ]
        return jsonify({"ok": True, "terms": result})

    @app.post("/api/audio-selection")
    def audio_selection():
        payload = request.get_json(silent=True) or {}
        backend = payload.get("backend")
        try:
            device = int(payload.get("device"))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid audio device"}), 400

        available = {
            (source.backend, source.device): source for source in list_audio_sources()
        }
        selected = available.get((backend, device))
        if selected is None:
            return jsonify({"error": "Audio source is no longer available"}), 400

        save_local_settings({
            "audio_backend": selected.backend,
            "input_device": selected.device,
        })
        if on_audio_selected is not None:
            on_audio_selected()
        return jsonify({"ok": True, "name": selected.name})

    return app
