import os, subprocess, sys, time
from pathlib import Path

R = Path(r"F:\Pill\tmp\opencode\sonic-repo")
XML8 = R / "voice_watchdog_task.xml"
XML16 = R / "_wd_task_utf16le.xml"
LOG = R / "_wd_register_log.txt"
QLOG = R / "_wd_query_log.txt"
TASK = "SonicVoiceWatchdog"
PY = sys.executable

def w(path, text):
    Path(path).write_text(text, encoding="utf-8")

lines = []
def o(x):
    lines.append(str(x))

o("STEP1_READ_XML=" + str(XML8.exists()))
if XML8.exists():
    raw = XML8.read_bytes()
    o("XML_BYTES=" + str(len(raw)))
    txt = None
    bom = raw[:3]
    if bom == b"\xef\xbb\xbf":
        txt = raw[3:].decode("utf-8")
    elif raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        txt = raw.decode("utf-16")
    else:
        txt = raw.decode("utf-8")
    o("XML_HAS_BOM=" + str(bom == b"\xef\xbb\xbf"))
    # пишем UTF-16LE + BOM (ровно то, что нужно schtasks /XML)
    XML16.write_bytes(b"\xff\xfe" + txt.encode("utf-16le"))
    o("XML16_WRITTEN_BYTES=" + str(XML16.stat().st_size if XML16.exists() else -1))

r = subprocess.run(
    ["schtasks", "/Create", "/TN", TASK, "/XML", str(XML16), "/F"],
    capture_output=True, timeout=30,
)
o("SCHTASKS_CREATE_RC=" + str(r.returncode))
o("SCHTASKS_CREATE_OUT=" + (r.stdout + r.stderr).decode("utf-8", errors="replace").strip())
w(LOG, "\n".join(lines))

q = subprocess.run(
    ["schtasks", "/Query", "/TN", TASK, "/V", "/FO", "LIST"],
    capture_output=True, timeout=30,
)
ql = []
ql.append("SCHTASKS_QUERY_RC=" + str(q.returncode))
ql.append("SCHTASKS_QUERY_OUT=" + (q.stdout + q.stderr).decode("utf-8", errors="replace").strip())
w(QLOG, "\n".join(ql))

o("DONE")
w(LOG, "\n".join(lines))
print("LOG_WRITTEN=" + str(LOG.exists()) + " RC=" + str(r.returncode))
