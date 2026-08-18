from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from .state import CaptionStore


def create_app(captions: CaptionStore, highlight_terms: list[str] | None = None) -> Flask:
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

    @app.get("/api/caption")
    def caption():
        result = captions.snapshot()
        result["highlight_terms"] = highlight_terms or []
        return jsonify(result)

    return app
