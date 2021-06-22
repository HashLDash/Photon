# $ErrorActionPreference = "Stop"

$host.UI.RawUI.WindowTitle = "Windows Installer - Photon"

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) 
{
   echo "To install Photon, you need administrator privileges!"
   timeout /t 3
   exit
}

while ((Get-Command "choco.exe" -ErrorAction SilentlyContinue) -eq $null) 
{
   echo "Chocolatey was not found! Do you want to install it?"
   pause
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
   $env:Path = "$env:Path;$env:AllUsersProfile\chocolatey\bin"
}

$dependencies = ""
$show_dependencies = ""

if (((Get-Command "python.exe" -ErrorAction SilentlyContinue) -eq $null) -or ((Get-Item (Get-Command "python.exe").Path).length -eq 0))
{
   $dependencies = "python;"
   $show_dependencies = "python "
}

if ((Get-Command "gcc.exe" -ErrorAction SilentlyContinue) -eq $null)
{
   $dependencies = "${dependencies}mingw;"
   $show_dependencies = "${show_dependencies}mingw "
}

if ((Get-Command "git.exe" -ErrorAction SilentlyContinue) -eq $null)
{
   $dependencies = "${dependencies}git;"
   $show_dependencies = "${show_dependencies}git "
}

if ($dependencies -ne "")
{
   echo "To use Photon, you need to install the following programs: ${show_dependencies}"
   pause
   choco install -y "$dependencies"
} 
else 
{
   echo "The programs Photon needs are already installed!"
}

if ((Get-Command "python.exe" -ErrorAction SilentlyContinue) -ne $null) 
{
   python -m pip install pyreadline
   $scriptPath = split-path -parent $MyInvocation.MyCommand.Definition
   echo "Installing Photon . . ."
   python "${scriptPath}\install.py"
}
else
{
   echo "Python was not found!"
}

pause
