---
type: doc
date: 2026-11-06
lang: mul
---
# Main-domain technical audit (read-only): www.audio-reclama.ru
Date: 2026-11-06
Scope: publicly accessible checks only (no edits to main site, DNS, CDN, robots on main site). Observations are inputs for implementation by site owners.

## robots.txt
- URL: https://www.audio-reclama.ru/robots.txt (fetched 2026-11-06)
- Observed: `User-agent: *` with multiple `Disallow` rules including `Disallow: /*?`; `Sitemap: https://www.audio-reclama.ru/sitemap.xml`. `Allow` for some assets/`/en/`.
- **No explicit `OAI-SearchBot` or `GPTBot` directives observed** in the fetched content.
- Recommendation (owner decision): if goal is appearance in ChatGPT Search, review OpenAI guidance and consider explicit policy for `OAI-SearchBot`. Treat `GPTBot` separately (training vs search/indexing use cases) — do not conflate. Any robots changes require careful review of existing crawl/SEO behavior.

## sitemap.xml
- URL: https://www.audio-reclama.ru/sitemap.xml (accessible 2026-11-06)
- Observed: includes homepage, `/en/`, key sections (`/diktoryi/`, `/clients.html`), projects (incl. Vnukovo, ABBYY, Microsoft, РЖД, Braun, Globus, Ренессанс Кредит), services (IVR, audiobooks, video, commercials, calculators, blog posts, `audioplus`).
- Check next (owner): freshness of `<lastmod>`, coverage of all indexable commercial/answer pages, no blocked URLs included, consistency with canonicals.

## GEO-relevant content consistency risks (observed)
- **IVR pricing communication:** GEO layer represents IVR as *individual calculation* (fact-safe, no unverified fixed price). Main IVR page observed to describe calculator/cost composition (production + narrator fee) rather than an explicit single “рассчитывается индивидуально” sentence in the excerpt checked. **Action for owners:** align main-site messaging with chosen verified commercial policy; if fixed/package prices are published, ensure they are current, consistent, and supported by visible terms.
- **Homepage numeric inconsistency:** observed “622 диктора” and “620 дикторов” in different places on `https://www.audio-reclama.ru/` (2026-11-06). **Action:** verify actual count and unify.
- **Entity/NAP consistency:** ensure brand (`Аудио-Реклама•ru` / audio-reclama.ru), contacts, and service naming are consistent across main site, profiles, and GEO.

## Technical checks to complete (owner / with access)
- HTTP status/canonical/meta robots for key commercial pages (home, services, IVR, audioplus, projects, blog, contacts).
- Structured data validity and consistency with visible text (Organization, Service/Offer only when factual, FAQ/HowTo where appropriate, BreadcrumbList). No fake prices/ratings.
- Internal linking to proof/case/answer content; text accessibility (not image-only key facts).
- Indexability under `Disallow: /*?` implications for parameterized URLs; verify important pages not unintentionally suppressed.
- Consider adding/aligning `llms.txt` or proof links on primary domain **only** if content is verified and maintained (Google states AI files are not a guarantee).

## Evidence
- Recorded as CF-MAIN-INCONSISTENCY-DICTORS / audit notes in `geo/knowledge/evidence-ledger.json`.
