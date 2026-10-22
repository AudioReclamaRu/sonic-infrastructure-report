# -*- coding: utf-8 -*-
"""cycle_planner.py — horizon planner + self-correction for the Culture of Voice cycle.

The editorial workbench (editorial_queue.py) reports state; this tool acts on the two
gaps it can only flag: the empty horizon and a stalled cycle.

  1. PLAN    — hold slots for HORIZON_DAYS ahead at the observed cadence (median of the
               last slot intervals), 06:45 GMT, filling only from evidence cards that are
               `status: verified`, are not already referenced by a slot and whose guid
               does not exist. Only append-only rows are ever written; published guid,
               existing rows and concepts.json are never touched.
  2. TASK    — when verified cards cannot fill the horizon, or a circuit breaker trips
               (dead publisher, quota not counting, stuck due slot, red exits, low recall,
               stale layers), emit a restoration task instead of inventing news.
  3. REPORT  — reports/editorial/cycle-YYYY-MM-DD.{md,json} is the planner's output;
               editorial_queue.py renders it as section 6 of the daily queue.

usage: python tools/cycle_planner.py [--dry-run] [--horizon 14]
exit:  always 0 (a broken circuit is a task, never a failed cadence — same contract
       as editorial_queue.py).
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
FEED = os.path.join(REPO, 'feed')
STATE = os.path.join(REPO, 'state')
REPORTS = os.path.join(REPO, 'reports')
OUTDIR = os.path.join(REPORTS, 'editorial')
TASKS_LOG = os.path.join(STATE, 'cycle_tasks.jsonl')
TG_PUB = os.path.join(os.path.dirname(REPO), 'tg', 'tg_published.txt')
BLOB = 'https://github.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/'

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import editorial_queue as eq

MONTHS = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
          'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
WDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def rfc822(d):
    return '%s, %02d %s %04d 06:45:00 GMT' % (
        WDAYS[d.weekday()], d.day, d.strftime('%b'), d.year)


def _read(path):
    try:
        with io.open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


def load_evidence():
    """evidence cards -> dicts; only `status: verified` cards may enter a plan."""
    cards = []
    for p in sorted(glob.glob(os.path.join(REPO, 'evidence', 'E-*.md'))):
        txt = _read(p)
        cid = re.search(r'^id:\s*(\S+)', txt, re.M)
        st = re.search(r'^status:\s*(\S+)', txt, re.M)
        prim = re.search(r'Primary:\s*(\S+)', txt)
        m = re.search(r'Short statement\s*\n(.+?)(?:\n\n|\nSource)', txt, re.S)
        stmt = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
        cards.append({
            'id': cid.group(1) if cid else os.path.basename(p)[:-3],
            'status': (st.group(1) if st else '').lower(),
            'primary': prim.group(1) if prim else '',
            'statement': stmt,
        })
    return cards


def slug_from_primary(primary, card):
    s = (primary or '').strip()
    m = re.match(r'https?://[^/]+/(.+)$', s)
    path = m.group(1) if m else ''
    path = re.sub(r'[?#].*$', '', path).strip('/')
    parts = [re.sub(r'[^a-z0-9]+', '-', p.lower()).strip('-')
             for p in path.split('/') if p]
    parts = [p for p in parts if p and p not in ('index', 'posts', 'news', '2026')]
    if parts:
        slug = '-'.join(parts[-2:]) if len(parts) > 1 else parts[-1]
        slug = slug[:48].strip('-')
    else:
        # no URL in Primary (e.g. "official texts — leginfo..."): latin words of the
        # card's own short statement, so the guid stays human-readable ASCII
        words = re.findall(r'[A-Za-z][A-Za-z0-9-]{2,}',
                           re.sub(r'\(.*?\)', ' ', card.get('statement') or ''))
        stop = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was',
                'were', 'its', 'not', 'but', 'toward', 'treat', 'objects', 'voice'}
        words = [w.lower() for w in words if w.lower() not in stop]
        slug = '-'.join(words[:3])
    if not slug:
        slug = card['id'].lower().replace('_', '-')
    return slug


def title_for(card):
    """Skeleton title: the card's own short statement (real text, capped) — the final
    caption comes from the concept headline anyway."""
    stmt = card.get('statement') or ''
    cut = re.split(r'(?<=[.!?])\s', stmt, maxsplit=1)[0]
    cut = cut.replace('~~~', ' — ').strip()
    if not cut:
        cut = card['id']
    if len(cut) > 70:
        cut = cut[:69].rstrip() + '…'
    return '[%s] %s (черновик)' % (card['id'], cut)


def load_concepts():
    try:
        return json.load(io.open(os.path.join(FEED, 'concepts.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def slot_dates(items):
    dts = []
    for it in items:
        for fmt in ('%a, %d %b %Y %H:%M:%S GMT', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
            try:
                dts.append(dt.datetime.strptime(it['date'], fmt).replace(tzinfo=dt.timezone.utc))
                break
            except ValueError:
                continue
    return sorted(dts)


def observed_cadence(dts):
    """Median of the recent (last 6) slot intervals in whole days; floor 1, default 2."""
    diffs = [(dts[i + 1] - dts[i]).total_seconds() / 86400.0
             for i in range(len(dts) - 1)]
    diffs = [int(round(x)) for x in diffs[-6:] if 0 < x <= 14]
    if not diffs:
        return 2
    diffs.sort()
    return max(1, diffs[len(diffs) // 2])


def plan_horizon(items, cards, horizon_days):
    """Dates to fill + which verified cards are free to take them."""
    today = dt.datetime.now(dt.timezone.utc).date()
    dts = slot_dates(items)
    used_evid = set()
    guids = set()
    for it in items:
        guids.add(it['guid'])
        m = re.search(r'(E-\d{4}-\d{3})', it.get('url', '') + ' ' + it.get('title', ''))
        if m:
            used_evid.add(m.group(1))
    taken_dates = {d.date() for d in dts}
    cadence = observed_cadence(dts)
    last = dts[-1].date() if dts else today
    nxt = last + dt.timedelta(days=cadence)
    if nxt <= today:                      # never emit a slot that is already due:
        nxt = today + dt.timedelta(days=cadence)  # a dead cycle must not burst-publish
    limit = today + dt.timedelta(days=horizon_days)
    dates = []
    while nxt <= limit:
        if nxt not in taken_dates:
            dates.append(nxt)
        nxt += dt.timedelta(days=cadence)
    free = [c for c in cards
            if c['status'] == 'verified' and c['id'] not in used_evid]
    return dates, free, cadence, guids, used_evid, last, today


def circuit_tasks(health, items, pub, concepts, today, cards, pub_age):
    """Breakers -> tasks. Every task says what a human/machine must DO."""
    tasks = []

    def add(tid, sev, detail, action):
        tasks.append({'id': tid, 'severity': sev, 'detail': detail, 'action': action})

    hb = health.get('heartbeat_age_min')
    if hb is None or hb > 15:
        add('publisher-dead', 'RED',
            'heartbeat %s' % ('MISSING' if hb is None else '%d min' % hb),
            'поднять publisher --loop / проверить SonicOrchestratorWatchdog')

    due = [it for it in items if it['guid'] not in pub and not _is_future(it)]
    missing = [it for it in due if it['guid'] not in concepts]
    stuck = [it for it in due if it['guid'] in concepts]
    if missing:
        add('concept-missing', 'RED',
            'просроченных слотов без концепта: %d (%s)'
            % (len(missing), ', '.join(it['guid'] for it in missing[:5])),
            'написать 9 полей концепта (санкция владельца) — публикация остаётся за concept_gate')
    if stuck:
        add('publish-stuck', 'AMBER',
            'слоты с концептом не опубликованы: %d (%s)'
            % (len(stuck), ', '.join(it['guid'] for it in stuck[:5])),
            'проверить rejected.txt / вердикты / квоту publisher')

    pub_today = [g for g in pub if g.endswith(today.isoformat())]
    quota_file = os.path.join(STATE, 'quota-%s.json' % today.isoformat())
    if pub_today and not os.path.exists(quota_file):
        # only a post-publication run of the fixed publisher can be blamed: the
        # restart mtime (pid file) marks where inc_quota started existing
        pid_file = os.path.join(STATE, 'orchestrator.pid')
        started = None
        try:
            started = os.path.getmtime(pid_file)
        except OSError:
            pass
        pub_after_restart = started is None or _mtime(TG_PUB) > started
        if pub_after_restart:
            add('quota-not-counting', 'RED',
                'сегодня опубликовано %d после старта publisher, файла квоты нет'
                % len(pub_today),
                'проверить inc_quota в publisher.run_cycle')
        else:
            add('quota-not-counting', 'AMBER',
                'сегодняшние %d публикаций сделаны ДО рестарта (inc_quota ещё не '
                'действовал); квота не записана' % len(pub_today),
                'наблюдать: файл quota появится со следующей публикацией после рестарта')

    if health.get('poll_exit') not in (0, None):
        add('poll-red', 'AMBER', 'primary_poll exit=%s (%s)'
            % (health.get('poll_exit'), health.get('poll_run')),
            'проверить transport/search в primary_poll')
    if health.get('verify_exit') == 1:
        add('verify-red', 'AMBER', 'claims_verify exit=1 (%s) — SOURCE ERROR' % health.get('verify_run'),
            'исправить первичный URL/claim в state/claims.jsonl')
    recall = health.get('recall_pct')
    if recall is not None and recall < 60:
        add('recall-low', 'AMBER', 'recall KPI %s%% (<60)' % recall,
            'расширить discovery surface (reports/missed: loss stages)')
    sig_days = eq.age_days(_newest(REPORTS, 'signals', '*.md'))
    if sig_days is None or sig_days > 7:
        add('signals-stale', 'AMBER', 'reports/signals: %s' % eq.flag(sig_days, 'возраст'),
            'опубликовать сигнал недели (редакция)')

    covered = set()
    for ln in eq._lines(os.path.join(STATE, 'claims.jsonl')):
        try:
            covered.add(json.loads(ln).get('evidence_id'))
        except ValueError:
            pass
    gap = [c['id'] for c in cards if c['id'] not in covered]
    if gap:
        add('claims-gap', 'AMBER', 'evidence без registered claim: %s' % ', '.join(gap),
            'зарегистрировать claim (verify_claims --seed) для верификации первички')
    return tasks


def _newest(base, sub, pattern):
    files = [f for f in glob.glob(os.path.join(base, sub, pattern))
             if re.match(r'\d{4}-\d{2}-\d{2}', os.path.basename(f))]
    return os.path.basename(max(files)) if files else None


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _is_future(it):
    now = dt.datetime.now(dt.timezone.utc)
    for fmt in ('%a, %d %b %Y %H:%M:%S GMT', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
        try:
            return dt.datetime.strptime(it['date'], fmt).replace(tzinfo=dt.timezone.utc) > now
        except ValueError:
            continue
    return False


def append_slots(rows):
    path = os.path.join(FEED, 'items.csv')
    raw = open(path, 'rb').read().decode('utf-8')
    if raw and not raw.endswith('\n'):
        raw += '\r\n'
    if rows:
        raw += '\r\n'.join(rows) + '\r\n'
        open(path, 'wb').write(raw.encode('utf-8'))


def log_new_tasks(tasks, today):
    """state/cycle_tasks.jsonl — append-only history of breaker trips, one row per
    task per day (no spam on the daily cadence)."""
    seen = set()
    for ln in eq._lines(TASKS_LOG):
        try:
            rec = json.loads(ln)
            if rec.get('day') == today.isoformat():
                seen.add(rec.get('id'))
        except ValueError:
            continue
    fresh = [t for t in tasks if t['id'] not in seen]
    if fresh:
        with io.open(TASKS_LOG, 'a', encoding='utf-8') as fh:
            for t in fresh:
                fh.write(json.dumps(dict(t, day=today.isoformat(),
                                         ts=dt.datetime.now().replace(microsecond=0).isoformat()),
                                    ensure_ascii=False) + '\n')
    return fresh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='report only, no items.csv write')
    ap.add_argument('--horizon', type=int, default=14, help='planning horizon in days')
    a = ap.parse_args()

    now = dt.datetime.now()
    items, due, upcoming, pub_count, pub_age = eq.section_publish()
    health = eq.section_health()
    cards = load_evidence()
    concepts = load_concepts()
    pub = set(eq._lines(TG_PUB))
    ledger = eq.load_ledger()
    strong, weak, archived = eq.section_decision(ledger)

    dates, free, cadence, guids, used_evid, last_slot, today = plan_horizon(
        items, cards, a.horizon)

    rows, planned = [], []
    for d, card in zip(dates, free):
        slug = slug_from_primary(card['primary'], card)
        guid = '%s-%s' % (slug, d.isoformat())
        if guid in guids:
            continue
        src = BLOB + 'evidence/%s.md' % card['id']
        rows.append('~~~'.join([rfc822(d), title_for(card), '', src, guid, slug]))
        planned.append({'date': d.isoformat(), 'guid': guid, 'evidence': card['id']})
        guids.add(guid)

    tasks = circuit_tasks(health, items, pub, concepts, today, cards, pub_age)
    if len(planned) < len(dates):
        need = len(dates) - len(planned)
        tasks.insert(0, {
            'id': 'evidence-inventory', 'severity': 'RED',
            'detail': ('на горизонт %d дн. нужно %d слотов, verified-карточек свободно %d '
                       '(не хватает %d)' % (a.horizon, len(dates), len(free), need)),
            'action': ('открыть и верифицировать %d новых факт-карточек из STRONG-кандидатов; '
                       'НЕ выдумывать слоты без подтверждённой первички' % need)})
    if not upcoming and not planned:
        tasks.append({
            'id': 'horizon-empty', 'severity': 'RED',
            'detail': 'последний слот %s, будущих слотов нет' % last_slot,
            'action': 'восстановить план публикаций (см. evidence-inventory)'})

    if rows and not a.dry_run:
        append_slots(rows)
    fresh_tasks = log_new_tasks(tasks, today) if not a.dry_run else []

    payload = {
        'generated': now.replace(microsecond=0).isoformat(),
        'horizon_days': a.horizon, 'cadence_days': cadence,
        'last_slot': str(last_slot), 'dry_run': a.dry_run,
        'horizon_slots': [d.isoformat() for d in dates],
        'planned': planned, 'slots_appended': 0 if a.dry_run else len(rows),
        'free_verified_cards': [c['id'] for c in free],
        'strong_pending': len(strong),
        'tasks': tasks, 'tasks_new_today': [t['id'] for t in fresh_tasks],
    }

    md = ['# ПЛАН ЦИКЛА %s' % now.strftime('%Y-%m-%d %H:%M'), '',
          '## 1. ГОРИЗОНТ', '',
          '- последний слот: **%s**; каденс: **%d дн.**, 06:45 GMT; горизонт: %d дн.'
          % (last_slot, cadence, a.horizon),
          '- плановых дат: **%d**, verified-карточек свободно: **%d**'
          % (len(dates), len(free)),
          '- добавлено слотов: **%d**%s'
          % (0 if a.dry_run else len(rows), ' (dry-run)' if a.dry_run else ''), '']
    if planned:
        md.append('| дата | guid | evidence |')
        md.append('|---|---|---|')
        for p in planned:
            md.append('| %s | %s | %s |' % (p['date'], p['guid'], p['evidence']))
        md.append('')
    md += ['## 2. ЗАДАЧИ (%d)' % len(tasks), '']
    if not tasks:
        md.append('- обрывов не обнаружено')
    for t in tasks:
        md.append('- **[%s] %s** — %s\n  - действие: %s'
                  % (t['severity'], t['id'], t['detail'], t['action']))
    md += ['', '## 3. STRONG-КАНДИДАТЫ ДЛЯ НОВЫХ ФАКТ-КАРТОЧЕК (%d, top 10)' % min(10, len(strong)), '']
    if not strong:
        md.append('- STRONG-кандидатов нет — источник первички пуст, чинить poll/scan')
    for r in strong[:10]:
        md.append('- %s :: %s\n  - %s'
                  % (r.get('date') or '?', (r.get('title') or '').replace('|', '/'),
                     r.get('url') or ''))
    md += ['', 'Следующий шаг: редакция/агент верифицирует факт-карточку (FACT GATE), '
           'затем концепт → concept_gate → публикация. Машина слоты без verified-карточки не создаёт.', '']

    text = '\n'.join(md)
    print(text)
    if not a.dry_run:
        if not os.path.isdir(OUTDIR):
            os.makedirs(OUTDIR)
        day = now.strftime('%Y-%m-%d')
        with io.open(os.path.join(OUTDIR, 'cycle-%s.md' % day), 'w', encoding='utf-8') as fh:
            fh.write(text)
        with io.open(os.path.join(OUTDIR, 'cycle-%s.json' % day), 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print('written: reports/editorial/cycle-%s.{md,json}' % day)
    return 0


if __name__ == '__main__':
    sys.exit(main())
