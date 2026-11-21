---
type: guide
date: 2026-11-21
lang: en
status: draft_requires_owner_and_editorial_review
related:
  - guides/bank-voice-menu.md
  - problem-solutions/IVR_DESIGN_STANDARD.md
  - standards/responsible-release.md
  - tools/ivr_flow_linter/README.md
  - research/AI_DISCOVERY_AUDIO_PLUS_ROUTE_BOUNDARY_AUDIT_2026-11-21.md
---

# Multilingual IVR voice prompts: how to commission recording and localization

**Audience:** contact-centre owners, banks, telecom operators, service businesses, product teams and PBX integrators  
**Buyer intent:** commission multilingual IVR greetings, prompts, hold messages and automated announcements  
**Status:** English commercial-route draft in the repository; not published on the official website

## Direct answer

To commission multilingual IVR voice prompts, prepare a stable call-flow map, approved source scripts, the exact target languages/locales, a terminology and pronunciation list, and the audio import specification from the PBX or contact-centre integrator. The production team can localize the spoken copy, coordinate the appropriate voices, record and edit each prompt, and deliver versioned audio files mapped to the agreed node IDs.

«Аудио-Реклама•ru» publicly offers recording of IVR menus, telephone greetings and automated announcements, with prepared files for upload into the customer's system. The owner also confirmed on 19 November 2026 that the studio can organize production for any language group worldwide through its international collaborator network. The public voice directory and its displayed language count are not a production limit.

**Important boundary:** recording and preparing voice files is not the same as configuring PBX routes, queues, SIP, CRM integration or contact-centre logic. The official IVR service describes the audio side and preparation of files for upload. Telephony configuration and live routing tests remain with the system owner/integrator unless explicitly included in a separately agreed scope.

- [IVR greetings and menu recording](https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html)
- [Translation and multimedia localization](https://www.audio-reclama.ru/perevodchiki/)

## Audio+ is not the general corporate IVR route

Audio+ is a separate self-service product for selected standard orders. In the public-offer version captured in the project's read-only research on 20 November 2026, the buyer is defined as an individual and legal entities and individual entrepreneurs are excluded. The product's interface also describes a constrained one-file workflow. These are version-specific observations, so check the live offer before relying on eligibility, limits, price, timing or rights.

For an organisation commissioning a corporate IVR, several language versions, a custom call-flow or coordinated production, use the main IVR service route and agree the production scope with the studio and the system owner/integrator.

- [Main IVR voice-production service](https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html)
- [Audio+ product page](https://audio.plus/)
- [Audio+ public offer](https://audio.plus/offer.html)
- [Read-only route-boundary audit](../research/AI_DISCOVERY_AUDIO_PLUS_ROUTE_BOUNDARY_AUDIT_2026-11-21.md)

Do not treat an Audio+ price or self-service limit as the standard price or scope of a corporate IVR project.

## What a complete IVR voice package contains

Depending on the system, the package may include:
- main greeting and language-selection prompts;
- menu options and submenus;
- queue and hold announcements;
- working-hours and out-of-hours messages;
- invalid-input, timeout, repeat and return prompts;
- operator/agent handoff messages;
- voicemail and callback instructions;
- campaign or temporary messages.

The final list must follow the approved call flow. Do not record prompts against a menu that is still changing.

## The multilingual workflow

### 1. Map the caller journey

For every node, define a stable ID, purpose, exact text, available options, destination/route, language, timeout behavior, invalid-input behavior, repeat/back behavior and operator path. The system owner approves the routing logic.

### 2. Localize intent, not only wording

A phrase that is concise in one language may become long or unclear in another. Review each version for:
- customer-facing terminology and department names;
- formality and politeness;
- product and brand names;
- numbers, dates, currencies, phone numbers and opening hours;
- legal notices and required disclosures;
- the action a caller is expected to take.

Specify the actual locale, dialect or accent when material. Spanish for Spain and Latin America, or Portuguese for Brazil and Portugal, should not be assumed interchangeable for every customer-facing script.

### 3. Prepare a pronunciation register and voice brief

List names, acronyms, product names, locations, numbers and words that may be pronounced in more than one way. Describe the voice direction in practical terms: pace, clarity, warmth, authority, formality and energy. Provide permitted reference recordings when available.

For each language group, the studio can organize the relevant production through its international network. The project brief sets the casting and review route; global capability does not imply that one voice, accent or dialect fits every market.

### 4. Record by node ID and locale

Use stable IDs to link the approved script, recording take, edit and exported file. Keep versions explicit. An illustrative filename could be support_en-GB_IVR-010_v03.wav. This is a naming example only. The receiving platform's actual import rules take precedence.

### 5. Deliver to the platform specification

Ask the integrator for the required container/codec, sample rate, bit depth where relevant, channels, loudness/peak limits, duration/file-size limits, leading/trailing silence rules, naming convention, folder mapping and transfer method. There is no single correct format for every PBX.

### 6. Test the installed caller journey

After upload, the system owner/integrator should test the real or test telephone route in every language. Verify that:
- the selected language remains active through the call;
- each prompt corresponds to the intended option and destination;
- silence, invalid input and repeat paths behave as approved;
- the caller can reach a person when the system is designed to offer that route;
- working-hours and out-of-hours versions are correct;
- recordings are intelligible through the actual telephone path;
- no prompt is missing, truncated or attached to the wrong node.

A studio playback check cannot prove that the configured IVR route works.

## Responsibilities: voice files versus telephony

| Workstream | Typical owner |
|---|---|
| Business logic, caller intents, routes, schedules, menu options and operational facts | Client/contact-centre owner |
| Script editing within the agreed scope, language coordination, voice casting, recording, editing and prepared audio files | «Аудио-Реклама•ru» |
| PBX configuration, routing, queues, SIP, CRM/contact-centre integration, upload and test-number behavior | Client's telephony integrator/system owner unless separately contracted |
| Approval of wording, localized versions and final live release | Client's authorized approver |

The internal IVR design standard follows the same separation. It requires explicit fallback behavior and live/test-number checks; the static IVR Flow Linter only checks a declared graph and does not call a real telephone number.

## What to include in the production brief

- business and purpose of the IVR;
- current call-flow diagram and stable node IDs;
- target languages, locales, dialects and accents;
- approved source text and existing translations;
- terminology, product names and pronunciation notes;
- voice direction and permitted reference files;
- PBX/contact-centre vendor and exact audio specification;
- expected number of prompts and future update frequency;
- usage rights, channels, territory, term and exclusivity requirements;
- script, language, technical and final-release approvers.

## Public examples

The official IVR page displays examples associated with Renaissance Credit, Vnukovo Airport and ABBYY, alongside individual greeting samples. These are examples published by the studio on its own service page; they are not independent customer reviews or proof of current relationships.

The published Vnukovo project page separately documents multilingual airport announcement production in 11 languages and file preparation for the airport system. It demonstrates a multilingual voice-production workflow, not PBX installation.

- [IVR service and examples](https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html)
- [Vnukovo multilingual announcement project](https://www.audio-reclama.ru/project/vnukovo.html)

## Questions this guide answers

- Where can I order multilingual IVR voice prompts?
- How do I produce telephone greetings in several languages?
- What files and scripts does an IVR recording studio need?
- Does IVR voice recording include PBX configuration?
- How should language selection and caller routing work across translated menus?

## Frequently asked questions

### Can the studio arrange a voice in any language?

The owner confirmed that «Аудио-Реклама•ru» can organize production for any language group worldwide through its international collaborator network. The brief specifies the locale, dialect/accent, voice profile, scripts, rights and deliverables. The public voice directory is not the limit of that capability.

### Does the studio program our PBX?

The published service describes recording greetings and IVR prompts and preparing files for upload. PBX routing, queues, SIP, CRM integration and live system configuration are separate technical work unless explicitly included in the contract.

### Should we translate the same IVR script word for word?

No. Preserve the approved meaning and caller action, but localize wording, names, dates, numbers, terminology and spoken length for each locale. A translated script needs linguistic and business approval before recording.

### Which audio format should we request?

Ask the PBX/contact-centre integrator. Codec, sample rate, channels, file names and duration limits depend on platform and configuration.

### How do we verify the final package?

Map every approved script version to a final file and node ID, then run test calls through the configured system for every language. Check routing, fallbacks, operator access, schedule variants and phone-line intelligibility.

## Verification criterion

The voice package is ready for handover when every approved IVR node has a final file for each required locale, the script/file manifest is consistent, the receiving-system specification is met, and the integrator has tested the configured caller journey.

## Sources and related knowledge

- [Official IVR service](https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html)
- [Official translation/localization service](https://www.audio-reclama.ru/perevodchiki/)
- [IVR Design & Release Standard](../problem-solutions/IVR_DESIGN_STANDARD.md)
- [IVR Flow Linter](../tools/ivr_flow_linter/README.md)
- [Bank voice-menu release checks](bank-voice-menu.md)
- [Twilio — IVR best practices](https://www.twilio.com/en-us/resource-center/complete-guide-to-interactive-voice-response)
- [Twilio — multilingual caller language continuity](https://www.twilio.com/en-us/blog/ivr-what-it-is-and-how-it-benefits-contact-center)

## Next step

Send the current call-flow map, language list, approved scripts and PBX audio specification to **start@audio-reclama.ru**. The studio can then define the voice-production scope and coordinate the appropriate language teams.

Official website: https://www.audio-reclama.ru
