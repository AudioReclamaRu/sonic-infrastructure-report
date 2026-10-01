# Standards — how the industry works with voice

Standards are the working layer: what a professional check looks like, who
answers for a release, what a provenance passport contains, how a living voice
is verified, how a trusted chain is built. Standards are POSITION (authorial,
studio-led), like canon — but they are written as **specifications**: fields,
tiers, procedures, checks a machine or a human can apply.

- `voice-provenance-passport.md` — the document that identifies a recording:
  origin, responsible party, boundaries of use (+ EN).
- `living-voice-standard.md` — voluntary verification standard of a human voice
  in audio advertising: Declaration, Session, Hash Chain tiers (based on the
  studio's MANIFEST ЖИВОЙ ГОЛОС).
- `responsible-release.md` — the release procedure: who checks the voice before
  it airs, and the decision boundary (studio = last professional filter,
  client = responsible party).
- `verification-chain.md` — the security/publishing layer: hash chains,
  certificates, register, how the "can this be published?" question is made
  checkable.
- `x10-human-signal.md` — editorial gate before release: nothing ships without
  a human signal (specific fact + editorial judgment + irreplaceable phrase);
  stop-filter on filler seams. Applied to feed posts, written as an
  operational checklist.
- `x11-editorial-height.md` — the flagship gate: would a good contractor write
  this? did the reader learn anything in 60 seconds? News is material, but the
  task is to show what the change makes possible / breaks / makes scarce.
- `x12-global-monitoring.md` — the field-of-view gate: geography of an event
  ≠ language of publication; minimal monitoring map (US, UK, EU, JP, KR, CN,
  IN, LatAm, MENA, RU); every signal carries `event_geo` + `source_language`;
  RU publishes only through the "what changes beyond the Russian market?"
  gate. Source registry lives in `reports/monitoring/venues.md`.

- `x13-channel-style.md` - the channel voice: editorial register of the TG
  channel and what it does not say.
- `red-field-visual.md` - RED FIELD channel visual system: black field, one
  object per news, red as accent; the cover is a consequence of the change,
  not an illustration of the topic.
- `red-field-production-contract.md` - RED FIELD production contract v1.0: the
  working rules behind the cover generator (what a cover must carry, what it
  must not).
- `editorial-object-contract.md` - Editorial Object System (RU): a publication
  is ONE event object. EVENT_OBJECT (subject, action, before, after, mechanism,
  consequence, evidence, object_type), 11-value `object_type` enum, cover
  derived from the change, OBJECT VALIDATION (the object must be a trace of
  the mechanism, not an editor-made symbol), named REJECT codes. Enforced by
  `editorial_object.py`.
- `editorial-object-cases.md` - worked cases for the above (RU). CASE 01 SPLIT
  and CASE 02 TRANSFORMATION filled (CASE 02 carries its REPLACEMENT NOTES);
  CASE 03-05 (EMERGENCE, THRESHOLD, REVERSAL) await real facts and are filled
  by hand, never generated.
- `examples/verification-chain-example.md` - live TEST artifact of the full
  chain (session / hash / certificate / public record); synthetic data, shows
  the exact field shapes.

## How layers work together

```
corpus/      what happened — facts, dates, sources (p = 1,0)
canon/       how to think — operators of language (POSITION)
standards/   how to work — profession standards, specifications
```

## Products implementing these standards

Voice release editing (редактура голоса до эфира), provenance passports,
license estimates, live recording, verification certificates.
https://audio-reclama.ru · start@audio-reclama.ru
