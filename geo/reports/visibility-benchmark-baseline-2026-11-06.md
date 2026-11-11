---
type: doc
date: 2026-11-06
lang: en
---
# AI Visibility Benchmark — baseline protocol (Audio-Reclama)
Date: 2026-11-06
Rule: **No growth claims without baseline.** No fabricated results.

## Platforms (minimum)
- ChatGPT Search
- Google AI Overviews / AI Mode (as available)
- Microsoft Copilot (Bing grounding)
- Gemini

## Test design
- Language: ru (primary), optionally en for selected queries.
- Region/context: record (e.g., Russia / unspecified / user locale) — do not guess.
- Queries: use `geo/knowledge/query-matrix.json` + manual set (brand + non-brand). Record exact query text.
- Cadence: baseline now (manual/semi-manual) + periodic repeats (e.g., monthly) with same core set.
- Evidence capture: screenshot or saved response text + cited URLs + timestamp. Store in a private/approved location if client data involved; public repo stores only anonymized/approved summaries.

## Record fields per run
| field | description |
|---|---|
| run_id | unique id |
| date | ISO datetime |
| platform | chatgpt_search / google_aio / copilot / gemini |
| language | ru/en |
| region | stated/observed |
| query | exact text |
| audio_reclama_mentioned | yes/no/unclear |
| cited_url | URL(s) cited, if any |
| citation_target | main domain / GEO / other |
| fact_accuracy | accurate / partial / incorrect / n/a |
| inaccuracies | short note |
| competitors_mentioned | list |
| notes | context |

## Baseline template (CSV header)
`run_id,date,platform,language,region,query,audio_reclama_mentioned,cited_url,citation_target,fact_accuracy,inaccuracies,competitors_mentioned,notes`

## Current status
- No automated/real UI benchmark executed in this pass (no access/approval/tooling). This file establishes protocol and templates only.
