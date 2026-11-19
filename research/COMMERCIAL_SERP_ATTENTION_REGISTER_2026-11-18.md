---
type: doc
date: 2026-11-18
lang: mul
---

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

### 2A. Russia-only search cut and the video discovery gateway

A separate country-filtered GSC read for `RUS` shows why the commercial and informational paths should be evaluated separately. The full Russia-only evidence is in [E-2026-072](../evidence/E-2026-072.md).

| Page | RU clicks | RU impressions | CTR | Avg. position |
|---|---:|---:|---:|---:|
| Radio advertising | 3 | 838 | 0.36% | 10.7 |
| IVR / telephone greetings | 4 | 611 | 0.65% | 27.6 |
| Video voiceover service | 2 | 155 | 1.29% | 44.7 |
| Audiobook production | 30 | 1,041 | 2.88% | 30.4 |
| Jingles / sound media | 0 | 120 | 0.00% | 33.4 |
| Corporate songs / anthems | 0 | 17 | 0.00% | 47.3 |
| Presentation voiceover | 0 | 7 | 0.00% | 36.9 |
| Existing video-voiceover tutorial (blog) | 121 | 3,289 | 3.68% | 7.2 |

**Highest-leverage discovery surface:** the 2020 how-to article already ranks for Russian queries such as `как озвучить видео` (438 impressions, 34 clicks, position 1.7) and `как озвучивать видео` (187 impressions, 33 clicks, position 1.3). The dedicated video service page is much weaker in the same country window. This suggests a strong informational entry point that should be connected to a clear, accurate professional-service path; it does not prove enquiries or that contextual links are absent.

**Freshness warning:** the live article still contains technical advice that the existing audit found inaccurate or too universal (including a fixed 15 cm microphone distance, an unqualified “20%” music level and a malformed `−20 to −10 dB` range). It also uses a legacy brand spelling in its attribution/footer. The technical audit and a revised draft for the **same existing URL** are already in the repo. Do not create a duplicate article or copy the old values into AI answers. The draft is not published; the official website remains read-only.

**Other Russia-only opportunities:**
- Radio: `аудиореклама заказать` — 89 impressions, 0 clicks, position 7.7; `аудиореклама записать` — 49 impressions, 0 clicks, position 7.1. Compare actual SERP titles/snippets and competing results before assigning a cause.
- IVR: `голосовое приветствие для атс` — 99 impressions, 1 click, position 21.4; `запись ivr` — 35 impressions, 1 click, position 44.3. Reuse the existing IVR answer and design standard.
- Audiobooks: the service page has 30 clicks and 1,041 impressions; price/quotation queries already generate clicks, but its average position is 30.4. Improve the estimation brief without inventing public prices or delivery promises.

The Russia-only cut is not interchangeable with the unfiltered Search Console summary in E-2026-068. Page totals and query rows are separate aggregations and must not be added together.

### 2B. Voice-catalog entity clarity and multilingual discovery

A second high-signal path is the existing voice catalogue. A Russia-only GSC cut shows strong demand for the English-language catalogue, and a large visibility surface for known voices. The full evidence and crawler details are in [E-2026-073](../evidence/E-2026-073.md).

| Existing catalogue page | RU clicks | RU impressions | CTR | Avg. position |
|---|---:|---:|---:|---:|
| English-language voices | 80 | 813 | 9.84% | 4.7 |
| Known Russian voices | 34 | 5,816 | 0.58% | 8.8 |
| Female Russian voices | 16 | 535 | 2.99% | 6.1 |
| Male Russian voices | 13 | 944 | 1.38% | 8.7 |

The English page receives query traffic such as `диктор по английскому языку` (197 impressions, 32 clicks, position 1.6) and `диктор английского языка` (142 impressions, 28 clicks, position 1.7). This is a proven existing route in the Russia search sample, not a reason to create another language page.

The 2026-11-17 technical crawl found 7 catalogue/category pages without H1 and duplicate meta descriptions on the male/female Russian pages. The same two pages each exposed 101 images without alt in the crawl; audit image-by-image so meaningful portraits receive accurate alt while decorative images stay empty. The “known voices” page has 5,816 RU impressions but only 34 clicks; review its live SERP snippet and broad-query relevance before changing copy.

**Review-only priority:** repair headings and distinct descriptions on the existing URLs, preserve the high-performing English page, and improve meaningful image alternatives. Candidate wording is recorded in E-2026-073. No changes to the live catalogue were made; no availability or performer credentials are inferred.

### 2C. Public crawler access and page-level AI semantics

A read-only audit of live public metadata and machine-access files is recorded in [E-2026-074](../evidence/E-2026-074.md). It adds a technical priority beyond query targeting:

- `https://www.audio-reclama.ru/llms.txt` returns 404. A root-level, source-grounded candidate is ready for owner review, but `llms.txt` is a voluntary agent-navigation convention, not a proven ranking or citation lever. Keep it low priority behind crawlability, entity consistency, useful page content and accurate metadata.
- `robots.txt` and sitemap are reachable. Sitemap contains 1,186 URLs, including 703 individual voice profiles, 308 filter/category pages, 137 blog URLs and 12 portfolio pages. Do not create more category pages by default.
- The video-voiceover service page and seven key catalogue pages lack an extracted H1. Male/female category pages share a description. Candidate H1/title/descriptions are in `research/AI_DISCOVERY_SITE_IMPLEMENTATION_PACK_2026-11-18.md`.
- The English entry `/en/` returns 200 but has sparse visible content and its Open Graph URL points at the homepage. It is intentionally excluded from the root llms candidate until its content and page-level metadata are corrected.
- `robots.txt` includes `Disallow: /en/*` and `Allow: /en/`. Google's current matching rules make the more-specific Allow effective for `/en/`; Yandex documents prefix-length precedence and Allow on equal-length matches, but verify it in Yandex Webmaster before making a universal crawler-access claim. No live robots rules were changed.
- The public pages use `noyaca`; this is not `noindex` and there is no reason to remove it for AI SEO. Meta-description quality and actual visible page semantics deserve attention instead.

No JSON-LD additions are proposed until the live page source is checked for existing markup. The repository's JSON-LD profile is a comparison candidate, not proof that structured data is deployed on the official site.

### 2C. Root llms.txt and AI crawler access — live recheck 19.11.2026

The 18.11.2026 snapshot in E-2026-074 recorded a 404 for the root `llms.txt`. A new read-only fetch on 19.11.2026 successfully retrieved the public file. This supersedes the earlier 404 only as a statement about the **current** state; the previous observation remains a valid dated snapshot.

**What is now confirmed**
- `https://www.audio-reclama.ru/llms.txt` is live and contains service/catalogue navigation, a bilingual introduction, project references, contact links and important caveats.
- The public file correctly warns that the English localization is partial and that the number of languages represented by voice talent is not the number of website language versions.
- `robots.txt` and `sitemap.xml` are both publicly retrievable; the sitemap lists 1,186 URLs.
- The live robots file has a generic `User-agent: *` group and no explicit `OAI-SearchBot` or `GPTBot` group. Key public service/catalogue routes inherit the generic policy and are not caught by the listed private/transactional path exclusions.
- OpenAI distinguishes `OAI-SearchBot` (ChatGPT Search discovery) from `GPTBot` (potential model-training crawl). The purposes are separate; no claim of an actual crawl, index or citation follows from robots permission alone.

**Live-file correction candidate**
- The published llms file uses an alternative Latin rendering of the brand and a trailing slash on the homepage URL, contrary to the mandatory canonical naming rule.
- A corrected, owner-review-only text is prepared in [LLMS_TXT_CORRECTED_OWNER_REVIEW_2026-11-19.md](LLMS_TXT_CORRECTED_OWNER_REVIEW_2026-11-19.md). It preserves the existing caveats and links; it is not published.
- Keep the existing root file. Do not create another version, change robots.txt or modify the CMS without explicit permission.

**Policy caution**
- The live robots file contains both `Disallow: /en/*` and `Allow: /en/`. Google's parser treats the trailing wildcard as redundant and gives precedence to the more-specific Allow; Yandex has its own matching rules, so verify the pair in Yandex Webmaster before claiming cross-engine access for all /en/ URLs. No robots edit is proposed.
- The English page currently has `og:url` pointing to the Russian homepage and only 19 GSC impressions / 0 clicks across 11 countries in 16.08–16.11.2026. Treat it as a partial entry page, not a working international acquisition surface.

Full evidence and boundaries: [E-2026-075](../evidence/E-2026-075.md).

### 3. Social distribution: TikTok is now connected, but its first measured post has zero views

The first social snapshot in E-2026-069 was taken before TikTok OAuth / Metricool sync completed. The later Metricool brand settings now confirm TikTok account `audio_reclama_ru` alongside Facebook, Instagram and YouTube; vidIQ also confirms an active, publish-capable TikTok connection.

The current TikTok read (E-2026-070) returns one 10-second video in the 2026-10-19–2026-11-18 window and records 0 views, 0 likes, 0 comments and 0 shares. Metricool reports 0 current followers. Reach, watch time and traffic-source cells are null, and the impression-source distribution query returned no rows. Since the integration was first connected on 2026-11-18, account history may be incomplete. This does not establish a shadowban or For You ineligibility. The immediate operational blocker is verification of the post's public visibility and eligibility in TikTok Studio; do not treat zero views as evidence about retention.

A subsequent public-profile check found the profile page reachable and indexable by the external extractor, with 1 follower, 0 likes and one video entry. The public embed for the only returned post says "Video currently unavailable." This still does not prove a ban. TikTok's own developer documentation provides a more concrete candidate: posts made by unaudited Content Posting API clients are restricted to SELF_ONLY; upload-to-inbox also requires a final in-app share. Verify whether the post is set to Everyone and fully published before attributing the zero to account-level penalties. See [E-2026-071](../evidence/E-2026-071.md).

The Instagram Reel “Бесплатный дофамин. Сценарий — в комплекте.” remains the strongest of three returned Reels (259 views, reach 196, 8 interactions, average watch time 5.44 seconds). This small sample supports testing a specific curiosity-generating promise over generic studio promotion, but does not establish causation.

Metricool's Tuesday activity estimates indicate initial test slots around 16:00 Moscow for YouTube and 10:00–12:00 Moscow for Facebook. Treat these as hypotheses, not measured online audience or guaranteed reach. Instagram's returned timing values were all zero; no schedule recommendation is warranted from that response.

## Recommended order of work

### P1 — Convert existing high-intent search visibility

1. **Radio ads:** compare the live Google result and top competing results for `заказать аудиоролик`, `заказать радиоролик`, and `аудиореклама заказать`. Prepare alternative title/description and above-the-fold value propositions for review. Each version should make the service, examples, scope, price basis (if verified), turnaround (if verified), and next step obvious.
2. **IVR:** create a query-to-content gap map for greeting, IVR menu, recording, voice talent, structure, number of languages, revision policy, delivery formats, and telephony integration. Mark facts that need owner confirmation.
3. **Video voiceover:** prioritise exact query match for “озвучка ролика стоимость” and related service terms. Add proof-oriented examples and the specification required for a quote only after confirming what can be delivered.
4. **Audiobooks:** build a transparent brief/checklist for estimating length, finished audio hours, editing/mastering, rights, sample reading, and delivery. Do not invent a per-minute price.

### P1 — Resolve TikTok post visibility and account standing

1. Verify the TikTok account region and the real country/network used when the post was published. 2026 reporting documents continuing Russia-side functionality restrictions; do not substitute a VPN or fake region for a proper account check.
2. Verify that the existing post is fully published and its audience is Everyone; specifically eliminate the TikTok Content Posting API's documented SELF_ONLY limitation for unaudited clients.
3. Inspect TikTok Studio Account Check, Inbox → System notifications → Account updates, and the existing post's More insights / Analytics eligibility notice. Appeal only a stated incorrect restriction.
4. Compare TikTok Studio's public-availability state with Metricool's zero views and the public embed failure. Do not delete or re-upload the post while its state is unknown.

### P2 — Route informational attention to useful commercial next steps

1. From high-traffic dubbing/voiceover articles, draft contextual internal-link placements to genuinely relevant services (not blanket banners).
2. Preserve the existing publication queue. Do not create another TikTok queue or change creative while public availability and account standing remain unverified.
3. Use Creator Search Insights to map existing queued items to actual TikTok searches and content gaps; use relevant captions/hashtags rather than generic #FYP.
4. Build authentic niche distribution through substantive comments, relevant creator collaborations, Duet/Stitch and genuine external sharing from existing owned channels. Treat this as audience development, not a guaranteed ranking switch.
5. Reuse approved assets in platform-native versions for YouTube Shorts, Instagram Reels, Facebook Reels and TikTok, while respecting the pre-language creative rule and keeping platform watermarks out of source masters.

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
- TikTok is connected to Metricool and vidIQ; the only returned post has zero recorded views and its public embed says unavailable. Account-level suppression is not proven; a private-only third-party API post and Russia-side region limitations are documented alternatives to account-wide recommendation suppression. New posts remain owner-approval-only; no location spoofing, purchased accounts, or fictitious identity recommended.
- AI visibility benchmarks: keep unrun prompts blind until the baseline test is executed; do not prime external AI systems using internal answer packs.
- This register is a research deliverable for owner review, not an implementation approval.

## Evidence index

- [E-2026-065 — Official page metadata and audio-demo inventory](../evidence/E-2026-065.md)
- [E-2026-066 — Competitor public pricing claims](../evidence/E-2026-066.md)
- [E-2026-067 — GSC commercial-page snapshot](../evidence/E-2026-067.md)
- [E-2026-068 — Commercial landing-page query performance](../evidence/E-2026-068.md)
- [E-2026-069 — Connected social-channel snapshot](../evidence/E-2026-069.md)
- [E-2026-070 — TikTok first-post distribution snapshot and diagnostic](../evidence/E-2026-070.md)
- [E-2026-071 — TikTok account-level discoverability and publishing-path diagnostics](../evidence/E-2026-071.md)
- [E-2026-072 — Russia-only Search Console and video discovery-path audit](../evidence/E-2026-072.md)
- [E-2026-073 — Voice-catalog discoverability and semantic clarity](../evidence/E-2026-073.md)
- [E-2026-074 — Official-site AI access and semantic consistency](../evidence/E-2026-074.md)
- [E-2026-075 — Live llms.txt, robots policy and page metadata recheck](../evidence/E-2026-075.md)
- [Corrected root llms.txt proposal for owner review](LLMS_TXT_CORRECTED_OWNER_REVIEW_2026-11-19.md)
- [Live root llms.txt review summary](LLMS_TXT_LIVE_REVIEW_2026-11-19.md)

Competitor price data is self-published by competitors and is not independent validation. All performance values retain the source and date window in the evidence files.