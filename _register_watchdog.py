# -*- coding: utf-8 -*-
"""Регистрация desktop-сторожа §8.9 через schtasks (XML в UTF-16LE).
Один проход: перекодировка -> /Create -> /Query подтверждение. Без shell-строк."""
import os, subprocess, sys

R = r'F:\Pill\tmp\opencode\sonic-repo'
XML_SRC = os.path.join(R, 'voice_watchdog_task.xml')
XML_16 = os.path.join(R, '_watchdog_task_utf16.xml')
TASK = 'SonicVoiceWatchdog590'
PY = sys.executable

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace')

print('XML_SRC_EXISTS=' + str(os.path.exists(XML_SRC)))

# 1) читаем XML как UTF-8 (то, что лежит на диске)
with open(XML_SRC, 'r', encoding='utf-8') as f:
    x = f.read()
print('XML_READ_LEN=' + str(len(x)))

# 2) перекодировка в UTF-16LE с BOM — ровно то, что умеет schtasks
open(XML_16, 'w', encoding='utf-16').write(x)
print('XML_16_WRITTEN=' + str(os.path.exists(XML_16)))

# 3) регистрация
r = sh('schtasks', '/Create', '/TN', TASK, '/XML', XML_16, '/F')
print('CREATE_RC=' + str(r.returncode))
print('CREATE_OUT=' + (r.stdout + r.stderr).strip()[:400])

# 4) подтверждение
q = sh('schtasks', '/Query', '/TN', TASK, '/V', '/FO', 'LIST')
print('QUERY_RC=' + str(q.returncode))
if q.returncode == 0:
    for ln in q.stdout.splitlines():
        t = ln.strip()
        if t.lower().startswith(('taskname', 'задача', 'task to run', 'действие', 'status', 'статус', 'schedule', 'расписание')):
            print('Q> ' + t[:150])
else:
    print('QUERY_OUT=' + (q.stdout + q.stderr).strip()[:300])

# 5) чистим временный файл
try:
    os.remove(XML_16)
except OSError:
    pass
print('DONE')
