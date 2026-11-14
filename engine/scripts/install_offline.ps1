$ErrorActionPreference = 'Stop'
$engineRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $engineRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3.13 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 x64 is required for the bundled wheels.' }
}
& '.\.venv\Scripts\python.exe' -m pip install --no-index --find-links wheelhouse -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Offline installation failed.' }
& '.\.venv\Scripts\python.exe' -m vigile init
if ($LASTEXITCODE -ne 0) { throw 'Initialization failed.' }
