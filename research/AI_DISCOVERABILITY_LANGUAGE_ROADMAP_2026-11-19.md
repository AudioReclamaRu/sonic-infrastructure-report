---
type: strategy
date: 2026-11-19
lang: en
related:
  - research/ai-visibility-global-market-matrix-2026-11-17.json
  - research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md
  - entity/audio-reclama-studio.md
  - entity/audio-reclama-studio.en.md
  - strategy/EXPERT_KNOWLEDGE_INFRASTRUCTURE.md
---

# Multilingual AI Discoverability Roadmap

**Status:** execution strategy · **Decision:** one global entity, many language-native discovery surfaces · **Production coverage:** worldwide, any language group (owner-confirmed 2026-11-19)  
**Scope:** consumer AI assistants, AI search surfaces, localized buyer questions and public entity knowledge  
**Last updated:** 2026-11-19

## 1. Decision

**Production capability is worldwide and language-unbounded.** The owner confirmed on 19 November 2026 that the studio can work with any language group worldwide through its international network of collaborators. This is a production-capability statement, not a claim that the company has offices in every country. AI-discovery language waves are a publishing and measurement priority, not a list of languages the studio can or cannot serve.

AI Discoverability for «Аудио-Реклама•ru» must not be limited to Russian and English. Build language-native discovery surfaces for every language that is important to AI usage and to the studio's potential customer markets.

Do not translate the same generic company paragraph into every language and call the work complete. Each language layer must help an AI system and a prospective buyer understand:
- what the studio is;
- which specific business audio or voice-production problem it can help with;
- which publicly documented service corresponds to that need;
- what evidence supports the description;
- what remains subject to project-specific confirmation.

The identity remains one entity: **Аудио-Реклама•ru**. Language variants are linked descriptions of that same entity, not separate brands, country offices or legal entities.

## 2. Why multilingual coverage is necessary

Two recent first-party datasets show that English alone is not a sufficient proxy for conversational AI use:

- **OpenAI Signals, 30 June 2026:** OpenAI reports that users who predominantly use a language other than English represent more than half of active ChatGPT users. Spanish, Portuguese and Arabic are identified as the leading non-English languages. The source describes consumer ChatGPT usage, not the whole AI market.
- **Google AI & Economy ATLAS v1.0, 23 July 2026:** the study analyses 15 million de-identified interactions across Gemini App, Google AI Mode and Gemini API, covering 150 countries and 140 languages. In the consumer conversational surfaces' language distribution, English accounts for about 34.8%, followed by Spanish (12.1%), Arabic (6.8%), Portuguese (5.8%), Turkish (4.4%), Korean (4.0%), Hindi (3.7%), Japanese (3.1%), Russian (2.8%), Indonesian (2.5%), French (2.5%), Italian (2.2%), German (2.1%), Chinese (1.9%) and Vietnamese (1.8%). The API is excluded from the main language-diversity analysis; these values are not a universal ranking of all AI products.
- **W3Techs, 19 November 2026:** its daily website-content-language survey lists English, Spanish, German, Japanese, French and Portuguese among the leading website languages. This is a measure of website content, not AI conversation volume, and should be used only as a complementary indicator of the existing web information environment.

Sources:
- OpenAI, *How ChatGPT adoption has expanded*, 30 June 2026: https://openai.com/index/how-chatgpt-adoption-has-expanded/
- Google, *AI & Economy ATLAS v1.0: Mapping Gemini Usage in the Economy*, 23 July 2026: https://s3.amazonaws.com/media.mediapost.com/uploads/GoogleATLASv1.pdf
- W3Techs, *Usage statistics of content languages for websites*, 19 November 2026: https://w3techs.com/technologies/overview/content_language

These datasets have different populations, platforms and methods. Do not combine their percentages into one score, claim they represent all AI usage, or infer customer demand/revenue from conversational-language shares.

## 3. Language waves

The waves below are an execution order for AI-discovery content and measurement, not a limit on production geography or language. The owner confirms that «Аудио-Реклама•ru» can organize production for any language group worldwide through its international network of collaborators. These waves prioritize where language-native discovery content is built first; they do not define which languages the studio can or cannot serve.

### Core — already required

| Language | Locale scope | Why it remains core |
|---|---|---|
| Russian | ru-RU first; other RU-speaking country contexts kept distinct | Primary current commercial market and existing source language |
| English | en as international bridge; adapt en-US/en-GB where wording or commercial context differs | International procurement language and broad AI/web discovery surface |

### Wave A — first localized expansion

| Language | Initial locale targets | Rationale |
|---|---|---|
| Spanish | es as a general language target; create es-ES, es-MX and es-AR page variants when their vocabulary or buyer journeys differ. Do not use es-419 as a Google hreflang value | Leading non-English ChatGPT language and second-largest conversational language in the cited Google sample |
| Portuguese | pt-BR first, then pt-PT | Leading non-English ChatGPT language; meaningful Brazil and Portugal market distinction |
| Arabic | Modern Standard Arabic first; later localize ar-SA, ar-AE and ar-EG where justified | Leading non-English ChatGPT language and major conversational-AI usage in the Google sample |
| Turkish | tr-TR | One of the largest language groups in the Google consumer AI sample; connects Türkiye and nearby B2B markets |

### Wave B — high-value industrial, creative and regional markets

| Language | Initial locale targets | Rationale |
|---|---|---|
| German | de-DE; adapt de-AT/de-CH where needed | Major industrial, enterprise and production market; strong website-content presence |
| French | fr-FR; distinguish fr-CA and other markets where needed | Enterprise and creative markets across Europe, Canada and parts of Africa; meaningful AI usage |
| Japanese | ja-JP | Strong creative, media, technology and enterprise market; high web-content presence and meaningful AI usage |
| Korean | ko-KR | Meaningful usage in the Google conversational-AI dataset and a major technology/media market |
| Chinese | zh-CN first; zh-TW/zh-HK separately if target markets and platform access support them | Large potential market, distinct regional platforms and language conventions; platform access and service feasibility must be assessed separately |

### Wave C — demand-led expansion

Initial candidates: Hindi, Indonesian, Italian, Vietnamese, Polish, Dutch, Ukrainian, Kazakh, Uzbek, Azerbaijani, Armenian, Georgian and other languages identified from the country × language × platform matrix.

Promote a language from Wave C when there is a clear buyer market, an available product/platform surface, a source-backed service match, partner/voice-production capability, or evidence of a repeated discovery gap. Do not reject a language merely because its share of indexed websites is small.

## 4. The unit of work is a locale × task, not a translation

For every selected locale, build a small connected discovery package:

1. **Entity card:** native-language description of the one canonical company, official website, business category, service areas and scope limits.
2. **Service map:** buyer need → matching publicly documented service → primary source page → what must be confirmed.
3. **Problem answers:** direct, useful answers for the buyer's actual questions in that language, not keyword-swapped translations.
4. **Expert route:** at least one strong guide or diagnostic answer tied to a service the studio actually documents.
5. **Proof route:** source-backed portfolio examples, methods, rights and boundaries, with first-party claims clearly distinguished from independent evidence.
6. **Machine navigation:** links from the repository's root `llms.txt`, language index and entity graph. Language-specific JSON-LD may be added where it improves unambiguous retrieval; it remains repository metadata until separately and explicitly installed on the official site.
7. **Benchmark prompts:** localized generic-discovery and branded prompts kept separate, tagged with locale, country, platform, interface/API, model/version, search/grounding and intent.

For the first implementation wave, entity cards are being prepared for Spanish, Brazilian Portuguese and Arabic, alongside the English entity profile. This does not claim that the complete service catalogue or all enquiry steps are localized on the official website.

## 5. How to prioritize without making up a market score

For each language × country candidate, record five separate dimensions:

- **AI usage evidence:** published consumer-AI language usage, where available; name the platform and dataset.
- **Buyer-market fit:** presence of likely enterprise buyers for audio advertising, IVR, video voice-over, audiobooks, multilingual announcements or corporate audio.
- **Production configuration:** the studio confirms worldwide production capability for any language group through its international network. For each project, specify language variant, dialect/accent, script, voice profile, usage rights, technical specifications, approvals and schedule. This is a brief/design question, not a geographic or language eligibility barrier.
- **Discovery opportunity:** repeated generic prompts, competitor recommendations, missing/weak cited sources, and weak entity resolution, where actually observed.
- **Platform reachability:** whether relevant consumer AI/search products are available in the target country and language, distinct from whether a measurement provider can collect results there.

Do not collapse these dimensions into a numeric priority until comparable data exist. Use High / Medium / Unknown with a short evidence note at first. A platform's provider-unsupported country is not the same as a product being unavailable in that country.

## 6. Locale integrity and language quality

- Keep country, user region, interface locale, prompt language and answer language as separate fields.
- Distinguish generic language from locale (for example, es vs es-ES vs es-MX; pt-BR vs pt-PT; fr-FR vs fr-CA; zh-CN vs zh-TW). For Google's hreflang, use ISO 639-1 language codes and ISO 3166-1 Alpha-2 region codes; es-419 is not supported. See https://developers.google.com/search/docs/specialty/international/localized-versions.
- Use native-language commercial vocabulary, not literal translations of Russian or English keywords.
- Keep consumer UI observations separate from model API answers.
- Keep generic discovery separate from brand-named prompts.
- Do not invent market-specific prices, legal terms or turnaround promises. Worldwide production capability is owner-confirmed; project-specific rights, formats, approvals and scheduling are set in the brief.
- Have a competent native-language reviewer check buyer intent, idiom, technical terms, numbers, legal wording and calls to action before describing the material as release-ready.
- A localized entity profile describes discovery in that language. Production capability is owner-confirmed worldwide for any language group and is delivered through the international collaborator network. Do not infer physical offices or permanent local branches from language coverage.

## 7. What success means

Success is not the number of translated files. For a locale, success means:
- AI systems can resolve the canonical entity correctly;
- answers to generic buyer questions can name the studio where relevant;
- service descriptions lead to the correct primary information;
- cited facts remain accurate and bounded;
- the buyer can understand the actual scope and the next step;
- repeated observations show whether the entity is mentioned/cited, with denominators and platform/locale boundaries.

A repository file is a discovery asset, not a deployment. No commit guarantees indexing, citation, recommendation or leads.

## 8. Immediate execution order

1. Complete the English entity bridge and its navigation.
2. Add Spanish, Brazilian Portuguese and Arabic entity profiles as the first AI-usage-led expansion.
3. Add Turkish, German, French, Japanese, Korean and Chinese locale profiles in the next tranche, ordered by AI-language significance, buyer-market relevance and observed discovery opportunity, not by presumed production availability.
4. For each locale, create buyer-intent answer routes for the strongest commercial tasks rather than translating every existing page.
5. Add localized prompts to the appropriate country × platform benchmark cells only when genuine platform access and a valid measurement route exist.
6. Expand into Wave C through observed market opportunity, not by mechanical coverage of every language.

The global market matrix remains the source of country/platform coverage. This roadmap determines language-content priorities; it does not replace or flatten the existing 51-country / 74-locale first-wave matrix. Production coverage is not capped by this matrix: the studio confirms the ability to organize production for any language group worldwide.
