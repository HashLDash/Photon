''' Install all dependencies for running projects with
    the corresponding language on the target platform. '''

import os
import sys

UPDATED_REPO = False

def commandName(package):
    ''' Return the command line name of the given package '''
    if package == 'nodejs':
        return 'node'
    return package

def haveDependencies(lang, platform):
    ''' Return True if all dependencies are installed
        for the corresponding lang and platform or
        False otherwise. '''
    for dep in deps[(lang, platform)]:
        if not programIsInstalled(dep):
            break
    else:
        return True
    print('Some dependencies must be installed for this target language.')
    return False

def resolveDependencies(lang, platform):
    ''' Run the corresponding dependency solver. '''
    global solver    
    solver[(lang, platform)]()
    #TODO: Check if the installation was successful
    # or print the error message and terminate the program

def getSystem():
    ''' Obtains a simple description of the current operating system platform. '''
    if sys.platform in {'linux', 'linux2', 'darwin'}:
        return "unix"
    elif os.name == "nt" or os.environ.get('OS', '') != 'Windows_NT' or sys.platform in {'win32', 'cygwin', 'msys'}:
        return "win"
    return None

def programIsInstalled(name):
    ''' Verify if program is installed it system. '''
    try:
        platform_os = getSystem()
        if platform_os == "win":
            return str(os.popen(f'where /q {name} && echo %ERRORLEVEL%').read()).strip() == "0"
        elif platform_os == "unix":
            return str(os.popen(f'command -v {name}').read()).strip() != ""
        else:
            raise Exception('`platform_os` not supported')
    except Exception as e:
        print(f"error: {e}")
        return False

# INIT - Installer for Win32/Windows (Chocolatey)
def powershellIsInstalled():
    if programIsInstalled("powershell"):
        print("# PowerShell is installed!")
        return True
    else:
        print("# PowerShell was not found!")
        return False

def chocoIsInstalled():
    if programIsInstalled("choco"):
        print("# Chocolatey is installed!")
        return True
    else:
        print("# Chocolatey was not found!")
        return False

def chocoInstall():
    if not powershellIsInstalled():
        return False
    if chocoIsInstalled():
        return True
    shell_exec_cmd = "powershell -Command \"Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \\\"/c Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); ; timeout /t 5; exit\\\"\""
    print('# Installing Chocolatey - Command: \r\n')
    print(f'{shell_exec_cmd}\r\n')
    print('# Result:')
    print(str(os.popen(shell_exec_cmd).read()))
    return chocoIsInstalled()

def chocoInstaller(name):
    if not chocoInstall():
        return False
    shell_exec_cmd = "powershell -Command \"Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \\\"/c choco install " + name + "; timeout /t 5; exit\\\"\""
    print('# Installing dependency with Chocolatey - Command: \r\n')
    print(f'{shell_exec_cmd}\r\n')
    print('# Result:')
    print(str(os.popen(shell_exec_cmd).read()))
    return True

# INIT - Installer for Darwin/macOS (HomeBrew)

def brewInstall():
    if not programIsInstalled('bash'):
        return False
    if programIsInstalled('brew'):
        return True
    shell_exec_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    print('# Installing HomeBrew - Command: \r\n')
    print(f'{shell_exec_cmd}\r\n')
    print('# Result:')
    print(str(os.popen(shell_exec_cmd).read()))
    return brewIsInstalled()

def brewInstaller(name):
    shell_exec_cmd = ""
    if not brewInstall():
        return False
    if name == "dart":
        shell_exec_cmd = "brew tap dart-lang/dart; "
    shell_exec_cmd += f'brew install {name}'
    print('# Installing dependency with HomeBrew - Command: \r\n')
    print(f'{shell_exec_cmd}\r\n')
    print('# Result:')
    print(str(os.popen(shell_exec_cmd).read()))
    return True

# INIT - Installers for Linux (APT, PACMAN, EMERGE, ZYPPER and DNF)
linux_cmds = {'dmd': 'curl https://dlang.org/install.sh | bash -s || (mkdir -p ~/dlang && wget '
                     'https://dlang.org/install.sh -O ~/dlang/install.sh && chmod +x ~/dlang/install.sh && '
                     '~/dlang/install.sh)'}
linux_cmds['node prompt-sync'] = 'npm install prompt-sync -G'
if os.path.exists('/etc/debian_version'):  # debian, ubuntu, pop!_os, zorin os
    linux_cmds['before'] = 'sudo apt-get update'
    linux_cmds['gcc'] = 'sudo apt install build-essential'
    linux_cmds['dmd'] = 'sudo wget https://netcologne.dl.sourceforge.net/project/d-apt/files/d-apt.list -O ' \
                        '/etc/apt/sources.list.d/d-apt.list && sudo apt-get update --allow-insecure-repositories && ' \
                        'sudo apt-get -y --allow-unauthenticated install --reinstall d-apt-keyring && sudo apt-get ' \
                        'update && sudo apt install dmd-compiler dub libcurl3 libphobos2-79 libphobos2-dev '
    linux_cmds['haxe'] = 'sudo apt-get install haxe && mkdir ~/haxelib && haxelib setup ~/haxelib'
    linux_cmds['nodejs'] = 'sudo apt install nodejs'
    linux_cmds['dart'] = "sudo apt-get install apt-transport-https && sudo sh -c 'wget -qO- " \
                         "https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -' && sudo sh -c 'wget " \
                         "-qO- https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_stable.list > " \
                         "/etc/apt/sources.list.d/dart_stable.list' && sudo apt-get update && sudo apt-get install " \
                         "dart "
elif os.path.exists('/etc/arch-release'):  # arch, manjaro
    linux_cmds['before'] = 'sudo pacman -Syy'
    linux_cmds['gcc'] = 'sudo pacman -S gcc'
    linux_cmds['dmd'] = 'sudo pacman -S dmd'
    linux_cmds['haxe'] = 'sudo pacman -S haxe'
    linux_cmds['nodejs'] = 'sudo pacman -S nodejs'
    linux_cmds['npm'] = 'sudo pacman -S npm'
    linux_cmds['dart'] = 'sudo pacman -S dart'
elif os.path.exists('/etc/gentoo-release'):  # gentoo
    linux_cmds['before'] = 'sudo emerge --sync'
    linux_cmds['gcc'] = 'sudo emerge sys-devel/gcc'
    linux_cmds['dmd'] = 'sudo emerge app-portage/layman && sudo layman -f -a dlang && sudo emerge dev-lang/dmd'
    linux_cmds['nodejs'] = 'sudo emerge nodejs'
elif os.path.exists('/etc/SuSE-release'):  # opensuse
    linux_cmds['before'] = 'sudo zypper refresh'
    linux_cmds['gcc'] = 'sudo zypper install gcc'
    linux_cmds['haxe'] = 'sudo zypper install haxe && mkdir ~/haxelib && haxelib setup ~/haxelib'
    linux_cmds['nodejs'] = 'sudo zypper install nodejs4'
elif os.path.exists('/etc/redhat-release'):  # red hat, centos, fedora
    linux_cmds['before'] = 'sudo dnf check-update; sudo yum check-update'
    linux_cmds['gcc'] = 'sudo dnf install gcc || sudo yum install gcc'
    linux_cmds['haxe'] = '(sudo dnf install haxe || (sudo yum install epel-release; sudo yum install haxe)) && mkdir ' \
                         '~/haxelib && haxelib setup ~/haxelib'
    linux_cmds['nodejs'] = 'sudo dnf module install nodejs:12'

def linuxInstaller(package):
    global UPDATED_REPO
    if package in linux_cmds:
        if 'before' in linux_cmds and not UPDATED_REPO:
            os.system(f'sh -c "{linux_cmds["before"]}"')
            UPDATED_REPO = True

        shell_exec_cmd = f'sh -c "{linux_cmds[package]}"'
        print('# Installing dependency - Command: \r\n')
        print(f'{shell_exec_cmd}\r\n')
        print('# Result:')
        os.system(shell_exec_cmd)
    else:
        print(f"We couldn't try to automatically install `{package}`, please install it manually.")
        return False

    if programIsInstalled(commandName(package)):
        print(f'Dependency `{package}` has been successfully installed!')
        return True
    else:
        print(f'Dependency `{package}` was not found.')
        return False

# INIT - Linux
def resolveCLinux():
    ''' Install gcc '''
    return linuxInstaller('gcc')

def resolvePyLinux():
    ''' Install python '''
    return linuxInstaller('python')

def resolveDLinux():
    ''' Install dmd '''
    return linuxInstaller('dmd')

def resolveHaxeLinux():
    ''' Install haxe '''
    return linuxInstaller('haxe')

def resolveJsLinux():
    ''' Install nodejs and deps '''
    return linuxInstaller('nodejs') and linuxInstaller('npm') and linuxInstaller('node prompt-sync')

def resolveDartLinux():
    ''' Install dart '''
    return linuxInstaller('dart')

# INIT - Win32
def resolveCWin32():
    ''' Install gcc '''
    chocoInstaller("mingw")
    return programIsInstalled("gcc")

def resolvePyWin32():
    ''' Install python '''
    chocoInstaller("python")
    return programIsInstalled("python")

def resolveDWin32():
    ''' Install dmd '''
    chocoInstaller("dmd")
    return programIsInstalled("dmd")

def resolveHaxeWin32():
    ''' Install haxe '''
    chocoInstaller("haxe")
    return programIsInstalled("haxe")

def resolveJsWin32():
    ''' Install nodejs '''
    chocoInstaller("nodejs")
    chocoInstaller("npm")
    linuxInstaller("node prompt-sync")
    return programIsInstalled("node") and programIsInstalled("npm")

def resolveDartWin32():
    ''' Install dart '''
    chocoInstaller("dart-sdk")
    return programIsInstalled("dart")

# INIT - Darwin
def resolveCDarwin():
    ''' Install gcc '''
    brewInstaller("gcc")
    return programIsInstalled("gcc")

def resolvePyDarwin():
    ''' Install gcc '''
    brewInstaller("gcc")
    return programIsInstalled("gcc")

def resolveDDarwin():
    ''' Install dmd '''
    brewInstaller("dmd")
    return programIsInstalled("dmd")

def resolveHaxeDarwin():
    ''' Install haxe '''
    brewInstaller("haxe")
    return programIsInstalled("haxe")

def resolveJsDarwin():
    ''' Install nodejs '''
    brewInstaller("nodejs")
    brewInstaller("npm")
    linuxInstaller("node prompt-sync")
    return programIsInstalled("node") and programIsInstalled("npm")

def resolveDartDarwin():
    ''' Install dart '''
    brewInstaller("dart")
    return programIsInstalled("dart")

solver = {
    ('c', 'linux'): resolveCLinux,
    ('c', 'win32'): resolveCWin32,
    ('c', 'darwin'): resolveCDarwin,
    ('py', 'linux'): resolvePyLinux,
    ('py', 'win32'): resolvePyWin32,
    ('py', 'darwin'): resolvePyDarwin,
    ('d', 'linux'): resolveDLinux,
    ('d', 'win32'): resolveDWin32,
    ('d', 'darwin'): resolveDDarwin,
    ('haxe', 'linux'): resolveHaxeLinux,
    ('haxe', 'win32'): resolveHaxeWin32,
    ('haxe', 'darwin'): resolveHaxeDarwin,
    ('js', 'linux'): resolveJsLinux,
    ('js', 'win32'): resolveJsWin32,
    ('js', 'darwin'): resolveJsDarwin,
    ('dart', 'linux'): resolveDartLinux,
    ('dart', 'win32'): resolveDartWin32,
    ('dart', 'darwin'): resolveDartDarwin,
}

deps = {
    ('c', 'linux'): ['gcc'],
    ('c', 'win32'): ['gcc'],
    ('c', 'darwin'): ['gcc'],
    ('py', 'linux'): ['python'],
    ('py', 'win32'): ['python'],
    ('py', 'darwin'): ['python'],
    ('d', 'linux'): ['dmd'],
    ('d', 'win32'): ['dmd'],
    ('d', 'darwin'): ['dmd'],
    ('haxe', 'linux'): ['haxe'],
    ('haxe', 'win32'): ['haxe'],
    ('haxe', 'darwin'): ['haxe'],
    ('js', 'linux'): ['node','npm'],
    ('js', 'win32'): ['node','npm'],
    ('js', 'darwin'): ['node','npm'],
    ('dart', 'linux'): ['dart'],
    ('dart', 'win32'): ['dart'],
    ('dart', 'darwin'): ['dart'],
}
