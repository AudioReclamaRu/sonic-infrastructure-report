---
type: tool
date: 2026-11-17
lang: en
related:
  - tools/AI_VISIBILITY_RUN_PASSPORT.md
  - tools/AI_VISIBILITY_COVERAGE_ANALYZER.md
  - tools/AI_VISIBILITY_BENCHMARK.md
---

# AI Visibility Final Report

The final report builder combines the validated run/result passports, queue coverage and answered-only benchmark summary into one reproducible JSON and/or Markdown report.

## Run

\`\`\`bash
python tools/ai_visibility_report.py ^
  --passport research/runs/RU-2026-11-17-001/passport.json ^
  --result research/runs/RU-2026-11-17-001/result.json ^
  --json-out research/runs/RU-2026-11-17-001/report.json ^
  --markdown-out research/runs/RU-2026-11-17-001/report.md
\`\`\`

## Validation gates

Before generating either output, the tool:

1. Validates the plan passport and finalized result passport, including artifact hashes, run ID, queue-cell matching, CSV-to-JSON linkage and region attestation provenance.
2. Revalidates the benchmark CSV structure.
3. Recomputes coverage from the exact queue files frozen in the plan passport.
4. Recomputes benchmark groups from the finalized CSV.

Any validation error stops report generation. The report does not alter the source artifacts.

## Report contents

- Run ID, plan/result hashes, region verification status and attestation reference.
- Planned, observed and missing cells, collection coverage and answer-status counts.
- Coverage by market/locale, platform, measurement mode and intent.
- Answered-only discovery and critical-error metrics, plus score aggregates.
- Missing planned cells and interpretation safeguards.

## Interpretation rules

- Collection coverage is not visibility success.
- Only OK and PARTIAL rows contribute to answered-only benchmark metrics.
- Blocked, unavailable, unsupported, error and untested outcomes are not zero visibility.
- Consumer UI, model API and search-results UI remain separate measurement modes.
- A validated report proves consistency of the supplied artifacts and pipeline, not the truth of the original captured answers or the authenticity of screenshots.

## Tests

\`\`\`bash
python -m unittest tools.tests.test_ai_visibility_report -v
\`\`\`

The builder is offline-only. It performs no provider requests, geolocation lookups, paid checks, website changes or publication.
