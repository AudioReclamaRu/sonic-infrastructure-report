# AGENTS.md — how to work in this repository

Contract for any AI agent (or person) reading, querying or extending this repo.
Written 2026-10-01 after an audit found the entry points contradicting the code.

## What this repository is

A dated, source-backed fact corpus about what changes in the voice market under
generative AI, plus a canon of the industry's language and profession standards
for voice provenance and release responsibility. **No claim without a source; no
number retrofitted with a story.**

Three question layers, and the layer you need is decided by the question:

| Question | Layer | Read |
|---|---|---|
| "What happened?" | facts | `corpus/`, `evidence/`, `reports/intel/` |
| "How should I think about it?" | position | `canon/`, `TERMINOLOGY.md`, `dictionary/` |
| "How do I do this work?" | specification | `standards/`, `feed/`, `publisher.py` |

## Reading order

1. `llms.txt` — the layer names and canonical terms, with direct file pointers.
2. `MAP.md` — the one-screen chain Evidence → Reports → Entities → Terms →
   Standards → Workflow.
3. `README.md` — structure and the key deductions.
4. `FACT-METHOD.md` (RU) — **read before making any evidence claim.** Defines
   RADAR `p = 1,0`, the verdicts СОСТОЯЛОСЬ / ПЕРЕНОС / ОШИБКА, falsifiers, and
   the source hierarchy. Skipping it is how agents misread evidence status.
5. `evidence/E-2026-014.md` — one evidence record end to end, to learn the
   `Status / Type / Audience / Last updated` header and the `p=` format.
6. `standards/editorial-object-contract.md` (RU) — the machine-checkable
   editorial contract: 11-value `object_type` enum, 8-field `event_object`,
   cover derivation, named `REJECT` codes.

## Trust order (important)

When two files disagree, believe them in this order:

1. **The code.** `publisher.py:109` `REQ_CONCEPT_FIELDS` is the publication gate
   of record — not any prose description of it.
2. **A generated artifact.** `reports/INDEX.json`, `feed/images/manifest.json`,
   `tools/intent-templates.json`.
3. **The evidence layer.** `evidence/E-*.md` with `p=1,0` and a primary source.
4. **Prose docs.** `llms.txt`, `README.md`, `MAP.md`, `standards/`, `feed/`.

Reason: docs are written by hand and have drifted before (they described a
`win` field that never existed). If you find a doc contradicting the code, the
doc is wrong — fix the doc in the same change.

## Language

Facts of record are often Russian-first, with `.en.md` twins for the
international corpus. **An `.en` variant is authoritative when both exist.** The
editorial and visual standards (`standards/x10`–`x13`, `red-field-*`,
`editorial-object-*`) are Russian by decision, not by accident — do not treat
their being Russian as a defect, and do not machine-translate their normative
terms: «выпускающий голос», «Ошибка Карты», «Поле Принадлежности»,
«Закон Обряда», «Право Присутствовать» are defined terms, in `TERMINOLOGY.md`.

## Do not bulk-read these

- `reports/scans/` — 2.2 MB, ~35–46 unique URLs per ~170 KB file, mostly
  repeated evergreen items. Use `reports/intel/*.json` (deduplicated, typed).
  See `reports/README.md`.
- `feed/` — 59 of its 69 files are PNG. Read `feed/README.md` and
  `feed/images/manifest.json` instead of listing the directory.
- `state/` — runtime. Logs, pids, heartbeats, the live loop's scratch space.

## The live loop is not yours

`publisher.py --loop` runs as a long-lived process. `state/` is its working
state.

- Do not stop, restart or "fix" the running publisher.
- Do not stage `state/`, `reports/`, `register.csv`, `calendar*.html`,
  `news-view.html`, `feed/leads.csv` or `tg/` in a commit — they are runtime
  output, not content. `.gitignore` already lists most of them; when you add a
  runtime file, extend it.
- `state/rejected.txt` and `state/*_jsonl` are runtime. `state/rejected.txt`
  existing means a concept is currently frozen; its absence means nothing is.

## Adding content

- A **fact** belongs in `evidence/E-YYYY-NNN.md` with a primary source, `p=`,
  a verdict trace and a falsifier. Facts are cited by ID, never retold.
- A **position** belongs in `canon/` and is labelled POSITION — it is not a fact.
- A **specification** belongs in `standards/` and must be applicable: fields,
  tiers, checks a machine or a human can run.
- Editorial work is governed by `standards/editorial-object-contract.md`; the
  cases in `standards/editorial-object-cases.md` are filled **by hand** from real
  events and are never generated.
- Before committing, run `python tools/make_reports_index.py --check` if you
  touched anything under `reports/`.
