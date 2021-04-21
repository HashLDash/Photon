#!/usr/bin/env python3

# Photon installer script

import os
import sys

with open('core/photon.py') as w:
    code = w.read()

code = code.replace('@PHOTON_INSTALL_PATH',f'"{os.getcwd()}/core"')

if sys.platform in {'linux','darwin'}:
    try:
        with open('/usr/local/bin/photon','w') as w:
            w.write(code)

        os.chmod('/usr/local/bin/photon',0o777)
        print("Successfully installed!")
    except PermissionError:

        print(
        " Please run this script with the 'sudo' command.\n",
        "Example:\n    'sudo python3 install.py'")
else:
    print('Automatic installation in this system is not supported yet.')
