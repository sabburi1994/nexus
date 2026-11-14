# 6. Decisions and risks for the owner

## 6.1 Decisions only the owner can make

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | **Who invoices and collects in India** | A: from Luxembourg; B: Indian company or LLP; C: Indian partner reseller | C for the pilot, B after proof of demand (document 4, 4.5) |
| D2 | **Pricing model** | Keep 3% / per lead performance pricing; or flat subscription with lead reporting | Flat 4,999 + GST for the pilot; no Razorpay Route; revisit after measuring leads (document 1, 1.6) |
| D3 | **Where client hosting is billed** | Free a slot on a personal billing account; ask Google for more quota; open a separate business billing account (later in the Indian entity's name) | Separate business billing account if possible, otherwise free a slot from a retired project; never mix with the personal 50 USD caps |
| D4 | **First city and local partner** | Hyderabad, Agra, Coastal AP | The city with a trusted partner; default Hyderabad |
| D5 | **Region for client data** | europe-west1 now; asia-south1 from the start | europe-west1 for the pilot, region portable, decide at day 90; India region for any client that requires it |
| D6 | **What "Claude AI" means in Tier 2** | Operator builds assistants on the Claude API (or Claude on Vertex AI); or clients buy Claude seats and the operator trains them; or use Gemini and drop the brand name | Build on the API with a small model default and per client caps; sell the outcome, not a model brand |
| D7 | **Time commitment and on site presence** | Part time remote; periodic trips; local representative | Budget at least one on site week per city and a paid local partner; part time doubles every roadmap estimate |
| D8 | **Where these documents live** | Keep in the public `nexus` repo; move to a private repo | These pages contain pricing strategy and a candid critique; consider moving `docs/business/` to a private repo and keeping only generic hosting guidance public |

## 6.2 Main risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Tier 1 economics: too little revenue per client to cover human time | High | High | Multi tenant product, 45 minute onboarding cap, partner first line support, price review at day 90 |
| Promises the software cannot keep (15 minute go live, verified leads, GBP sync, Claude assistants) | High (today) | High (trust, refunds) | Remove from pitches until shipped; concierge pilot with honest wording |
| Regulatory exposure from payment splitting (GST e-commerce operator, TCS, withholding) | High if Route is used | High | Client's own gateway; operator invoices separately |
| Unsolicited previews and WhatsApp outreach (content rights, impersonation, number bans, telemarketing rules) | Medium | High | Consent first outreach, unlisted and expiring previews, no scraped photos or reviews |
| Medical and coaching sector rules (patient referral fees, misleading claims, minors' data) | Medium | High | Flat pricing for doctors, factual content, no pixels on coaching sites, parental consent flow |
| DPDP breach or cross tenant leak | Low to medium | Very high (penalties up to 250 crore INR, reputation) | Row level security tests, per tenant databases for Tier 2, minimal forms, breach runbook, quarterly restore and access review |
| Tier 2 AI usage cost above the retainer | Medium | Medium | Included allowance, small model default, hard per client cap |
| Single person dependency in Luxembourg, time zone and travel | High | Medium | Local partner, runbooks, recorded training, response targets in IST |
| Translation errors in Telugu or Hindi on prices or health text | Medium | Medium | Native review, glossary, prices never machine translated |
| Owner's personal platform affected by client load or incidents | Low with separation | High | Separate project, billing and database; client budgets with Pub/Sub alerts |

## 6.3 Open questions to answer before the pilot

1. Is the owner's employment or residence status in Luxembourg compatible with running this
   business, and in which legal form?
2. Who is the local partner in the first city, and on what terms (fee, revenue share, exclusivity)?
3. Are the proposals' prices inclusive or exclusive of GST?
4. Who owns the client's domain, GBP listing and content after cancellation? (Recommendation: the
   client always does.)
5. Does any target segment in the first city need India only hosting by contract?
6. Which clients, if any, may be told they are a pilot, with a free or refundable first period?
