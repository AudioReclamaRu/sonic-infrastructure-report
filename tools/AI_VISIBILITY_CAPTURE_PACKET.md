---
type: tool
date: 2026-11-17
lang: en
related:
  - tools/AI_VISIBILITY_RUN_PASSPORT.md
  - tools/AI_VISIBILITY_BENCHMARK.md
  - tools/AI_VISIBILITY_FINAL_REPORT.md
---

# AI Visibility Manual Capture Packet

The capture packet generator prepares blank CSV and JSON templates from a frozen run passport. It does not collect answers, create observations or infer missing values.

## Prepare

\`\`\`bash
python tools/ai_visibility_capture.py ^
  --passport research/runs/RU-2026-11-17-001/passport.json ^
  --output-dir research/runs/RU-2026-11-17-001/capture-packet
\`\`\`

The command requires a valid passport with VERIFIED regional status and an intact region attestation. It refuses to overwrite an existing output directory.

## Output

- capture.csv: one blank benchmark row for each planned queue cell, with run, market, query, platform and measurement mode prefilled.
- evidence/: one primary JSON draft template per planned cell, with stable observation IDs and the exact attestation ID/SHA-256.
- capture-manifest.json: packet status, run/passport references, queue hashes and template inventory.
- README_CAPTURE.md: operator instructions and validation/finalization sequence.

## Operator requirements

Templates are explicitly marked NOT_TESTED. They are not valid evidence until the operator fills them from an actual captured session.

For each observation, record the actual UTC timestamp, exact product, actual region and the evidence supporting that region, complete answer, source/capture references, outcome status and applicable scores. Do not invent or backdate any value.

Every observation must occur within 30 minutes of the verified regional session capture. If the window expires, stop and create a new attestation and a new run passport; do not reuse stale regional proof.

Keep consumer UI, model API and search-results UI separate. A failed, blocked or unavailable attempt must retain its actual status and must not be turned into zero visibility.

## Finish

After completing the packet, validate the benchmark CSV and evidence records against every queue and the exact region attestation. Then finalize the run passport, validate the result passport and generate the final report. Any mismatch blocks finalization.

The packet builder is offline-only. It performs no provider requests, geolocation lookups, paid checks, website changes or publication.
