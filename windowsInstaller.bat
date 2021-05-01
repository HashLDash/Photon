@echo off
title Windows Installer - Photon
cls
echo.
IF EXIST %SYSTEMROOT%\SYSTEM32\WDI\LOGFILES GOTO GOTADMIN
color 0f
echo Commands for running with normal privileges
set mydir=%~dp0
powershell -Command "Start-Process \"%mydir%windowsInstaller.bat\" -Verb RunAs"
msg /TIME 5 * Await Windows Installer of Photon!
timeout /t 5
exit

:GOTADMIN
color 1f
echo Commands for running with admin privileges
powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c New-ItemProperty -Path HKLM:Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -PropertyType DWord -Value 0 -Force; Set-ItemProperty -Path HKLM:\Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -Value 0 -Force; timeout /t 5; exit\""
powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); ; timeout /t 5; exit\""
powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c choco install python mingw git -y; timeout /t 5; exit\""
powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c python '%~dp0/install.py'; timeout /t 5; exit\""
timeout /t 5
exit
