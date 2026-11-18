# Commercial Search & Social Attention Register — 2026-11-18

## Purpose and scope

This register converts the latest first-party search and connected social-channel observations into a review-only growth plan for `Аудио-Реклама•ru`. It does not authorize or perform changes to the official website, posts, profiles, campaigns, or integrations.

**Evidence window**
- Google Search Console: 2026-08-15 to 2026-11-15, web search, selected property `https://www.audio-reclama.ru/`.
- Metricool/vidIQ: social-account snapshot retrieved 2026-11-18; post observations requested for 2026-10-19 to 2026-11-17.
- All observations are dated and limitations are preserved in [E-2026-068](../evidence/E-2026-068.md) and [E-2026-069](../evidence/E-2026-069.md).

## What the data says

### 1. Attention is concentrated in informational content

The leading page in the three-month GSC page report was an article comparing dubbing studios: 1,534 clicks from 90,461 impressions, average position 5.3. Other leading pages cover cartoon dubbing (482 clicks, 18,483 impressions) and how to voice a video (403 clicks, 14,444 impressions).

That indicates real search attention around voice, dubbing, and production knowledge. It does **not** show that this attention turns into orders. Those high-traffic pages should be treated as potential distribution surfaces for relevant, useful service paths—not as proven lead generators.

### 2. Commercial pages show a measurable opportunity gap

| Priority | Commercial page | Clicks | Impressions | CTR | Avg. position | Main finding |
|---|---|---:|---:|---:|---:|---|
| P1 | Radio ad production | 15 | 1,387 | 1.08% | 9.7 | Buyer phrases rank around positions 4–8 but receive zero clicks in the observed rows |
| P1 | IVR / telephone greeting | 12 | 1,375 | 0.87% | 30.9 | Many relevant phrases sit around positions 20–70 |
| P1 | Video voiceover | 2 | 223 | 0.90% | 35.0 | “озвучка ролика стоимость” has 117 impressions at position 52.4 |
| P2 | Audiobook production | 33 | 1,276 | 2.59% | 27.8 | Price and quotation questions already generate clicks, but ranking positions remain weak |
| P2 | Corporate songs | 0 | 65 | 0.00% | 21.4 | Early, low-volume demand; no clicks yet |
| P2 | Presentation voiceover | 0 | 61 | 0.00% | 14.6 | Very low-volume signal; too early to infer performance |

**Radio page detail:** `заказать аудиоролик` — 144 impressions, position 6.2, zero clicks; `аудиореклама заказать` — 96 impressions, position 7.9, zero clicks; `заказать радиоролик` — 47 impressions, position 4.5, zero clicks.

**IVR detail:** `голосовое приветствие для атс` — 120 impressions, position 24.0; `запись ivr` — 53 impressions, position 45.1; `ivr цена` — 13 impressions, position 7.9 and zero clicks.

**Audiobook detail:** `озвучка книги цена` — 156 impressions, 5 clicks, position 17.2; `заказать озвучку книги` — 136 impressions, 4 clicks, position 29.8.

Do not assume the cause is price, metadata, copy, or UX until the competing search results and actual page are compared. The zero-click near-page-one terms merit a SERP/snippet audit; lower-ranking pages merit relevance, proof, and internal-link review.

### 3. Social distribution has three connected networks, not four

Metricool confirms Facebook, Instagram, and YouTube under the active brand; vidIQ confirms an owner-level publish-capable YouTube connection. TikTok was absent from both current connection inventories.

The Instagram Reel “Бесплатный дофамин. Сценарий — в комплекте.” was the strongest of three returned Reels in this window (259 views, reach 196, 8 interactions, average watch time 5.44 seconds). The sample is too small to generalize, but the pattern supports testing short creative that opens with a concrete benefit and shows a real deliverable.

Metricool's Tuesday activity estimates indicate initial test slots around 16:00 Moscow for YouTube and 10:00–12:00 Moscow for Facebook. Treat these as hypotheses, not measured online audience or guaranteed reach. Instagram's returned timing values were all zero; no schedule recommendation is warranted from that response.

## Recommended order of work

### P1 — Convert existing high-intent search visibility

1. **Radio ads:** compare the live Google result and top competing results for `заказать аудиоролик`, `заказать радиоролик`, and `аудиореклама заказать`. Prepare alternative title/description and above-the-fold value propositions for review. Each version should make the service, examples, scope, price basis (if verified), turnaround (if verified), and next step obvious.
2. **IVR:** create a query-to-content gap map for greeting, IVR menu, recording, voice talent, structure, number of languages, revision policy, delivery formats, and telephony integration. Mark facts that need owner confirmation.
3. **Video voiceover:** prioritise exact query match for “озвучка ролика стоимость” and related service terms. Add proof-oriented examples and the specification required for a quote only after confirming what can be delivered.
4. **Audiobooks:** build a transparent brief/checklist for estimating length, finished audio hours, editing/mastering, rights, sample reading, and delivery. Do not invent a per-minute price.

### P2 — Route informational attention to useful commercial next steps

1. From high-traffic dubbing/voiceover articles, draft contextual internal-link placements to genuinely relevant services (not blanket banners).
2. Prepare short video scripts from the same knowledge: one problem, one demonstration/example, one result, one non-pushy next step.
3. Create 3–5 test variations around clear benefit-led hooks; measure retention and shares rather than relying on raw views only.
4. Use platform-native versions for YouTube Shorts, Instagram Reels, and Facebook Reels. Keep a clean source master without another platform's watermark; adjust caption, title, and CTA to each platform.

### P3 — Measurement setup (blocker before ROI claims)

- OpenSEO sees the selected GSC property, but `list_google_analytics_properties` returned no GA4 properties for the project.
- Windsor.ai lists a connected GA4 account but its trial limits history to 30 days; recent reads returned empty rows. This is a connector/data issue, not evidence of zero site traffic.
- Before assessing orders, bind the correct GA4 property and verify events for form submissions, phone clicks, email clicks, and messaging links. Reconcile those events with CRM/telephone enquiries before using “conversion” language.
- Do not add a new tracking script or alter the website until separately authorized.

## Free-tool decision

No additional plugin is recommended at this point. The current stack already covers:
- **OpenSEO + Google Search Console:** first-party search queries, page performance, and SERP research; GSC reads through OpenSEO used no credits.
- **Ahrefs:** competitor/backlink/keyword and AI visibility research (use only within existing plan limits).
- **vidIQ:** YouTube channel and video discovery, analysis, and authorized YouTube publishing.
- **Metricool:** connected Facebook, Instagram, YouTube scheduling and social analytics.
- **Windsor.ai:** multiple data-source connectors, but this account's trial limits history to the last 30 days and recent GA4/Facebook reads returned empty rows.
- **Similarweb:** not installed and not needed; don't purchase it for this work.

Plugin search did not surface a dedicated Yandex Metrica / Yandex Webmaster / VK Clips connector that is both clearly useful and verified free. Windsor's connector catalogue includes some source integrations, but their existence does not mean the accounts are connected or the trial includes historical data. Do not install an overlapping analytics tool without a specific missing measurement to solve.

## Change-control status

- Official website: read-only; no page, metadata, CMS, form, analytics code, robots, sitemap, or configuration changes.
- Social accounts: no new profiles or posts; no drafts scheduled or published in this pass.
- Paid tools, credits, placements, and ad spend: none purchased or activated.
- TikTok: not connected; no location spoofing, purchased accounts, or fictitious identity recommended.
- AI visibility benchmarks: keep unrun prompts blind until the baseline test is executed; do not prime external AI systems using internal answer packs.
- This register is a research deliverable for owner review, not an implementation approval.

## Evidence index

- [E-2026-065 — Official page metadata and audio-demo inventory](../evidence/E-2026-065.md)
- [E-2026-066 — Competitor public pricing claims](../evidence/E-2026-066.md)
- [E-2026-067 — GSC commercial-page snapshot](../evidence/E-2026-067.md)
- [E-2026-068 — Commercial landing-page query performance](../evidence/E-2026-068.md)
- [E-2026-069 — Connected social-channel snapshot](../evidence/E-2026-069.md)

Competitor price data is self-published by competitors and is not independent validation. All performance values retain the source and date window in the evidence files.