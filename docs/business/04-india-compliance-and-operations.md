# 4. Compliance and operations for India

This is an engineer's reading of the rules to frame questions, **not legal or tax advice**. Items
marked *confirm* need an Indian chartered accountant or lawyer, and the EU items a Luxembourg adviser.

## 4.1 DPDP Act 2023 and client data

**Status.** The Digital Personal Data Protection Act 2023 applies through the DPDP Rules notified in
November 2025, with most duties of data fiduciaries (notices, security safeguards, breach
reporting, retention, children's data) phased in over about 18 months, that is around mid 2027
(*confirm the exact dates*). A pilot in 2026 to 2027 runs into full applicability, so build to the
rules from the first client rather than retrofit.

**Roles.**

| Data | Who decides why and how (Data Fiduciary) | Operator's role |
|---|---|---|
| Customers' inquiries, bookings, orders, patient or student leads on a client's site | The client business | **Data Processor**, acting only on the client's instructions under a written contract |
| Client owners' and staff contact details, invoices, support chats | The operator (or the Indian entity / partner) | Data Fiduciary |
| Prospect lists, preview sites, outreach messages | The operator | Data Fiduciary, and the riskiest processing in the plan (4.2) |
| Tier 2 documents loaded into assistants (catalogues, SOPs, customer lists) | The client | Processor; plus the model provider as a sub processor |

**What the platform must do (as processor, so that clients can meet their duties):**

* **Contract:** a data processing agreement with every client: purposes, categories, sub processors
  (Google Cloud, the model provider, Meta for WhatsApp, the payment gateway), security measures,
  breach notice to the client within 24 hours, deletion or return at the end, audit cooperation.
* **Notice and consent on every form:** short, itemised notice of what is collected and why, in
  English **and** Telugu or Hindi (the Act allows any language in the Eighth Schedule, which
  includes both), with a link to the client's privacy notice and a consent checkbox that is not
  pre ticked. Store the consent record (time, notice version, language) with the lead.
* **Withdrawal and rights:** a way for a person to withdraw consent, ask for a copy, correct, or
  erase, routed to the client; the portal must let the client act on it in a few clicks.
* **Minimisation:** collect name, phone, preferred time and a short choice list. No free text
  "describe your symptoms" on clinic forms, no exam marks or ID numbers on coaching forms.
* **Retention:** delete leads after a set period (for example 12 months) unless the client
  converts them; delete everything for a client within 30 days of leaving, after giving them an
  export.
* **Security safeguards:** encryption in transit and at rest (default on Google Cloud), per tenant
  access control (document 3), access logs kept for at least a year, backups, least privilege
  service accounts, no personal data in logs (`sanitize_text` already redacts emails), and a tested
  restore.
* **Breach runbook:** detect, contain, tell the client within 24 hours with facts they need to
  notify the Data Protection Board and affected people.
* **Children:** the Act requires verifiable parental consent for anyone under 18 and bans tracking,
  behavioural monitoring and targeted advertising directed at children. Coaching centres (H2, A5, C9)
  will receive leads from students who are minors: their forms should ask whether the person is a
  parent or guardian or 18+, and their pages should carry **no analytics or advertising pixels**.
* **Health context:** clinics and diagnostic businesses (H1, H8, A6, A10, C5, C12) handle inquiries
  that reveal health information. The Act has no separate "sensitive" category, but the penalty for
  failing to protect data is up to 250 crore INR and the reputational harm is worst here. Keep these
  clients on the minimum form and consider a dedicated database.

**EU side.** Because the operator is established in Luxembourg, the GDPR very likely also applies to
the operator's own processing, including as a processor for Indian clients (records of processing,
processor contracts, security, transfer rules). *Confirm with a Luxembourg adviser*; the practical
effect is to keep the same contract and security set, which overlaps heavily with DPDP.

## 4.2 Previews and outreach: the riskiest part of the plan

The launch plans build 100 to 120 "live previews" of businesses that have not asked, then pitch
them over WhatsApp. Issues:

* **Content rights:** photos on Google Maps belong to whoever uploaded them; reviews and listing data
  are under Google's terms, which restrict scraping and storing. Use only facts the business
  publishes (name, address, hours, category) and generic or generated imagery, or the Places API
  within its caching rules.
* **Impersonation and confusion:** a public site under the business's name that the business did
  not authorise can look like passing off. Previews must be unlisted (`noindex`, unguessable link),
  carry a visible "sample prepared by <brand>, not affiliated with <business>" banner, and expire
  after 14 days.
* **Personal data:** owner and doctor names and personal mobile numbers are personal data; the
  operator becomes a fiduciary for the prospect list and needs a notice and a deletion rule.
* **WhatsApp:** WhatsApp's business policy requires the person's opt in before a business sends
  them messages; unsolicited bulk messages get numbers restricted or banned, which would also take
  down the support channel. **Large scale cold calls and SMS** may count as unsolicited commercial
  communication under TRAI rules (*confirm*).
* **Recommendation:** first contact in person, by phone at low volume, or through a referral partner;
  build the preview only after a "yes, show me"; move to WhatsApp once the person has agreed.

## 4.3 Sector rules that affect targets

| Segment | Rule to check (*confirm*) | Effect on the product |
|---|---|---|
| Doctors and clinics | National Medical Commission conduct regulations restrict soliciting patients and paying for patient referrals | No per patient lead pricing for doctors; factual content only, no testimonials or claims |
| Coaching (H2, A5, C9) | 2024 central guidelines for coaching centres; consumer authority guidance on misleading coaching ads | No "guaranteed rank" claims; show registration where required |
| Real estate (H10) | RERA: project registration number on every project advertisement | Template field for RERA numbers, mandatory on project pages |
| Food (H4, A3) | FSSAI licence for food businesses selling online | FSSAI number field, mandatory before checkout goes live |
| Pharma (H9) | Restrictions on advertising prescription drugs to the public | B2B catalogue behind a login for verified buyers |
| Hotels, tours (H7, A1, A8, C11) | Consumer protection e-commerce rules for the seller's terms (cancellation, refunds, grievance contact) | Template terms and grievance contact per client |

## 4.4 Data residency: India region or europe-west1

* The DPDP Act allows transfer of personal data outside India except to countries the government
  restricts by notification (*confirm whether any list has been published*). Hosting ordinary client
  data in europe-west1 is therefore not prohibited by the Act itself.
* **Payments:** RBI's storage rule binds payment system operators (the gateway), not a merchant's
  website. Keep only order and payment reference ids on the platform; never card or bank details.
* **Contracts can require more:** hospitals, government linked or port related buyers (some Tier 2
  targets) may require India hosting or a government empanelled cloud. Google Cloud has India regions
  (Mumbai, Delhi).
* **Model calls:** storage in India does not mean inference in India. Global model endpoints may
  process prompts elsewhere. If a client needs in country processing, pick a model and endpoint
  available in an India region and say exactly what is covered.
* **Recommendation:** pilot in europe-west1, keep everything region portable, state the hosting
  location in each contract, and decide on asia-south1 at the end of the pilot (document 3, 3.3).

## 4.5 Invoicing and GST

**The core question is who invoices and collects in India.**

| Option | How it works | Pros | Cons |
|---|---|---|---|
| A. Invoice from Luxembourg | EU sole trader or company invoices Indian clients | Nothing new in India | Small shops cannot easily pay a foreign invoice; GST registered clients pay GST under reverse charge and may have to withhold income tax and file remittance forms; for **unregistered** small businesses, online services from abroad likely fall under OIDAR, which requires the foreign supplier to **register for GST in India** and charge 18%; Razorpay and UPI collection are not available to a foreign entity |
| B. Indian entity (Private Limited or LLP) | Entity contracts, invoices with 18% GST, collects by UPI / Razorpay | Normal local business; clients trust a local GST invoice; can hold the Razorpay account | Setup and yearly compliance cost (a CA's fees, filings); a Private Limited company needs a director resident in India; Luxembourg tax consequences of owning it |
| C. Indian partner reseller | A local partner (an IT firm or one of the CA partners) sells, invoices and supports under licence; the operator licenses the platform to the partner | Fastest; partner brings the local presence the plan needs anyway | Revenue share; dependence on one partner; needs a solid licence and data processing agreement |

**Recommendation:** C for the pilot, B once there is proof of demand. Either way:

* Price lists must say "plus 18% GST" explicitly (gap 4 in document 1).
* Likely service codes: IT design and development, and hosting services (SAC 9983 group); *confirm*.
* GST registration is required above 20 lakh INR turnover for services in these states, and
  **compulsory from day one** for an e-commerce operator that must collect tax at source.
* **Avoid the Razorpay Route split model.** If the platform collects customers' payments and pays
  out to merchants, it very likely becomes an *e-commerce operator* under GST section 52 (compulsory
  registration, TCS on the merchants' sales, monthly returns) and has income tax withholding duties
  on those sales (section 194-O), and it carries refund and chargeback exposure. Let each client use
  their own payment account and invoice the operator's fee separately.
* **Luxembourg side** (*confirm*): a trade licence if trading as an individual, VAT registration and
  reporting (services to Indian businesses are generally outside EU VAT but still reported), income
  tax, and whether any employment contract allows a side business.

## 4.6 Payments

* **Client's customers pay the client:** each client keeps or opens their own gateway account
  (Razorpay, or a UPI QR / payment links from their bank). The platform builds checkout and verifies
  webhooks with a per client secret. Gateway fees (roughly 2% on many methods on standard plans; UPI
  pricing differs) are the client's and must be stated, because the proposals' 3% sits on top.
* **Operator's own fees:** through the Indian entity or partner: annual fee by UPI, or monthly
  Tier 2 retainers by UPI AutoPay or gateway subscriptions; GST invoice issued automatically.
* **Gateway partner programmes** may pay a referral commission for merchants the operator onboards,
  which is a way to earn on transaction volume without touching the money (*check the gateway's
  current partner terms*).
* Never handle card or bank numbers; never hold client money.

## 4.7 Local languages

| Need | Hyderabad | Agra | Coastal AP |
|---|---|---|---|
| Storefront | English + Telugu (Hindi optional; Urdu optional for some old city businesses) | English + Hindi | English + Telugu |
| Owner updates by WhatsApp | Telugu, Hindi, mixed with English | Hindi, Hinglish | Telugu, Tenglish |
| Workshops | Telugu, Hindi or English | Hindi | Telugu |

Product implications:

* Separate language URLs (`/te/`, `/hi/`) with `hreflang` so Google indexes both; Indian number and
  currency formatting (lakh, crore, INR sign).
* Self host Noto Sans Telugu and Noto Sans Devanagari subsets (the current CSP only adds Google
  Fonts; self hosting is faster and avoids a third party).
* Machine translation is a draft. Prices, medical, legal and dietary text must be reviewed by a
  native speaker; build a per vertical glossary. Telugu output quality from general models is
  usually weaker than Hindi: test on real samples before promising.
* Voice notes: Telugu and Hindi speech recognition exists in Google's speech services and in
  multimodal models; measure accuracy on 50 real, noisy, code mixed voice notes before relying on it,
  and always read the result back to the owner for confirmation.
* Workshops in Telugu or Hindi need a native speaking trainer on site; recorded short videos in each
  language cut repeat work.

## 4.8 Support model

* **Hours:** India is 4.5 hours ahead of Luxembourg in winter and 3.5 hours in summer. Indian business
  hours 10:00 to 18:00 IST are 05:30 to 13:30 in Luxembourg in winter. Publish support hours in IST.
* **Two lines:**
  * *Local first line* (field partner or representative, per city): onboarding visits, photos, KYC
    help, "how do I", in the local language.
  * *Operator second line*: content approval, platform incidents, Tier 2 changes, data requests.
* **Channels:** one WhatsApp Business number for support (never a personal number), the client
  portal, phone for Tier 2. No email notifications from the platform; alerts to the operator go to a
  push channel (Cloud Monitoring app or a Pub/Sub to chat bridge).
* **Response targets:** Tier 1 next business day; Tier 2 within 4 business hours; site outage
  acknowledged within 1 hour in IST business hours.
* **Runbooks:** site down; wrong price or content; client wants to leave (export, domain transfer,
  deletion); data subject request; suspected breach; payment webhook failures; WhatsApp number
  restricted.
* **Seasonality:** wedding and festival seasons (Sankranti, Ugadi, Dussehra, Diwali) and admission
  seasons bring edit requests and traffic peaks for exactly the targeted segments; plan capacity
  and freeze risky releases around them.
