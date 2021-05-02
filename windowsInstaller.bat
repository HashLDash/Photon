@ECHO OFF
TITLE Windows Installer - Photon
CLS
ECHO.
IF EXIST %SYSTEMROOT%\SYSTEM32\WDI\LOGFILES GOTO GT_ADMIN
COLOR 0F
ECHO Commands for running with normal privileges
SET mydir=%~dp0
POWERSHELL -COMMAND "Start-Process \"%mydir%windowsInstaller.bat\" -Verb RunAs"
TIMEOUT /T 3 /NOBREAK
EXIT

:GT_ADMIN
COLOR 1F
ECHO Commands for running with admin privileges
MSG /TIME 3 * Await Windows Installer of Photon! (Part 1)
POWERSHELL -COMMAND "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c New-ItemProperty -Path HKLM:Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -PropertyType DWord -Value 0 -Force; Set-ItemProperty -Path HKLM:\Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -Value 0 -Force; timeout /t 3; exit\""
MSG /TIME 3 * Await Windows Installer of Photon! (Part 2)
POWERSHELL -COMMAND "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); ; timeout /t 3; exit\""
MSG /TIME 3 * Await Windows Installer of Photon! (Part 3)
POWERSHELL -COMMAND "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c choco install python mingw git -y; timeout /t 3; exit\""
MSG /TIME 3 * Await Windows Installer of Photon! (Part 4)
POWERSHELL -COMMAND "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c python '%~dp0/install.py'; timeout /t 3; exit\""
MSG /TIME 3 * Photon successfully installed!
TIMEOUT /T 3 /NOBREAK
EXIT
