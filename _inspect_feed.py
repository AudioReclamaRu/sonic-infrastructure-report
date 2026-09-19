# -*- coding: utf-8 -*-
import sys, os, re, datetime
sys.stdout.reconfigure(encoding='utf-8')
R = r'F:\Pill\tmp\opencode\sonic-repo'
raw = open(os.path.join(R, 'feed', 'items.csv'), encoding='utf-8').read()
rows = [r for r in raw.splitlines() if r.strip()]
now = datetime.datetime.now(datetime.timezone.utc)
print('NOW_UTC=', now.isoformat())
print('TOTAL_ROWS=', len(rows))
print('--- per-row date|published-guess (first 5 tokens) ---')
published = 0
future = 0
due = 0
parsed = []
for i, r in enumerate(rows):
    parts = r.split('~~~')
    if len(parts) < 5:
        continue
    dt = parts[0].strip()
    title = parts[1][:45]
    try:
        d = datetime.datetime.strptime(dt, '%a, %d %b %Y %H:%M:%S %Z')
        # %Z даст UTC только если 'GMT' -> заменяем
    except Exception:
        pass
    # нормальная попытка: без %Z
    try:
        d = datetime.datetime.strptime(dt.split(' GMT')[0].split(' +')[0], '%a, %d %b %Y %H:%M:%S')
        d = d.replace(tzinfo=datetime.timezone.utc)
        state = 'DUE' if d <= now else 'FUT'
        if d <= now:
            due += 1
        else:
            future += 1
    except Exception as e:
        state = 'NO_DATE(' + repr(e)[:20] + ')'
    # опубликован или нет: последний токен может быть датой GMT
    print('%-4d %-10s %s | %s' % (i, state, dt[:28], title))
print('SUMMARY due(past)=', due, ' future=', future)
