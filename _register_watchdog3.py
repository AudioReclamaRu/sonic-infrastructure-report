# -*- coding: utf-8 -*-
"""Регистрация Scheduled Task SonicVoiceWatchdog590.
Вывод schtasks пишем в UTF-8 лог (не в консоль) -> никакого cp1251 mojibake."""
import os, subprocess, datetime, locale

R = r'F:\Pill\tmp\opencode\sonic-repo'
XML_SRC = os.path.join(R, 'voice_watchdog_task.xml')
XML_16 = os.path.join(R, '_wd_task_utf16.xml')
LOG = os.path.join(R, '_wd_register3.log')
TASK = 'SonicVoiceWatchdog590'

def now():
    return datetime.datetime.now().strftime('%H:%M:%S')

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(now() + ' ' + msg + '\n')

def sch(*args):
    cp = locale.getpreferredencoding(False) or 'cp866'
    try:
        p = subprocess.run(args, capture_output=True)
        def dec(b):
            return b.decode(cp, errors='replace')
        return p.returncode, dec(p.stdout).replace('\n', ' | '), dec(p.stderr).replace('\n', ' | ')
    except Exception as e:
        return -1, '', 'EXC ' + repr(e)

def main():
    try:
        if os.path.exists(LOG):
            os.remove(LOG)
        log('START cp=' + locale.getpreferredencoding(False))
        log('XML_SRC_EXISTS=' + str(os.path.exists(XML_SRC)))
        with open(XML_SRC, 'r', encoding='utf-8') as f:
            x = f.read()
        log('XML_READ_LEN=' + str(len(x)))
        data = x.encode('utf-16')
        with open(XML_16, 'wb') as f:
            f.write(data)
        log('XML_16_WRITTEN=' + str(os.path.exists(XML_16)) + ' BYTES=' + str(len(data)) + ' BOM=' + hex(data[0]) + hex(data[1]))
        rc, out, err = sch('schtasks', '/Create', '/TN', TASK, '/XML', XML_16, '/F')
        log('CREATE_RC=' + str(rc))
        log('CREATE_STDOUT=' + out[:800])
        log('CREATE_STDERR=' + err[:800])
        if rc == 0:
            rc2, out2, err2 = sch('schtasks', '/Query', '/TN', TASK, '/V', '/FO', 'LIST')
            log('QUERY_RC=' + str(rc2))
            log('QUERY_STDOUT=' + out2[:1500])
            if rc2 != 0:
                log('QUERY_STDERR=' + err2[:500])
        else:
            log('SKIP_QUERY (create failed)')
        log('DONE')
        print('WD_REGISTER3_DONE')
    except Exception as e:
        log('FATAL ' + repr(e))
        print('WD_REGISTER3_FATAL')

if __name__ == '__main__':
    main()
