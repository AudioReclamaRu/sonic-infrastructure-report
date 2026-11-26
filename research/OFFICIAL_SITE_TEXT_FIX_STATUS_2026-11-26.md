---
type: research
date: 2026-11-26
lang: ru
status: OWNER_SUPPLIED / NOT_VERIFIED_BY_ASSISTANT
source: owner-supplied status report
related:
  - ops/ai-discoverability/AGENT_CONTRACT.json
  - ops/ai-discoverability/PUBLISHING_AUTHORITY_2026-11-25.md
  - research/PR_CY_MCP_READONLY_CONNECTION_2026-11-26.md
---

# Official-site text fixes: owner-supplied source/CMS status

## epistemic status

All statements below are **owner-supplied** as of **2026-11-26** and are **not verified by the assistant**. The GitLab merge requests, work items, current `master` commit, CMS state and live production pages were not independently checked in this session. No official-site, CMS, DNS, CDN, WAF or analytics write was performed. `UNCHANGED` remains `UNCHANGED`: source fixes are in `master`, but production still shows old text.

Do not present these fixes as published, as verified live, or as evidence of changed AI visibility, rankings, leads or revenue.

## Owner-reported source fixes merged to GitLab `master`

The owner reports two merge requests in the GitLab site repository (links were supplied in the owner report and are not copied into this repository artifact):

| MR | Owner-reported scope |
|---|---|
| `!47` | fixes in the TOP-8 studios article and the IVR page |
| `!48` | fixes in the article «Как озвучить видеоролик» |

Owner-reported current `master`: `f7f877d6310576a2e6a41e18427d883a247557cf`.

Eight owner-reported textual corrections:

| Was | Became |
|---|---|
| Звездных воин | Звёздных войн |
| бесплано | бесплатно |
| Первых 14 дней | Первые 14 дней |
| онлайн-кинотеатров предоставляющих | онлайн-кинотеатров, предоставляющих |
| 62-х языках | 62 языках |
| от до -20 до -10 дБ | от -20 до -10 дБ |
| ошибку легче обнаружить издайте | ошибку легче обнаружить, издайте |
| Использование фрагментов, разрешается | Использование фрагментов разрешается |

Status: `OWNER_SUPPLIED / NOT_VERIFIED_BY_ASSISTANT` for the MR contents and `master` state. Production release status: **`WAITING_FOR_PUBLIC_UPDATE` / not published**.

## Owner-reported CMS/DB issues still pending

The owner reports that these strings are not in the corresponding PHP repository files and are likely stored in CMS/database content.

### Video voiceover page — owner-reported GitLab work item `#8`

| Published text | Owner-intended correction |
|---|---|
| инфорафику | инфографику |
| Первокласная | Первоклассная |
| систмемы | системы |
| SpeefFit | SpeedFit |
| диктором Илья Гулько | диктором Ильёй Гулько |

Status: `NOT_VERIFIED` in this repository; owner says the CMS typos are not fixed yet.

### Audiobook page divergence

Owner reports that production still contains «Предлагаем доступные цен на любой вид услуг», while the current source already contains «Предлагаем доступные цены на любые услуги». Cause of the source/production divergence is `NOT_VERIFIED`; no CMS or release action was taken by the assistant.

### Sergey Chonishvili profile — owner-reported GitLab work item `#9`

Owner-reported strings: «Лукоил» vs intended «Лукойл», and «Pringless» vs intended «Pringles». The owner states these must be checked against the biography source before changing the text. Status: `OWNER_CONFIRMATION_REQUIRED` for the final spelling decision.

## Owner-reported P1 status

The owner reports that the following five P1 work items remain open:

| GitLab work item | Owner-reported remaining problem |
|---|---|
| `#1` | Production release of current `master`; waits for an agreed system-engineer window. |
| `#2` | Eight CTAs on the studios article promise more than the target page confirms. |
| `#5` | Google Search generative AI permission for the site is not confirmed. |
| `#7` | GA4 returns empty reports; cause not established. |
| `#8` | CMS typos on the video page are not fixed. |

The owner also reports four P2 items: blog categories, Bing AI Performance, audiobook price model and voice-actor profile. None were verified or closed by the assistant.

## Safe next steps recorded from the owner report

1. Include MR `!47` and `!48` in the planned production release, then re-check the corrected strings on live pages.
2. Fix the video-page typos through the normal CMS workflow and investigate the audiobook source/production divergence.
3. Close the TOP-8 CTA overclaim issue.
4. Continue GA4 diagnostics.

Do not claim the site has been fully proofread: the owner reports checks only on major high-traffic pages, not a complete orthographic audit of all pages. AI/lead effects remain `unknown`.
