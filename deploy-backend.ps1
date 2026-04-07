# Rebuild backend image, push to Azure Container Registry with a UNIQUE tag (forces Container Apps to pull).
# Usage (from PowerShell):
#   .\deploy-backend.ps1
#   .\deploy-backend.ps1 -Version v5
#
# Then in Azure Portal: Container App -> Containers -> set Image tag to the same Version -> Save and deploy.

param(
    [string]$Registry = "xahivecyber.azurecr.io",
    [string]$ImageName = "xahive-compliance",
    [string]$Version = ("v" + (Get-Date -Format "yyyyMMdd-HHmm"))
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"

if (-not (Test-Path (Join-Path $Backend "Dockerfile"))) {
    Write-Error "Dockerfile not found at: $Backend"
}

Set-Location $Backend

Write-Host "Building $Registry/${ImageName}:$Version and :latest ..."
docker build -t "${ImageName}:$Version" -t "${ImageName}:latest" .

docker tag "${ImageName}:$Version" "${Registry}/${ImageName}:$Version"
docker tag "${ImageName}:latest" "${Registry}/${ImageName}:latest"

Write-Host "Pushing $Registry/${ImageName}:$Version and :latest ..."
docker push "${Registry}/${ImageName}:$Version"
docker push "${Registry}/${ImageName}:latest"

Write-Host ""
Write-Host "Done. Use this tag in Azure Container App -> Containers -> Image tag: $Version"
Write-Host "Then Save and deploy (or add env DEPLOY_TRIGGER with a new value)."
Set-Location $Root
