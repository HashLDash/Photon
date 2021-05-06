@ECHO OFF

SET mydir=%~dp0
powershell -command "Start-Process powershell -Verb RunAs -PassThru -ArgumentList \"-ExecutionPolicy RemoteSigned -NoProfile -File %mydir%\windowsInstaller.ps1\""
