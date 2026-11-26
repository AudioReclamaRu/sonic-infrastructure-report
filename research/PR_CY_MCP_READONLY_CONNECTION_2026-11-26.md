---
type: research
date: 2026-11-26
lang: ru
status: VERIFIED
source: PR-CY MCP
related:
  - ops/ai-discoverability/AGENT_CONTRACT.json
  - ops/ai-discoverability/PUBLISHING_AUTHORITY_2026-11-25.md
---

# PR-CY MCP: read-only connection and first data snapshot

## Scope and result

A permanent, read-only PR-CY MCP connection is configured for the OpenCode user scope and verified after a background-service restart. The first data snapshot was obtained through MCP tools only. No site, CMS, analytics, DNS, CDN or WAF write was performed; no form, paid check, AI prompt, catalog profile or external message was submitted.

Status: `VERIFIED` for the connection, configuration, tool availability and the reported dataset values. AI/lead effects remain `unknown`; this is traffic and search-report data, not AI citation or answer share.

## Connection evidence

| Item | Result | Status |
|---|---|---|
| `opencode mcp list` after service restart | `✓ pr-cy connected`; `✓ prime-lad-mesh connected` | `VERIFIED` |
| PR-CY endpoint | `https://mcp-server.pr-cy.ru`, remote Streamable HTTP | `VERIFIED` |
| Authorization | Header uses `{env:PRCY_API_KEY}`; no literal key in config, project files, Git, logs or this report | `VERIFIED` |
| Global config | `F:\Pill\tmp\opencode\xdg\config\opencode\opencode.jsonc`; existing `prime-lad-mesh` preserved; no duplicate `pr-cy` | `VERIFIED` |
| Global instruction | `F:\Pill\tmp\opencode\xdg\config\opencode\AGENTS.md`; loaded into a session started outside `E:\ASTRAEA_V10` | `VERIFIED` |
| Tool catalog after restart | PR-CY tools available again in the same session | `VERIFIED` |
| Mutating/limit-consuming tools | Not called | `VERIFIED` |

The separate `opencode run` check from another directory was not used as evidence because the OpenCode provider token is expired. That failure is unrelated to PR-CY MCP and did not change the PR-CY connection. The global instruction was independently confirmed by the harness instruction update.

## Retrieval conventions

All values below were retrieved on **2026-11-26** from **PR-CY MCP**. Engines, regions, devices and reporting sources are kept separate. Empty result arrays are recorded as `NOT_VERIFIED` / no stored data in the queried view, never as zero.

## Project and limits

Retrieved: 2026-11-26; source: PR-CY MCP; reporting period: current account state at retrieval.

| Field | Value |
|---|---|
| Project id | `162079` |
| Domain | `www.audio-reclama.ru` |
| Status | `active` |
| Created | `2026-11-01 12:49:48` |
| Keywords initialized | `false` |
| GA / GSC / Metrica connected | `true` / `true` / `true` |
| Yandex Webmaster connected | `false` |
| Base analytics system | `metrika` |
| Wordstat type | `general` |
| Advanced auto update / crawler auto update / weekly report | `true` / `true` / `true` |

Limits snapshot (same source and retrieval date):

| Limit | Available | Used | Period |
|---|---:|---:|---|
| `checks` | 10 | 0 | day |
| `forceCrawlerUpdates` | 0 | 0 | day |
| `pdfReports` | 0 | 0 | day |
| `projects` | 1 | 1 | none |
| `projectsDaily` | 1 | 0 | day |
| `standardAnalysis` | 100 | 0 | day |
| `teams` | 0 | 0 | none |

No `checks` were spent. `check_positions`, `check_prompts`, keyword/group mutation and report-generation tools were not called.

## Keyword tracking state

Retrieved: 2026-11-26; source: PR-CY MCP; project `162079`.

| Search option | Engine | Language | Region | Device | Top | Created |
|---|---|---|---|---|---:|---|
| `135383` | `yandexLive` | ru | Москва | desktop | 10 | `2026-11-01 12:50:00` |
| `135384` | `google` | ru | Москва | desktop | 30 | `2026-11-01 12:50:00` |

- `get_keywords`: `count=0`, `total=0`, `has_more=false`.
- `get_project_keyword_groups`: empty array.
- `get_keywords_summaries` for `135383`: empty array.
- `get_keywords_summaries` for `135384`: empty array.
- `get_keywords_positions_history` for `135383`, period `2026-10-26`—`2026-11-26`, limit 100: empty array.
- `get_keywords_positions_history` for `135384`, same period and limit: empty array.

Status: `NOT_VERIFIED` for ranking/position conclusions. Absence of stored keyword rows is not a zero position and not evidence of zero demand.

## GSC views through PR-CY

Retrieved: 2026-11-26; source: PR-CY MCP; source parameter `gsc` only; reporting period `2026-10-27`—`2026-11-23`. Yandex Webmaster is not connected on this project, so no webmaster view was queried.

| Tool | View | Result |
|---|---|---|
| `get_pages_summary_by_dates` | daily totals | empty array |
| `get_pages_summary` | pages, sorted by `-impressions`, limit 20 | empty array |
| `get_keywords_pages_summary` | query/page, sorted by `-impressions`, limit 20 | empty array |

Status: `NOT_VERIFIED` for clicks, impressions, CTR and position from these PR-CY GSC views. Do not convert empty arrays into zeros and do not mix these views with the separate GSC/OpenSEO datasets already held in the repository.

## Yandex Metrica views through PR-CY

Retrieved: 2026-11-26; source: PR-CY MCP; reporting period `2026-10-27`—`2026-11-23`; counter id visible in the API query: `1413317`. These are Metrica sessions/users, not AI answers or leads.

### Visits

`get_metrika_visits` returned `ym:s:visits = 6034`, with `sampled=false`, `data_lag=0`.

### Sources summary

`get_metrika_sources_summary`, first 20 of 29 rows. Metrics are visits, users, bounce rate (%), page depth and average visit duration (seconds).

| Source | Visits | Users | Bounce % | Depth | Avg duration |
|---|---:|---:|---:|---:|---:|
| Direct traffic | 2529 | 2274 | 50.29655991 | 1.38196916 | 66.53934361 |
| Search engine traffic / Google | 1574 | 1454 | 24.841169 | 1.53049555 | 172.11499365 |
| Search engine traffic / Yandex | 1274 | 1156 | 21.35007849 | 1.6177394 | 171.43406593 |
| Internal traffic | 265 | 237 | 16.60377358 | 1.88301887 | 167.2754717 |
| Recommendation system traffic / Yandex Zen | 135 | 135 | 14.81481481 | 2.32592593 | 110.06666667 |
| Link traffic / mail.ru | 119 | 119 | 0 | 2.74789916 | 146.86554622 |
| Social network traffic / VK | 11 | 9 | 9.09090909 | 1.81818182 | 420.45454545 |
| Search engine traffic / Bing | 10 | 10 | 30 | 1.6 | 71.6 |
| Link traffic / alice.yandex.ru | 3 | 3 | 33.33333333 | 1.33333333 | 32 |
| Search engine traffic / DuckDuckGo | 2 | 2 | 50 | 1 | 40 |

Report totals: `5974` visits, `5414` users, `33.66253766`% bounce, `1.54753934` page depth, `127.32892534` seconds average duration; `sampled=false`, `data_lag=0`. The visits endpoint and sources report are separate aggregations; do not merge their totals.

### Start pages

`get_metrika_pages_report`, dimension `ym:s:startURL`, metrics `ym:s:users` and `ym:s:visits`, first 20 of 403 rows.

| Start URL | Users | Visits |
|---|---:|---:|
| canonical homepage (`https://www.audio-reclama.ru`; Metrica startURL was recorded without `www`) | 701 | 739 |
| `/blog/audioreklama-v-internete-kak-ona-rabotaet.html` | 398 | 400 |
| `/blog/top-8-studiy-ozvuchivaniya-filmov-i-serialov-18.html` | 302 | 311 |
| `/diktoryi/muzhskie-diktor-golosa/russian-diktor-sergey-chonishvili.html` | 284 | 286 |
| `/diktoryi/zhenskie-diktor-golosa/russian-diktor-elizaveta-chaban.html` | 201 | 201 |
| `/diktoryi/zhenskie-diktor-golosa/russian-diktor-kseniya-brzhezovskaya.html` | 192 | 192 |
| `/diktoryi/filter/muzhskie-diktor-golosa.html` | 148 | 166 |
| `/diktoryi/filter/zhenskie-diktor-golosa.html` | 128 | 130 |
| `/blog/business-sound/teoriya-u-obraznogo-dvizheniya.html` | 126 | 126 |
| `/diktoryi/filter/izvestnye-golosa.html` | 126 | 133 |

Report totals: `5473` users, `6034` visits; `total_rows=403`, `sampled=false`, `data_lag=0`. URLs in the table after the home page are paths under the canonical site `https://www.audio-reclama.ru`.

## Boundaries and next checks

- These are search/session observations from a connected analytics account. They do not prove AI citations, answer-share, lead generation, revenue or a RU consumer-UI observation.
- `alice.yandex.ru` referral rows are measured referral traffic only; they are not proof of an Alice skill, Alice AI answer or order channel.
- Bing sessions are measured search-engine traffic only; the native Bing AI Performance export remains `WAITING_FOR_PUBLIC_UPDATE` / unavailable unless separately authorized.
- No official-site file changed. `UNCHANGED` remains `UNCHANGED`.
- Future PR-CY work must re-check the period, retrieval date, source, engine, region and device before comparison. No result here should be merged with GSC/OpenSEO data that uses a different period or device split.
