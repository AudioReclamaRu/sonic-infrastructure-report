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

## Expanded discovery nodes and candidate clusters

A second public-index search pass added 14 RUTUBE video nodes to the graph (see the node CSV). Two candidate similarity edges are recorded without asserting identity:
- Two generic "Озвучивание видео роликов" uploads have the same broad title but displayed durations of 28 sec and 70 sec.
- Two Webcom promo uploads both display 35 sec but have different IDs and titles.

These are discovery leads only. No video-file or audiovisual comparison was performed for either pair.

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
