# Living Voice Standard — verification of a human voice in audio advertising

**Type:** standard/specification (voluntary, publicly binding once adopted)
**Status:** studio position; the studio's MANIFEST «ЖИВОЙ ГОЛОС» v0.1
**Facts base:** ../corpus/edison-blind-test.md (why verification matters)
**Published:** 10.09.2026 · Languages: RU (record), EN (annex)

---

## Article 1 · Purpose

The Living Voice Standard is a voluntary but publicly binding standard for
**verifiable human voice** in audio advertising. Using the mark "Живой Голос /
Living Voice" means accepting this standard without exceptions.

It is **not** a technical regulation: it does not prescribe the means of
production. It fixes one rule of honest labelling:

> If a voice in an audio recording belongs to a living person — that must be
> provable. If a voice is generated, modelled, or synthesized — that must be
> stated.

## Article 2 · Basic terms

- **Living Voice** — a person's voice recorded with their direct participation,
  without synthetic generation, material modification, or substitution.
- **Living Voice Declaration** — written confirmation by the voice artist (or
  their authorized representative) that a voice in a given audio recording is
  their own live voice, recorded with their direct participation.
- **Session Control** — verification in which the artist is present at the
  recording and confirms the voice's belonging during the session.
- **Hash Chain** — a sequence of cryptographic fingerprints of audio files,
  fixing recording integrity from session to publication.
- **Verification Mark** — the graphic marker «Живой Голос», placed on materials
  verified under this standard.
- **Subscriber's Voice** — a voice belonging to the advertising client (not the
  artist), used in the advertisement.

## Article 3 · Verification levels (cumulative)

| Level | Name | Requirement |
|---|---|---|
| I | Declaration | Signed Living Voice Declaration — sufficient for the Mark |
| II | Session | + a verifier present at the recording session |
| III | Hash Chain | + chained cryptographic digests from session to publication |

## Article 4 · Procedure

1. The artist applies to the verifier (Uho Planety / authorized auditor) with a
   verification request.
2. The verifier confirms receipt and the order of verification within 5 working
   days.
3. On completion, the verifier issues a **Living Voice Certificate**:
   artist's name, verification level, audio material identifier, verification
   date, hash of the recording (levels II and III), unique certificate number.
4. Certificate validity: **12 months** from issue.

## Article 5 · Use of the Mark

The Mark is placed on a material when:
- (a) a valid Certificate (level I, II, or III) exists; or
- (b) the material contains no voice (instrumental, nature sounds) and this is
  declared separately.

The Mark is **not** placed on materials containing:
- (a) generated/ai (TTS) voice without the explicit label «Синтетический голос /
  Synthetic voice»;
- (b) materially modified voice (pitch-shift, voice conversion, similar)
  without the label «Голос модифицирован / Voice modified»;
- (c) a third party's voice without a Declaration.

Misuse entails public delisting and review of trust in all earlier
Certificates of that artist.

## Article 6 · Obligations of the artist

- Guarantee the truth of the Declaration.
- On discovering substitution or unlabelled synthetic voice: notify the
  verifier immediately, secure Certificate revocation, remove the Mark.
- Answer personally to the verifier and to the listener.

## Article 7 · Obligations of the client (advertiser)

- Have a valid Certificate at the moment of using the Mark.
- Not alter the material after verification without re-check.
- State the verification level with the Mark. No Mark on unverified materials,
  even if the voice is human.

## Article 8 · Rights of the listener

Any listener may request certificate authenticity (within 3 working days) and
demand a public review upon reasonable doubt.

## Article 9 · Public register

The verifier maintains a public Register of Living Voice Certificates:
number, artist name (with consent), level, date, status (valid / expired /
revoked). Published at least once every 7 days.

## Article 10 · Data protection

Audio recordings are **not** stored and **not** transferred to third parties;
verification is based on hashes, not audio data. Data is stored encrypted;
access only for verification by request of the artist or auditor.

## Article 11 · Attitude to synthetic voice

This standard is **not** a protest against synthetic voice as technology.
Synthetic voice is an admissible tool with honest labelling. The standard is
against **misuse**: substitution, deception, devaluation of live artists'
skill. The division into "live / synthetic" is not a confrontation but a rule
of fair play.

---

## ENGLISH LAW ANNEX

**WHEREAS:**

(a) advances in synthetic voice technology create audio indistinguishable from
human speech to the average listener (see ../corpus/edison-blind-test.md: 61%,
May 2026);

(b) such capability creates risk of consumer deception and professional harm
while offering legitimate creative and commercial applications;

(c) the broadcasting and audio advertising industries require a **voluntary**
standard distinguishing human-voiced content from synthetic content without
impeding progress;

(d) this standard is professional self-regulation, not statutory regulation.

**DEFINITIONS** (abridged):

- "Certificate" — Living Voice Certificate under Article 4.
- "Living Voice" — a natural person's voice recorded with direct participation,
  without synthetic generation, material modification, or substitution.
- "Material Modification" — alteration via pitch-shifting, voice conversion,
  neural style transfer or analogous technology changing perceived identity.
- "Synthetic Voice" — audio produced wholly or partly by TTS, voice cloning,
  generative audio models, or analogous techniques.
- "Hash Chain" — sequence of cryptographic digests linking audio files from
  recording to publication, each incorporating its predecessor's digest.

**VERIFICATION TIERS** — as Article 3: I Declaration; II Session Control;
III Hash Chain (tamper-evident provenance).

**CERTIFICATE** must contain: artist name, tier, material identifier,
verification date, digest (II/III), unique number, expiry (12 months).

**PUBLIC REGISTER** — number, name (consent), tier, date, status, updated ≥ 1/7d.

**DISPUTES** — mediation by the verifier; on failure a reasoned public decision;
further review panel of three active Tier II+ certificate holders.

**RELATION TO SYNTHETIC VOICE** — no prohibition with clear labelling; directed
solely at misrepresentation; establishes only a standard of honesty, no value
hierarchy between human and synthetic voice.

---

## Форма Декларации (приложение, самостоятельный бланк)

> **ДЕКЛАРАЦИЯ ЖИВОГО ГОЛОСА** (шаблон на сайте студии):
> «Я, … (ФИО), подтверждаю, что голос в аудиозаписи «…» (идентификатор),
> дата записи … , является моим собственным живым голосом, записанным при
> моём непосредственном участии. Я не использовал синтетическую генерацию,
> существенную модификацию или замену голоса. Я ознакомлен с Манифестом
> „Живой Голос“ и принимаю его условия. Я осведомлён об ответственности,
> включая публичное объявление о лишении знака.» (дата, подпись)

---

## Related

- ../canon/right-to-be-present.md — why honesty is infrastructure of trust.
- ../canon/voice-provenance.md — releasing voice / provenance as product.
- ../standards/verification-chain.md — level III build-out.

CARRIER

AUDIO-REKLAMA.RU / STANDARDS / LIVING-VOICE-STANDARD / V1.0 / 10.09.2026