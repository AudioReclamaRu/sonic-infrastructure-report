@echo off
REM run-cycle-planner.cmd - daily horizon plan (7-14 days) + circuit-breaker tasks
REM for the Culture of Voice cycle. Kept as a .cmd so %ERRORLEVEL% is expanded per
REM line and the tool's own exit code reaches Task Scheduler verbatim.
setlocal
set OPENBLAS_NUM_THREADS=1
set LOG=F:\Pill\tmp\opencode\sonic-repo\state\cycle_planner.task.log
echo ==== %DATE% %TIME% ==== >> %LOG%
C:\Python314\python.exe F:\Pill\tmp\opencode\sonic-repo\tools\cycle_planner.py >> %LOG% 2>&1
echo EXITCODE=%ERRORLEVEL% >> %LOG%
exit /b %ERRORLEVEL%
