<#
.SYNOPSIS
  Build the Nexus showcase image and roll it out with Terraform, in a dedicated or an existing project.

.DESCRIPTION
  Terraform is the only path for infrastructure. This script:
    1. builds the framework wheel,
    2. builds and pushes the image with Cloud Build (as the build service account), tagged with the git SHA,
    3. runs terraform apply in infra/terraform with that image tag.
  First time set up of a new project is described step by step in ROLLOUT.md.

.EXAMPLE
  ./deploy.ps1 -ProjectId nexus-showcase-123456 -DomainName nexus.example.com

.EXAMPLE
  ./deploy.ps1 -ProjectId existing-app-project -SharedProject   # host project already runs other services
#>
param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [string]$Region = "europe-west1",
    [string]$Service = "nexus-showcase",
    [string]$Repository = "nexus-showcase",
    [string]$DomainName = "",
    [string]$Tag = "",
    [switch]$AutoApprove,
    [switch]$SharedProject
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Native tools (gcloud, git, python, terraform) report progress on stderr; Windows PowerShell 5.1
# would turn that into terminating errors under "Stop", so native calls run under "Continue" and
# are checked through their exit code instead.
function Invoke-Checked {
    param([string]$What, [scriptblock]$Command)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $Command } finally { $ErrorActionPreference = $previous }
    if ($LASTEXITCODE -ne 0) { throw "$What failed with exit code $LASTEXITCODE" }
}

$buildSa = "$Service-build@$ProjectId.iam.gserviceaccount.com"
$rootDir = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$backendDir = Join-Path $PSScriptRoot "backend"
$wheelsDir = Join-Path $backendDir "wheels"
$tfDir = Join-Path $PSScriptRoot "infra\terraform"

# Guard against deploying into the wrong project by accident: an existing project that runs other
# Cloud Run services is supported, but only when -SharedProject says so explicitly.
$ErrorActionPreference = "Continue"
$existing = @(gcloud run services list --project $ProjectId --region $Region --format "value(metadata.name)" 2>$null |
    Where-Object { $_ -is [string] -and $_ -and $_ -ne $Service })
$ErrorActionPreference = "Stop"
if ($existing.Count -gt 0 -and -not $SharedProject) {
    throw "Project $ProjectId also runs: $($existing -join ', '). Pass -SharedProject if hosting the showcase there is intended."
}

if (-not $Tag) {
    $dirty = git -C $rootDir status --porcelain
    if ($dirty) { throw "Working tree has uncommitted changes; commit first so the image tag (git SHA) is meaningful, or pass -Tag." }
    $Tag = (git -C $rootDir rev-parse --short=12 HEAD).Trim()
}
$image = "$Region-docker.pkg.dev/$ProjectId/$Repository/$($Service):$Tag"

Write-Host "==> Building nexus-agent-framework wheel from $rootDir"
if (Test-Path $wheelsDir) { Remove-Item -Recurse -Force $wheelsDir }
New-Item -ItemType Directory -Force -Path $wheelsDir | Out-Null
Invoke-Checked "wheel build" { python -m build --wheel --outdir $wheelsDir $rootDir }

Write-Host "==> Building $image with Cloud Build as $buildSa"
Invoke-Checked "Cloud Build" {
    gcloud builds submit $backendDir `
        --project $ProjectId `
        --region $Region `
        --config (Join-Path $backendDir "cloudbuild.yaml") `
        --substitutions "_IMAGE=$image" `
        --gcs-source-staging-dir "gs://$ProjectId-$Service-build-src/source" `
        --service-account "projects/$ProjectId/serviceAccounts/$buildSa"
}

Write-Host "==> terraform apply (image tag $Tag)"
$tfArgs = @("-chdir=$tfDir", "apply", "-input=false", "-var", "project_id=$ProjectId", "-var", "region=$Region",
    "-var", "service_name=$Service", "-var", "repository_id=$Repository", "-var", "image_tag=$Tag")
if ($DomainName) { $tfArgs += @("-var", "domain_name=$DomainName") }
if ($AutoApprove) { $tfArgs += "-auto-approve" }
Invoke-Checked "terraform init" { terraform "-chdir=$tfDir" init -input=false }
Invoke-Checked "terraform apply" { terraform @tfArgs }

Write-Host "==> Rolled out $image"
