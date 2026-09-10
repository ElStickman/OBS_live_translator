"""Windows desktop entry point; the OBS overlay remains a local HTTP page."""
from __future__ import annotations

import ctypes
from contextlib import redirect_stderr, redirect_stdout
import os
from pathlib import Path
import traceback


def prepare_user_directory(resources: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("config.json", "config.gaming.json"):
        try:
            with (destination / name).open("x", encoding="utf-8") as target:
                target.write((resources / name).read_text(encoding="utf-8"))
        except FileExistsError:
            pass
    (destination / "highlight_terms.txt").touch(exist_ok=True)


def launch() -> None:
    data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LiveTwitchTranslator"
    try:
        prepare_user_directory(Path(__file__).resolve().parent, data_dir)
        os.chdir(data_dir)
        # Keep diagnostics available in the windowed executable, where stdio is None.
        with (data_dir / "translator.log").open("w", encoding="utf-8", buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
            try:
                from main import main

                main(desktop=True)
            except BaseException:
                traceback.print_exc()
                raise
    except BaseException as error:
        ctypes.windll.user32.MessageBoxW(
            None, f"The translator could not start: {error}\n\n"
            f"Details: {data_dir / 'translator.log'}\n"
            "Verify that Microsoft Edge WebView2 Runtime is installed.",
            "Live Twitch Translator", 0x10,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    launch()
