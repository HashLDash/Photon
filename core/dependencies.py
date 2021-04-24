# Install all dependencies for running projects with the
# corresponding language on the target platform

import os
import sys

def haveDependencies(lang, platform):
    ''' Return True if all dependencies are installed
        for the corresponding lang and platform or
        False otherwise. '''
    for dep in deps[(lang, platform)]:
        if not programIsInstalled(dep):
            break
    else:
        return True
    return False

def resolveDependencies(lang, platform):
    global solver
    ''' Run the corresponding dependency solver '''
    solver[(lang, platform)]()
    #TODO: Check if the installation was successful
    # or print the error message and terminate the program

# Obtains a simple description of the current operating system platform
def getSystem():
    if sys.platform in {'linux', 'linux2', 'darwin'}:
        return "unix"
    elif os.name == "nt" or os.environ.get('OS', '') != 'Windows_NT' or sys.platform in {'win32', 'cygwin', 'msys'}:
        return "win"
    return None 

# Verify if program is installed it system
def programIsInstalled(name):
    try:
        platform_os = getSystem()
        if platform_os == "win":
            return str(os.popen(f'where /q {name} && echo %ERRORLEVEL%').read()).strip() == "0"
        elif platform_os == "unix": 
            return str(os.popen(f'which {name}').read()).strip() != ""
        else:
            raise Exception('`platform_os` not supported')
    except Exception as e:
        print(f"error: {e}")
        return False

# INIT - Chocolatey to Windows
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
    shell_exec_cmd = "powershell -Command \"Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \\\"/c " + name + "; timeout /t 5; exit\\\"\""
    print('# Installing dependency with Chocolatey - Command: \r\n')
    print(f'{shell_exec_cmd}\r\n')
    print('# Result:')
    print(str(os.popen(shell_exec_cmd).read()))
    return True

def printResultPostChocoInstaller(name):
    if programIsInstalled(name):
        print(f'Dependency `{name}` has been successfully installed!')
        return True
    else:
        print(f'Dependency `{name}` was not found.')
        return False
# END - Chocolatey to Windows

def resolveCLinux():
    ''' Install gcc '''
    pass

def resolveDLinux():
    ''' Install dmd '''
    pass

def resolveHaxeLinux():
    ''' Install haxe '''
    pass

def resolveJsLinux():
    ''' Install nodejs '''
    pass

def resolveDartLinux():
    ''' Install dart '''
    pass

def resolveCWin32():
    ''' Install gcc '''
    chocoInstaller("mingw")
    return printResultPostChocoInstaller("gcc")

def resolveDWin32():
    ''' Install dmd '''
    chocoInstaller("dmd")
    return printResultPostChocoInstaller("dmd")

def resolveHaxeWin32():
    ''' Install haxe '''
    chocoInstaller("haxe")
    return printResultPostChocoInstaller("haxe")

def resolveJsWin32():
    ''' Install nodejs '''
    chocoInstaller("nodejs")
    return printResultPostChocoInstaller("node")

def resolveDartWin32():
    ''' Install dart '''
    chocoInstaller("dart-sdk")
    return printResultPostChocoInstaller("dart")

def resolveCDarwin():
    ''' Install gcc '''
    pass

def resolveDDarwin():
    ''' Install dmd '''
    pass

def resolveHaxeDarwin():
    ''' Install haxe '''
    pass

def resolveJsDarwin():
    ''' Install nodejs '''
    pass

def resolveDartDarwin():
    ''' Install dart '''
    pass

solver = {
    ('c', 'linux'): resolveCLinux,
    ('c', 'win32'): resolveCWin32,
    ('c', 'darwin'): resolveCDarwin,
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
    ('d', 'linux'): ['dmd'],
    ('d', 'win32'): ['dmd'],
    ('d', 'darwin'): ['dmd'],
    ('haxe', 'linux'): ['haxe'],
    ('haxe', 'win32'): ['haxe']
    ('haxe', 'darwin'): ['haxe'],
    ('js', 'linux'): ['node'],
    ('js', 'win32'): ['node'],
    ('js', 'darwin'): ['node'],
    ('dart', 'linux'): ['dart'],
    ('dart', 'win32'): ['dart'],
    ('dart', 'darwin'): ['dart],
}
