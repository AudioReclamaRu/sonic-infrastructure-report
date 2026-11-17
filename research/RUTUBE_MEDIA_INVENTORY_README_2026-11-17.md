---
type: research
date: 2026-11-17
lang: en
related:
  - research/RUTUBE_MEDIA_INVENTORY_2026-11-17.csv
  - research/MEDIA_CONTENT_AUDIT_2026-11-17.md
---

# RUTUBE Public Media Inventory — 2026-11-17

This inventory captures 37 publicly indexed RUTUBE assets attributed to the public creator label **Аудио-Реклама•ru — флагман деловой звукозаписи**. It is a research snapshot, not an owner analytics export. Display titles normalize minor brand-spelling and punctuation variants to the canonical brand; source URLs remain the authority for the exact platform title.

## Fields and interpretation

- `asset_id`: stable RUTUBE video ID.
- `displayed_views`, `displayed_followers`: values visible in the public indexed card at research time; they are not reach, watch time, retention, unique viewers or conversions.
- `displayed_age_label`: platform age text as surfaced in the result.
- `indexed_publication_timestamp`: timestamp rendered by the indexed result, where available. It frequently conflicts with the age label (e.g. 2025-12-18 versus 11–16 years ago). Preserve both; do not select one as the true original publication date without page-level evidence.
- `capture_date`: date this research snapshot was compiled (2026-11-17), not the platform's publication date.
- `duplicate_status`: `confirmed_cross_platform_link` means the RUTUBE description explicitly linked to a YouTube video ID; `user_confirmed_identical_content` records the user's direct audiovisual review; `possible_same_service_cluster` or `possible_related_version` remains a candidate only, not a proven duplicate.
- Blank numeric/date fields mean not reliably captured, not zero/none.

## Findings

1. The second discovery pass added 14 indexed assets: advertising spots (РИО, OneOwner, МЕГА, Скоровар, НЕПРОСПИ, ТЦ Новая Эра, and a Vladimir regional campaign), two general video-voiceover samples, a separate Ilya Gulko demo, a PhotoFunia video-making sample, an older Webcom promo, and an НСС synchronous-voiceover item. The НСС item is marked temporarily unavailable, not deleted.
2. Three additional indexed items extend the service map: an НСС tariff-plan commercial (15 sec), a Russian Wealth greeting/IVR sample (24 sec), and a Sarov Business Bank deposit video (10 sec). The Sarov item is explicitly marked temporarily unavailable in the public result; it is not treated as deleted.
3. The inventory spans service explainer, presentation narration, localization, dubbing/lip-sync, subtitles, advertising voice-over, voice demos, sound design, logo audio and film-trailer narration.
4. Three generic presentation-narration entries (IDs `6b2195a00c6681c760fe3027e83c988f`, `a859a8ccbfddcd613676ca8786766ab9`, `498c5b58d739c33ad029a3dc98484678`) are treated as the same content based on the user's direct audiovisual review on 2026-11-17. This is recorded as `user_confirmed_identical_content`, not as an independently computed audio/video fingerprint. Their indexed durations (1:25, 3:07 and 1:20) conflict materially; retain all three source records and investigate whether duration metadata, page rendition or clip boundaries explain the discrepancy. Do not silently collapse the source IDs.
5. Two generic "Озвучивание видео роликов" samples (IDs `3f16c932b8b6ecce805ab51a95abda4e` and `2b525619cc77d1bf3cab10c4f193b555`) have different durations (28 sec and 70 sec); they remain separate, with a candidate service cluster only.
6. Two Webcom promo entries have the same displayed duration (35 sec) but different titles/IDs (`bb09d1b11b3bf0fd842696c2225a9477` and `183370cb7bf9436a4726c0088f111223`); this is a possible related-version cluster, not proof of duplicate content.
7. Two items labelled Едок share a project name and 20-second duration but have different titles and IDs. This is a possible related-version cluster, not a confirmed duplicate.
8. The service explainer RUTUBE description explicitly includes the YouTube URL `https://www.youtube.com/watch?v=MJJcbzR2wto`. This is a direct cross-platform link and a strong seed for matching the two assets.
9. The indexed publication timestamp often shows 18 December 2025 while the age label says 11–16 years ago. This likely reflects different date semantics or migration/indexing behavior, but the cause is not established. Treat this as a metadata anomaly, not proof of reuploading.
## Limitations

- Public search results do not expose full channel analytics or account ownership.
- Some snippets omit counters or exact timestamps; blank cells are intentionally left blank.
- No video files were downloaded or compared frame-by-frame/audio-fingerprint-wise in this pass.
- Client names in titles/descriptions do not establish current permission to reuse logos, publish case studies or promote client work.
- No account login, claim, edit, upload, deletion, outreach, promotion, paid service, spending or official website change occurred.

## Source coverage

All asset URLs and captured fields are in `RUTUBE_MEDIA_INVENTORY_2026-11-17.csv`. This is a selected indexed sample of 37 items, not yet a complete channel scrape.
