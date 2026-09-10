# Verification Chain — how integrity of a released voice is kept

**Type:** standard/specification (studio position, authorial)
**Status:** POSITION — builds on ../standards/living-voice-standard.md (Level III)
**Published:** 10.09.2026 · Language of record: EN

---

## Why

When a synthetic voice is indistinguishable from a human one (Edison/SSRS, May
2026: 61%), «who recorded this» stops being audible. It becomes a question
answered by **evidence**: presence at a session, consent, and a tamper-evident
chain from recording to publication. The chain is the production form of
honesty (canon 04) and the technical form of provenance (canon 05).

## The verification tiers (cumulative)

| Tier | Name | Evidence |
|---|---|---|
| I | Declaration | signed Living Voice Declaration |
| II | Session | verifier present at the recording session, notes (date, time, location, identity) |
| III | Hash Chain | chained cryptographic digests from source recording through processing to publish |

Tiers are cumulative: III includes obligations of I and II.

## Hash chain construction (Level III)

```
H0 = digest(source recording)
H1 = digest(H0 || processed_v1)        each link incorporates the digest of the previous one
H2 = digest(H1 || processed_v2)
...
Hn = digest(Hn-1 || published_version)  final digest belongs to the released file
```

Properties:

- **Tamper-evident:** any change after publishing breaks the chain.
- **Ordering:** every later digest commits to every earlier one.
- **No audio exposure:** only digests are stored/compared; audio data never
  leaves the client and is never transferred to third parties.
- **Reproducible check:** any party can re-derive Hn from the files and compare
  with the certificate.

## Certificate (issued by the verifier, valid 12 months)

- artist's name; verification tier (I/II/III); material identifier;
- verification date; digest of the recording (II/III);
- unique certificate number; status (valid / expired / revoked).

## Public register

The verifier maintains a public register: certificate number, artist name (with
consent), tier, date, status. Updated at least every 7 days. Any listener may
request authenticity within 3 working days and demand a public review on
reasonable doubt.

## Label rules

- OK to mark: verified human voice (certificate exists); or material with no
  voice (instrumental/nature), declared as such.
- Never mark: unlabelled synthetic voice; materially modified voice without the
  label «Voice modified»; third-party voice without a declaration; unverified
  material — even if the voice is human.

## Related

- ../standards/living-voice-standard.md — the standard this chain implements.
- ../standards/voice-provenance-passport.md — the document that carries the
  chain's final digest and responsible party.
- ../standards/responsible-release.md — the procedural pre-air check.
- ../canon/error-of-the-map.md — why the check is uncircumventable by design.

## Product

Verification certificates, hash-locked releases, provenance passports, public
register. https://audio-reclama.ru · start@audio-reclama.ru

CARRIER

AUDIO-REKLAMA.RU / STANDARDS / VERIFICATION-CHAIN / V1.0 / 10.09.2026