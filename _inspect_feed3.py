# -*- coding: utf-8 -*-
"""Честный разбор items.csv: строка = 'date~~~subject~~~body...' ТРЕБУЕТ разделитель '~~~' ТОЧНО,
но body сам содержит '~~~'->guid. Реальный формат: date~~~title~~~body~~~guid (4 поля, guid последний).
Разбор с конца: последний '~~~' -> guid, предпоследний -> body."""
import sys, os, datetime, email.utils
sys.stdout.reconfigure(encoding='utf-8')
R = r'F:\Pill\tmp\opencode\sonic-repo'
ITEMS = os.path.join(R, 'feed', 'items.csv')
TG_PUB = r'F:\Pill\tmp\opencode\tg\tg_published.txt'

now = datetime.datetime.now(datetime.timezone.utc)
print('NOW_UTC=' + now.isoformat())

def parse_date(s):
    return email.utils.parsedate_to_datetime(s)

lines = [l.rstrip('\r') for l in open(ITEMS, encoding='utf-8') if l.strip('\r\n')]
print('LINES_CNT=' + str(len(lines)))

items = []
for i, ln in enumerate(lines, 1):
    # разделитель '~~~' разделяет ровно 6 полей в фиде? посмотрим реальную строку по '~~~'
    parts = ln.split('~~~')
    if len(parts) != 6:
        print('SKIP row %d fields=%d first200=%r' % (i, len(parts), ln[:90]))
        continue
    date_s, subj, body, guid, _, _ = parts
    dt = parse_date(date_s) if date_s else None
    items.append({'line': i, 'date_s': date_s, 'dt': dt, 'subj': subj, 'guid': guid})

print('PARSED_ITEMS_CNT=' + str(len(items)))

published = set()
if os.path.exists(TG_PUB):
    for ln in open(TG_PUB, encoding='utf-8'):
        g = ln.strip()
        if g:
            published.add(g)
print('TG_PUBLISHED_CNT=' + str(len(published)))

due_state = []
for it in items:
    if it['dt'] is None:
        st = 'NO_DATE'
    else:
        st = 'DUE_PAST' if it['dt'] <= now else 'FUT'
    pub = 'PUB' if it['guid'] in published else '--'
    due_state.append((it['dt'] or now, st, pub, it['subj'][:50], it['guid']))

due_state.sort(key=lambda x: (x[0] is None, x[0]))
print('=== SORTED (date | state | pub | title) ===')
for dt, st, pub, subj, guid in due_state:
    print(repr(str(dt))[:30].ljust(32), st.ljust(10), pub, '|', subj, '|', guid)

#  предметный ответ
overdue = [x for x in due_state if x[1] == 'DUE_PAST' and x[2] == '--']
pub_ok = [x for x in due_state if x[2] == 'PUB']
print('OVERDUE_UNPUBLISHED_CNT=' + str(len(overdue)))
print('PUBLISHED_CNT=' + str(len(pub_ok)))
fut = [x for x in due_state if x[1] == 'FUT']
print('FUT_CNT=' + str(len(fut)) + ' FIRST_FUT=' + (str(sorted(x for x in (it['dt'] for it in items) if x and x > now)[0]) if fut else '--'))
