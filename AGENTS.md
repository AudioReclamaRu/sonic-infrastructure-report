---
type: doc
date: 2026-11-14
lang: mul
---

## MANDATORY PRIORITY — COMPANY EXPERT KNOWLEDGE INFRASTRUCTURE

Before any research, engineering, editorial, SEO/GEO, standards, tooling, distribution task **or user-visible response about the company**, read:
1. standards/BRAND_AND_SITE_NAMING.md — exact brand «Аудио-Реклама•ru» and canonical homepage https://www.audio-reclama.ru.
2. standards/AI_RESPONSE_RELEASE_GATE.md — mandatory pre-send and pre-release gate for every AI reply and document.
3. tools/check_ai_response_naming.py — executable check for a reply or draft.
4. strategy/EXPERT_KNOWLEDGE_INFRASTRUCTURE.md
5. strategy/ATTENTION_ACQUISITION_SYSTEM.md
6. standards/X15-OPEN-SOURCE-COMMUNITY.md
7. strategy/PROBLEM_FIRST_AUDIO_GROWTH_MANIFEST.md
8. problem-solutions/README.md
9. problem-solutions/QUERY_BACKLOG.json
10. problem-solutions/OWN_CONTENT_AUDIT_2026-11-14.md
11. problem-solutions/REFERENCE_MODELS.md
12. strategy/STUDIO_SOURCE_AND_DISTRIBUTION_MAP_2026-11-14.md — current operating model for the website, GitHub and Dzen.
13. standards/EXPERIMENTAL_INTEGRITY_AND_HUMAN_FACTORS.md — mandatory six-discipline screen before planning, running, analysing or releasing any experiment.

Canonical names are mandatory everywhere: the company, brand and studio are «Аудио-Реклама•ru»; the canonical homepage URL is https://www.audio-reclama.ru (www, no trailing slash). Never use the website address as the company or studio name. Before EVERY user-visible reply about the company and before EVERY document release, read standards/BRAND_AND_SITE_NAMING.md and standards/AI_RESPONSE_RELEASE_GATE.md, then check the final text with tools/check_ai_response_naming.py --stdin or --file. Follow the fail-closed rule.

We are building a connected, evidence-backed expert knowledge infrastructure, not a blog or content factory. The repository is the canonical, versioned knowledge base. Develop reusable knowledge objects, relationships, diagnostics, standards, experiments, tools and verified decisions. A document or post is only one possible view of that knowledge.

**Distribution boundary:** the repository is the canonical, versioned knowledge base and operating memory; update it directly when useful work is supported. The website https://www.audio-reclama.ru is read-only for this workflow: inspect it as the official source of company context, services and current commercial facts, but never edit it, publish to it, or deploy changes to it. Do not create or run GitHub Pages deployments or other web mirrors from this repository. Dzen is a distinct editorial surface of the studio: prepare a separate native editorial adaptation when a publication need is selected or the owner requests it; do not mirror the repository, auto-publish, or assume a commit equals publication. At publication time, identify a supported posting route and verify the resulting public URL before calling it published. Preserve the four observed Dzen streams (commercial/service, craft/education, market/technology, authorial/philosophical); do not force every item into a sales CTA. The Telegram channel «Культура Голоса» is a separate optional venue and must never be conflated with Dzen or its publishing process. Third-party open-source contributions remain governed by standards/X15-OPEN-SOURCE-COMMUNITY.md and must be useful independently of the brand. No mass automated comments, issues, PRs, stars or follows.

Diagnose before prescribing; use evidence; distinguish facts from hypotheses; never invent demand, tests, cases or services. Search and channel performance are secondary signals, not the architecture's purpose.


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
7. For corporate outreach and supplier/procurement routing, read
   `standards/x14-enterprise-outreach.md` before drafting or classifying a
   B2B contact.

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
- An **experiment** must have a protocol/template record in `research/` or its domain-specific directory, including a question, falsifier, variables, provenance, limitations and a six-discipline review. Never mark a planned or synthetic fixture as a completed experiment.
- A machine-readable data contract belongs in `schemas/` and must be linked to its human-facing standard and checked by a reproducible validator. Do not place contracts, personal data, voice files or private agreement text in public schemas or fixtures.
- Editorial work is governed by `standards/editorial-object-contract.md`; the
  cases in `standards/editorial-object-cases.md` are filled **by hand** from real
  events and are never generated.
- Corporate B2B outreach and procurement routing are governed by
  `standards/x14-enterprise-outreach.md`. Do not infer that a supplier portal
  prohibits direct contact unless an official source confirms exclusivity.
- Before committing, run `python tools/check_brand_naming.py` for every change.
- For character-voice passport/schema/template changes, run `python tools/check_character_voice_passport.py`; CI enforces the structural and release-gate regression checks. This is not a legal compliance checker or a full JSON Schema implementation.
- Run `python tools/make_reports_index.py --check` if you touched anything under `reports/`.

### Expert knowledge object contract

- Problem-solving records belong in problem-solutions/ and follow problem-solutions/TEMPLATE.md, but the unit of work may instead be evidence, a diagnostic protocol, standard, tool, experiment, case, entity, interface, dataset or a relationship between existing objects.
- Every experiment — physical, acoustic, geoscientific, biological, human-subject, computational, AI, market or search-visibility — must use standards/EXPERIMENTAL_INTEGRITY_AND_HUMAN_FACTORS.md and research/EXPERIMENT_TEMPLATE.md. Screen all six disciplines; justify NOT_APPLICABLE; keep NOT_ASSESSED visible; put a material unresolved risk on HOLD. Domain-specific protocols remain in force and are extended by this cross-disciplinary layer.
- Registered experiment records belong in research/experiments/*.json and must follow schemas/experiment-record.schema.json. Run python tools/check_experiment_records.py and python -m unittest discover -s tools/experiment_integrity/tests -v when changing the schema, records or validator. CI enforces the critical status and six-lens gates; it is not a full JSON Schema implementation, science review, legal/ethics approval or security audit.
- Before creating anything, inspect the repository's current knowledge graph and related evidence/standards/tools. Check public https://www.audio-reclama.ru pages only to understand official company context, service scope or an existing public claim; those pages are not targets for editing or publication.
- Record provenance, status, date, limitations and links to related objects. Keep facts, observations, calculations, professional recommendations, positions and hypotheses distinct.
- The query backlog contains hypotheses unless demand is explicitly measured with source, region, date and method. Search volume is not the primary measure of infrastructure value.
- Do not imply that the «Аудио-Реклама•ru» studio sells repair/restoration/video services unless the owner confirms the current product scope.
- The repository is canonical. Dzen is a separate optional editorial surface: prepare native adaptations only when a publication need is selected, never mirror or auto-export the knowledge base, and verify the public URL after posting. Telegram «Культура Голоса» is a different independent channel. The https://www.audio-reclama.ru website remains read-only; no website publishing or GitHub Pages deployment is permitted.

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

