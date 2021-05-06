# $ErrorActionPreference = "Stop"

$host.UI.RawUI.WindowTitle = "Windows Installer - Photon"

New-ItemProperty -Path HKLM:Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -PropertyType DWord -Value 0 -Force
Set-ItemProperty -Path HKLM:\Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -Value 0 -Force

Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
$env:Path = "$env:Path;$env:AllUsersProfile\chocolatey\bin"

if ((Get-Command "python.exe" -ErrorAction SilentlyContinue) -eq $null) 
{ 
   $dependencies = " python"
}
if ((Get-Command "gcc.exe" -ErrorAction SilentlyContinue) -eq $null) 
{ 
   $dependencies = "$dependencies mingw"
}
if ((Get-Command "git.exe" -ErrorAction SilentlyContinue) -eq $null) 
{ 
   $dependencies = "$dependencies git"
}

if (Get-Variable 'dependencies' -ErrorAction 'Ignore') {
  choco install $dependencies
}

pip install pyreadline

$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition
python "$scriptPath\install.py"

Pause