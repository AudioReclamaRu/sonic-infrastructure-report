# Phase 3 — Evidence Verification & Authority Building (pass 1)
Date: 2026-11-07
Scope: 28 entries in `geo/knowledge/evidence-ledger.*` + clarifications in `geo/knowledge/blog-facts.json`. No mass page generation. No edits to main site. Unrelated working-copy changes archived separately (`F:\Pill\tmp\opencode\geo-site-wip-*`).

## Method (honest)
- Prioritized entries by business significance/risk (P1 commercial+trust+conflicts; P2 key definitions/case/formats; P3 historical/attributed market stats).
- Attempted accessible verification: fetched key `audio-reclama.ru` pages (blog posts for podcast/Vnukovo, `/audioplus/`, `/audio/golosovoe-privetstvie-menu-ivr.html`, homepage observations already recorded). `websearch` returned no results in this environment; third-party primary reports (IAB Russia, Mediascope, PwC/IAB USA, Bridge Ratings, TNS, Voices.com, Data Insight/People&Screens, Яндекс analytics) were **not independently re-verified** where no primary URL/access was available.
- Did **not** assign `verified` without independent primary confirmation within stated claim scope. Did **not** invent sources, KPIs, prices, or metrics.

## Classifications added (`phase3_classification`)
| Classification | Count (indicative) | Meaning |
|---|---:|---|
| `partially_verified` | 4 | Accessible official/observed evidence found; full current owner/primary confirmation or scope limits remain (AUDIO+ observed, IVR fact-safe alignment needed, contacts observed). |
| `partially_verified_milestone` | 1 | BF-VNUKOVO-001 confirmed by fetched blog text as reported milestone/progress, **not** canonical final proof. |
| `contradicted_observation` | 1 | Main-site homepage shows conflicting “622/620 дикторов” (unresolved). |
| `unverified_primary` | 16 | Attributed/cited third-party stats/forecasts/research; primary not independently re-verified in this pass. Kept as historical/attributed; **not** 2026 market state. |
| `editorial_definition` | 6 | Practical/editorial explanations/definitions or process guidance; not empirical third-party statistics. |

## Key corrections/clarifications
- **Historical guardrail strengthened:** all `cited_in_blog` entries now explicitly note Phase 3 historical/attributed context and “не использовать как актуальное состояние рынка 2026 без независимой проверки первоисточника”.
- **BF-2020-001:** blog confirms 850k/30M text, but article passage names no primary source — remains `unverified_primary`.
- **BF-2020-002/003/004, BF-HOSTREAD-001:** blog citations (Bridge Ratings, PwC/IAB USA, Mediascope) observed in article text; primary reports still not independently verified.
- **BF-VNUKOVO-001:** blog text fetched 2026-11-07 confirms milestone wording (>2000 files, 9 languages, excluding RU/EN, project not completed at publication). Status remains milestone.
- **CF-AUDIOPLUS-ORDER:** `/audioplus/` fetched 2026-11-07 shows 1990 ₽ / ≤90 words / one-file framing; classified `partially_verified` (informational, verify full current terms).
- **CF-IVR-INDIVIDUAL:** IVR page fetched; GEO remains fact-safe (no unverified fixed numeric price). Main-site messaging alignment still owner action.
- **CF-MAIN-INCONSISTENCY-DICTORS:** unresolved contradiction recorded.

## Checks
- `python tools/build_geo_site.py --check` → OK
- `python tools/build_geo_site.py --safe` → OK (HTML not regenerated; `combined.json` preserved enriched blocks)

## Next (Phase 3 continuation / owners)
1. Obtain/verify **primary** report URLs for highest-value cited stats (PwC/IAB USA podcast formats/host-read, IAB Russia/Mediascope digital audio, Data Insight/People&Screens ROI) with exact claim scope + date/wave + quote/figure.
2. Owner confirmation on main site: 622 vs 620, current Audio+ packs/terms, IVR pricing communication/canonical policy, contacts.
3. Only after primary confirmation: promote specific claims to `verified` with scope-limited wording; otherwise keep `unverified_primary`/`partially_verified` or remove from answer surfaces.
4. Do not use Phase 3 as evidence of AI visibility improvement (P6 baseline still unexecuted).
