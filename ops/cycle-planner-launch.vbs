' cycle-planner-launch.vbs - run the planner before editorial_queue (09:45 vs 09:55)
' so the daily queue renders section 6 (plan + tasks) from a same-day report.
' bWait = True: wscript stays alive for the whole run, so Task Scheduler keeps the
' task Running (ExecutionTimeLimit actually bounds python) and the cmd's exit code
' surfaces as LastTaskResult.
Set sh = CreateObject("WScript.Shell")
sh.Run "F:\Pill\tmp\opencode\sonic-repo\ops\run-cycle-planner.cmd", 0, True
