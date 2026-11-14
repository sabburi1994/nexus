# Showcase rollout: move to a dedicated Google Cloud project

Moves the public showcase (`nexus-showcase` on Cloud Run, domain `nexus.abburi.info`) out of the
project it shares with another app into a project of its own, managed by Terraform
(`apps/showcase/infra/terraform`). After the move:

* the runtime service account `nexus-showcase-run` has **no project roles** (the showcase makes no
  server side model calls; visitors may bring their own Gemini key per request);
* Cloud Build runs as `nexus-showcase-build`, which can push only to the app's own Artifact Registry
  repository `nexus-showcase`;
* Cloud Run: min 0, max 2 instances, 1 CPU, 512Mi, CPU only during requests, startup CPU boost,
  `/health` startup and liveness probes, deletion protection on.

All commands are PowerShell, run from the repository root of a **clean checkout of `main` at the
merged commit** (the image tag is the git SHA). Terraform keeps its state locally in
`apps/showcase/infra/terraform/terraform.tfstate` (git ignored): keep that file and back it up.

Prerequisites: `gcloud` signed in as the owner, `gcloud auth application-default login` done
(Terraform uses ADC), Terraform 1.5 or newer, Python with `pip install build`.

## 0. Variables

```powershell
$OldProject = "<project id that runs nexus-showcase today>"   # from the hand-over note; not committed here
$Region     = "europe-west1"
$Domain     = "nexus.abburi.info"
$Service    = "nexus-showcase"
$Project    = "nexus-showcase-$(Get-Random -Minimum 100000 -Maximum 1000000)"
$Tf         = "apps/showcase/infra/terraform"
$Tag        = (git rev-parse --short=12 HEAD).Trim()
"Project: $Project  Tag: $Tag"
git status --porcelain   # must print nothing
```

Write `$Project` down: every later step and every later deploy needs it.

## 1. Create the project and link billing

```powershell
gcloud projects create $Project --name "Nexus showcase"
$Billing = (gcloud billing projects describe $OldProject --format "value(billingAccountName)") -replace '^billingAccounts/', ''
gcloud billing projects link $Project --billing-account $Billing
gcloud billing projects describe $Project --format "value(billingEnabled)"   # expect True
```

## 2. Enable the APIs Terraform itself needs

Terraform enables the app APIs (Cloud Run, Artifact Registry, Cloud Build, Logging, Secret Manager).
It needs these first:

```powershell
gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com iam.googleapis.com --project $Project
```

## 3. Terraform: foundation (APIs, service accounts, registry)

The Cloud Run service needs an image that does not exist yet, so the first apply is targeted.
`image_tag=bootstrap` only satisfies the required variable; no service is created in this step.

```powershell
terraform -chdir=$Tf init
terraform -chdir=$Tf apply -var "project_id=$Project" -var "image_tag=bootstrap" `
  -target module.nexus_base `
  -target google_artifact_registry_repository.images `
  -target google_service_account.build `
  -target google_artifact_registry_repository_iam_member.build_push `
  -target google_project_iam_member.build_logs `
  -target google_project_iam_member.build_source_read
```

Give IAM a minute or two to propagate before the build.

## 4. Build the image with Cloud Build, tagged with the git SHA

```powershell
Remove-Item -Recurse -Force apps/showcase/backend/wheels -ErrorAction SilentlyContinue
python -m build --wheel --outdir apps/showcase/backend/wheels .
$Image = "$Region-docker.pkg.dev/$Project/nexus-showcase/$($Service):$Tag"
gcloud builds submit apps/showcase/backend `
  --project $Project --region $Region `
  --config apps/showcase/backend/cloudbuild.yaml `
  --substitutions "_IMAGE=$Image" `
  --service-account "projects/$Project/serviceAccounts/$Service-build@$Project.iam.gserviceaccount.com"
gcloud artifacts docker images list "$Region-docker.pkg.dev/$Project/nexus-showcase" --include-tags
```

## 5. Terraform: full apply (Cloud Run service, no domain yet)

```powershell
terraform -chdir=$Tf apply -var "project_id=$Project" -var "image_tag=$Tag"
$Url = terraform -chdir=$Tf output -raw service_url
$Url
```

## 6. Verify the new service on its run.app URL

```powershell
Invoke-RestMethod "$Url/health"                               # status ok
(Invoke-RestMethod "$Url/api/v1/framework-health").version    # 0.3.0 (the old service reports 0.2.0)
(Invoke-WebRequest "$Url/" -UseBasicParsing).StatusCode       # 200, UI served
Invoke-RestMethod "$Url/api/v1/scan" -Method Post -ContentType "application/json" `
  -Body '{"target":"Grid storage","sector":"Energy"}' | Select-Object model     # deterministic-baseline
gcloud run services describe $Service --project $Project --region $Region `
  --format "value(spec.template.spec.serviceAccountName,spec.template.spec.containers[0].image)"
gcloud projects get-iam-policy $Project --flatten "bindings[].members" `
  --filter "bindings.members:$Service-run@" --format "value(bindings.role)"       # expect nothing
```

Stop here and roll back (section 9, first case) if any check fails.

## 7. Move the domain mapping

The domain must be verified for the signed in account:

```powershell
gcloud domains list-user-verified   # must list abburi.info (or the domain itself)
Resolve-DnsName $Domain -Type CNAME | Select-Object NameHost   # ghs.googlehosted.com
```

A domain can be mapped in one place at a time, so the old mapping goes first. The site is
unavailable (or serves a certificate error) from this point until the new certificate is issued,
usually 15 to 60 minutes. DNS does not change: the CNAME to `ghs.googlehosted.com` stays.

```powershell
gcloud beta run domain-mappings describe --domain $Domain --region $Region --project $OldProject   # note it for rollback
gcloud beta run domain-mappings delete --domain $Domain --region $Region --project $OldProject --quiet
terraform -chdir=$Tf apply -var "project_id=$Project" -var "image_tag=$Tag" -var "domain_name=$Domain"
terraform -chdir=$Tf output domain_mapping_records   # expect CNAME ghs.googlehosted.com.
```

Wait for the certificate (repeat until `Ready` and `CertificateProvisioned` are `True`):

```powershell
gcloud beta run domain-mappings describe --domain $Domain --region $Region --project $Project `
  --format "table(status.conditions[].type,status.conditions[].status,status.conditions[].message)"
```

## 8. Verify the custom domain and certificate

```powershell
(Invoke-RestMethod "https://$Domain/api/v1/framework-health").version    # 0.3.0 = new service
(Invoke-WebRequest "https://$Domain/health" -UseBasicParsing).Headers["X-Nexus-Framework-Version"]   # 0.3.0
curl.exe -sSvo NUL "https://$Domain/health" 2>&1 | Select-String "subject:|issuer:|expire date:|SSL certificate verify ok"
```

Expect a certificate for the domain issued by Google Trust Services, `SSL certificate verify ok`,
and HTTP 200.

## 9. Rollback

* **New service fails before step 7**: nothing user facing changed. Fix and repeat steps 4 and 5,
  or leave the new project idle. To remove it: set `deletion_protection = false`
  (`-var deletion_protection=false`), apply, then `terraform -chdir=$Tf destroy -var "project_id=$Project" -var "image_tag=$Tag"`.
* **New service or certificate fails after step 7**: remove the new mapping and restore the old one
  (the old service still runs until step 10):

  ```powershell
  terraform -chdir=$Tf apply -var "project_id=$Project" -var "image_tag=$Tag"   # no domain_name: mapping removed
  gcloud beta run domain-mappings create --service $Service --domain $Domain --region $Region --project $OldProject
  ```

## 10. Remove the old service (only after step 8 passed)

```powershell
gcloud run services describe $Service --region $Region --project $OldProject --format "value(status.url)"   # confirm the target
gcloud run services delete $Service --region $Region --project $OldProject --quiet
```

The old project's `cloud-run-source-deploy` repository still holds the showcase images. After the
service is gone they can be removed too (check the listing first):

```powershell
gcloud artifacts docker images list "$Region-docker.pkg.dev/$OldProject/cloud-run-source-deploy/$Service" --include-tags
gcloud artifacts packages delete $Service --repository cloud-run-source-deploy --location $Region --project $OldProject --quiet
```

Then hand over to the cloud settings session: the old project's default compute service account no
longer needs any rights for the showcase.

## Routine deploys afterwards

From a clean checkout at the commit to ship:

```powershell
./apps/showcase/deploy.ps1 -ProjectId $Project -DomainName $Domain
```

It refuses to run in a project that hosts other Cloud Run services, builds with Cloud Build as the
build account, tags the image with the git SHA and applies Terraform with that tag.
