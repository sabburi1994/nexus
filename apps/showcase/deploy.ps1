param(
    [string]$ProjectId = "finhub-510316",
    [string]$Region = "europe-west1",
    [string]$Service = "nexus-showcase"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Ensuring latest nexus-framework wheel is packaged..."
$rootDir = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$wheelsDir = Join-Path $PSScriptRoot "backend\wheels"
New-Item -ItemType Directory -Force -Path $wheelsDir | Out-Null

if (-not (Test-Path "$rootDir\dist\nexus_framework-0.1.0-py3-none-any.whl")) {
    Write-Host "Building wheel from $rootDir..."
    python -m build $rootDir
}
Copy-Item "$rootDir\dist\nexus_framework-0.1.0-py3-none-any.whl" $wheelsDir -Force

Write-Host "==> Deploying Nexus Showcase to Google Cloud Run ($ProjectId, $Region)..."
$backendDir = Join-Path $PSScriptRoot "backend"

gcloud run deploy $Service `
    --source $backendDir `
    --project $ProjectId `
    --region $Region `
    --allow-unauthenticated `
    --quiet `
    --set-env-vars "GCP_PROJECT_ID=$ProjectId,GEMINI_MODEL=gemini-3.8-flash"
