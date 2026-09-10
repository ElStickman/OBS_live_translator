# Live Twitch Translator for Windows

1. Extract the entire ZIP into a folder. Keep `_internal` next to the executable.
2. Install Microsoft Edge WebView2 Runtime if it is missing:
   https://developer.microsoft.com/microsoft-edge/webview2/
3. For the default NVIDIA profile, install an NVIDIA driver, CUDA 12 cuBLAS
   and cuDNN 9 and make their DLLs available in PATH. These are not bundled.
4. Open `LiveTwitchTranslator.exe`, choose your audio source, and save to start.
   Internet is needed for the first model download; subsequent runs reuse it.
5. In OBS, add a Browser Source using `http://127.0.0.1:8765` at 1920 x 1080.
   Keep the desktop application open while using the overlay.

Python does not need to be installed. The build targets 64-bit Windows 10/11.
Closing the window stops audio capture and the local overlay server.
Run only one instance at a time; port 8765 must be available.

## Personal settings

Settings, saved microphone selection, highlighted terms and `translator.log`
live in `%LOCALAPPDATA%\LiveTwitchTranslator`, outside the installation folder.
The two default configuration profiles are copied only on first use, so replacing
the application folder preserves your settings. Highlighted terms start empty;
edit them in the application. No example or personal term list is distributed.

To use the gaming profile, create a shortcut to the executable and append
`--config config.gaming.json` to its target. Audio device selection is remembered
by backend and index; verify it after changing audio drivers or hardware.

The Whisper model cache is managed separately by Hugging Face. The default
`large-v3` model requires substantial GPU memory; use the gaming profile if needed.
If startup fails, consult `translator.log`. Model and audio errors also appear
in the settings window.

This build is unsigned. It has no auto-updater or installer. Test it on a second
Windows PC with the prerequisites before publishing a public release.
