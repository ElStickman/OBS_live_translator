from __future__ import annotations

import argparse
import queue
import threading
import webbrowser

from translator.audio import PhraseRecorder
from translator.config import Settings
from translator.devices import print_audio_sources
from translator.engine import TranslationWorker
from translator.highlights import load_highlight_config
from translator.state import CaptionStore
from translator.web import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Spanish-to-English live captions for OBS")
    parser.add_argument(
        "--list-devices", action="store_true", help="show audio input devices and exit"
    )
    parser.add_argument(
        "--config", default="config.json", help="path to the JSON configuration file"
    )
    parser.add_argument(
        "--audio-selection",
        default="audio_selection.json",
        help="path to the locally saved audio selection",
    )
    parser.add_argument(
        "--no-selector",
        action="store_true",
        help="use the saved audio source without opening the selector",
    )
    args = parser.parse_args()
    if args.list_devices:
        print_audio_sources()
        return

    settings = Settings.from_file(args.config, args.audio_selection)
    highlight_terms, highlight_colors = load_highlight_config(
        settings.highlight_terms_file
    )
    language_options = {"mode": settings.language_mode}
    captions = CaptionStore()
    controls: queue.Queue[tuple[str, object | None]] = queue.Queue()
    app = create_app(
        captions,
        highlight_terms,
        selection_path=args.audio_selection,
        highlight_terms_path=settings.highlight_terms_file,
        highlight_colors=highlight_colors,
        language_options=language_options,
        on_audio_selected=lambda: controls.put(("switch", None)),
    )

    web_thread = threading.Thread(
        target=lambda: app.run(
            host=settings.host,
            port=settings.port,
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )
    web_thread.start()
    print(f"OBS overlay: http://{settings.host}:{settings.port}")

    if not args.no_selector:
        selector_url = f"http://{settings.host}:{settings.port}/settings"
        print(f"Audio selector: {selector_url}")
        webbrowser.open(selector_url)
    else:
        controls.put(("switch", None))

    translator: TranslationWorker | None = None
    recorder: PhraseRecorder | None = None
    recorder_thread: threading.Thread | None = None

    def run_recorder(active_recorder: PhraseRecorder) -> None:
        try:
            active_recorder.run()
        except Exception as error:
            controls.put(("recorder_failed", (active_recorder, error)))

    try:
        while True:
            command, payload = controls.get()
            if command == "recorder_failed":
                failed_recorder, error = payload
                if failed_recorder is recorder:
                    recorder = None
                    recorder_thread = None
                    print(f"Audio capture failed: {error}")
                    print(f"Choose another source at http://{settings.host}:{settings.port}/settings")
                continue

            if command != "switch":
                continue

            if recorder is not None:
                print("Switching audio source...")
                recorder.stop()
                if recorder_thread is not None:
                    recorder_thread.join(timeout=5)

            settings = Settings.from_file(args.config, args.audio_selection)
            if translator is None:
                translator = TranslationWorker(
                    settings, captions, highlight_terms, language_options
                )
                translator.start()
                print(f"Highlighted terms: {', '.join(highlight_terms) or 'none'}")

            recorder = PhraseRecorder(settings, translator.submit)
            recorder_thread = threading.Thread(
                target=run_recorder,
                args=(recorder,),
                daemon=True,
            )
            recorder_thread.start()
    except KeyboardInterrupt:
        if recorder is not None:
            recorder.stop()
        if recorder_thread is not None:
            recorder_thread.join(timeout=5)


if __name__ == "__main__":
    main()
