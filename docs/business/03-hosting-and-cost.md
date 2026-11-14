# 3. Hosting model and cost

All prices are **estimates from public list prices** as known at the time of writing (USD, before
tax). Check each one on the Google Cloud, Anthropic and Meta pricing pages before quoting a client.

## 3.1 Constraints from the current platform

* Both of the owner's billing accounts are at their **project link quota**: a recent attempt to
  create a dedicated project for the showcase failed for this reason, and the showcase was placed in
  an existing project instead.
* The Postgres instance shared by the owner's own apps is a `db-f1-micro` (about 25 connections)
  with most of its connection budget already allocated, and it holds personal data. **Client data
  must not go there.**
* Platform standards to keep: Cloud Run with request based CPU (`cpu_idle = true`), scale to zero,
  at most 2 instances, security headers, non root containers, images tagged with the git SHA, GCS
  remote state, local git hooks, no email notifications.
* The personal caps (50 USD infra, 50 USD AI per month) are for the owner's own apps. Client costs
  should be tracked and capped separately so a client spike never eats the personal budget.

## 3.2 Per client project or shared multi tenant project

| | One Google Cloud project per client | One shared `clients` project, tenants inside |
|---|---|---|
| Isolation | Strongest: IAM, quotas, logs, billing all separate | Logical: per tenant service accounts, databases, secrets and labels; Cloud SQL client role and Vertex AI access are project wide |
| Billing quota | Needs one project link per client: **blocked today** | Needs one free slot once |
| Fixed cost per client | Its own Cloud SQL (about 10 USD a month minimum), registry, state | Shares one instance and registry; near zero marginal cost |
| Cost attribution | Automatic (per project) | Labels (`tenant`, `tier`) and an in app usage ledger |
| Ops effort | One Terraform root, state, budget and API set per client | One platform root plus a small root per Tier 2 client |
| Exit / handover | Transfer the whole project | Export database and content; redeploy elsewhere |
| Fits | Tier 2 clients who require it **and pay their own Google Cloud bill** | All Tier 1 (as rows in one service) and most Tier 2 |

**Recommendation**

1. **One shared project, `clients` (production).** Free one billing slot by unlinking billing from a
   retired project once its backups are checked (or ask Google for a quota increase, or open a
   separate business billing account; see decision D3 in document 6). Use Cloud Run tagged
   revisions with no traffic for previews instead of a second staging project.
2. **Tier 1 is not per client infrastructure at all**: one storefront service, one database,
   tenants as rows protected by Postgres row level security; only the custom domain is per tenant.
3. **Tier 2 gets per client resources inside the shared project**: own service account, own
   database and user on the shared instance, own secrets, own Cloud Run service(s) and job(s), own
   Terraform state prefix and budget.
4. **Client owned project** (the client's Google Cloud account and billing, operator given a
   scoped IAM role) for any Tier 2 client who needs strict isolation, data residency of their own
   choosing, or large usage. This sidesteps the quota entirely and puts the cloud bill on the client.

## 3.3 Region

| | europe-west1 (Belgium), today's platform | asia-south1 (Mumbai) or asia-south2 (Delhi) |
|---|---|---|
| Latency to the target cities | About 130 to 160 ms round trip plus cold start | About 20 to 40 ms |
| Cloud Run domain mapping | Available (free) | At the time of writing not offered in this region; needs a global external Application Load Balancer (about 18 USD a month fixed) or a hosting front end |
| Cloud Run price tier | Tier 1 (cheapest) | Tier 2 (higher unit price) |
| Selling point "your data stays in India" | No | Yes, for stored data; model inference location depends on the model and endpoint used |
| Legal requirement under DPDP | Not required for ordinary business data (document 4) | Same |

**Recommendation:** run the pilot in europe-west1 (no fixed load balancer, all patterns already
proven), keep the region a variable everywhere, and serve storefront pages as static, cacheable
HTML so most page views never touch the cold service. Decide at the end of the pilot whether to move
client data to asia-south1, before the database grows; move earlier if a Tier 2 client contract
requires India residency (decision D5).

Once there are more than about 15 tenants, put a **global external Application Load Balancer with
Cloud CDN and a Certificate Manager certificate** in front of Cloud Run (serverless network endpoint
group). It costs about 18 USD a month plus egress, gives Indian edge caching, handles any number of
tenant domains, and makes a later move to asia-south1 a backend swap rather than a domain migration.

## 3.4 Terraform layout using the Nexus modules

Client infrastructure and the tenant list live in a **new private repository** (for example
`nexus-clients`), never in this public one. Modules are pulled from this repo by tag.

```text
nexus-clients/                     (private)
  platform/                        state prefix platform/
    main.tf      APIs, state bucket, registry, Cloud SQL instance (nexus_cloud_sql),
                 storefront service (nexus_cloud_run), migrate job (nexus_cloud_run_job),
                 budgets with Pub/Sub only notifications, later load balancer + CDN
  tier1/                           state prefix tier1/
    tenants.yaml code, vertical, domain, languages (no personal data)
    main.tf      for_each tenant: domain mapping (or LB certificate entry)
  clients/<code>/                  state prefix clients/<code>/  (one per Tier 2 client)
    main.tf      nexus_app (enable_ai only if needed), service account, database + user,
                 secrets, nexus_cloud_run services, nexus_cloud_run_job, label budget
```

```hcl
module "portal" {
  source                = "git::https://github.com/sabburi1994/nexus.git//infra/terraform/modules/nexus_cloud_run?ref=v0.3.1"
  project_id            = var.project_id
  region                = var.region
  service_name          = "c-${var.client_code}-portal"
  image                 = "${var.region}-docker.pkg.dev/${var.project_id}/clients/portal"
  image_tag             = var.git_sha            # never "latest"
  service_account_email = google_service_account.client.email
  cloud_sql_instances   = [var.sql_connection_name]
  secret_files          = [{ secret_id = google_secret_manager_secret.db.secret_id, mount_path = "/run/secrets/db", file_name = "password" }]
  max_instances         = 2
  labels                = { tenant = var.client_code, tier = "t2" }
}
```

**Remote state per client:** one versioned GCS bucket in the `clients` project with uniform access,
only the operator's account as writer, and one prefix per root (`platform/`, `tier1/`,
`clients/<code>/`). Each prefix has its own lock, so a mistake in one client's plan cannot touch
another's state. Off boarding a client is `terraform destroy` on its prefix (after flipping
`deletion_protection`), then deleting the prefix.

**Artifact Registry:** one repository `clients` (images `storefront`, `portal`, `assistant`), images
tagged with the git SHA, cleanup policy keeping the last 10 tagged versions and deleting untagged
after 14 days (same as the showcase). Builds run with a dedicated build service account that can
write only to this repository and read only its own staging bucket (pattern in
`apps/showcase/infra/terraform/main.tf`).

**Secret Manager:** one secret per credential per client (database password, the client's Razorpay
webhook secret, WhatsApp token if the client uses one), with `secretAccessor` granted on that secret
only to that client's service account (`grant_secret_access` in the modules). No project wide
accessor. Never store a client's payment keys if the design can avoid it (section 2.3: the client's
own merchant account, webhooks verified with a per client secret).

## 3.5 Shared Cloud SQL with per tenant databases

* **Instance:** a new `nexus_cloud_sql` instance in the `clients` project. Start at `db-f1-micro`
  (about 25 connections) for the pilot; move to `db-g1-small` (about 50 connections) before adding
  the fourth Tier 2 client. PITR, SSL only, no authorized networks, socket connector only (module
  defaults).
* **Tier 1:** one database `storefront`, every table has `tenant_id`, Postgres **row level
  security** policies keyed on a session setting the app sets per request, plus tests that a query
  without a tenant returns nothing.
* **Tier 2:** one database and one login user per client, created by Terraform with the password
  read from that client's secret (module `users` map). After creation, run per client:

  ```sql
  ALTER DATABASE c_h9 OWNER TO c_h9;
  REVOKE ALL ON DATABASE c_h9 FROM PUBLIC;
  ```

  Users created through the Cloud SQL API join `cloudsqlsuperuser`; without the revoke, every
  tenant user could connect to every database. The module does not run this SQL today: add it to
  each client's migrate job, and test it by trying to connect across tenants.
* **What is shared and why it is acceptable:** `roles/cloudsql.client` is granted at project level,
  so any tenant service account can open a socket to the instance; isolation is enforced by Postgres
  credentials and grants. Health or finance Tier 2 clients get their own instance (about 10 USD a
  month more) or their own project.
* **Connection budget:** storefront 2 instances x pool 3 = 6; each Tier 2 client 2 x 2 + 1 for the
  job = 5. A `db-f1-micro` holds the storefront plus 3 Tier 2 clients; a `db-g1-small` about 8.

## 3.6 Monthly cost per client (estimates)

Assumptions: 1 USD = 88 INR; europe-west1; storefront pages mostly static and cached; one shared
`clients` project; the free tiers on the billing account are already used by the owner's apps, so
they are ignored; model prices from the providers' current list (Claude Haiku 5.5 at 0.10 / 0.50
USD per million input / output tokens, Claude Sonnet 5.5 at 2 / 10, cache reads about a tenth of
input); WhatsApp India template prices roughly 0.115 INR (utility) and 0.78 INR (marketing) per
message, service replies inside the 24 hour window free.

**Shared platform, fixed per month**

| Item | Pilot (up to about 15 tenants) | Scale (100+ tenants) |
|---|---|---|
| Cloud SQL `db-f1-micro` + 10 GB SSD + backups | about 10 USD | `db-g1-small`: about 28 USD |
| Artifact Registry, state bucket, build staging, secrets | about 1 USD | about 2 USD |
| Load balancer + CDN | none (domain mappings) | about 18 USD + egress |
| Cloud Scheduler, logging (within free allotment per project) | under 1 USD | about 1 USD |
| **Total fixed** | **about 12 USD** | **about 50 USD** |

**Tier 1 client, marginal per month**

| Item | Estimate |
|---|---|
| Cloud Run compute (2,000 page views, mostly cached) | under 0.05 USD |
| Egress (about 1 GB) | about 0.10 USD |
| AI content (onboarding spread over the year, monthly edits, review drafts) with a small model | 0.05 to 0.20 USD |
| Voice note transcription (10 minutes) | about 0.15 USD |
| WhatsApp utility messages (monthly report, edit confirmations) | about 0.02 USD |
| **Marginal** | **about 0.30 to 0.50 USD** |
| **With share of fixed costs** | **about 1.10 USD at 15 tenants, about 0.80 USD at 100** |

Against about 4.70 USD a month of base revenue, cloud and AI are not the problem; operator time is.

**Tier 2 client, per month**

| Item | Estimate |
|---|---|
| Portal + assistant services on Cloud Run (50,000 requests, about 1 s each) | 1.50 to 3 USD |
| Share of the shared Cloud SQL instance | about 3 USD (or 10 to 30 USD for a dedicated instance) |
| Secrets, registry share, jobs, document storage (5 GB) | about 1 USD |
| **Infrastructure** | **about 5 to 8 USD** |

AI usage dominates Tier 2 and depends on the model and the number of staff using it. Per request
assumed: 8,000 input tokens (6,000 of them a cached catalogue or SOP context), 800 output tokens,
no extended reasoning (reasoning tokens bill as output and can double these figures):

| Usage pattern | Requests / month | Claude Haiku 5.5 class | Claude Sonnet 5.5 class |
|---|---|---|---|
| Light: 10 staff x 10 requests x 22 days | 2,200 | about 1.50 USD | about 28 USD |
| Medium: 30 x 20 x 22 | 13,200 | about 9 USD | about 165 USD |
| Heavy: 100 x 20 x 22 | 44,000 | about 30 USD | about 555 USD |

The 10,000 INR retainer is about 114 USD. **A medium client on a mid tier model costs more in
tokens than the retainer brings in.** Price Tier 2 with an included AI allowance (for example
20 USD a month), a small model by default with the mid tier model only for quote drafting, and usage
above the allowance billed at cost plus a margin, with a hard monthly cap the client agrees to.
Claude through Vertex AI is billed by Google at its own partner prices; check them before choosing
between the Anthropic API and Vertex AI.

## 3.7 Keeping each client under a cap

Budgets in Google Cloud alert, they do not stop spending, and alerts arrive hours late. So the cap is
enforced in layers, cheapest first:

1. **Structural caps** (already platform standard): `max_instances = 2`, request based CPU,
   timeouts, per IP rate limits (`apps/showcase/backend/src/abuse_controls.py` is a starting point),
   upload size limits.
2. **Per tenant usage ledger, enforced before every paid call.** A table
   `usage(tenant, month, model, input_tokens, output_tokens, cost_usd, messages, stt_minutes)` and
   one wrapper around every model, speech and WhatsApp call that refuses when the tenant's monthly cap
   is reached (fail closed, show "monthly AI allowance used"). This generalises
   `AgentContext.max_budget_usd` (`src/nexus/agents/context.py`) from per run to per tenant per
   month. Suggested caps: Tier 1 0.50 USD, Tier 2 the agreed allowance.
3. **Provider side limits:** a separate Anthropic workspace (or API key) per Tier 2 client with its
   own spend limit where the Console offers it; Vertex AI requests carry a `tenant` label so the
   billing report splits by client.
4. **Labels and budgets:** labels `tenant` and `tier` on every Cloud Run service, job, bucket and
   secret. One budget for the `clients` project (for example 40 USD in the pilot) and one budget per
   Tier 2 label, with notifications to a **Pub/Sub topic only** (`disable_default_iam_recipients =
   true`, no email channels). A small Cloud Run job subscribed to the topic records the alert and, at
   100%, sets the tenant's AI flag off in the database.
5. **Monthly reconciliation:** compare the ledger with the billing report by label; re-price any
   client whose real cost is over 30% of their fee.
