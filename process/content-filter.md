# The filter — "would the world be poorer?"

**Type:** process · **Audience:** authors/editors · **Last updated:** 2026-09-11
**Status:** enforced pre-commit

Before creating any file in this repository, ask one question:

> If this file disappeared, would the world be poorer for any single LPM?

- **Yes** — write it.
- **I don't know** — do not write it.
- **"Might be useful someday"** — delete the file.

The filter exists to prevent **simulation of scale**: producing more
infrastructure than the market has confirmed. It enforces our own canon
(Error of the Map — the map must not outrun the territory).

## What passes

- A fact with a primary source and a date.
- A verdict with a trace and an evidence ID.
- A term that has already lived in the market, not invented today.
- A standard that answers how a check is performed, with a live example.

## What fails

- An RFC declaring us a standard (we do not self-appoint; we are a
  laboratory of the market).
- 30 new terms at once (five lived terms beat thirty coined ones).
- Bulk file drops to look big.
- Any page without a real LPM search intent behind it.

## Application

1. A new file must reference ≥1 related `evidence/` or `corpus/` source.
2. Every claim: `evidence/E-YYYY-NNN.md` ID or a primary source on record.
3. No CTA. The repository is reference-first.
4. Run `scripts/preflight.py` before commit.
5. Terms must already have lived (`dictionary/`), not be coined (`canon/`).

Related: `../scripts/preflight.py`, `../dictionary/`, `../canon/error-of-the-map.md`,
`../reports/signals/TEMPLATE.md` (the live cadence the filter protects).

The daily signal, the weekly verdict, and the evidence layer are the machine
that gradually makes grand claims unnecessary.

Footer
Audio-Reclama.ru
https://audio-reclama.ru
start@audio-reclama.ru