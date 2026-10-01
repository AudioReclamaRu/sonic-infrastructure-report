# reports/ — the live operational layer

This directory is **not** the fact corpus. `corpus/` and `evidence/` are the
fact layer; `reports/` is what the studio produced *while watching* the market,
plus machine-readable run output. It is 84 of the repository's tracked files, and
it used to be reachable only through Russian prose in `standards/x12*` and
`x13*` or by reading PowerShell in `tools/`. This file plus the generated index
make it navigable by an agent that reads no Russian.

## Index (start here)

- **`reports/INDEX.json`** — machine index, one row per tracked file:
  `{path, kind, date, bytes, guids[], evidence[], url_count?, unique_urls?,
  rows?, row_keys?}`. Generated, never hand-edited.
  Regenerate: `python tools/make_reports_index.py`
  Verify (exit 1 if stale): `python tools/make_reports_index.py --check`
  The index covers **tracked** files only, so a clone's index always matches
  what the clone actually has.

## The layers

| Directory | Kind | What it is | Volume | Read it? |
|---|---|---|---|---|
| `intel/` | `signal_rows` | Daily machine-readable fact stream, `.md` + `.json` per day | 408 KB, 325 rows | **SEARCH THIS** |
| `signals/` | `signal_note` | Dated editorial signal note («Today's Interface») | 8 files | yes |
| `verdicts/` | `verdict_log` | Append-only verdict record: CONFIRMED / RESCHEDULED / SOURCE ERROR | 1 file | yes |
| `monitoring/` | `registry` | Venue/source registry, owner: intel runner; per `standards/x12-global-monitoring.md` | 1 file | yes |
| `outreach/` | `outreach_draft` | Outreach letters to outlets (`draft-YYYY-MM-DD-N.md`), RU operational | 22 files | on demand |
| `scans/` | `scan_dump` | Raw market scan dumps | **2.2 MB, 13 files** | **NO — see below** |
| `status-*.md`, `status.html` | `run_status` | Daily run status, generated views | 13 files | rarely |

## `intel/` schema (the layer worth parsing)

Top level is exactly `{date, rows}`. Each row carries 18 fields, stable across
the whole series (verified 2026-10-01 over every `intel/*.json` on disk):

`source_language`, `event_geo`, `domain`, `ent`, `mkt`, `prc`, `pts`, `score`,
`tier`, `status`, `title`, `url`, `snippet`, `src`, `svc`, `contact_email`,
`contact_page`, `contact_ready`

Codes (`ent`, `mkt`, `src`, `svc`, `prc`, `tier`) are decoded in
`tools/intent-templates.json` and `standards/x12-global-monitoring.md`. Read
those before interpreting a field.

## Why `scans/` is a trap

`scans/scans-YYYY-MM-DD.md` are raw dumps. Each file is ~170 KB but contains only
**35–46 unique URLs** — the same evergreen items repeat many times per file and
again across days. The whole directory is 2.2 MB, larger than `intel/` by 5×,
for near-zero marginal information.

- Do not glob-and-read `scans/`.
- For "what is new in the market", read `intel/intel-<date>.json` — it is
  deduplicated by construction and typed.
- `scans/` remains as a raw trail. Deduplicating it at generation time is a
  separate, later change; nothing depends on it today.

## Provenance of a published post

```
reports/intel/intel-YYYY-MM-DD.json   (a fact enters here)
        ↓
evidence/E-YYYY-NNN.md               (the fact is fixed with a source + verdict)
        ↓
reports/signals/<date>.md            (what the fact changed)
        ↓
reports/verdicts/verdict-index.md    (the verdict on it)
        ↓
feed/items.csv + feed/concepts.json  (if it gets published)
```

`feed/rss.xml` maps published `guid` → source document; it is the practical
back-link from a published post back to this layer.
