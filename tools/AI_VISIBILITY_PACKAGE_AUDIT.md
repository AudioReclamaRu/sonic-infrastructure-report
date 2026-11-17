---
title: "AI Visibility Run Package Audit"
type: "engineering"
status: "active"
---

# AI Visibility Run Package Audit

The package auditor verifies a prepared run directory after creation or after it has been copied to another machine.

## Command

```powershell
python tools/ai_visibility_package.py --package-dir .\artifacts\ai-visibility\run-001
```

The command is offline. It does not contact AI providers, perform measurements, change the website, or modify the package.

## Checks

- Package schema and lifecycle are correct.
- Query-module, queue, regional-attestation and plan-passport files exist inside the package and match their recorded SHA-256 hashes.
- The regional attestation still validates as independently reviewed VERIFIED evidence, including the hashes of its copied evidence files.
- The plan passport validates and binds the exact packaged module, queue and attestation.
- Queue row count matches the manifest and every planned row remains `NOT_TESTED`.
- Capture packet schema, run ID, passport hash, attestation ID/hash and planned-cell count match the package.
- Capture CSV and JSON templates remain drafts: no timestamps, answers, product labels, region observations or scores have been inserted.
- Every template has a unique observation ID and the expected run ID.
- Package and capture instructions are present.
- Referenced paths cannot escape the package root.

## Interpretation

A successful audit means the plan package is intact and its blank capture packet is internally consistent. It does not prove that the regional claim is true, that a real session occurred, or that any AI-visibility measurement has been collected. A successful audit is not a visibility result.
