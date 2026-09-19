import os, sys, subprocess, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
R = r'F:\Pill\tmp\opencode\sonic-repo'
PYEXE = r'C:\Python314\python.exe'
wd = os.path.join(R, 'voice_watchdog.py')
vbs = os.path.join(R, 'voice_watchdog.vbs')
xml = os.path.join(R, 'voice_watchdog_task.xml')
print('WD_EXISTS=' + str(os.path.exists(wd)))
print('VBS_EXISTS=' + str(os.path.exists(vbs)))
print('XML_EXISTS=' + str(os.path.exists(xml)))
if os.path.exists(wd):
    r = subprocess.run([PYEXE, '-m', 'py_compile', wd], capture_output=True, text=True)
    print('WD_PYCOMPILE_RC=' + str(r.returncode))
if os.path.exists(xml):
    with open(xml, 'rb') as f:
        head = f.read(4)
    print('XML_BOM=' + ('UTF16-LE' if head[:2] == b'\xff\xfe' else ('UTF16-BE' if head[:2] == b'\xfe\xff' else 'NONE/UTF8')))
hb = os.path.join(R, 'state', 'heartbeat.txt')
print('HB_EXISTS=' + str(os.path.exists(hb)))
if os.path.exists(hb):
    print('HB_AGE_S=' + str(int(time.time() - os.path.getmtime(hb))))
q = subprocess.run(['schtasks', '/Query', '/TN', 'SonicVoiceWatchdog', '/V', '/FO', 'LIST'],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print('SCHTASKS_QUERY_RC=' + str(q.returncode))
print('TASK_STATUS_RAW_HEAD=' + (q.stdout.strip().splitlines()[0:6] if q.stdout.strip() else 'EMPTY'))
