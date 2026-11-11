---
type: doc
date: 2026-11-07
lang: mul
---
# Phase 3 — Evidence Verification & Authority Building
Date: 2026-11-07 (pass 1 + pass 2)
Scope: 28 entries in `geo/knowledge/evidence-ledger.*` + clarifications in `geo/knowledge/blog-facts.json`. No mass page generation. No edits to main site. Unrelated working-copy changes archived separately (`F:\Pill\tmp\opencode\geo-site-wip-*`).

## Method (honest)
- Prioritized entries by business significance/risk (P1 commercial+trust+conflicts; P2 key definitions/case/formats; P3 historical/attributed market stats).
- Pass 1: fetched key `audio-reclama.ru` pages (blog posts for podcast/Vnukovo, `/audioplus/`, `/audio/golosovoe-privetstvie-menu-ivr.html`). `websearch` returned no useful results in that pass.
- Pass 2 (same session): used `websearch`/`webfetch` to locate accessible study coverage and report summaries. Direct fetch of some primary PDFs (e.g., IAB/PwC on iab.com, iabrus.ru) was blocked/limited in this environment; where a named primary study/report is clearly identified and key claim scope is supported by accessible credible coverage (Mediascope news, industry reporting citing the study), entries were promoted to **`partially_verified` with scope limits** — **not** `verified` (primary report text/wave/table not fully independently reviewed here).
- Did **not** assign `verified` without independent primary confirmation within stated claim scope. Did **not** invent sources, KPIs, prices, or metrics.

## Classifications (`phase3_classification`, after pass 2)
| Classification | Count | Meaning |
|---|---:|---|
| `partially_verified` | 8 | Accessible official/observed evidence or credible study coverage found; full current owner/primary confirmation or scope limits remain. |
| `partially_verified_milestone` | 1 | BF-VNUKOVO-001 confirmed by fetched blog text as reported milestone/progress, **not** canonical final proof. |
| `contradicted_observation` | 1 | Main-site homepage shows conflicting “622/620 дикторов” (unresolved). |
| `unverified_primary` | 12 | Attributed/cited third-party stats/forecasts/research; primary not independently re-verified to promotion threshold in this pass. Kept as historical/attributed; **not** 2026 market state. |
| `editorial_definition` | 6 | Practical/editorial explanations/definitions or process guidance; not empirical third-party statistics. |

## Key corrections/clarifications
- **Historical guardrail strengthened:** all `cited_in_blog` entries explicitly note Phase 3 historical/attributed context and “не использовать как актуальное состояние рынка 2026 без независимой проверки первоисточника”.
- **BF-2019-001 → `partially_verified` (scope-limited):** Sostav (2019-03-12, https://www.sostav.ru/publication/digital-audio-36115.html) reports IAB Russia estimate: RU digital audio ad market **465.3M RUB in 2018** vs 155M in 2017; cites data sources (Digital Box, IMHO, Unisound, Digital Audio Mail.Ru Group, Yandex, EMG) and methodology (funds from advertisers/agencies to sellers/publishers). Forecast figures in the same blog claim (2019/2022) remain not separately verified.
- **BF-2019-002 → `partially_verified` (scope-limited):** Mediascope news (2018-11-15, initiative of IAB Russia, https://mediascope.net/en/news/1066607/) + Adindex (https://adindex.ru/news/researches/2018/11/15/206761.phtml) confirm key findings: **72%** of online audio listeners (target: cities 100k+, online audio without paid subscriptions/ad blockers) notice digital audio ads; **85%** of those who notice agree to listen in exchange for free content (plus 68% discounts, 53% ≤15s, 60%/53% banners, 56% take action). Blog’s demographic detail “18-45, смешанная выборка” is not explicitly stated in accessible Mediascope summary — kept as scope limitation.
- **BF-2020-003 → `partially_verified` (scope-limited):** IAB/PwC U.S. Podcast Advertising Revenue Study FY2019 (2020) categorizes/measures podcast ad types including **host-read** and **announcer-read/pre-produced** (FY2019 revenue shares in accessible summaries: host-read 66%, announcer-read/pre-produced 27%, supplied 6%). Primary PDF URL identified (direct fetch blocked here): https://www.iab.com/wp-content/uploads/2020/07/Full-Year-2019-IAB-Podcast-Ad-Rev-Study_v20200710-FINAL-IAB_v2.pdf. Blog’s Russian “3 формата” phrasing is a simplified mapping — not a verbatim primary taxonomy; US FY2019 context.
- **BF-HOSTREAD-001 → `partially_verified` (scope-limited):** format distinction supported by IAB/PwC; blog’s qualitative trust/loyalty effect claim remains not independently proven as a universal causal finding.
- **BF-2020-004 remains `unverified_primary`:** exact 51% (Mediascope) not confirmed in accessible summaries found in this pass.
- **BF-2020-001, BF-2020-002:** remain `unverified_primary` (850k/30M lacks named primary in article passage; Bridge Ratings $500M forecast not independently re-verified).
- **BF-VNUKOVO-001:** milestone confirmed by blog text (2026-11-07 fetch), not canonical final proof.
- **CF-AUDIOPLUS-ORDER / CF-IVR-INDIVIDUAL / CF-CONTACTS / CF-MAIN-INCONSISTENCY-DICTORS:** unchanged from pass 1 evidence/limits.

## Checks
- `python tools/build_geo_site.py --check` → OK
- `python tools/build_geo_site.py --safe` → OK (HTML not regenerated; `combined.json` preserved enriched blocks)

## Next (Phase 3 continuation / owners)
1. Obtain/verify **primary** report URLs for highest-value cited stats (PwC/IAB USA podcast formats/host-read, IAB Russia/Mediascope digital audio, Data Insight/People&Screens ROI) with exact claim scope + date/wave + quote/figure.
2. Owner confirmation on main site: 622 vs 620, current Audio+ packs/terms, IVR pricing communication/canonical policy, contacts.
3. Only after primary confirmation: promote specific claims to `verified` with scope-limited wording; otherwise keep `unverified_primary`/`partially_verified` or remove from answer surfaces.
4. Do not use Phase 3 as evidence of AI visibility improvement (P6 baseline still unexecuted).
