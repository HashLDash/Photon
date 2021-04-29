powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); ; timeout /t 5; exit\""

powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c choco install python; timeout /t 5; exit\""

powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c choco install mingw; timeout /t 5; exit\""

powershell -Command "Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \"/c python %~dp0\install.py; timeout /t 5; exit\""

