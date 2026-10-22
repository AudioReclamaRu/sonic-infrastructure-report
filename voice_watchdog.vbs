' voice_watchdog.vbs — скрытый (hidden) запуск desktop-сторожа ГОЛОС.
' Паттерн §8.9 (wscript.exe + uac-обёртка, НЕ голый powershell в Task Scheduler):
'   sh.Run "<cmd>", 0, False  -> окно консоли НЕ показывается даже при LogonType=Interactive.
' Ссылается на ТОТ ЖЕ python.exe и ТОТ ЖЕ voice_watchdog.py, что сторож.
Option Explicit
Dim sh
Set sh = CreateObject("WScript.Shell")
sh.Run "C:\Python314\python.exe F:\Pill\tmp\opencode\sonic-repo\voice_watchdog.py", 0, False
Set sh = Nothing