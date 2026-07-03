@echo off
REM Cross-shell launcher: works from cmd, Git Bash, or PowerShell.
REM Invokes the PowerShell start script with an execution-policy bypass so it
REM never fails on the default policy in the VS Code terminal.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-backend.ps1" %*
