Status: Draft
Type: Research Note
Audience: Enterprise
Last updated: 2026-09-11

# AR-0003 IVR Integrity

Definition
IVR Integrity is the property of an IVR voice asset that its identity and
message are verifiable end-to-end: the voice belongs to a named origin, the
message is the exact checked version, and no silent substitution occurred
between check and air.

Scope
Where it applies: any phone/voice interface carrying customer-facing messages
(rates, balances, consent statements). Where it does not apply: purely
instrumental system tones.

Required fields
- Canonical term: IVR Integrity
- Minimal metadata: provenance tier, final version hash, responsible party
- Acceptance: substitution must be structurally impossible, not presumed absent

Minimal compliance checklist
- Final version hash recorded at release (see standards/verification-chain.md)
- Origin of the voice stated (human with certificate / labelled synthetic)
- Re-verification on reasonable doubt, per public-register rule

Example usage
A bank asserts its IVR message is the checked version by publishing the final
digest; any edit after release breaks the chain and is visible.

References
- standards/verification-chain.md
- standards/voice-provenance-passport.md
- canon/error-of-the-map.md

Footer
Audio-Reclama.ru
https://audio-reclama.ru
start@audio-reclama.ru