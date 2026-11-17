---
type: protocol
date: 2026-11-17
lang: ru
related:
  - research/AI_VISIBILITY_REGION_ATTESTATION_SCHEMA_2026-11-17.json
  - tools/AI_VISIBILITY_RUN_PASSPORT.md
  - tools/AI_VISIBILITY_BENCHMARK.md
---

# RU Consumer AI Vantage-Point Attestation

## Purpose

The RU baseline must be collected from a demonstrably Russian network vantage point. A Netherlands session, VPN exit, proxy, cloud host or remote desktop must never be relabeled as a Russian consumer session.

This protocol defines a manually assembled evidence pack and an offline validator. It does not discover the operator's location, query geolocation services, or independently prove the truth of submitted evidence.

## Evidence pack

One JSON attestation references four kinds of artifacts:

1. **Two independent IP-geolocation observations.** Both must report RU, have distinct providers and independence groups, distinct evidence files, and timestamps within 30 minutes of the consumer UI capture.
2. **Network-owner / ASN evidence.** It must identify the access network as a local residential ISP, mobile carrier or business ISP and agree with the declared connection type.
3. **Consumer UI session capture.** A screenshot or equivalent original artifact showing the platform/product and ru-RU interface locale, captured in the same 30-minute window.
4. **Operator declaration.** The operator explicitly states direct connection and no VPN, proxy or remote desktop.

The network section stores a keyed HMAC fingerprint of the public IP, not the raw IP address. The HMAC key must remain outside the repository and evidence pack. Never commit credentials, cookies, account tokens, raw IP addresses or personal account identifiers.

## Review and status semantics

Run:

\`\`\`bash
python tools/ai_visibility_region.py path/to/ru-region-attestation.json
\`\`\`

Possible statuses:

| Status | Meaning |
|---|---|
| EVIDENCE_INCOMPLETE | Required evidence is missing, malformed, stale, inconsistent or has a failed integrity check |
| PENDING_REVIEW | Structure and evidence-file hashes pass, but an independent reviewer has not approved |
| VERIFIED | All required evidence is present and hash-valid, and a reviewer other than the operator has approved |
| REJECTED | An independent reviewer rejected the attestation |

A VERIFIED result means the evidence pack passed this protocol's structural and review gates. It is not cryptographic proof of physical location, network ownership, vendor independence or the truth of screenshots. The human reviewer must inspect the original evidence and assess those claims.

## Non-negotiable safeguards

- VPN, proxy, cloud-hosting, remote-desktop and unknown network types cannot qualify for the RU consumer baseline.
- Geolocation observations must agree on RU and be contemporaneous with the UI session.
- The reviewer must differ from the operator and provide a timestamp and rationale.
- Do not manually edit a queue or observation from UNVERIFIED to VERIFIED. After review, regenerate the queue with `ai_visibility_queue.py --region-attestation` and create the run passport with the same attestation; the tools enforce the matching hashes and deterministic queue output.
- Model API calls and search-results UI observations are not consumer UI sessions.
- No network lookup, AI query, paid check, tracker, proxy, website change or publication is performed by this validator.

## Files

- JSON Schema: research/AI_VISIBILITY_REGION_ATTESTATION_SCHEMA_2026-11-17.json
- Offline validator: tools/ai_visibility_region.py
- Regression tests: tools/tests/test_ai_visibility_region.py
