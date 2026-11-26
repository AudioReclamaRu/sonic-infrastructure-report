---
type: research
date: 2026-11-26
lang: ru
status: OWNER_CONFIRMATION_REQUIRED / OWNER_SUPPLIED / NOT_VERIFIED_BY_ASSISTANT
source: owner-supplied status report and later owner re-check (conflicting merge accounts)
related:
  - ops/ai-discoverability/AGENT_CONTRACT.json
  - ops/ai-discoverability/PUBLISHING_AUTHORITY_2026-11-25.md
  - research/PR_CY_MCP_READONLY_CONNECTION_2026-11-26.md
---

# Official-site text fixes: owner-supplied source/CMS status

## epistemic status

All statements below are **owner-supplied** as of **2026-11-26** and are **not verified by the assistant**. The GitLab merge requests, work items, current `master` commit, CMS state and live production pages were not independently checked in this session. No official-site, CMS, DNS, CDN, WAF or analytics write was performed. `UNCHANGED` remains `UNCHANGED`.

The owner later re-checked the GitLab side and stated that **all listed changes remain in branches under review, no MR is merged or published, and there is no pipeline or live-site check yet**. That contradicts the earlier owner statement that MR `!47` and `!48` were merged into `master`. Both accounts are preserved below; the merge state is `OWNER_CONFIRMATION_REQUIRED`, not `VERIFIED`.

Do not present any fix as merged, published, verified live, or as evidence of changed AI visibility, rankings, leads or revenue.

## Earlier owner report: fixes claimed merged to GitLab `master` (disputed by later re-check)

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

Status of this earlier account: `OWNER_SUPPLIED / NOT_VERIFIED_BY_ASSISTANT`. It is **disputed** by the later owner re-check recorded below; do not treat `!47`/`!48` as merged or `f7f877d6310576a2e6a41e18427d883a247557cf` as the confirmed current `master`. Production release status: **`WAITING_FOR_PUBLIC_UPDATE` / not published** in both accounts.

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

1. Resolve the conflicting owner accounts of the GitLab merge state before any release planning.
2. Only after a confirmed merge and release, re-check the corrected strings on live pages.
3. Fix the video-page typos through the normal CMS workflow and investigate the audiobook source/production divergence.
4. Close the TOP-8 CTA overclaim issue and continue GA4 diagnostics.

Do not claim the site has been fully proofread: the owner reports checks only on major high-traffic pages, not a complete orthographic audit of all pages. AI/lead effects remain `unknown`.

## Later owner re-check (2026-11-26, addendum)

The owner subsequently re-checked the GitLab side and reported: **all listed changes remain in branches under review; no MR is merged or published; pipeline and a check on the working site are still absent.** No assistant verification of the branches was performed.

- Status: `OWNER_CONFIRMATION_REQUIRED / OWNER_SUPPLIED / NOT_VERIFIED_BY_ASSISTANT` for the merge/publication state.
- This contradicts the earlier owner statement that MR `!47` and `!48` were merged into `master`. Both accounts are preserved above; neither is independently verified.
- Working state to use until clarified: **nothing treated as merged, nothing published, `UNCHANGED` on production**, pipeline and live-site check absent.
- Additional owner-supplied SEO proposals: metadata for cartoon voiceover in MR `!71` and a service description in JSON-LD in MR `!68`. Both remain branch proposals, **not published to production**. Their contents were not checked here.
- No CMS, release, pipeline or website action was taken by the assistant. Pipeline absence and live-site absence are owner-reported, not assistant-measured.
