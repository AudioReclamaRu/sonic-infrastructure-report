---
type: tool
date: 2026-11-17
lang: en
related:
  - tools/AI_VISIBILITY_RUN_PASSPORT.md
  - tools/AI_VISIBILITY_CAPTURE_PACKET.md
  - tools/AI_VISIBILITY_FINAL_REPORT.md
---

# AI Visibility Run Bootstrap

The run bootstrap command assembles the verified-run prerequisites in one offline operation: queue, plan passport, capture packet and package manifest.

## Prepare a run

\`\`\`bash
python tools/ai_visibility_prepare_run.py ^
  --module research/queries/ru-generic-discovery.json ^
  --region-attestation research/ru-region-attestation.json ^
  --run-id RU-2026-11-17-001 ^
  --output-dir research/runs/RU-2026-11-17-001 ^
  --operator-label operator-1
\`\`\`

The command requires an independently reviewed VERIFIED region attestation, validates the frozen query module, creates a VERIFIED queue, seals the run passport and generates blank capture templates.

## Package contents

- inputs/query-module/ — exact byte-for-byte snapshot of the frozen query module.
- inputs/region-attestation/ — exact attestation plus every referenced evidence file, preserving attestation-relative paths.
- queue.csv — deterministic queue generated from the snapshotted query module.
- passport.json — sealed run plan with module, queue and region attestation hashes; its input paths resolve inside the package.
- capture-packet/ — blank CSV and JSON capture templates.
- run-package.json — hashes and references for the assembled package.
- README_RUN.md — next-step instructions.

The package is created in a temporary sibling directory and moved into place only after all stages validate. Existing output directories are never overwritten. The module and regional evidence inputs are snapshotted into the package so the plan does not depend on absolute paths back into the original workspace. The attestation JSON and evidence bytes are copied unchanged; evidence paths must remain inside the attestation's source directory.

## After preparation

Follow capture-packet/README_CAPTURE.md. Complete templates only from actual sessions, then validate the evidence, finalize and validate the result passport, and generate the final report.

The tool does not collect AI responses, perform geolocation lookups, or infer region. It does not call providers, consume paid credits, modify the website or publish anything.
