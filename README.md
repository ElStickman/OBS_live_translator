# Live Twitch Translator

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
git clone <repository-url>
cd RaspberryTwitchBot
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

### 5. Select the microphone

List the available audio devices:

```powershell
python main.py --list-devices
```

If the correct microphone is not the system default, place its device number in
`config.json`:

```json
"input_device": 1
```

### 6. Run the translator

```powershell
python main.py
```

The first run downloads the `large-v3` model and may take several minutes. When
startup completes, the console displays messages similar to:

```text
Whisper model ready.
OBS overlay: http://127.0.0.1:8765
Listening for Spanish speech...
```

Speak a short Spanish phrase and open <http://127.0.0.1:8765> in a browser. The
English translation should appear with the same styling used by OBS.

### Later runs

After the first installation, start the application with:

```powershell
cd RaspberryTwitchBot
.venv\Scripts\Activate.ps1
python main.py
```

The model remains in the local Hugging Face cache and is not normally downloaded
again.

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
- `input_device`: optional microphone device name or number; `null` uses the default.
- `speech_threshold`: raise this value if background noise activates recording.
- `min_speech_ms`: minimum speech duration; `250` preserves short words.
- `silence_ms`: pause used to close a phrase; `450` reduces response latency.
- `max_phrase_ms`: safety limit for one continuous phrase.
- `caption_seconds`: number of seconds a caption remains visible.
- `highlight_terms_file`: file containing words or phrases shown in yellow.
- `host` and `port`: local address used by the OBS overlay.

To use another configuration file without modifying the default:

```powershell
python main.py --config config.custom.json
```

## Highlighted words and phrases

`highlight_terms.txt` is optional and ignored by Git so personal names are not
published. To enable highlighting, copy `highlight_terms.example.txt` to
`highlight_terms.txt` and add one word or phrase per line. An absent or empty
file simply disables highlighting. Matching is case-insensitive. These entries
are also supplied to Whisper as context to improve recognition of names and
project-specific terminology.

Example:

```text
ExampleBrand
Raspberry Pi
Twitch
Special phrase
```

Restart the application after editing the file. Refresh the browser-source
cache in OBS if it is still displaying an older overlay version.

## Tests

Run the test suite from the activated virtual environment:

```powershell
python -m unittest discover -s tests -v
```

## Current limitations

Phrase detection uses a lightweight volume threshold. It works well for a
controlled microphone signal, but music or substantial background noise may
require sensitivity calibration or a more advanced voice-activity detector.
