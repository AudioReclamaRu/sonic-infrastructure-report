Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""F:\Pill\tmp\opencode\sonic-repo\post-orchestrator.ps1""", 0, False
