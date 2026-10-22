Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""F:\Pill\tmp\opencode\sonic-repo\tools\signal-scan.ps1""", 0, False
