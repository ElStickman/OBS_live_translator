$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Set-Location -LiteralPath $ProjectDir

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $SystemPython = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
    Write-Host "Creating virtual environment in $VenvDir..."
    & $SystemPython -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "Installing Python dependencies..."
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $VenvPython -m pip install -r requirements-nvidia.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "Using existing virtual environment: $VenvDir"
}

Write-Host "Checking Python dependencies..."
& $VenvPython -m pip install --disable-pip-version-check -q -r requirements-nvidia.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $VenvPython main.py @args
exit $LASTEXITCODE
