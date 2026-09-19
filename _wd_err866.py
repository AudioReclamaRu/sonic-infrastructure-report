# -*- coding: utf-8 -*-
import os, subprocess
R = r'F:\Pill\tmp\opencode\sonic-repo'
XML_16 = os.path.join(R, '_wd_task_utf16.xml')
TASK = 'SonicVoiceWatchdog590'
LOG = os.path.join(R, '_wd_err866.txt')
p = subprocess.run(['schtasks', '/Create', '/TN', TASK, '/XML', XML_16, '/F'],
                   capture_output=True)
out = p.stdout.decode('cp866', errors='replace')
err = p.stderr.decode('cp866', errors='replace')
with open(LOG, 'w', encoding='utf-8') as f:
    f.write('RC=%d\nSTDOUT:\n%s\nSTDERR:\n%s\n' % (p.returncode, out, err))
print('ERR866_DONE')
