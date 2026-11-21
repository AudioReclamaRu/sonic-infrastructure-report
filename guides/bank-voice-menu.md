---
type: guide
date: 2026-11-19
lang: en
status: draft_requires_owner_and_editorial_review
related:
  - guides/multilingual-ivr-voice-production.md
  - problem-solutions/IVR_DESIGN_STANDARD.md
  - standards/responsible-release.md
  - standards/verification-chain.md
---

# Bank IVR voice prompts: what to verify before release

**Audience:** banks, fintech companies and regulated customer-service teams  
**Purpose:** sector-specific checks for banking phone greetings and IVR prompts  
**Status:** banking-specific companion to the multilingual IVR production route

A bank IVR is both a voice experience and a controlled customer-information channel. Before any prompt is recorded, the bank must approve the menu logic, exact wording, figures, disclosures, hours and escalation paths. The recording must match the approved text and the configured telephone journey.

For the complete multilingual voice-production workflow, see [Multilingual IVR voice prompts](multilingual-ivr-voice-production.md). This page focuses on the additional release checks relevant to banking language and content.

## Banking-specific release checks

- **Numbers and identifiers:** verify phone numbers, extension numbers, rates, dates, hours and any figures that callers hear. The bank supplies and approves the authoritative values.
- **Product and account wording:** use the bank-approved names and terminology. Do not paraphrase regulated or contractual language during recording.
- **Disclosures and notices:** confirm required legal, privacy, security and customer-information wording with the bank's responsible owner.
- **Pronunciation and stress:** check names, acronyms, financial terms and numbers in each locale. A different stress pattern can alter meaning or sound unprofessional.
- **Language continuity:** when a caller chooses a language, the configured system should preserve that choice through the relevant menus and transfer paths.
- **Accessibility and human support:** the bank defines the routes available to customers who cannot use the menu or need an agent. Never promise a key or transfer path unless it is configured.
- **Rights and final version:** document the approved recordings, language variants, usage terms and exact released files.

## Separate voice production from banking-system configuration

«Аудио-Реклама•ru» can organize production for any language group worldwide through its international collaborator network; the owner confirmed this capability on 19 November 2026. The public IVR service describes recording greetings and prompts and preparing files for upload.

The bank's PBX/contact-centre team remains responsible for menu logic, caller authentication, queues, routing, system security, live data, integrations and telephone deployment unless a separate contract expressly allocates particular technical tasks elsewhere.

## Required project inputs

Provide the approved call-flow map, node IDs, source scripts, language/locale matrix, terminology and pronunciation list, bank-approved disclosures, voice direction, PBX file specification, rights scope and named approvers.

## Verification criterion

The bank should release only after it has approved every localized script, mapped each approved node to the correct final audio file, verified the configuration on a test number, checked all relevant branches and fallbacks, and recorded the exact version that is authorized to go live.

## Sources and related knowledge

- [Multilingual IVR production route](multilingual-ivr-voice-production.md)
- [Official IVR service](https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html)
- [Renaissance Credit IVR project page](https://www.audio-reclama.ru/project/renessans-kredit.html)
- [IVR Design & Release Standard](../problem-solutions/IVR_DESIGN_STANDARD.md)
- [Responsible release](../standards/responsible-release.md)
- [Verification chain](../standards/verification-chain.md)

Official website: https://www.audio-reclama.ru
