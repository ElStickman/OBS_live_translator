#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

# WSL cannot always launch a Windows virtual environment's python.exe directly.
# Delegate to PowerShell so CUDA, Windows audio devices, and the existing venv
# all remain in the same Windows environment.
if grep -qi microsoft /proc/version 2>/dev/null && [[ -f "$VENV_DIR/Scripts/python.exe" ]]; then
  WINDOWS_SCRIPT="$(wslpath -w "$PROJECT_DIR/deploy.ps1")"
  echo "WSL detected; launching the Windows virtual environment through PowerShell..."
  exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WINDOWS_SCRIPT" "$@"
fi

find_system_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
  elif command -v python >/dev/null 2>&1; then
    command -v python
  else
    echo "Error: Python 3.10 or later was not found in PATH." >&2
    exit 1
  fi
}

find_venv_python() {
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    printf '%s\n' "$VENV_DIR/bin/python"
  elif [[ -x "$VENV_DIR/Scripts/python.exe" ]]; then
    printf '%s\n' "$VENV_DIR/Scripts/python.exe"
  else
    return 1
  fi
}

cd "$PROJECT_DIR"

if ! VENV_PYTHON="$(find_venv_python)"; then
  SYSTEM_PYTHON="${PYTHON_BIN:-$(find_system_python)}"
  echo "Creating virtual environment in $VENV_DIR..."
  "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
  VENV_PYTHON="$(find_venv_python)"

  echo "Installing Python dependencies..."
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r requirements-nvidia.txt
else
  echo "Using existing virtual environment: $VENV_DIR"
fi

echo "Checking Python dependencies..."
"$VENV_PYTHON" -m pip install --disable-pip-version-check -q -r requirements-nvidia.txt

exec "$VENV_PYTHON" main.py "$@"
