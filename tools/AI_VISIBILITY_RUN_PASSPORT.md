---
type: tool
date: 2026-11-17
lang: ru
related:
  - tools/AI_VISIBILITY_QUEUE_PLANNER.md
  - tools/AI_VISIBILITY_COVERAGE_ANALYZER.md
  - tools/AI_VISIBILITY_BENCHMARK.md
---

# AI Visibility Run Passport

The run-passport tool freezes the exact inputs to an AI-visibility measurement run and later binds collected evidence to that frozen plan. It is offline-only and performs no provider requests.

## 1. Freeze a planned run

Generate queue CSVs first with \`ai_visibility_queue.py\`. Then create a passport:

\`\`\`bash
python tools/ai_visibility_run.py create ^
  --run-id RU-2026-11-17-001 ^
  --module research/queries/ru-generic-discovery.json ^
  --queue research/queues/ru-generic-discovery.csv ^
  --output research/runs/RU-2026-11-17-001/passport.json ^
  --region-status UNVERIFIED
\`\`\`

Repeat \`--module\` and \`--queue\` for each frozen module and its generated queue. The passport records SHA-256 and byte size for every input, plus a compact query/platform/market matrix summary.

## 2. Verify before collection

\`\`\`bash
python tools/ai_visibility_run.py validate ^
  --passport research/runs/RU-2026-11-17-001/passport.json
\`\`\`

This detects changed, missing or replaced input files and modifications to the passport payload.

## 3. Validate evidence, then finalize

First run the existing benchmark and evidence validators, including exact queue linkage:

\`\`\`bash
python tools/ai_visibility_benchmark.py validate research/runs/RU-2026-11-17-001/observations.csv
python tools/ai_visibility_evidence.py validate-batch research/runs/RU-2026-11-17-001/evidence/ ^
  --csv research/runs/RU-2026-11-17-001/observations.csv ^
  --queue research/queues/ru-generic-discovery.csv
\`\`\`

Then freeze the output artifacts against the exact plan hash:

\`\`\`bash
python tools/ai_visibility_run.py finalize ^
  --passport research/runs/RU-2026-11-17-001/passport.json ^
  --run-id RU-2026-11-17-001 ^
  --observations-csv research/runs/RU-2026-11-17-001/observations.csv ^
  --evidence-dir research/runs/RU-2026-11-17-001/evidence/ ^
  --output research/runs/RU-2026-11-17-001/result.json
\`\`\`

Verify the completed run:

\`\`\`bash
python tools/ai_visibility_run.py validate-final ^
  --passport research/runs/RU-2026-11-17-001/passport.json ^
  --result research/runs/RU-2026-11-17-001/result.json
\`\`\`

## Integrity and interpretation

- Plan passport and result passport are separate immutable records. The result references the exact SHA-256 of the plan passport.
- Query modules, queue files, CSV observations and individual JSON evidence records are hashed with SHA-256 and their byte sizes are recorded.
- The tool never edits queues or observations.
- The current v1 passport intentionally supports only \`UNVERIFIED\` region status. It cannot promote the Netherlands/VPN or an operator assertion into a verified Russian vantage point. A future region-attestation workflow must define independent evidence and provenance before enabling that state.
- SHA-256 detects accidental or deliberate byte changes relative to the recorded digest; it does not authenticate who created the file, prove the source is truthful, or provide a digital signature.
- Run IDs are caller-supplied labels, not globally unique guarantees. Operators should use a stable unique naming convention.
- The tool does not replace benchmark/evidence validation and does not calculate visibility. Blocked, unavailable and error outcomes are not zero visibility.
- No AI/provider requests, paid checks, paid trackers, website changes, publishing, or network calls are made.

## Tests

\`\`\`bash
python -m unittest tools.tests.test_ai_visibility_run -v
\`\`\`
