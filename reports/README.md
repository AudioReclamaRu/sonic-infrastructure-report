# reports/ — the live operational layer

This directory is **not** the fact corpus. `corpus/` and `evidence/` are the
fact layer; `reports/` is what the studio produced *while watching* the market,
plus machine-readable run output. It is 84 of the repository's tracked files, and
it used to be reachable only through Russian prose in `standards/x12*` and
`x13*` or by reading PowerShell in `tools/`. This file plus the generated index
make it navigable by an agent that reads no Russian.

## Index (start here)

- **`reports/INDEX.json`** — machine index, one row per tracked file:
  `{path, kind, date, generated?}` plus, for the stable layers, `guids`,
  `evidence` and `url_count`. Generated, never hand-edited.
  Regenerate: `python tools/make_reports_index.py`
  Verify (exit 1 if stale): `python tools/make_reports_index.py --check`
  Volume table on demand: `python tools/make_reports_index.py --measure`
  The index covers **tracked** files only, so a clone's index always matches
  what the clone actually has.

  Two things are deliberately **not** in the index:
  - measurements of `generated: true` files (`intel/`, `scans/`, `outreach/`,
    `status-*`), which the live loop rewrites without a commit;
  - `bytes` for any file — size is a property of the local checkout, not of the
    committed content (with `autocrlf` the same file measures 5885 bytes in one
    clone and 5984 in another, so a stored size made `--check` pass locally and
    fail on every clone).

  Volumes below are point-in-time figures for this checkout; re-run `--measure`.

## The layers

Measured 2026-10-01 via `--measure`; re-run it rather than trust the numbers.

| Directory | Kind | What it is | Volume | Read it? |
|---|---|---|---|---|
| `intel/` | `signal_rows` | Daily machine-readable fact stream, `.md` + `.json` per day | 26 tracked files, 408 KB; working tree holds 21 json / 481 rows | **SEARCH THIS** |
| `signals/` | `signal_note` | Dated editorial signal note («Today's Interface») | 8 files, 10 KB | yes |
| `verdicts/` | `verdict_log` | Append-only verdict record: CONFIRMED / RESCHEDULED / SOURCE ERROR | 1 file | yes |
| `monitoring/` | `registry` | Venue/source registry, owner: intel runner; per `standards/x12-global-monitoring.md` | 1 file | yes |
| `outreach/` | `outreach_draft` | Outreach letters to outlets (`draft-YYYY-MM-DD-N.md`), RU operational | 22 files, 47 KB | on demand |
| `scans/` | `scan_dump` | Raw market scan dumps | **2.2 MB, 13 files** | **NO — see below** |
| `status-*.md`, `status.html` | `run_status` | Daily run status, generated views | 15 files | rarely |

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

## A clone lags this layer — on purpose

`reports/` is local-first. The live loop writes new daily output continuously
(intel, scans, outreach, status) and by repo rule runtime output is not staged
by hand, so `git` tracks this layer only as far as the studio publishes it. As of
2026-10-01 the tracked part ends at 2026-09-23 while the working tree holds
through 2026-10-01.

Consequences for an agent:

- `reports/INDEX.json` indexes the **tracked** subset, so it always describes what
  the clone actually has — never promise it will list a file that is not there.
- If you need the current signals, ask for a commit of the layer rather than
  concluding from a clone that the market was quiet on those days.

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
