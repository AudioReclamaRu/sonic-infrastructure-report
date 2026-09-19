# -*- coding: utf-8 -*-
"""Diagnostika: chto by publisher.py (realnaia selektciia) opublikoval pryamo seichas.

Importiruem publisher.py, vyzyvaem ego-zhe load_items + due-select. Bez indeksov-vgadok."""
import sys, os, datetime, importlib.util, traceback
sys.stdout.reconfigure(encoding='utf-8')

R = r'F:\Pill\tmp\opencode\sonic-repo'
PUB = os.path.join(R, 'publisher.py')
LOG = os.path.join(R, '_wd_duecheck.log')

now = datetime.datetime.now(datetime.timezone.utc)

def log(m):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(datetime.datetime.now().strftime('%H:%M:%S') + ' ' + m + '\n')

def main():
    if os.path.exists(LOG):
        os.remove(LOG)
    log('NOW_UTC=' + now.isoformat())
    try:
        spec = importlib.util.spec_from_file_location('publisher', PUB)
        pub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pub)
        log('MODULE_LOADED=True')
    except Exception as e:
        log('MODULE_LOAD_FAILED=' + repr(e))
        log(traceback.format_exc())
        return

    # Какие имена функций/атрибутов реально есть в publisher? Печатаем существующие с 'item' или 'due'.
    names = [n for n in dir(pub) if not n.startswith('__')]
    log('ATTRS_ITEM=' + ','.join(n for n in names if 'item' in n.lower() or 'due' in n.lower() or 'publ' in n.lower() or 'select' in n.lower() or 'next' in n.lower()))

    # Пытаемся понять, как publisher решает: есть ли функция типа select_due/next_due
    # и как она формирует кандидатов. Ищем в исходнике строки с 'due'/'GMT'/'dow'.
    src = open(PUB, encoding='utf-8').read()
    for ln in src.splitlines():
        low = ln.lower()
        if any(k in low for k in ('def due', 'def select', 'due_at', 'parse_date', 'is_due', 'dow', 'today', 'date(')) and len(ln.strip()) < 160:
            log('SRC ' + ln.strip()[:150])

    # Зовём load_items (реальный) — считаем, что он есть.
    items = getattr(pub, 'load_items', None)
    if items is None:
        log('NO_LOAD_ITEMS')
        return
    try:
        itlist = items()
        log('ITEMS_CNT=' + str(len(itlist)))
    except Exception as e:
        log('LOAD_ITEMS_FAIL=' + repr(e) + traceback.format_exc())
        return

    # трекер TG
    tg = set()
    tgp = os.path.join(R, 'tg', 'tg_published.txt')
    if os.path.exists(tgp):
        for ln in open(tgp, encoding='utf-8'):
            g = ln.strip()
            if g:
                tg.add(g)
    log('TG_TRACKER_CNT=' + str(len(tg)))

    # Селекция: items с date<=now и guid НЕ в tg. Используем атрибуты guid/date прямо.
    due = []
    for it in itlist:
        guid = it.get('guid') if isinstance(it, dict) else getattr(it, 'guid', None)
        try:
            d = it.get('date') if isinstance(it, dict) else getattr(it, 'date', None)
        except Exception:
            d = None
        if isinstance(d, str) and not d.startswith(('Mon', 'Tue', 'Wed', 'Thu')):
            try:
                d2 = pub.parse_date(d) if hasattr(pub, 'parse_date') else None
            except Exception:
                d2 = None
        log('ITEM guid=' + str(guid)[:30] + ' date=' + str(d)[:25] + ' in_tg=' + str(guid in tg) + ' title=' + (it.get('title') if isinstance(it, dict) else '')[:40])
        if guid in tg:
            continue
        if isinstance(d, str) and pub.parse_date and d2 and d2 <= now:
            due.append((d2, guid, it.get('title') if isinstance(it, dict) else ''))
    due.sort(key=lambda x: x[0])
    log('DUE_NOW_CNT=' + str(len(due)))
    for dd, g, t in due[:12]:
        log('  DUE ' + dd.isoformat() + ' | ' + str(g) + ' | ' + t[:50])
    log('FUT_MIN=' + ('' if not due else ''))

if __name__ == '__main__':
    main()
    print('DUECHECK_DONE')
