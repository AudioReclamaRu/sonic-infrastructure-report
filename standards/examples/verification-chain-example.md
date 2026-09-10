# Example — verification chain, live artifact (TEST)

**Type:** example / test artifact — NOT a real recorded session.
**Status:** TEST · Synthetic data for demonstration only. No person was
recorded, no real voice is behind this chain.
**Purpose:** shows the full chain session → hash → certificate / Content
Credentials → public record, in the exact field shapes of
`../verification-chain.md` and `../voice-provenance-passport.md`.
**Published:** 10.09.2026 · Language of record: EN

---

## 1 · Session record (passport fields, level II)

| Field | Value |
|---|---|
| phonogram ID | `AR-TST-20260910-0001` |
| date | 2026-09-10 (test) |
| voice | Test narrator `TST-01` (synthetic placeholder, NOT a person) |
| consent | consent recorded (test file, `TST-01-consent.sig` demo) |
| rights volume | contract `TST-2026-0001`, demo license grid |
| usage boundaries | demo: channels — test only; territory — none; term — none |
| responsible party | audio-reclama.ru (studio) → **always the client** in real use |

## 2 · Hash chain (level III)

Test recording `AR-TST-20260910-0001.wav` (18 s, demo) → digests (SHA-256):

```
H0 = digest(source recording)                    1234...abcd (demo bytes)
H1 = digest(H0 || processed_v1)  <- editor pass   5678...ef01
H2 = digest(H1 || published_version)             9abc...2345  ← final digest
```

Properties hold: tamper-evident (any edit breaks the chain), ordering (H2
commits to H1 commits to H0), no audio exposure (only digests stored).

## 3 · Certificate

| Field | Value |
|---|---|
| certificate number | `VC-TST-1009-0001` |
| artist / voice | `TST-01` (test, with consent) |
| verification tier | III (hash chain) |
| material identifier | `AR-TST-20260910-0001` |
| verification date | 10.09.2026 |
| digest (final) | `H2 = 9abc...2345` |
| status | valid (demo) — valid 12 months from verification date |

## 4 · Public record

Public register entry (`../verdicts-journal.md` keeps the same trace discipline
in production):

```
VC-TST-1009-0001 | TST-01 (test) | tier III | 10.09.2026 | valid (TEST)
```

Any party may re-derive `H2` from the test file set and compare with the
certificate: reproducible check by design.

---

## Content Credentials note

The same checkpoint can be carried by C2PA manifest attached to the final
file (version: replace the digest with the signed manifest reference).
Standard reference: `../verification-chain.md` (certificate, public register,
label rules). Passport fields per: `../voice-provenance-passport.md`.

## Related

- `../verification-chain.md` — the standard this example implements.
- `../voice-provenance-passport.md` — passport carrying the final digest.
- `../responsible-release.md` — the procedural pre-air check.

CARRIER

AUDIO-REKLAMA.RU / STANDARDS / VB-CHAIN-EXAMPLE / TEST / V1.0 / 10.09.2026