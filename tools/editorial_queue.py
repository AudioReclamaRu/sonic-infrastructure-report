# -*- coding: utf-8 -*-
"""editorial_queue.py — the editorial workbench: what needs a HUMAN decision today.

Builds reports/editorial/queue-YYYY-MM-DD.{md,json} out of the runtime state of the
live loop. It is pure data — titles, dates, urls, statuses, ages — and it never
writes prose that would stand in for an editorial decision. The SIGNAL / VERDICT /
PUBLISH steps stay with the editors; this file only removes the "what do I look at"
overhead in front of them.

Sections:
  1. ТРЕБУЕТ РЕШЕНИЯ   — STRONG discoveries not yet acted on + WEAK needing eyes
  2. ФАКТЫ / CLAIMS    — evidence cards without a registered claim (primary URL gap)
  3. ИЗДАТЕЛЬСКАЯ ОЧЕРЕДЬ — feed/items.csv due & unpublished, next slot, last publish
  4. УСТАРЕВШИЕ СЛОИ   — signals / verdicts / editorial trail age (red when > 7 days)
  5. ЗДОРОВЬЕ КОНТУРА  — heartbeat, last poll/verify exit codes, recall audit, intel

usage: python tools/editorial_queue.py [--no-write]
exit:  always 0 (a stale layer is reported, never made to fail the cadence)
"""
from __future__ import unicode_literals

import argparse
import datetime as dt
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STATE = os.path.join(REPO, 'state')
FEED = os.path.join(REPO, 'feed')
REPORTS = os.path.join(REPO, 'reports')
OUTDIR = os.path.join(REPORTS, 'editorial')
LEDGER = os.path.join(STATE, 'primary_seen.jsonl')
TG_PUB = os.path.join(os.path.dirname(REPO), 'tg', 'tg_published.txt')
STALE_DAYS = 7
FRESH_DAYS = 30

if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from primary_poll import grade, ENDPOINTS
except Exception:
    grade = None
    ENDPOINTS = {}


def regrade(rec):
    """Current classifier, plus the pure-vertical promotion primary_poll applies
    at write time (a vertical feed's whole beat is our beat). The ledger is
    append-only, so this must be recomputed on every read."""
    rel = grade(rec.get('title') or '') if grade else rec.get('relevance')
    if rel == 'WEAK':
        for epn in eps(rec):
            if (ENDPOINTS.get(epn) or {}).get('vertical'):
                rel = 'STRONG'
                break
    return rel


def _read(path):
    try:
        with io.open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


def _mtime_age(path):
    try:
        return (dt.datetime.now() - dt.datetime.fromtimestamp(os.path.getmtime(path))).total_seconds() / 86400.0
    except OSError:
        return None


def _lines(path):
    return [ln.rstrip('\r\n') for ln in _read(path).splitlines() if ln.strip()]


def load_ledger():
    seen = {}
    for ln in _lines(LEDGER):
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        if rec.get('key'):
            seen[rec['key']] = rec
    return list(seen.values())


def age_days(datestr):
    if not datestr:
        return None
    try:
        d = dt.datetime.strptime(datestr[:10], '%Y-%m-%d').date()
    except ValueError:
        return None
    return (dt.date.today() - d).days


def _is_fresh(rec, days=FRESH_DAYS):
    a = age_days(rec.get('date'))
    return a is None or a <= days


def section_decision(ledger):
    """Re-grades every ledger row with the current classifier (the ledger is
    append-only and keeps the grade from the day it was written; a later fix to
    grade() must take effect on read). STRONG is then split by age: only fresh
    candidates are 'requiring a decision', the rest move to the archive."""
    strong, weak = [], []
    for r in ledger:
        rel = regrade(r)
        r = dict(r)
        r['relevance'] = rel
        if rel == 'STRONG':
            strong.append(r)
        elif rel == 'WEAK':
            weak.append(r)
    strong.sort(key=lambda x: x.get('date') or '', reverse=True)
    weak.sort(key=lambda x: x.get('date') or '', reverse=True)
    fresh = [r for r in strong if _is_fresh(r)]
    archived = [r for r in strong if not _is_fresh(r)]
    return fresh, weak, archived


def section_claims():
    cards = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(REPO, 'evidence', 'E-*.md')))
    claims = []
    for ln in _lines(os.path.join(STATE, 'claims.jsonl')):
        try:
            claims.append(json.loads(ln))
        except ValueError:
            pass
    covered = {c.get('evidence_id') for c in claims}
    latest = {}
    for ln in _lines(os.path.join(STATE, 'verdictions.jsonl')):
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        cid = rec.get('claim_id')
        if cid and (cid not in latest or rec.get('ts', '') > latest[cid].get('ts', '')):
            latest[cid] = rec
    return cards, claims, latest


def section_publish():
    items = []
    for row in _lines(os.path.join(FEED, 'items.csv')):
        if row.startswith(('TITLE~~~', 'DESC~~~')):
            continue
        p = row.split('~~~')
        if len(p) < 6:
            continue
        items.append({'date': p[0].strip(), 'title': p[1].strip(), 'url': p[3].strip(),
                      'guid': p[4].strip(), 'tag': p[5].strip()})
    pub = set(_lines(TG_PUB))
    now = dt.datetime.now(dt.timezone.utc)
    due = []
    upcoming = []
    for it in items:
        d = None
        for fmt in ('%a, %d %b %Y %H:%M:%S GMT', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
            try:
                d = dt.datetime.strptime(it['date'], fmt).replace(tzinfo=dt.timezone.utc)
                break
            except ValueError:
                continue
        if d is None:
            continue
        it['_dt'] = d
        if d <= now and it['guid'] not in pub:
            due.append(it)
        elif d > now:
            upcoming.append(it)
    upcoming.sort(key=lambda x: x['_dt'])
    return items, due, upcoming, len(pub), _mtime_age(TG_PUB)


def section_layers():
    sig = glob.glob(os.path.join(REPORTS, 'signals', '*.md'))
    sig = [os.path.basename(p)[:-3] for p in sig if re.match(r'\d{4}-\d{2}-\d{2}', os.path.basename(p))]
    idx_text = _read(os.path.join(REPORTS, 'verdicts', 'verdict-index.md'))
    vd_dates = re.findall(r'Date:\s*(\d{4}-\d{2}-\d{2})', idx_text)
    return {
        'signals_last': max(sig) if sig else None,
        'verdict_index_last': max(vd_dates) if vd_dates else None,
        'verdicts_state_age': _mtime_age(os.path.join(STATE, 'verdicts.jsonl')),
        'editorial_state_age': _mtime_age(os.path.join(STATE, 'editorial.jsonl')),
        'items_age': _mtime_age(os.path.join(FEED, 'items.csv')),
    }


def last_exit(path):
    code, when = None, None
    for ln in _lines(path):
        m = re.search(r'EXITCODE=(-?\d+)', ln)
        if m:
            code = int(m.group(1))
        m2 = re.search(r'====\s*(\d{1,2}\.\d{1,2}\.\d{4} [\d:,]+)\s*====', ln)
        if m2:
            when = m2.group(1).strip()
    return code, when


def section_health():
    polls = sorted(glob.glob(os.path.join(STATE, 'primary_poll.task.log')))
    verifies = sorted(glob.glob(os.path.join(STATE, 'claims_verify.task.log')))
    pc, pt = last_exit(polls[-1]) if polls else (None, None)
    vc, vt = last_exit(verifies[-1]) if verifies else (None, None)
    audits = sorted(glob.glob(os.path.join(REPORTS, 'missed', 'missed-audit-*.json')))
    recall = None
    if audits:
        try:
            with io.open(audits[-1], encoding='utf-8') as fh:
                recall = json.load(fh).get('recall_pct')
        except (OSError, ValueError):
            pass
    intel = os.path.join(REPORTS, 'intel', 'intel-%s.json' % dt.date.today().isoformat())
    intel_rows = None
    if os.path.exists(intel):
        try:
            with io.open(intel, encoding='utf-8') as fh:
                intel_rows = len(json.load(fh).get('rows') or [])
        except (OSError, ValueError):
            pass
    return {
        'heartbeat_age_min': (None if _mtime_age(os.path.join(STATE, 'heartbeat.txt')) is None
                              else round(_mtime_age(os.path.join(STATE, 'heartbeat.txt')) * 1440)),
        'poll_exit': pc, 'poll_run': pt,
        'verify_exit': vc, 'verify_run': vt,
        'recall_pct': recall,
        'intel_rows_today': intel_rows,
        'status_age_h': (None if _mtime_age(os.path.join(REPORTS, 'status.html')) is None
                         else round(_mtime_age(os.path.join(REPORTS, 'status.html')) * 24, 1)),
    }


def eps(rec):
    """ledger stores endpoints as a comma-joined string; older rows may be lists."""
    e = rec.get('endpoints') or []
    return e if isinstance(e, list) else [x for x in str(e).split(',') if x]


def section_cycle():
    """Latest planner output (cycle_planner.py): horizon plan + restoration tasks.
    The planner runs before this queue (09:45 vs 09:55); a missing or aged file is
    itself a signal — the loop that should plan the horizon has not run."""
    files = sorted(glob.glob(os.path.join(OUTDIR, 'cycle-*.json')))
    if not files:
        return None, None
    path = files[-1]
    try:
        with io.open(path, encoding='utf-8') as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None, None
    day = re.search(r'cycle-(\d{4}-\d{2}-\d{2})\.json$', path)
    return data, (age_days(day.group(1)) if day else None)


def flag(days, what):
    if days is None:
        return '%s: нет данных' % what
    if days > STALE_DAYS:
        return '%s: **УСТАРЕЛО %d дн.** (> %d)' % (what, days, STALE_DAYS)
    return '%s: %d дн.' % (what, days)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-write', action='store_true')
    a = ap.parse_args()

    now = dt.datetime.now()
    ledger = load_ledger()
    strong, weak, archived = section_decision(ledger)
    cards, claims, latest = section_claims()
    items, due, upcoming, pub_count, pub_age = section_publish()
    layers = section_layers()
    health = section_health()
    cycle, cycle_age = section_cycle()

    md = ['# ОЧЕРЕДЬ РЕДАКЦИИ %s' % now.strftime('%Y-%m-%d %H:%M'), '',
          'Машина собирает **данные**: кандидаты, статусы, возраст слоёв.',
          'Решение (SIGNAL → VERDICT → PUBLISH) принимает редакция. Текст не генерируется.', '',
          '## 1. ТРЕБУЕТ РЕШЕНИЯ', '',
          '### STRONG — кандидат в материал / evidence (%d)' % len(strong), '',
          '| дата | возраст | класс | заголовок | источник |',
          '|---|---|---|---|---|']
    for r in strong:
        d = r.get('date') or ''
        age = age_days(d)
        md.append('| %s | %s | %s | %s | %s |' % (
            d, ('%d дн.' % age) if age is not None else '?',
            r.get('src_class', ''), (r.get('title') or '').replace('|', '/'),
            '%s / %s' % (r.get('domain', ''), ','.join(eps(r)))))

    if archived:
        md += ['', '### STRONG — архив (> %d дн., вне решения) (%d)'
               % (FRESH_DAYS, len(archived)), '',
               '| дата | возраст | класс | заголовок | источник |',
               '|---|---|---|---|---|']
        for r in archived[:20]:
            d = r.get('date') or ''
            age = age_days(d)
            md.append('| %s | %s | %s | %s | %s |' % (
                d, ('%d дн.' % age) if age is not None else '?',
                r.get('src_class', ''), (r.get('title') or '').replace('|', '/'),
                r.get('domain', '')))
        if len(archived) > 20:
            md.append('| ... | | | ещё %d старых | |' % (len(archived) - 20))

    fresh_weak = [r for r in weak if (age_days(r.get('date')) or 999) <= 21]
    md += ['', '### WEAK — нужен глаз редактора (%d свежих из %d)'
           % (len(fresh_weak), len(weak)), '',
           '| дата | возраст | класс | заголовок | источник |',
           '|---|---|---|---|---|']
    for r in fresh_weak:
        d = r.get('date') or ''
        age = age_days(d)
        md.append('| %s | %s | %s | %s | %s |' % (
            d, ('%d дн.' % age) if age is not None else '?',
            r.get('src_class', ''), (r.get('title') or '').replace('|', '/'),
            r.get('domain', '')))

    covered = {c.get('evidence_id') for c in claims}
    gap = [c for c in cards if c not in covered]
    md += ['', '## 2. ФАКТЫ / CLAIMS', '',
           '- evidence-карт: **%d**, зарегистрированных claims: **%d**'
           % (len(cards), len(claims)),
           '- coverage gap (нет primary URL → не верифицируются): **%d**'
           % len(gap)]
    if gap:
        md.append('- не покрыты: `%s`' % '`, `'.join(gap))
    for c in claims:
        v = latest.get(c.get('claim_id'), {})
        md.append('- %s → **%s** (last %s) [%s]'
                  % (c.get('claim_id'), v.get('verdict', 'NOT RUN'),
                     (v.get('ts') or '?')[:10], c.get('status')))

    md += ['', '## 3. ИЗДАТЕЛЬСКАЯ ОЧЕРЕДЬ', '',
           '- строк в `feed/items.csv`: **%d**; опубликовано TG guid: **%d**'
           % (len(items), pub_count),
           '- просрочено и не опубликовано: **%d**' % len(due)]
    for it in due[:10]:
        md.append('  - %s :: %s' % (it['date'], it['title'][:70]))
    if upcoming:
        nxt = upcoming[0]
        md.append('- ближайший слот: %s :: %s' % (nxt['date'], nxt['title'][:70]))
    else:
        md.append('- ближайший слот: **НЕТ — очередь пуста**')
    md.append('- последняя публикация в TG: %s назад'
              % ('%.1f дн.' % pub_age if pub_age is not None else 'нет данных'))

    md += ['', '## 4. УСТАРЕВШИЕ СЛОИ', '',
           '- ' + flag(age_days(layers['signals_last']), 'reports/signals (последняя заметка)'),
           '- ' + flag(age_days(layers['verdict_index_last']), 'reports/verdicts (последний вердикт)'),
           '- ' + flag(layers['verdicts_state_age'] and int(layers['verdicts_state_age']),
                       'state/verdicts.jsonl'),
           '- ' + flag(layers['editorial_state_age'] and int(layers['editorial_state_age']),
                       'state/editorial.jsonl'),
           '- ' + flag(layers['items_age'] and int(layers['items_age']), 'feed/items.csv (очередь)')]

    md += ['', '## 5. ЗДОРОВЬЕ КОНТУРА', '',
           '- heartbeat: %s' % (('%d мин назад' % health['heartbeat_age_min'])
                                if health['heartbeat_age_min'] is not None else 'НЕТ'),
           '- primary_poll: exit=%s (%s)' % (health['poll_exit'], health['poll_run']),
           '- claims_verify: exit=%s (%s)' % (health['verify_exit'], health['verify_run']),
           '- recall KPI (MISSED_MAJOR_EVENTS_PER_WEEK): %s%%' % health['recall_pct'],
           '- intel сегодня строк: %s' % health['intel_rows_today'],
           '- status.html: %s ч назад' % health['status_age_h'], '']

    md += ['## 6. ПЛАН ЦИКЛА И ЗАДАЧИ', '']
    if cycle is None:
        md += ['- **план не сформирован** — cycle_planner.py не запускался '
                '(задача SonicCyclePlanner / отчёт reports/editorial/cycle-*.json)', '']
    else:
        tasks = cycle.get('tasks') or []
        red = [t for t in tasks if t.get('severity') == 'RED']
        md.append('- отчёт: %s, **%d дн. назад**; горизонт %s дн., каденс %s дн.'
                  % (cycle.get('generated', '?'), cycle_age if cycle_age is not None else '?',
                     cycle.get('horizon_days'), cycle.get('cadence_days')))
        md.append('- плановых дат: %d, добавлено слотов: %d, свободных verified-карточек: %d'
                  % (len(cycle.get('horizon_slots') or []),
                     cycle.get('slots_appended') or 0,
                     len(cycle.get('free_verified_cards') or [])))
        slots = cycle.get('horizon_slots') or []
        if slots:
            md.append('- ближайшие даты: %s' % ', '.join(slots[:5]))
        md.append('- задач: **%d** (RED %d)'
                  % (len(tasks), len(red)))
        for t in tasks:
            md.append('  - [%s] **%s** — %s'
                      % (t.get('severity'), t.get('id'), t.get('detail')))
        md.append('')

    payload = {
        'generated': now.replace(microsecond=0).isoformat(),
        'strong_pending': len(strong), 'strong_archived': len(archived),
        'weak_pending': len(weak),
        'weak_fresh': len(fresh_weak),
        'evidence_cards': len(cards), 'claims': len(claims),
        'claims_gap': gap,
        'publish': {'items': len(items), 'due_unpublished': len(due),
                    'upcoming': len(upcoming), 'tg_published': pub_count},
        'layers': layers, 'health': health,
        'cycle': cycle, 'cycle_age_days': cycle_age,
        'strong_titles': [{'date': r.get('date'), 'title': r.get('title'),
                           'url': r.get('url'), 'class': r.get('src_class')}
                          for r in strong],
        'strong_archived_titles': [{'date': r.get('date'), 'title': r.get('title'),
                                    'url': r.get('url'), 'class': r.get('src_class')}
                                   for r in archived],
        'weak_fresh_titles': [{'date': r.get('date'), 'title': r.get('title'),
                               'url': r.get('url'), 'class': r.get('src_class')}
                              for r in fresh_weak],
    }

    print('\n'.join(md))
    if not a.no_write:
        if not os.path.isdir(OUTDIR):
            os.makedirs(OUTDIR)
        day = now.strftime('%Y-%m-%d')
        with io.open(os.path.join(OUTDIR, 'queue-%s.md' % day), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(md) + '\n')
        with io.open(os.path.join(OUTDIR, 'queue-%s.json' % day), 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print('\nwritten: reports/editorial/queue-%s.{md,json}' % day)
    return 0


if __name__ == '__main__':
    sys.exit(main())
