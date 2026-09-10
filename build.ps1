param([string]$Python = "")
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if (-not $Python) {
    $Python = Join-Path $PSScriptRoot ".venv-build\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) {
        python -m venv .venv-build
        if ($LASTEXITCODE -ne 0) { throw "Could not create build environment" }
    }
}
& $Python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install build dependencies" }

& $Python -m PyInstaller --noconfirm --onedir --windowed --noupx `
    --name LiveTwitchTranslator `
    --add-data "translator/static:translator/static" `
    --add-data "config.json:." --add-data "config.gaming.json:." `
    --add-data "LICENSE:." --add-data "THIRD_PARTY_NOTICES.md:." `
    --collect-all faster_whisper --collect-all ctranslate2 `
    --collect-all pyaudiowpatch --collect-all _sounddevice_data `
    --collect-all webview --recursive-copy-metadata faster-whisper `
    --recursive-copy-metadata pywebview --recursive-copy-metadata Flask `
    --recursive-copy-metadata sounddevice --recursive-copy-metadata PyAudioWPatch `
    desktop.py
if ($LASTEXITCODE -ne 0) { throw "Executable build failed" }

Copy-Item -LiteralPath "DISTRIBUTION.md", "LICENSE", "THIRD_PARTY_NOTICES.md" -Destination "dist/LiveTwitchTranslator"
$PythonLicense = & $Python -c "import sys; from pathlib import Path; print(Path(sys.base_prefix) / 'LICENSE.txt')"
Copy-Item -LiteralPath $PythonLicense -Destination "dist/LiveTwitchTranslator/Python-LICENSE.txt"
& $Python -m pip freeze | Set-Content -LiteralPath "dist/LiveTwitchTranslator/dependencies.txt"
& $Python -m zipfile -c "dist/LiveTwitchTranslator-windows-x64.zip" "dist/LiveTwitchTranslator"
if ($LASTEXITCODE -ne 0) { throw "Could not create distribution ZIP" }
Write-Host "Ready: dist/LiveTwitchTranslator-windows-x64.zip"
