# Live Twitch Translator

[![Tests](https://github.com/ElStickman/OBS_live_translator/actions/workflows/tests.yml/badge.svg)](https://github.com/ElStickman/OBS_live_translator/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?logo=githubsponsors)](https://github.com/sponsors/ElStickman)

A local Spanish-to-English speech translator that displays English captions as
a transparent OBS browser source. Audio is processed locally and is neither
stored nor sent to Twitch.

## Features

- Spanish speech translated into English with `faster-whisper`.
- NVIDIA GPU acceleration using CUDA and FP16.
- Transparent OBS overlay.
- Impact-style white captions with a black outline.
- Character-by-character caption animation.
- Configurable words and phrases highlighted in yellow.
- Short-phrase support and adjustable microphone sensitivity.

## Requirements

- Windows 10/11 or Linux.
- Python 3.10 or later.
- An NVIDIA GPU with an up-to-date driver.
- CUDA 12 with cuBLAS and cuDNN 9 available in `PATH`.
- A microphone available to the operating system.
- OBS Studio.

## Minimum hardware: translator only

The following is a practical minimum when the computer is primarily running the
translator and caption overlay:

- 64-bit Windows 10/11 or a current 64-bit Linux distribution.
- NVIDIA RTX 20-series GPU or newer.
- 6 GB of GPU VRAM.
- Four-core x86-64 processor.
- 8 GB of system RAM.
- 10 GB of free disk space for the virtual environment and model cache.
- Stable internet connection during the first model download.
- A microphone with a clean signal and correctly installed audio drivers.

A GPU with less VRAM may require changing `model` in `config.json` to `medium` or
`small`. This lowers memory usage and usually improves response time, but may
reduce recognition and translation accuracy.

## Minimum hardware: streaming and gaming

When the same computer runs the translator, OBS, and a game at the same time,
use this as a practical baseline:

- NVIDIA RTX 3060 12 GB, RTX 4060 Ti 16 GB, or better.
- Six-core processor with 12 threads or better.
- 16 GB of system RAM; 32 GB is strongly preferred for demanding games.
- SSD storage.
- NVIDIA NVENC hardware encoding enabled in OBS.
- Enough remaining GPU capacity to avoid running the game at 100% GPU usage.
- Directional microphone or noise-controlled audio input.

Actual game performance depends on resolution, frame rate, graphics settings,
and the selected OBS encoder settings. Limiting the game's frame rate can leave
the GPU headroom required by Whisper and OBS.

## Recommended hardware: streaming and gaming

- NVIDIA RTX 4070 12 GB or better.
- Eight-core processor or better.
- 32 GB of system RAM.
- NVMe SSD storage.

The RTX 5080 configuration used during development has ample capacity for
`large-v3` in FP16 while OBS and a game are running.

## First-time setup and run on Windows

### 1. Install system dependencies

Install these before setting up the Python project:

- Current NVIDIA graphics driver.
- CUDA Toolkit 12 for Windows x86-64.
- cuDNN 9 for CUDA 12, Windows x86-64.
- Python 3.10 or later.
- OBS Studio.

Restart Windows after installing CUDA and cuDNN. Open a new PowerShell window
and confirm that the required components are available:

```powershell
nvidia-smi
where.exe nvcc
where.exe cublas64_12.dll
where.exe cudnn64_9.dll
```

Every command must succeed. The returned paths must target `x86_64`, not
`arm64`.

### 2. Download the project

```powershell
git clone https://github.com/ElStickman/OBS_live_translator.git
cd Traductor_OBS
```

If the project is already downloaded, open PowerShell in its directory instead.

### 3. Create the Python environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-nvidia.txt
```

### 4. Review the configuration

The repository includes `config.json` with ready-to-run NVIDIA defaults. Edit it
to change the model, microphone, sensitivity, overlay address, or caption
duration. No configuration copy step is required.

### 5. Run and select the audio source

The deployment script creates or reuses `.venv`, checks dependencies, and starts
the application:

```bash
bash deploy.sh
```

On Windows, `deploy.ps1` is also available:

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

If `bash deploy.sh` is invoked through WSL while the project uses a Windows
virtual environment, the script automatically delegates to `deploy.ps1`. This
keeps CUDA and Windows audio-device access working.

Your browser opens <http://127.0.0.1:8765/settings>. Select either:

- A microphone or recording input.
- A `WASAPI loopback` source to capture audio played by Windows, such as
  `SteelSeries Sonar - Chat`.

The selection is saved automatically in the local `audio_selection.json` file;
manual device-index editing is not required. This file is ignored by Git because
audio devices are specific to each computer. Whisper starts after you press
**Save and start translator**.

The settings page remains available while the translator is running. Selecting
and saving another source switches the live capture stream without reloading the
Whisper model or restarting the application.

The same page also edits highlighted names and phrases. Enter one term per line
and save it; captions and Whisper's recognition prompt use the new list
immediately, without restarting the application. An empty list disables
highlighting while keeping `highlight_terms.txt` present.

The source-language selector can use automatic detection for every language or
restrict detection to English and Spanish. In restricted mode, Whisper chooses
the more likely of those two languages, transcribes English, and translates
Spanish into English. The selection applies immediately and is saved locally.

To print all sources in the terminal instead, run `bash deploy.sh --list-devices`.

The first run downloads the `large-v3` model and may take several minutes. When
startup completes, the console displays messages similar to:

```text
OBS overlay: http://127.0.0.1:8765
Audio selector: http://127.0.0.1:8765/settings
Whisper model ready.
Listening to 'SteelSeries Sonar - Chat ... [Loopback]' at 48000 Hz...
```

Speak a short Spanish phrase and open <http://127.0.0.1:8765> in a browser. The
English translation should appear with the same styling used by OBS.

### Later runs

After the first installation, start the application with:

```powershell
cd Traductor_OBS
bash deploy.sh
```

The model remains in the local Hugging Face cache and is not normally downloaded
again.

To skip opening the selector and reuse the source saved in
`audio_selection.json`:

```bash
bash deploy.sh --no-selector
```

## NVIDIA acceleration

The default configuration is optimized for an RTX 5080:

```json
"model": "large-v3",
"device": "cuda",
"compute_type": "float16"
```

Current versions of `faster-whisper` require CUDA 12 cuBLAS and CUDA 12 cuDNN
9. On Windows, the corresponding DLL files must be available in `PATH`. An
installed NVIDIA driver alone does not provide these libraries.

`requirements-nvidia.txt` installs the Python dependencies. CUDA and cuDNN are
Windows system dependencies and must be installed separately.

Confirm that Windows recognizes the GPU:

```powershell
nvidia-smi
```

The application loads Whisper on the GPU before opening the microphone. If a
required CUDA library is unavailable, startup stops with a configuration error.

## OBS configuration

1. Add a **Browser Source**.
2. Set its URL to `http://127.0.0.1:8765`.
3. Set its resolution to 1920 × 1080.
4. Enable the option to refresh the browser when the scene becomes active.

The page background is transparent. A caption appears after a spoken phrase is
translated and disappears after eight seconds by default.

## Configuration

Settings are read from the committed `config.json` file:

- `model`: Whisper model name; `large-v3` provides accurate translation.
- `device`: `cuda` runs the model on an NVIDIA GPU.
- `compute_type`: `float16` reduces VRAM use and uses Tensor Cores.
- `audio_backend`: default backend when no local audio selection exists.
- `input_device`: default input when no local audio selection exists.
- `speech_threshold`: raise this value if background noise activates recording.
- `no_speech_threshold`: Whisper confidence required to treat audio as speech;
  lower it to reject more noise-generated captions.
- `min_speech_ms`: minimum speech duration; `250` preserves short words.
- `silence_ms`: pause used to close a phrase; `450` reduces response latency.
- `max_phrase_ms`: safety limit for one continuous phrase.
- `caption_seconds`: number of seconds a caption remains visible.
- `highlight_terms_file`: file containing words or phrases shown in yellow.
- `language_mode`: `english_spanish` restricts detection to those languages;
  `all` enables automatic detection across every language supported by Whisper.
- `host` and `port`: local address used by the OBS overlay.

To use another configuration file without modifying the default:

```powershell
python main.py --config config.custom.json
```

### Gaming and streaming profile

`config.gaming.json` is a lower-latency profile for running the translator on
the same PC as a game and OBS. It uses the `medium` model, limits each phrase
to six seconds, keeps only the newest pending phrase, and checks the source
language again after every three phrases. Start it with:

```powershell
python main.py --config config.gaming.json
```

The default `config.json` remains the higher-quality profile. To tune a custom
profile, use `max_pending_phrases` to limit queued translation work and
`language_detection_interval` to set how many phrases pass before the next
English/Spanish language check. A value of `1` checks every phrase.

## Highlighted words and phrases

`highlight_terms.txt` is optional and ignored by Git so personal names are not
published. To enable highlighting, copy `highlight_terms.example.txt` to
`highlight_terms.txt` and add one word or phrase per line. Plain lines use the
default yellow. The settings page can assign a different color to each term and
saves custom colors after a tab (for example, `ExampleBrand<TAB>#ff3366`). An
absent or empty file simply disables highlighting. Matching is case-insensitive. These entries
are also supplied to Whisper as context to improve recognition of names and
project-specific terminology.

Example:

```text
ExampleBrand
Raspberry Pi
Twitch
Special phrase
```

Terms saved from the settings page apply immediately. If you edit the file
manually, restart the application. Refresh the browser-source cache in OBS only
if it is still displaying an older overlay version.

## Tests

Run the test suite from the activated virtual environment:

```powershell
python -m unittest discover -s tests -v
```

## Current limitations

Phrase detection uses a lightweight volume threshold. It works well for a
controlled microphone signal, but music or substantial background noise may
require sensitivity calibration or a more advanced voice-activity detector.

Speech recognition and machine translation can be inaccurate. Review captions
before relying on them for accessibility, safety-critical communication, legal
interpretation, or other high-impact uses.

## Privacy

Audio is captured and processed locally. The application does not intentionally
store recordings or send captured audio to the project maintainer. The first run
connects to Hugging Face to download the selected Whisper model unless it is
already cached locally.

Do not publish recordings, complete logs, device identifiers, or personal names
in bug reports. See [SECURITY.md](SECURITY.md) for private vulnerability reports.

## Contributing and support

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md) before opening a pull request. Use GitHub
Issues for reproducible bugs and feature requests, and read [SUPPORT.md](SUPPORT.md)
for support expectations.

## Support the project

The software is free and open source. If it is useful to you, consider
[sponsoring development through GitHub Sponsors](https://github.com/sponsors/ElStickman).
Sponsorship is optional and does not unlock functionality or guarantee support.

## License

The source code is available under the [MIT License](LICENSE). Third-party
components keep their respective licenses; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Project branding is addressed
separately in [TRADEMARKS.md](TRADEMARKS.md).

This independent project is not affiliated with or endorsed by OBS Project,
Twitch, NVIDIA, Microsoft, SteelSeries, or Hugging Face.
