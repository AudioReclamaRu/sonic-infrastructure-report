# MAP — how this repository works

**Type:** map · **Audience:** anyone opening the repository · **Last updated:** 2026-09-11
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
Interfaces
    ↓
Business Workflow
```

## What each layer is for

| Layer | Directory | Question it answers |
|---|---|---|
| Evidence | `evidence/` | With what proof does a fact stand? (E-YYYY-NNN IDs) |
| Reports | `reports/` | What changed for business today? (Daily Signal, Weekly Verdicts) |
| Entities | `entity/` | Who and what exists on the market — as stable, linkable records |
| Terms | `dictionary/` + `TERMINOLOGY.md` | What does a term mean here — one lived definition per term |
| Standards | `standards/` | How work is done: verification chain, release checks |
| Interfaces | `interfaces/` | The boundaries where human, AI, law, and responsibility meet — one page, one concept |
| Business Workflow | `USE_CASES.md` | Who reaches for which layer, and when |

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

Related
- README.md
- USE_CASES.md
- reports/verdicts/verdict-index.md
- interfaces/INTERFACE-001-voice-provenance.md
- corpus/
- canon/

Footer
Audio-Reclama.ru
https://audio-reclama.ru
start@audio-reclama.ru