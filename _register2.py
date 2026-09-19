import os, subprocess, sys
from pathlib import Path
R = Path(r"F:\Pill\tmp\opencode\sonic-repo")
LOG = R / "_wd_register2.log"
XML8 = R / "voice_watchdog_task.xml"
XML16 = R / "_wd_utf16le.xml"
L = []
def o(x): L.append(str(x))

src = XML8.read_text(encoding="utf-8", errors="replace")
XML16.write_text(src, encoding="utf-16")
o("UTF16_WRITTEN=" + str(XML16.exists()) + " BYTES=" + str(XML16.stat().st_size))

r = subprocess.run(
    ["schtasks", "/Create", "/TN", "SonicVoiceWatchdog", "/XML", str(XML16), "/F"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
o("CREATE_RC=" + str(r.returncode))
o("CREATE_OUT=" + (r.stdout + r.stderr).strip())

q = subprocess.run(
    ["schtasks", "/Query", "/TN", "SonicVoiceWatchdog", "/V", "/FO", "LIST"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
o("QUERY_RC=" + str(q.returncode))
o("QUERY_OUT=" + (q.stdout + q.stderr).strip())

LOG.write_text("\n".join(L) + "\n", encoding="utf-8")