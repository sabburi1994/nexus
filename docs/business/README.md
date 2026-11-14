# Nexus services business: analysis and plan

Status: draft for the owner, 14 Nov 2026. Analysis only: nothing here has been sent to anyone,
no cloud resources were created, and no money was spent.

These documents review the three launch proposals (Hyderabad, Agra, Coastal Andhra Pradesh) for
selling Nexus based services to Indian businesses, and set out how that business could actually
be delivered with Nexus and the owner's Google Cloud platform.

| # | Document | Question it answers |
|---|---|---|
| 1 | [Business model](01-business-model.md) | What is sold, to whom, at what price; how the three launches differ; what does not add up |
| 2 | [Delivery architecture](02-delivery-architecture.md) | How one client engagement runs end to end, and what Nexus can and cannot do today |
| 3 | [Hosting and cost](03-hosting-and-cost.md) | Shared vs per client projects, Terraform layout, isolation, per client cost and caps |
| 4 | [India compliance and operations](04-india-compliance-and-operations.md) | DPDP Act, residency, GST and invoicing, payments, languages, support |
| 5 | [Roadmap and 90 day pilot](05-roadmap-and-pilot.md) | What to build, in which order, effort, and a measurable first city pilot |
| 6 | [Decisions and risks](06-decisions-and-risks.md) | The decisions only the owner can make |

## Conventions

* **Targets** are referred to by code only: H1 to H10 (Hyderabad), A1 to A10 (Agra), C1 to C12
  (Coastal AP), sometimes with a generic segment word ("clinic", "hotel"). The proposals name
  segments and neighbourhoods, not individual businesses; the code table with neighbourhoods is kept
  privately outside this repository and is not needed to read these documents.
* **Money**: proposal prices are INR. Conversions use **1 USD = 88 INR** and **1 EUR = 100 INR**
  (assumptions, check the day's rate). Cloud and model prices are **list price estimates** from
  public price lists as known at the time of writing, in USD, before tax and free tiers unless
  stated. Re-check every figure on the provider's pricing page before quoting it to a client.
* **Legal and tax** statements are an engineer's reading of the rules, not legal or tax advice.
  Every item marked *confirm* needs an Indian chartered accountant or lawyer (and, for the EU side,
  a Luxembourg adviser) before launch.
* Google Cloud project and billing account identifiers are deliberately left out of this public
  repository.

## The five findings that matter most

1. **The Tier 1 price is viable only as a multi tenant product, not as Nexus generated apps.**
   At 4,999 INR a year (about 57 USD) a client can afford a few minutes of human time per month.
   One shared, template driven storefront serving every Tier 1 client is needed; generating and
   deploying a separate codebase per client with the 7 agent squad would cost more to review and
   maintain than the client pays. See [2](02-delivery-architecture.md) and [3](03-hosting-and-cost.md).
2. **Several promises in the proposals do not exist yet in Nexus or anywhere on the platform**:
   "live site in 15 minutes", WhatsApp onboarding and ledgers, Google Business Profile sync, Razorpay
   split settlement, verified lead counting, Telugu and Hindi storefronts, and "Claude AI
   assistants" (Nexus calls Gemini on Vertex AI only). The showcase simulator is scripted, and the
   ROI figures in `nexus metrics` are heuristics. None of this can be shown to clients as evidence yet.
3. **The performance pricing creates hard problems**: a lead sent through a WhatsApp link cannot be
   verified or deduplicated by the platform, so per lead billing invites disputes; collecting 3% via
   Razorpay Route very likely makes the operator an e-commerce operator under GST (registration, TCS)
   and needs an Indian merchant entity; "pay per patient lead" for doctors may conflict with medical
   ethics rules. A flat or tiered subscription is simpler and safer for the pilot.
4. **An Indian billing presence is a precondition**, not a detail: Razorpay onboarding, UPI
   collection, GST invoices and OIDAR rules for unregistered small businesses all point to an Indian
   entity or an Indian partner who invoices. This decision gates everything else.
5. **Client hosting must be separate from the owner's personal apps.** The existing shared Postgres
   instance is nearly out of connections and holds personal data; the billing accounts are at their
   project quota. Free a project slot (or open a business billing account), create one shared
   `clients` project with its own Cloud SQL instance, budgets and remote state, and keep the 50 USD
   personal caps untouched.
