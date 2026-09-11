# Voice Catalog — infrastructure

**Type:** infrastructure · **Status:** template-only, no generated pages yet
**Audience:** Enterprise · **Last updated:** 2026-09-11

The catalog turns voice assets into search entry pages for the enterprise
queries they answer. No fake pages: only the structure and taxonomy live here;
pages are generated only for real, verified voice assets of Audio-Reclama.ru.

Principles
- **Entry page, not a person card.** A page answers a search intent
  (`Голос для банков • мужской 35–45 • русский • IVR`), not "who we are".
- **Templates only.** `voice-page-template.md` defines the shape.
- **Taxonomy first.** `taxonomy.md` defines all attributes before any page exists.

## Files

- `taxonomy.md` — attribute set for voice entry pages
- `voice-page-template.md` — the page shape (metadata + body)
- This README — generation rules (whom to generate for, and when)

Related: `../standards/responsible-release.md` (release check the generated
pages must reflect), `../dictionary/` (lived terms, the vocabulary pages exist
to serve).

## Generation rules

- Generate only for real, verified assets; never invent voices.
- Only attributes from `taxonomy.md`; no ad-hoc fields.
- Every generated page: one H1, metadata block, ≥2 internal links, canonical
  site link, no CTA.

## Example URL pattern

```
/catalog/male-russian-corporate-35-45
```

A single real voice asset may answer dozens of long-tail queries (banking,
IVR, corporate, multilingual). The page is titled for the strongest one and
lists the rest in the body.

Footer
Audio-Reclama.ru
https://audio-reclama.ru
start@audio-reclama.ru