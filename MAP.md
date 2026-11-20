---
type: doc
date: 2026-11-17
lang: en
related: [interfaces/INTERFACE-001-voice-provenance.md, reports/verdicts/verdict-index.md]
---
# MAP — how this repository works

**Type:** map · **Audience:** anyone opening the repository · **Last updated:** 2026-11-17
**Status:** stable

One scheme. Everything hangs on it.

```
Evidence
    ↓
Reports
    ↓
Entities
    ↓
Terms
    ↓
Standards
    ↓
Schemas / Data Contracts
    ↓
Interfaces
    ↓
Business Workflow
```

## What each layer is for

| Layer | Directory | Question it answers |
|---|---|---|
| Company entity | `entity/` source-graded company record + Schema.org record | Who is the studio, what does its official source currently show, and what remains unverified? |
| Evidence | `evidence/` | With what proof does a fact stand? (E-YYYY-NNN IDs) |
| Reports | `reports/` | What changed for business today? (Daily Signal, Weekly Verdicts) |
| Entities | `entity/` | Who and what exists on the market — as stable, linkable records |
| Terms | `dictionary/` + `TERMINOLOGY.md` | What does a term mean here — one lived definition per term |
| Standards | `standards/` | How work is done: verification chain, release checks |
| Data Contracts | `schemas/` | Which fields and conditional gates machine-readable records must satisfy |
| Tools | `tools/` | Which repeatable checks can be run locally or in CI |
| Problem Solutions | problem-solutions/ | Why it happens, how to diagnose, fix and verify it |
| Interfaces | `interfaces/` | The boundaries where human, AI, law, and responsibility meet — one page, one concept |
| Business Workflow | `USE_CASES.md` | Who reaches for which layer, and when |
| Publishing | `feed/` + `publisher.py` | What did we publish, and how (schedule, concept gate, covers) |
| Open-source participation | `standards/X15-OPEN-SOURCE-COMMUNITY.md` + `strategy/ATTENTION_ACQUISITION_SYSTEM.md` | How to contribute to external projects through trust and useful work, not advertising |
| AI Discoverability operations | `ops/ai-discoverability/` + `strategy/AI_DISCOVERABILITY_AUTONOMOUS_OPERATING_MODEL_2026-11-20.md` | How does Megabrain choose, execute, validate and stop improvements toward useful discovery? |

## Strategic priority

Read strategy/EXPERT_KNOWLEDGE_INFRASTRUCTURE.md, strategy/ATTENTION_ACQUISITION_SYSTEM.md, standards/X15-OPEN-SOURCE-COMMUNITY.md, strategy/PROBLEM_FIRST_AUDIO_GROWTH_MANIFEST.md and problem-solutions/README.md first. The AI Discoverability operating model and file-based Megabrain contract define the execution loop, its autonomy boundaries, measurement gates and stop rules. Problem-solutions/ is the user-problem diagnostic layer. It is distinct from commercial GEO answers and enterprise guides. Its backlog begins with unmeasured hypotheses, not popularity claims. Public participation in third-party repositories follows X15: social trust, project-specific policy, verified contribution and long-term responsibility.

## Canonical company entity

The company itself has a dedicated, source-graded record in `entity/`. Its companion Schema.org JSON-LD is a portable representation for reuse by agents and tooling. These are repository artifacts, not a claim that structured data has been installed on the official website. Volatile counters and unsupported founding-date/client-outcome claims are deliberately excluded.

## Reading order

1. Start here: MAP.
2. Then `USE_CASES.md` — who uses what.
3. Then `dictionary/` — the living terms.
4. Then `corpus/` and `evidence/` — facts, and the proof they stand on.
5. Depths spelled out in `guides/` when a case needs one.

## How facts and verdicts connect

`corpus/` records what happened → `evidence/E-YYYY-NNN.md` fixes the proof →
`reports/signals/` marks what changed today → `reports/verdicts/verdict-index.md`
logs the verdict on it. Each next document leans on the previous one — that
chain (Evidence → Entity → Verdict → Signal) is what makes this a knowledge
graph, not a blog.

## How the channel publishes (Publishing layer)

`feed/items.csv` (schedule) → `feed/concepts.json` (editorial gate: the 9 fields
of `publisher.py:109` `REQ_CONCEPT_FIELDS` = headline, demo, explain,
consequence, visual_object, cover_prompt, demo_shift, object_type, cover_test;
the post passes only when all 9 are filled; REJECT freezes the guid in
`state/rejected.txt`, a runtime file that exists only while a concept is
frozen) → `feed/image_gen.py` (version-aware RED FIELD cover, one object per
news, uniqueness vs the last 20 covers) → `publisher.py` (autonomous TG-first
loop, idempotent by guid). Concepts may additionally carry `event_object` +
`article_structure` (Level B, Editorial Object System — see
`standards/editorial-object-contract.md`).
Contract details: `feed/README.md`.

Related
- README.md
- USE_CASES.md
- reports/verdicts/verdict-index.md
- interfaces/INTERFACE-001-voice-provenance.md
- corpus/
- canon/

Footer
Аудио-Реклама•ru
https://www.audio-reclama.ru
start@audio-reclama.ru
