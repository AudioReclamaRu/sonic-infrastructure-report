' bWait = False: wscript must stay alive for the whole run, otherwise Task Scheduler
' marks the task Ready/0 within a second while python keeps working in the background
' and the ExecutionTimeLimit is applied to nothing. Waiting also lets cmd's exit code
' (the tool's own exit code) surface as LastTaskResult.
Set sh = CreateObject("WScript.Shell")
sh.Run "F:\Pill\tmp\opencode\sonic-repo\ops\run-missed-audit.cmd", 0, False
