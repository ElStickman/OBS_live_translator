from __future__ import annotations

import argparse
import threading

from translator.audio import PhraseRecorder
from translator.config import Settings
from translator.engine import TranslationWorker
from translator.highlights import load_highlight_terms
from translator.state import CaptionStore
from translator.web import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Spanish-to-English live captions for OBS")
    parser.add_argument("--list-devices", action="store_true", help="show audio input devices and exit")
    parser.add_argument("--config", default="config.json", help="path to the JSON configuration file")
    args = parser.parse_args()
    if args.list_devices:
        PhraseRecorder.list_devices()
        return

    settings = Settings.from_file(args.config)
    highlight_terms = load_highlight_terms(settings.highlight_terms_file)
    captions = CaptionStore()
    translator = TranslationWorker(settings, captions, highlight_terms)
    recorder = PhraseRecorder(settings, translator.submit)
    app = create_app(captions, highlight_terms)

    translator.start()
    print(f"Highlighted terms: {', '.join(highlight_terms) or 'none'}")
    web_thread = threading.Thread(
        target=lambda: app.run(host=settings.host, port=settings.port, debug=False, use_reloader=False),
        daemon=True,
    )
    web_thread.start()
    print(f"OBS overlay: http://{settings.host}:{settings.port}")

    try:
        recorder.run()
    except KeyboardInterrupt:
        recorder.stop()


if __name__ == "__main__":
    main()
