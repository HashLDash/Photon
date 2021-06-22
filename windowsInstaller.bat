@echo off
title Windows Installer - Photon
set mydir=%~dp0
powershell -command "Start-Process powershell -Verb RunAs -PassThru -ArgumentList '-ExecutionPolicy RemoteSigned -NoProfile -File \"%mydir%\windowsInstaller.ps1\"'"
timeout /t 3
exit
