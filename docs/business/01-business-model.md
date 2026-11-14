# 1. Business model summary

## 1.1 What is sold

The three proposals describe the same two product tiers, sold door to door and over WhatsApp,
operated remotely from the EU with "Nexus" as the delivery engine.

| | Tier 1: Small Business Growth | Tier 2: Medium Business AI Enablement |
|---|---|---|
| Buyer | Owner run shops and practices: clinics, coaching centres, traders, cloud kitchens, boutiques, hotels, interior studios | 15 to 200 staff: pharma and industrial suppliers, exporters, hospital and diagnostic chains, real estate firms, distributors |
| Promise | More calls, bookings and direct orders at low risk | Faster quoting and support, staff productivity through "custom Claude AI" workflows and training |
| Deliverables | Mobile website; Google Business Profile (GBP) sync incl. review replies; tracked one tap WhatsApp inquiry; product or service catalogue; UPI and Razorpay split payment links; monthly WhatsApp ledger | Website plus B2B reorder and inquiry portal; AI assistants for quoting, support, reporting; prompt playbooks and SOP guides; two live workshops |
| Price | 4,999 INR / year base (includes first 10 leads a month) plus **either** 3% of direct online orders (settled automatically through Razorpay Route) **or** 25 INR per verified unique inquiry, capped at 3,500 INR a month | 25,000 INR setup + 10,000 INR / month retainer + 2% of portal attributed B2B orders, or a flat retainer instead |
| Onboarding | "15 minute WhatsApp flow": approve preview, pay, link bank, send 5 to 10 photos, site live in 15 minutes | "2 week build and train sprint": days 1 to 3 discovery, 4 to 8 configure assistants, 9 to 12 two workshops, day 14 hand over |
| Year 1 revenue per client (proposal's own projection) | 11,000 to 60,000+ INR | 1,45,000 to 3,25,000+ INR |

Go to market in all three: build 100 to 120 "live previews" of target businesses' sites before
contacting them, send ready made WhatsApp pitches, sign 20 to 25 Tier 1 clients in weeks 3 and 4,
close 2 to 3 Tier 2 sprints in weeks 5 to 8, and recruit chartered accountants (CAs) as referral
partners for a 20% share.

## 1.2 How the three launches differ

| | Hyderabad (H1 to H10) | Agra (A1 to A10) | Coastal AP corridor (C1 to C12) |
|---|---|---|---|
| Market framing | Dense metro: specialty healthcare, training hubs, wholesale, pharma corridor | Footwear cluster, tourism, education and retail | Four smaller cities 35 to 75 km apart plus Vizag; "under served, minimal competition" |
| Tier 1 / Tier 2 targets | 7 / 3 | 8 / 2 | 10 / 2 |
| Tier 1 upper revenue | 60,000+ | 58,000+ | 60,000+ |
| Tier 2 flat retainer option | 30,000 to 40,000 / month | 25,000 to 35,000 / month | 25,000 to 35,000 / month |
| Agency comparison | "85%+" cheaper; agencies 15 to 30k upfront + 10 to 20k / month | "80%+" cheaper; 10 to 20k upfront + 12 to 20k / month | No figure |
| Languages | Workshops in English, Telugu or Hindi; sites not stated as bilingual | Workshops in Hindi and English | Bilingual English + Telugu sites; owners update by Telugu voice or text on WhatsApp |
| "Local speed" claim | "Delivery hubs" in Hyderabad, Chennai, Mumbai | "Global delivery hubs" in Delhi, Mumbai | Not claimed; replaced by "regional flywheel" with one field representative |
| Launch volume (60 days) | 100 previews, 20 T1, 2 to 3 T2, 3 to 5 CA partners | 100 previews, 20 T1, 2 to 3 T2, 3 to 5 CA partners | 120 previews, 25 T1, 2 to 3 T2, 4 to 6 CA or trade association partners |
| Referral commission | 20% of base + conversion fees (duration unstated) | Same | 20% **recurring** |

The documents are largely one template with city words swapped. The Coastal AP version is the most
developed (bilingual product, field representative, trade associations) and fits a Telugu speaking
operator best; Hyderabad shares the language and has the densest demand; Agra adds Hindi and a
tourism heavy mix with the most GMV based targets.

## 1.3 Gaps and contradictions between the proposals

1. **Same segment, different tier.** Diagnostic chains are Tier 2 in Hyderabad (H8) and Agra (A10)
   but Tier 1 per lead in Vizag (C12). Pick one rule: tier by number of branches or staff, not city.
2. **Undefined price.** H10 (real estate) is offered "a per booked visit performance bonus" with no
   amount, no definition of a booked visit and no proof mechanism.
3. **Tier 2 revenue range ignores its own flat option.** 1,45,000 is exactly 25,000 + 12 x 10,000
   (zero portal revenue). The flat retainer option (25,000 to 40,000 a month) yields 3.25 to 5.05
   lakh a year, above the stated upper bound. Decide whether the flat retainer replaces or adds to
   the 10,000 base.
4. **Is 4,999 INR inclusive of GST?** Not stated anywhere. At 18% GST it is either 4,999 + 900 or
   4,236 net. Same for every other price.
5. **"Never face uncapped bills"** applies only to the per lead option. The 3% GMV option has no cap,
   and Razorpay's own fees are not mentioned (see 1.4).
6. **Bilingual product only in Coastal AP**, although Hyderabad is equally Telugu speaking and Agra
   customers expect Hindi. The product should be bilingual by default everywhere (English plus the
   local language).
7. **Referral commission terms differ** (one off vs recurring) and the base is unclear ("20% of base +
   conversion fees": for how long, paid from what, before or after GST and payment fees?).
8. **Delivery "hubs" differ by city and do not exist.** The platform runs in one Google Cloud region
   in Belgium (europe-west1). Google's edge network has points of presence in India, but nothing
   here is a "delivery hub" the operator runs.
9. **"Claude AI" vs Nexus.** Tier 2 is sold as "custom Claude workspaces / assistants". Nexus today
   calls only Gemini through Vertex AI (`src/nexus/providers/vertex.py`, `src/nexus/ai/pricing.py`).
   It is unclear whether the client buys Claude seats (and from whom), or the operator builds
   assistants on the Claude API. Who pays model usage is not in any price.
10. **Who owns the domain, the GBP listing, the content and the data** after cancellation is not
    stated. This matters for trust and for DPDP (document 4).

## 1.4 What looks unrealistic

**Revenue projections.**

* Tier 1 per lead revenue is capped at 4,999 + 12 x 3,500 = **46,999 INR**. The "60,000+" upper
  figure is reachable only through the 3% GMV route, which needs about **18 lakh INR of online
  orders a year** (about 1.5 lakh a month) through a brand new website. Plausible for a hotel taking
  direct bookings; not for a bakery, boutique or sweet shop starting from zero online sales.
* Even the 11,000 lower bound needs either 30 verified unique leads every month (10 free + 20 paid)
  or about 16,700 INR a month of online orders. Many small clients will sit at 4,999.
* **City level economics.** Hitting the 60 day goal (20 Tier 1 at about 11,000 plus 2 to 3 Tier 2 at
  1.45 lakh) gives an annual run rate of roughly **5 to 6.5 lakh INR (about 5,700 to 7,400 USD)**
  before GST, payment fees, 20% referral commissions, a field representative (a local hire costs
  roughly 2.5 to 4 lakh a year), travel for workshops, and model usage. One city is a learning
  pilot, not a business; profit needs several hundred Tier 1 clients or several Tier 2 clients.

**Timelines.**

* "Site live in 15 minutes after payment" is a software feature that does not exist (document 2).
  It is achievable only with a finished multi tenant storefront and an operator reviewing content;
  realistic same day, 15 minutes only after months of tooling work.
* "100 live previews in two weeks" means building sites for businesses that have not asked, using
  their name, photos and reviews. Even automated, someone must check each one, and it carries legal
  and reputational risk (document 4, section 4.2).
* "Tier 2: configure assistants on company catalogues in 5 days, two workshops, done in 14 days"
  for 25,000 INR (about 285 USD) is heavily underpriced for the work and travel involved, and
  assumes in person workshops by someone based in Europe.

**Claims.**

* "Cut quote turnaround by 50%" (Tier 2 pitches) has no evidence behind it. Nexus's own ROI tool is
  a heuristic (`src/nexus/metrics/roi.py`: hours = lines of code / 80, fixed DORA figures, a
  "vulnerabilities prevented" count derived from the file count). Do not cite it to clients.
* "85% / 80% cost advantage" compares a website to agencies that also run ads and SEO, and to food
  and travel aggregators whose commission buys demand. A website converts existing demand (Google
  Maps searches the business already receives); it does not create new demand. Say "keep the
  commission on customers who already find you", which is honest and still strong.
* "Verified unique inquiry, deduplicated by phone number" cannot be done for one tap WhatsApp
  (`wa.me`) links: the chat opens on the business's own phone and the platform never sees it
  (document 2, section 2.4).
* "Automatic 3% settlement via Razorpay Route" makes the operator the merchant on the payment and
  likely an e-commerce operator for GST; it needs an Indian entity and KYC (document 4).
* "Sub second mobile page loads" from a scale to zero service in Belgium is not guaranteed: a cold
  start takes one to several seconds and the round trip to India is about 130 to 160 ms. Achievable
  only if pages are static and served from a CDN (document 3).
* "Minimal competition" in Coastal AP is asserted, not shown. Local agencies, Google's free tools,
  and low cost site builders with Indian payment integrations all compete for the same owners.
* "Risk free / virtually risk free" wording in pitches should go: the client still pays the base
  fee and gives the operator access to their payment flow and Google listing.

## 1.5 What is good and worth keeping

* The segment choice is sensible: businesses that already get Google Maps traffic and lose margin
  to aggregators (hotels, food, tour operators) gain the most from direct booking and payment.
* Low entry price plus local referral partners (CAs, trade associations) is a credible channel in
  these cities.
* Vertical templates (clinic, coaching, catalogue trader, hotel, food) map well onto a small number
  of reusable storefront templates.
* Tier 2 AI enablement (SOP playbooks, quoting assistant, staff training) is a real need, and the
  operator's own experience running agents is a genuine differentiator, if priced for the work.

## 1.6 Recommended simplification for the pilot

| Item | Proposal | Pilot recommendation |
|---|---|---|
| Tier 1 price | 4,999 / year + 3% or 25 per lead | 4,999 / year + GST, flat, first 3 months free or refundable; optional "Growth" plan at a fixed monthly fee with a lead dashboard. Revisit performance pricing after measuring real lead volumes. |
| Payments | Platform collects via Razorpay Route and splits | Client's **own** Razorpay or UPI merchant account; the platform only builds the checkout. No operator money flow. |
| Lead counting | Verified unique leads billed | Count leads (form submissions and click events) and **report** them; do not bill on them in the pilot. |
| Tier 2 | 25,000 + 10,000 / month + 2% | Fixed scope discovery (paid), then a monthly retainer that includes a stated AI usage allowance; 2% only when the portal actually processes orders and attribution is unambiguous. |
| Languages | Telugu only in AP | English + Telugu (H, C) or English + Hindi (A) everywhere. |
| Previews | 100 unsolicited previews | 10 to 20 previews, built only from public facts, unlisted, marked "sample, not affiliated", deleted after 14 days if not accepted. |
