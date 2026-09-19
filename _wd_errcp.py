# -*- coding: utf-8 -*-
import os, subprocess
R = r'F:\Pill\tmp\opencode\sonic-repo'
XML_16 = os.path.join(R, '_wd_task_utf16.xml')
TASK = 'SonicVoiceWatchdog590'
OUT = os.path.join(R, '_wd_errcp.txt')
p = subprocess.run(['schtasks', '/Create', '/TN', TASK, '/XML', XML_16, '/F'],
                   capture_output=True)
raw_out, raw_err = p.stdout, p.stderr
lines = ['RC=%d' % p.returncode, '']
for cp in ['cp866', 'cp1251', 'cp437', 'cp850', 'cp1252', 'utf-8', 'cp775']:
    try:
        o = raw_err.decode(cp, errors='replace')
    except Exception as e:
        o = 'ERR ' + repr(e)
    lines.append('=== stderr as %s ===' % cp)
    lines.append(o)
    lines.append('')
try:
    oo = raw_out.decode('cp866', errors='replace')
except Exception:
    oo = repr(raw_out)
lines.append('=== stdout as cp866 ===')
lines.append(oo)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('WD_ERRCP_DONE')
