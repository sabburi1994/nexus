# 5. Roadmap and 90 day pilot

Effort sizes are for one developer working with AI coding assistance, in **full time weeks**:
S = up to 1 week, M = 2 to 3 weeks, L = 4 to 6 weeks. If the work is part time, double the
calendar time. Estimates assume the existing Nexus modules and showcase patterns are reused.

## 5.1 Vertical templates derived from the pitches

The 32 targets collapse into five Tier 1 templates and three Tier 2 starting points.

| Template | Targets | Core sections | Special rules |
|---|---|---|---|
| **Services and appointments** | H1, A6, C5, C12 (clinics); H2, A5, C9 (coaching); H6 (interiors) | Services, team, timings, map, request a callback form, WhatsApp and call buttons, FAQs | Clinics: factual content only, flat price. Coaching: no tracking pixels, parent or 18+ question |
| **Trade catalogue** | H3, A4, C3, C4, C7 | Searchable catalogue with grades or specs, MOQ, inquiry basket sent as form + WhatsApp | Optional buyer login for price lists |
| **Shop and lookbook** | H5, A2, A3, A7, C1, C2, C8 | Collections, product pages, checkout on the client's own gateway, shipping and returns | Food (A3): FSSAI number before checkout |
| **Stays and tours** | H7, A1, C11, A8 | Rooms or packages, availability request, advance payment, policies | Overbooking risk: start with "request + confirm", not instant booking |
| **Food ordering** | H4 | Menu, area, order and pay for pickup or delivery | FSSAI; menu price changes by WhatsApp |
| Tier 2: **B2B portal + quoting assistant** | H9, A9, C6, C10 | Catalogue, RFQ intake, assistant drafts quotes from the price book, staff approve | No autonomous sending |
| Tier 2: **Package booking + front desk assistant** | H8, A10 | Test packages, branch selection, booking, FAQ assistant | Health data minimisation; dedicated database |
| Tier 2: **Sales follow up assistant** | H10 | Project pages, site visit booking, follow up drafts in Telugu / Hindi / English | RERA numbers mandatory |

Start the pilot with three templates (Services, Trade catalogue, Stays) which cover 17 of the 25
Tier 1 targets and need no checkout.

## 5.2 Phases

### Phase 0: foundations and honesty fixes (about 3 weeks, before any client)

| Work | Size |
|---|---|
| Owner decisions D1 to D6 (document 6): billing presence, pricing, city, partner, region, Claude or Gemini | owner |
| Free a billing slot; create the `clients` project; private `nexus-clients` repo; state bucket; Cloud SQL `db-f1-micro`; Artifact Registry; budgets with Pub/Sub only notifications | S |
| Data processing agreement, client terms, privacy notice templates (EN, TE, HI) reviewed by a lawyer | owner + lawyer |
| Nexus: make README and showcase claims match the code (QA does not run tests, MCP exposes 5 tools, ROI is heuristic, simulator is scripted) | S |
| Nexus: QA actually runs the generated tests in a sandboxed subprocess with a timeout, and healing uses real failures | M |
| Nexus: fix generated package names, add a Dockerfile, make the DevOps agent render Terraform from the platform modules (max 2 instances, no project wide AI grant, no GitHub workflow file) | S |
| Nexus: `AnthropicProvider` beside `VertexAIProvider`, if Claude is part of the offer | S |

### Phase 1: Tier 1 minimum product (about 7 weeks)

| Work | Size |
|---|---|
| Multi tenant storefront service: tenant config, row level security, static pre rendering, custom domains, EN + TE / HI | L |
| Templates: Services, Trade catalogue, Stays | M |
| Intake web form + operator approval queue | S |
| Nexus content agent: `TenantProfile` schema, copy and translation drafts, catalogue extraction from photos, glossary per vertical | M |
| Lead capture (form + click events), consent log, monthly report | S |
| Per tenant usage ledger and cost guard (generalising `AgentContext.max_budget_usd`) | S |
| Client portal v0: see leads, request edits, export data, delete account | M |
| `nexus tenant` CLI: create, preview (tagged revision), publish, export, delete | S |

### Phase 2: complete Tier 1 during the pilot (about 7 weeks)

| Work | Size |
|---|---|
| Shop and Food templates; checkout on the client's own gateway with verified webhooks | M |
| WhatsApp Cloud API: edits and photos from owners, voice note transcription with read back, monthly report template | M |
| Google Business Profile: guided manual linking first; API posting only after access is granted | S |
| Load balancer + CDN + Certificate Manager once past about 15 tenants | S |
| Uptime checks, push alerts, runbooks, restore drill | S |

### Phase 3: Tier 2 productisation (about 9 weeks)

| Work | Size |
|---|---|
| Assistant service template: retrieval over client documents, tool calls behind approval, audit log, per client spend cap, small model default | L |
| B2B portal template (catalogue, RFQ, reorder) | L |
| Per client Terraform generator from a `clients/<code>` template; per client Anthropic workspace or key | S |
| Workshop kit: SOP playbook templates, short videos in Telugu and Hindi | M |
| Measured outcome reporting for Tier 2 (quote turnaround before and after, from the portal's own timestamps) | S |

### Phase 4: scale (after a successful pilot)

Second city with a new local partner; Indian entity and automated GST invoicing; partner portal with
commission statements; decision on asia-south1; self serve onboarding for the simplest template.

**Total before Tier 1 is complete: about 17 full time weeks (Phases 0 to 2).** The proposals' 60 day
launch therefore cannot rely on finished software; the pilot below runs as a **concierge pilot**:
Phase 1 software plus manual work by the operator and the local partner where tooling is missing.

## 5.3 90 day pilot for the first city

**Prerequisites (Day 0):** Phase 0 and Phase 1 done; a local partner contracted; the billing and
invoicing route chosen (document 4, 4.5); price list with GST; DPA and notices approved.

**City:** the one where the owner has a trusted local partner. Default suggestion: Hyderabad
(largest market, Telugu and Hindi, and the same partner and language extend later to the Coastal AP
corridor). Agra adds Hindi only and is the furthest from a Telugu speaking network.

| Days | Activities | Exit check |
|---|---|---|
| 1 to 30 | Partner and 3 referral partners briefed; outreach in person and through referrals only; 15 previews built after a "yes"; first 10 clients live on Services, Trade catalogue, Stays | 10 live clients with signed DPA; onboarding time measured for each |
| 31 to 60 | 25 clients live; Phase 2 WhatsApp edits and checkout shipped to 3 clients; first monthly reports; one paid Tier 2 discovery | Reports delivered on time; first renewal intent survey |
| 61 to 90 | 30 to 40 clients live; Tier 2 discovery turned into a scoped proposal; cost and time review; go or no go for city two | Success criteria below |

**Success criteria (measured, not projected):**

| Area | Metric | Target by day 90 |
|---|---|---|
| Demand | Tier 1 clients live with a signed DPA | at least 30 |
| Demand | Qualified meetings converted to signed clients | at least 25% |
| Demand | Paid Tier 2 discovery engagements | at least 1 |
| Delivery | Median time from complete intake to live site | at most 1 business day |
| Delivery | Operator plus partner time per onboarding / per client per month | at most 45 min / at most 15 min |
| Quality | Mobile Largest Contentful Paint at the 75th percentile, measured from India | at most 2.5 s |
| Quality | Storefront availability | at least 99.5% |
| Quality | Cross tenant data exposures; wrong prices published | 0; 0 |
| Value | Live clients with at least 10 counted leads in month 2 | at least 60% |
| Value | Clients stating they will renew at full price | at least 70% |
| Cost | Cloud plus AI per Tier 1 client per month | at most 1.50 USD |
| Cost | Total `clients` project spend per month | at most 40 USD |
| Compliance | Forms with bilingual notice and consent log; export and deletion tested | 100%; yes |

**Stop or rework if:** fewer than 15 clients live by day 90, operator time above 2 hours per client
per month, any cross tenant exposure, or renewal intent below 40%.

**Pilot budget to plan for (estimates):** cloud 15 to 40 USD a month; AI under 20 USD a month;
WhatsApp messaging a few USD; the local partner's fee or revenue share; referral commissions; travel
for at least one on site week; one off legal and accounting setup. The last three dominate.
