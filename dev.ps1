param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

Write-Host "Starting API on http://localhost:$Port ..."
Set-Location -LiteralPath ".\\backend"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
