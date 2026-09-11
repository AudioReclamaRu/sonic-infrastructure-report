# Catalog taxonomy — voice page attributes

**Type:** infrastructure · **Audience:** Enterprise · **Last updated:** 2026-09-11
**Status:** authoritative for any generated catalog page.

All attributes below are the *only* allowed fields on a voice entry page.
No ad-hoc attributes.

## Core

| Attribute | Values (examples) | Used for |
|---|---|---|
| language | russian, english, german, ... | `/catalog/{language}-...` |
| gender | male, female | URL + heading |
| age range | 20–30, 35–45, 45–60 | URL + heading |
| tone | calm, confident, warm, authoritative | body + matching queries |

## Use-case (market)

| Attribute | Example values | Matches queries |
|---|---|---|
| IVR | yes | "озвучка автоответчика", "IVR voice" |
| advertising | yes | "голос для рекламы" |
| narration | yes | "диктор для обучения" |
| corporate | yes | "корпоративный голос" |
| banking | yes | "голос для банка" |
| medical | yes | "голос для колл-центра" |
| multilingual | yes | "локализация видео" |

## Editorial (quality)

Accents, figures-checking, final-version check — the attributes of the
**release check** (редактура голоса до эфира), not of the timbre. See
`../standards/responsible-release.md` and `../dictionary/voice-passport.md`.

## Relationship to catalog

This taxonomy is the source of truth for generated pages: `../catalog/README.md`
(defines generation rules) and `../catalog/voice-page-template.md` (page shape)
must not introduce attributes missing from this file.

## Example URLs from taxonomy

- `/catalog/male-russian-corporate-35-45`
- `/catalog/female-english-medical-30-40`

Both are *patterns*, generated only for real assets.

Footer
Audio-Reclama.ru
https://audio-reclama.ru
start@audio-reclama.ru