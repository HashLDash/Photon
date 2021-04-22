#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photon installer script

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# INIT run_in_unix()
def run_in_unix(code):
    # INIT TCHAN
    try:
        with open('/usr/local/bin/photon', 'w') as w:
            w.write(code)
        os.chmod('/usr/local/bin/photon', 0o777)
        print("Successfully installed!")
    except PermissionError:
        print(
            " Please run this script with the `sudo` command.\n",
            "Example:\n `sudo python3 install.py`"
        )
        exit()
    # END TCHAN

# END run_in_unix()

# INIT run_in_win_nt()
def  run_in_win_nt(code):
    # INIT TCHAN
    p_dir = os.path.expandvars('%ProgramFiles%\\Photon')
    try:
        if not os.path.exists(p_dir):
            os.mkdir(p_dir)
        with open(os.path.join(p_dir, 'photon.py'), 'w') as w:
            w.write(code)
        with open(os.path.join(p_dir, 'photon.bat'), 'w') as w:
            w.write('@echo off\nset bat_dir=%~dp0\npython "%bat_dir%photon.py"')
        os.system(f'setx /M PATH "%PATH%;{p_dir}"')
    except PermissionError:
        exit('The installation has not been completed. Try to run the script as administrator')
    # END TCHAN

    # INIT MATHEUS
    if str(os.popen("powershell; exit").read()) == "":
        #print("# PowerShell detectado")
        pass
    else:
        exit("# Você não possui o PowerShell instalado")

    print("-" * 53)
    print("#" + bcolors.OKBLUE + "                     PHOTON                        " + bcolors.ENDC + "#")
    print("-" * 53)
    print("# Olá, seja bem vindo ao instalador de dependências #")
    print("#" + bcolors.OKGREEN + " Digite (S) para (Sim) ou (N) para (Não)           " + bcolors.ENDC + "#")

    print("-" * 53)
    print("# Dependências a serem instaladas " + bcolors.WARNING + "MinGW (GCC)," + bcolors.ENDC + "      #")
    print("# " + bcolors.WARNING + "DMD (D lang), Haxe, Node.js, Dart-SDK e Python"  + bcolors.ENDC + "    #")
    all_depen = input("# Instalar todas as dependências? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)
    print("-" * 53)
    if all_depen.upper() == "S":
        mingw = python = haxe = nodejs = dart = dmd = "S"
    else:
        mingw = input("# Deseja instalar o MinGW (GCC)? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)    
        haxe = input("# Deseja instalar o Haxe? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)
        nodejs = input("# Deseja instalar o Node.js? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)
        dart = input("# Deseja instalar o Dart-SDK? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)
        dmd = input("# Deseja instalar o DMD (D lang)? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)
        # python = input("# Deseja instalar o Python? " + bcolors.OKGREEN + "S|N: " + bcolors.ENDC)
        print("-" * 53)

    depen = ""

    if mingw.upper() == "S":
        depen += " mingw"
    if haxe.upper() == "S":
        depen += " haxe"
    if nodejs.upper() == "S":
        depen += " nodejs"
    if dart.upper() == "S":
        depen += " dart-sdk"
    if dmd.upper() == "S":
        depen += " dmd"
    if python.upper() == "S":
        depen += " python"

    if depen != "":
        depen = "choco install -y" + depen
    else:
        exit()

    shell_exec_cmd = "powershell -Command \"Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \\\"/c Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); ; timeout /t 15; exit\\\"\""
    print("# Instalando o Chocolatey - Comando: \r\n")
    print(shell_exec_cmd + "\r\n")
    print("# Resultado:")
    print(str(os.popen(shell_exec_cmd).read()))

    print("-" * 53)

    print("# Versão do Chocolatey instalado - Comando: \r\n")
    shell_exec_cmd = "choco --version"
    print(shell_exec_cmd + "\r\n")
    print("# Resultado:")
    print(str(os.popen(shell_exec_cmd).read()))

    print("-" * 53)

    shell_exec_cmd = "powershell -Command \"Start-Process powershell -Verb RunAs -PassThru -Wait -ArgumentList \\\"/c " + depen + "; timeout /t 15; exit\\\"\""
    print("# Instalando dependências com o Chocolatey - Comando: \r\n")
    print(shell_exec_cmd + "\r\n")
    print("# Resultado:")
    print(str(os.popen(shell_exec_cmd).read()))

    print("-" * 53)
    # END MATHEUS

# END run_in_win_nt()

try:

    import os
    import sys
    import ctypes

    def is_admin():
        try:
            return (os.getuid() == 0)
        except:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin():
        exit("Try to run the script as administrator")

    with open('core/photon.py') as w:
        code = w.read()

    if code == None or code == "":
        exit("Falha ao abrir `core/photon.py`")

    code = code.replace('@PHOTON_INSTALL_PATH', f'r"{os.getcwd()}/core"')

    if sys.platform in {'linux', 'linux2', 'darwin'}:
        run_in_unix(code)
    elif os.name == "nt" or os.environ.get('OS', '') != 'Windows_NT' or sys.platform in {'win32', 'cygwin', 'msys'}:
        run_in_win_nt(code)
    else:
        print('Automatic installation in this system is not supported yet.')

except Exception as e:
    print("error", e)
