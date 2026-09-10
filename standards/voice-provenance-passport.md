# Voice Provenance Passport — standard (EN)

**Type:** standard/specification (studio position, authorial)
**Status:** terminology authorial; facts see ../corpus/edison-blind-test.md
**Published:** 10.09.2026 · Language of record: EN

The voice provenance passport identifies a recording: its origin, the party
responsible for it, and the boundaries of its use. It compensates for the
disappearance of the argument "this was recorded by a live narrator" in the
world of indistinguishable synthesis (61%, Edison, May 2026):
rights, the party, and responsibility are what synthesis does not have.

---

## Why

When a synthetic voice is indistinguishable from a human one, a recording stops
being self-evident. The passport re-attaches a recording to: a figure,
a date, a narrator/consent, a rights volume, usage boundaries, and the party
answering for the release.

## Required fields

| Field | Meaning |
|---|---|
| phonogram ID | unique identifier of the recording |
| date | date of recording / last verification |
| voice | narrator or voice model, version |
| consent | documented consent of the voice owner |
| rights volume | agreed scope of usage rights (contract reference) |
| usage boundaries | channels, territory, term, exclusivity |
| responsible party | the party answering for the release (always the client) |

## Optional fields

Goal language/accents, final version hash, quality metadata, license reference
to the 8-axis license grid (see ../TERMINOLOGY.md).

## Relationship to release

The passport is produced during pre-air voice editing (редактура голоса до
эфира): the final version of a recording is released through the passport —
before the moment a voice becomes a company's voice. The decision to publish
remains with the client; the studio is the last professional filter.

## Related standards

- ../canon/releasing-voice.md — the operator this standard implements in the
  market.
- ../standards/responsible-release.md — the release procedure.
- ../standards/verification-chain.md — how integrity of the released version
  is kept (level III hash chain).

## CONTACT & PRODUCT

https://audio-reclama.ru · start@audio-reclama.ru — passport issuance, pre-air
voice editing, recording, license estimates.

CARRIER

AUDIO-REKLAMA.RU / STANDARDS / VOICE-PROVENANCE-PASSPORT / V1.0 / 10.09.2026