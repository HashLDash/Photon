#!/usr/bin/env python3

# Photon installer script

import os
import sys
from core.dependencies import haveDependencies, resolveDependencies

try:
    import ctypes
    haveCtypes = True
except ModuleNotFoundError:
    # Probably on raspberrypy
    haveCtypes = False

# Obtains a simple description of the current operating system platform
def getSystem():
    if sys.platform in {'linux', 'linux2', 'darwin'}:
        return "unix"
    elif os.name == "nt" or os.environ.get('OS', '') != 'Windows_NT' or sys.platform in {'win32', 'cygwin', 'msys'}:
        return "win"
    return None

# Returns if the script is being run as an administrator (ROOT)
def isAdmin():
    try:
        platform_os = getSystem()
        if platform_os == "unix":
            return os.getuid() == 0
        elif platform_os == "win":
            return ctypes.windll.shell32.IsUserAnAdmin()
        return False
    except:
        return False

platform_os = getSystem()

if haveCtypes and not isAdmin() and platform_os == "win":
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    except:
        pass

with open(f'{os.path.dirname(__file__)}/core/photon.py') as w:
    code = w.read()

code = code.replace('PHOTON_INSTALL_PATH =', f'PHOTON_INSTALL_PATH = r"{os.path.dirname(__file__)}/core" #')

if platform_os == "unix":
    try:
        with open('/usr/local/bin/photon', 'w') as w:
            w.write(code)
        os.chmod('/usr/local/bin/photon', 0o777)
        print("Successfully installed! Now you can use the photon command!")
        input('Press enter to close and play with Photon!')
    except PermissionError:
        print(
        " Please run this script with the 'sudo' command.\n",
        "Example:\n    'sudo python3 install.py'")
        input('Press enter to close.')
elif platform_os == "win":
    p_dir = os.path.expandvars('%ProgramFiles%\\Photon')
    try:
        if not os.path.exists(p_dir):
            os.mkdir(p_dir)
        with open(os.path.join(p_dir, 'photon.py'), 'w') as w:
            w.write(code)
        with open(os.path.join(p_dir, 'photon.bat'), 'w') as w:
            w.write('@echo off\nset bat_dir=%~dp0\npython "%bat_dir%photon.py" "%1" "%2" "%3"')
        os.system(f'setx /M PATH "%PATH%;{p_dir}"')
        print("Successfully installed! Now you can use the photon command!")
    except PermissionError:
        print('The installation has not been completed. Try to run the script as administrator')
else:
    print('Automatic installation in this system is not supported yet. Press enter to close.')
    input()
    sys.exit()

if not haveDependencies('c', sys.platform):
    resolveDependencies('c', sys.platform)
