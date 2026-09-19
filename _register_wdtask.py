import os, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R = r'F:\Pill\tmp\opencode\sonic-repo'
XML_UTF8 = os.path.join(R, 'voice_watchdog_task.xml')
XML_UTF16 = os.path.join(R, '_wdtask_utf16le.xml')
TASK = 'SonicVoiceWatchdog'

with open(XML_UTF8, 'r', encoding='utf-8') as f:
    text = f.read()

with open(XML_UTF16, 'w', encoding='utf-16-le') as f:
    f.write('\ufeff' + text)

print('XML_UTF16_WRITTEN=' + str(os.path.exists(XML_UTF16)))

def run(*a, **k):
    return subprocess.run(*a, **k, capture_output=True, text=True, encoding='utf-8', errors='replace')

r = run(['schtasks', '/Create', '/TN', TASK, '/XML', XML_UTF16, '/F'])
print('CREATE_RC=' + str(r.returncode))
print('CREATE_OUT=' + (r.stdout + r.stderr).strip()[:300])

q = run(['schtasks', '/Query', '/TN', TASK, '/V', '/FO', 'LIST'])
print('QUERY_RC=' + str(q.returncode))
if q.returncode == 0:
    for ln in q.stdout.splitlines():
        ln = ln.strip()
        if ln.startswith(('Задача', 'TaskName', 'Task To Run', 'Действие', 'Статус', 'Status', 'Состояние')):
            print('Q> ' + ln[:120])
else:
    print('QUERY_OUT=' + (q.stdout + q.stderr).strip()[:300])

os.remove(XML_UTF16)
print('REPORT_QS_DONE')
