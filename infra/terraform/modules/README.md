# Nexus platform Terraform modules

Shared building blocks for apps that run on Cloud Run in their own Google Cloud project.
A complete example that uses all of them is in [`examples/terraform/platform_app`](../../../examples/terraform/platform_app/main.tf).

| Module | What it creates |
| :--- | :--- |
| [`nexus_app`](nexus_app/main.tf) | Core APIs and the runtime service account; `roles/aiplatform.user` only when `enable_ai = true`. No project wide Secret Manager access. |
| [`nexus_cloud_run`](nexus_cloud_run/variables.tf) | Cloud Run v2 service with platform defaults, per secret IAM, optional Cloud SQL socket and Direct VPC egress, probes, public invoker toggle. |
| [`nexus_cloud_run_job`](nexus_cloud_run_job/variables.tf) | Cloud Run v2 job (migrations, batch) with an optional Cloud Scheduler trigger run by a dedicated invoker account. |
| [`nexus_cloud_sql`](nexus_cloud_sql/variables.tf) | Cloud SQL instance with PITR, SSL only, deletion protection, databases, and users whose passwords come from Secret Manager without entering state. |
| [`nexus_vm`](nexus_vm/main.tf) | Always free e2-micro VM (unchanged). |

## Platform defaults (`nexus_cloud_run`)

| Setting | Default | Why |
| :--- | :--- | :--- |
| `min_instances` / `max_instances` | `0` / `2` | Scale to zero; caps worst case spend. |
| `cpu_idle` | `true` | CPU billed only while handling requests. |
| `startup_cpu_boost` | `true` | Faster cold starts at no steady state cost. |
| `cpu` / `memory` | `"1"` / `"512Mi"` | |
| `image_tag` | required | Every deploy names its image; `latest` is rejected. |
| `deletion_protection` | `true` | `terraform destroy` needs an explicit opt out first. |
| `allow_unauthenticated` | `true` | Public services; set `false` for internal ones. |
| `grant_secret_access` | `true` | `secretAccessor` on each referenced secret only. |
| `startup_probe` | TCP on the port | Set `{ path = "/health" }` for an HTTP check. |
| `liveness_probe` | none | Set `{ path = "/health" }` to restart hung instances. |

Secrets: `secrets` exposes versions as environment variables; `secret_files` mounts them at
`<mount_path>/<file_name>` (one directory per secret, mount paths must not overlap).

## Migrating an app (Wave 2)

The resource addresses match what the apps use today (`google_cloud_run_v2_service`, plus
`google_cloud_run_service_iam_member` for public access), so adopting a module is a `moved` block
per resource, not a recreate:

```hcl
module "app_service" {
  source                = "../../../nexus/infra/terraform/modules/nexus_cloud_run" # or a git source pinned to a tag
  project_id            = var.project_id
  service_name          = "myapp"
  image                 = "europe-west1-docker.pkg.dev/${var.project_id}/containers/myapp"
  image_tag             = var.image_tag
  service_account_email = google_service_account.app.email
  deletion_protection   = false # keep what the app has today, flip later
}

moved {
  from = google_cloud_run_v2_service.myapp
  to   = module.app_service.google_cloud_run_v2_service.service
}

moved {
  from = google_cloud_run_service_iam_member.public_access
  to   = module.app_service.google_cloud_run_service_iam_member.public_access[0]
}
```

Run `terraform plan` and expect only in place updates (scaling, `cpu_idle`, probes, labels). A plan
that shows the service being replaced means an address or an immutable field differs: stop there.

Notes for upgrading callers of the previous module versions:

* `nexus_cloud_run`: `image` is now the repository path **without** a tag and `image_tag` is
  required. The public invoker resource now has `count`; the module carries the `moved` block for it.
* `nexus_app`: the project wide `roles/secretmanager.secretAccessor` grant is removed and is revoked
  on the next apply. Reference each secret through `nexus_cloud_run` / `nexus_cloud_run_job` (which
  grant per secret) before applying. The Vertex AI grant now has `count` (moved block included).
* `nexus_cloud_sql` needs Terraform 1.11+ and google provider 7+ (ephemeral resources and write only
  passwords). Bump `password_wo_version` after adding a new secret version to rotate a password.

## Validating

```bash
cd infra/terraform/modules/nexus_cloud_run && terraform init -backend=false && terraform validate
cd examples/terraform/platform_app && terraform init -backend=false && terraform validate
```
