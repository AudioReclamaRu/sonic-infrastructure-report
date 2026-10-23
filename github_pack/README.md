# audio-reclama.ru

llms.txt and structured-data pack for AI answer engines (AEO/GEO).

This repo does not change the production site. It hosts:
- `llms.txt` — summary for AI crawlers
- `faq-audio-reclama.json` — FAQPage JSON-LD (copy-paste into site later)
- `price-table.csv` — machine-readable price table cited by answer engines

## Usage
1. Publish this repo as-is (GitHub auto-indexes).
2. When ready to touch the site, add `faq-audio-reclama.json` to `<head>` as `<script type="application/ld+json">`.
3. Regenerate `price-table.csv` whenever prices change.
