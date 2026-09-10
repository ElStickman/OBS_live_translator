from __future__ import annotations

import argparse
import queue
import threading
import webbrowser
from werkzeug.serving import make_server

from translator.audio import PhraseRecorder
from translator.config import Settings
from translator.devices import print_audio_sources
from translator.engine import TranslationWorker
from translator.highlights import load_highlight_config
from translator.state import CaptionStore
from translator.web import create_app


def main(desktop: bool = False) -> None:
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
    stopping = threading.Event()
    runtime_status = {"message": "Choose an audio source to start.", "error": False}
    app = create_app(
        captions,
        highlight_terms,
        selection_path=args.audio_selection,
        highlight_terms_path=settings.highlight_terms_file,
        highlight_colors=highlight_colors,
        language_options=language_options,
        on_audio_selected=lambda: controls.put(("switch", None)),
        runtime_status=runtime_status,
    )

    server = make_server(settings.host, settings.port, app, threaded=True)
    web_thread = threading.Thread(target=server.serve_forever, daemon=True)
    web_thread.start()
    print(f"OBS overlay: http://{settings.host}:{settings.port}")

    if not args.no_selector and not desktop:
        selector_url = f"http://{settings.host}:{settings.port}/settings"
        print(f"Audio selector: {selector_url}")
        webbrowser.open(selector_url)
    elif args.no_selector:
        controls.put(("switch", None))

    translator: TranslationWorker | None = None
    recorder: PhraseRecorder | None = None
    recorder_thread: threading.Thread | None = None

    def run_recorder(active_recorder: PhraseRecorder) -> None:
        try:
            active_recorder.run()
        except Exception as error:
            controls.put(("recorder_failed", (active_recorder, error)))

    def run_controls() -> None:
        nonlocal recorder, recorder_thread, translator, settings
        while not stopping.is_set():
            command, payload = controls.get()
            if command == "stop":
                return
            if command == "recorder_failed":
                failed_recorder, error = payload
                if failed_recorder is recorder:
                    recorder = None
                    recorder_thread = None
                    print(f"Audio capture failed: {error}")
                    runtime_status.update(message=f"Audio capture failed: {error}", error=True)
                    print(f"Choose another source at http://{settings.host}:{settings.port}/settings")
                continue

            if command != "switch":
                continue

            if recorder is not None:
                print("Switching audio source...")
                recorder.stop()
                if recorder_thread is not None:
                    recorder_thread.join(timeout=5)

                if recorder_thread is not None and recorder_thread.is_alive():
                    runtime_status.update(message="Audio source is still stopping. Try again shortly.", error=True)
                    continue

            try:
                settings = Settings.from_file(args.config, args.audio_selection)
                if translator is None:
                    runtime_status.update(message="Loading speech model. The first download may take several minutes.", error=False)
                    worker = TranslationWorker(settings, captions, highlight_terms, language_options)
                    worker.start()
                    translator = worker
                if stopping.is_set():
                    return
                recorder = PhraseRecorder(settings, translator.submit)
                recorder_thread = threading.Thread(
                    target=run_recorder,
                    args=(recorder,),
                    daemon=True,
                )
                runtime_status.update(message="Model ready. Starting audio capture; speak to generate captions.", error=False)
                recorder_thread.start()
            except Exception as error:
                runtime_status.update(message=f"Could not start translator: {error}", error=True)
                print(runtime_status["message"])

    control_thread = None
    try:
        if desktop:
            import webview

            control_thread = threading.Thread(target=run_controls, daemon=True)
            control_thread.start()
            webview.create_window(
                "Live Twitch Translator", f"http://{settings.host}:{settings.port}/settings",
                width=960, height=850, min_size=(420, 540),
            )
            webview.start(gui="edgechromium")
        else:
            run_controls()
    except KeyboardInterrupt:
        pass
    finally:
        stopping.set()
        controls.put(("stop", None))
        if control_thread is not None:
            control_thread.join(timeout=5)
        if recorder is not None:
            recorder.stop()
        if recorder_thread is not None:
            recorder_thread.join(timeout=5)
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
