---
type: research
date: 2026-11-17
lang: en
related:
  - research/RUTUBE_MEDIA_INVENTORY_2026-11-17.csv
  - research/RUTUBE_WEBSITE_CASE_CROSSWALK_2026-11-17.csv
---

# Cross-platform Media Provenance Graph — 2026-11-17

## User-reviewed identical presentation-voiceover clips

The user directly reports that the three RUTUBE presentation-voiceover clips below are identical in content:
- `6b2195a00c6681c760fe3027e83c988f` — displayed duration 1:25
- `a859a8ccbfddcd613676ca8786766ab9` — displayed duration 3:07
- `498c5b58d739c33ad029a3dc98484678` — displayed duration 1:20

The graph records pairwise `user_reports_identical_audiovisual_content` edges. This is a user-review assertion, not an independently verified file hash or audiovisual fingerprint. The substantial duration mismatch remains open and must not be erased or explained by assumption.

## Current RUTUBE, YouTube and Dzen profile relationships

The public Dzen profile `https://dzen.ru/audioreclamaru` was fetched and displayed 294 followers. Its brand, email, profile description and self-reported WOW AWARDS 2018 claim match the RUTUBE and YouTube public profiles. Its metadata includes `noindex, follow`; this is recorded as a page directive, not a claim about all Dzen article indexing.

Three recent price-explainer articles are linked from the Dzen profile. Search/profile snippets state: English dubbing 30 sec from 3,500 RUB (Kazakh/Uzbek from 3,000); IVR minimum order from 1,999 RUB or 198 RUB/file in a 100-file package; advertising voiceover from 1,667 RUB/file in a 30-file package or 3,500 RUB one-off. Direct article fetches returned a temporary-unavailable message, so these remain snippet-only claims with no exact publication timestamp. See `DZEN_CONTENT_AND_PRICE_SNAPSHOT_2026-11-17.csv`.


The public RUTUBE channel page (`channel/73612493`) and public YouTube channel (`@audioreclama`) returned matching display brand, contact email, profile description and self-reported WOW AWARDS 2018 claim. The graph records a medium-confidence public profile-text match only; account ownership and admin access are not inferred.

A RUTUBE Short explicitly contains the Dzen URL `dzen.ru/audioreclamaru`. The graph records the link reference, not ownership of the Dzen profile. A direct fetch of the VK Video route redirected to a generic VK Video landing page; no absence or ownership conclusion is drawn.

The current channel page surfaced 20 standard videos and 20 Shorts. Their 40 IDs and page metadata are recorded separately from the 55-item historic/commercial portfolio inventory.

## Same-title duplicate groups confirmed by the user

The user clarified that **all videos carrying the same displayed label/title are identical because the user personally duplicated them**. Apply this rule across both the 55-item historical portfolio inventory and the separate 40-item current-channel snapshot. Accordingly, the following same-title groups are confirmed as identical in content by direct user statement:
- `О настоящем`: `a09326cb28c58665913f4b9adc96a42b` and `0c6e3a93eabaead32f8508a03271bce6` (both 173 sec; different IDs and publication dates).
- `Как внимание оживляет реальность?`: `d3165979354bec5ef112f0fc2fc5c373` and `adc39b0c0a683ac99e9520fb8772b851` (396 sec and 120 sec; video + Short).
- `Что меняется, когда мы обращаем внимание?`: `2bb4d1d1a5fae2124d8908d655ab04f7` and `252772852a7693e56f215c2be9d7929a` (506 sec and 113 sec; video + Short).
- `Озвучивание видео роликов. Аудио-Реклама•ru`: `3f16c932b8b6ecce805ab51a95abda4e` and `2b525619cc77d1bf3cab10c4f193b555` (28 sec and 70 sec).

The three presentation-voiceover records above are also user-confirmed identical content. Keep every platform ID, URL, date, duration and counter as a separate source record. The user's statement establishes content identity for this inventory; it does not establish byte-for-byte identity of downloaded files or replace an independently computed file hash/fingerprint. Duration discrepancies remain recorded, not silently reconciled.

## Expanded discovery nodes and candidate clusters

A second public-index search pass added 14 RUTUBE video nodes to the graph (see the node CSV). The generic "Озвучивание видео роликов" pair has the same displayed title and is now user-confirmed identical in content under the user's general same-title rule. The two Webcom promo uploads both display 35 sec but have different IDs and titles; they remain a candidate related-version cluster because the titles do not match. No file hash or independent audiovisual fingerprint was computed.

## Page-level verification: YouTube service-explainer target

A direct fetch of the exact YouTube URL `MJJcbzR2wto` returned the same Open Graph title and service-explainer description as the RUTUBE page `1d312c393658146cae1c56746592dd43`. This upgrades the edge from URL-only evidence to an exact URL plus title/description metadata match. The YouTube page body itself did not expose the video stream or full creator metadata, so byte-level or audiovisual identity remains unverified.

## Page-level metadata for the three user-confirmed presentation samples

The user reports that the three presentation-voiceover clips are identical in content. RUTUBE metadata now independently confirms their page durations and dates:
- `6b2195a00c6681c760fe3027e83c988f`: 86 sec; published 2025-12-15
- `a859a8ccbfddcd613676ca8786766ab9`: 188 sec; published 2015-07-10
- `498c5b58d739c33ad029a3dc98484678`: 80 sec; published 2015-07-10

This resolves the indexed timestamp discrepancy for these records, but does not reconcile the content identity assertion with the different durations. User review remains the identity evidence; RUTUBE metadata only establishes dates and duration fields. See `RUTUBE_PAGE_METADATA_VERIFICATION_2026-11-17.csv`.

## What is established

The public RUTUBE service-explainer page `1d312c393658146cae1c56746592dd43` includes an exact YouTube watch URL with video ID `MJJcbzR2wto`. Its description also includes a VK share URL whose query parameter wraps that same YouTube URL.

This yields two defensible edges:
1. RUTUBE description → exact YouTube URL reference.
2. RUTUBE description → VK share route wrapping that YouTube URL.

The second edge is **not** evidence of a VK-hosted copy. Nor does the first prove the YouTube target is an identical audiovisual file, a reupload, or still available.

## Separate platform presences

The public YouTube handle `@audioreclama` and VK Video community/surface `-18300431` were separately observed in earlier indexed research. They are recorded as brand-attributed public presences, but no exact asset-level connection to the RUTUBE video above is established.

## Files

- `CROSS_PLATFORM_MEDIA_NODES_2026-11-17.csv`: nodes with stable IDs and verification status.
- `CROSS_PLATFORM_MEDIA_EDGES_2026-11-17.csv`: only explicit, evidence-backed relations.

## Evidence rules

- Exact URL reference ≠ same media.
- For this user's RUTUBE inventory, same displayed video title = user-confirmed identical content because the user personally duplicated same-title videos. This is a direct user assertion, not independent binary identity verification. Same client, duration, creator label or channel without the same title does not by itself establish a duplicate.
- A share URL ≠ native platform upload.
- Search-index attribution ≠ account ownership or admin access.
- Unavailable or unfetched destination ≠ deleted asset.
- No video download, audiovisual fingerprinting, account login, profile claim/edit, upload, outreach, promotion, paid check or website change was performed.

## Source

- RUTUBE page and description: https://rutube.ru/video/1d312c393658146cae1c56746592dd43/
