# MISSED-EVENT AUDIT 2026-10-12

KPI `MISSED_MAJOR_EVENTS_PER_WEEK`; ladder SOURCE -> CANDIDATE -> CLASSIFY -> PUBLICATION.

- recall (SOURCE): **2/8 = 25.0%**
- classified STRONG: 0/8 = 0.0%
- published (verdict recorded): 0/8 = 0.0%
- discovery surface: 32 endpoints
- loss stages: CLASSIFY=2, SOURCE=6

| event | date | loss stage | matched item / reason | endpoint |
|---|---|---|---|---|
| ElevenLabs Eleven v4 / v4 Turbo | 2026-09-28 | SOURCE | not present on the current discovery surface (32 endpoints) | - |
| ElevenLabs valuation doubles to $22B | 2026-09-30 | SOURCE | not present on the current discovery surface (32 endpoints) | - |
| Tokyo court: human voice legal protection (AI clone) | 2026-09-30 | SOURCE | not present on the current discovery surface (32 endpoints) | - |
| Radiocentre: audio budget shift increases profit ROI | 2026-09-30 | CLASSIFY | Shifting search and social budget into audio increases profit | radiocentre-news |
| Radiocentre: UK commercial audio +20% over decade | 2026-10-01 | CLASSIFY | UK commercial audio forecast to deliver a new era of growth | radiocentre-news |
| Fireflies adds dictation | 2026-09-29 | SOURCE | not present on the current discovery surface (32 endpoints) | - |
| Telnyx Ultra adds Urdu and Odia voices | 2026-09-29 | SOURCE | not present on the current discovery surface (32 endpoints) | - |
| AssemblyAI/Exotel multilingual voice agents | 2026-09-30 | SOURCE | not present on the current discovery surface (32 endpoints) | - |

## raw results

```json
[
  {
    "event_id": "ev-001",
    "title": "ElevenLabs Eleven v4 / v4 Turbo",
    "date": "2026-09-28",
    "org": "ElevenLabs",
    "class": "VOICE_AI",
    "found_in_source": false,
    "first_source": null,
    "match_title": null,
    "match_url": null,
    "grade": null,
    "in_ledger": false,
    "has_verdict": false,
    "loss_stage": "SOURCE",
    "loss_reason": "not present on the current discovery surface (32 endpoints)"
  },
  {
    "event_id": "ev-002",
    "title": "ElevenLabs valuation doubles to $22B",
    "date": "2026-09-30",
    "org": "ElevenLabs/Reuters",
    "class": "BUSINESS",
    "found_in_source": false,
    "first_source": null,
    "match_title": null,
    "match_url": null,
    "grade": null,
    "in_ledger": false,
    "has_verdict": false,
    "loss_stage": "SOURCE",
    "loss_reason": "not present on the current discovery surface (32 endpoints)"
  },
  {
    "event_id": "ev-003",
    "title": "Tokyo court: human voice legal protection (AI clone)",
    "date": "2026-09-30",
    "org": "Tokyo District Court/AP",
    "class": "LAW_REG",
    "found_in_source": false,
    "first_source": null,
    "match_title": null,
    "match_url": null,
    "grade": null,
    "in_ledger": false,
    "has_verdict": false,
    "loss_stage": "SOURCE",
    "loss_reason": "not present on the current discovery surface (32 endpoints)"
  },
  {
    "event_id": "ev-004",
    "title": "Radiocentre: audio budget shift increases profit ROI",
    "date": "2026-09-30",
    "org": "Radiocentre",
    "class": "AUDIO_AD",
    "found_in_source": true,
    "first_source": "radiocentre-news",
    "match_title": "Shifting search and social budget into audio increases profit",
    "match_url": "https://www.radiocentre.org/shifting-search-and-social-budget-into-audio-increases-profit/?utm_source=rss&#038;utm_medium=rss&#038;utm_campaign=shifting-search-and-social-budget-into-audio-increases-profit",
    "grade": "WEAK",
    "in_ledger": true,
    "has_verdict": false,
    "loss_stage": "CLASSIFY",
    "loss_reason": "matched a feed item but graded WEAK; WEAK/NONE are not auto-promoted (human eyes only)",
    "match_date": "2026-09-30"
  },
  {
    "event_id": "ev-005",
    "title": "Radiocentre: UK commercial audio +20% over decade",
    "date": "2026-10-01",
    "org": "Radiocentre",
    "class": "AUDIO_AD",
    "found_in_source": true,
    "first_source": "radiocentre-news",
    "match_title": "UK commercial audio forecast to deliver a new era of growth",
    "match_url": "https://www.radiocentre.org/uk-commercial-audio-forecast-to-deliver-a-new-era-of-growth/?utm_source=rss&#038;utm_medium=rss&#038;utm_campaign=uk-commercial-audio-forecast-to-deliver-a-new-era-of-growth",
    "grade": "WEAK",
    "in_ledger": true,
    "has_verdict": false,
    "loss_stage": "CLASSIFY",
    "loss_reason": "matched a feed item but graded WEAK; WEAK/NONE are not auto-promoted (human eyes only)",
    "match_date": "2026-10-01"
  },
  {
    "event_id": "ev-006",
    "title": "Fireflies adds dictation",
    "date": "2026-09-29",
    "org": "Fireflies/TechCrunch",
    "class": "VOICE_AI",
    "found_in_source": false,
    "first_source": null,
    "match_title": null,
    "match_url": null,
    "grade": null,
    "in_ledger": false,
    "has_verdict": false,
    "loss_stage": "SOURCE",
    "loss_reason": "not present on the current discovery surface (32 endpoints)"
  },
  {
    "event_id": "ev-007",
    "title": "Telnyx Ultra adds Urdu and Odia voices",
    "date": "2026-09-29",
    "org": "Telnyx/Dev48",
    "class": "LOCALIZATION",
    "found_in_source": false,
    "first_source": null,
    "match_title": null,
    "match_url": null,
    "grade": null,
    "in_ledger": false,
    "has_verdict": false,
    "loss_stage": "SOURCE",
    "loss_reason": "not present on the current discovery surface (32 endpoints)"
  },
  {
    "event_id": "ev-008",
    "title": "AssemblyAI/Exotel multilingual voice agents",
    "date": "2026-09-30",
    "org": "AssemblyAI/Exotel",
    "class": "LOCALIZATION",
    "found_in_source": false,
    "first_source": null,
    "match_title": null,
    "match_url": null,
    "grade": null,
    "in_ledger": false,
    "has_verdict": false,
    "loss_stage": "SOURCE",
    "loss_reason": "not present on the current discovery surface (32 endpoints)"
  }
]
```
