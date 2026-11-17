---
type: research
date: 2026-11-17
lang: en
related:
  - research/RUTUBE_MEDIA_INVENTORY_2026-11-17.csv
  - research/RUTUBE_WEBSITE_CASE_CROSSWALK_2026-11-17.csv
---

# Cross-platform Media Provenance Graph — 2026-11-17

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
- Same title, client, duration, creator label or channel ≠ duplicate.
- A share URL ≠ native platform upload.
- Search-index attribution ≠ account ownership or admin access.
- Unavailable or unfetched destination ≠ deleted asset.
- No video download, audiovisual fingerprinting, account login, profile claim/edit, upload, outreach, promotion, paid check or website change was performed.

## Source

- RUTUBE page and description: https://rutube.ru/video/1d312c393658146cae1c56746592dd43/
