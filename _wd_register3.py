# -*- coding: utf-8 -*-
"""Регистрация Scheduled Task SonicVoiceWatchdog590.
Все выводы schtasks декодируются как bytes OEM->UTF-8 и пишутся в UTF-8 лог.
Никакой кириллицы в консоль."""
import os, subprocess, datetime, locale

R = r'F:\Pill\tmp\opencode\sonic-repo'
XML_SRC = os.path.join(R, 'voice_watchdog_task.xml')
XML_16 = os.path.join(R, '_wd_task_utf16.xml')
LOG = os.path.join(R, '_wd_register3.log')
TASK = 'SonicVoiceWatchdog590'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(datetime.datetime.now().strftime('%H:%M:%S') + ' ' + msg + '\n')

def sch(*a):
    cp = locale.getpreferredencoding(False) or 'cp866'
    p = subprocess.run(a, capture_output=True)
    out = p.stdout.decode(cp, errors='replace').encode('utf-8', errors='replace').decode('utf-8')
    err = p.stderr.decode(cp, errors='replace').encode('utf-8', errors='replace').decode('utf-8')
    return p.returncode, out, err

def main():
    if os.path.exists(LOG):
        os.remove(LOG)
    log('START cp=' + locale.getpreferredencoding(False))
    log('XML_SRC_EXISTS=' + str(os.path.exists(XML_SRC)))
    with open(XML_SRC, 'r', encoding='utf-8') as f:
        x = f.read()
    log('XML_READ_LEN=' + str(len(x)))
    # UTF-16LE + BOM ровно как требует schtasks
    data = x.encode('utf-16')  # python utf-16 = LE + BOM
    with open(XML_16, 'wb') as f:
        f.write(data)
    log('XML_16_WRITTEN=' + str(os.path.exists(XML_16)) + ' BYTES=' + str(len(data)) + ' BOM=' + hex(data[0]) + hex(data[1]))

    rc, out, err = sch('schtasks', '/Create', '/TN', TASK, '/XML', XML_16, '/F')
    log('CREATE_RC=' + str(rc))
    log('CREATE_STDOUT=' + out.replace('\n', ' | ')[:800])
    log('CREATE_STDERR=' + err.replace('\n', ' | ')[:800])

    if rc == 0:
        rc2, out2, err2 = sch('schtasks', '/Query', '/TN', TASK, '/V', '/FO', 'LIST')
        log('QUERY_RC=' + str(rc2))
        log('QUERY_STDOUT=' + out2.replace('\n', ' | ')[:1500])
        if rc2 != 0:
            log('QUERY_STDERR=' + err2.replace('\n', ' | ')[:500])
    else:
        log('SKIP_QUERY (create failed)')

    log('DONE')
    print('RONLYOK_WD3_DONE')

if __name__ == '__main__':
    main()
