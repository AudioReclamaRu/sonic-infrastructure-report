---
type: doc
date: 2026-10-01
lang: mul
---
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

- `reports/scans/` — 2.2 MB (measured 2026-10-01), ~35–46 unique urls per ~170 KB
  file, mostly repeated evergreen items. Use `reports/intel/*.json`
  (deduplicated, typed) instead. See `reports/README.md` and
  `python tools/make_reports_index.py --measure`.
- `feed/` — 59 of its 69 files are PNG. Read `feed/README.md` and
  `feed/images/manifest.json` instead of listing the directory.
- `state/` — runtime, with two tracked exceptions: `state/editorial.jsonl` and
  `state/verdicts.jsonl` are the verdict trail and are version-controlled on
  purpose. Logs, pids, heartbeats and scratch space are not.

## The live loop is not yours

`publisher.py --loop` runs as a long-lived process. `state/` is its working
state.

- Do not stop, restart or "fix" the running publisher.
- Do not stage `state/`, `reports/`, `register.csv`, `calendar*.html`,
  `news-view.html`, `feed/leads.csv` or `tg/` in a commit — they are runtime
  output, not content. `.gitignore` already lists most of them; when you add a
  runtime file, extend it.
- `reports/` is local-first: a clone tracks it only as far as the studio has
  published (through 2026-09-23 as of 2026-10-01) while the live loop keeps
  writing new days. Absence of a date in git is not absence of activity.
- `state/rejected.txt` and everything in `state/` except
  `state/editorial.jsonl` / `state/verdicts.jsonl` (the tracked verdict trail)
  is runtime. `state/rejected.txt` existing means a concept is currently frozen;
  its absence means nothing is.

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

## The frontmatter contract (all hand-authored .md)

Every hand-authored `.md` starts with a YAML header. It is the only place a
collection can be filtered on, so treat it as schema, not decoration:

```yaml
---
id: E-2026-014          # only when the file HAS a stable id
type: evidence          # see the type table below
date: 2026-09-11        # filename > legacy "Last updated" > last commit
lang: ru                # en | ru | mul (English doc carrying Russian terms)
status: verified        # only when the file states a status
related: [corpus/edison-blind-test.md]   # back-links, when they exist
---
```

- `type` values in use: `evidence`, `entity`, `corpus`, `operator`, `card`,
  `term`, `ar_note`, `interface`, `standard`, `guide`, `catalog`, `runbook`,
  `index`, `doc`.
- `lang: mul` is deliberate, not untidy: `AGENTS.md`, `README.md`,
  `USE_CASES.md` and several standards are English documents that keep Russian
  defined terms on purpose. Only `lang: en` means "no Russian at all".
- The legacy `Status: / Type: / Audience: / Last updated:` block is **kept** as
  the human-facing header; frontmatter is the machine surface. If you change a
  value in one, change it in the other.
- Generated layers (`reports/`, `state/`, everything in `feed/` except
  `feed/README.md`) are deliberately **excluded** — they are rewritten by the
  live loop, and a header the generator does not emit rots on the next run.
- Enforce with `python tools/add_frontmatter.py --check`; add new files through
  the same tool (`--apply`) so the shape stays uniform.

