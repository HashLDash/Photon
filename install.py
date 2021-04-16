#!/usr/bin/env python3

# Photon installer script

import os
import sys

with open('photon.py') as w:
    code = w.read()

code = code.replace('@PHOTON_INSTALL_PATH',f'"{os.getcwd()}/"')

if sys.platform in {'linux','darwin'}:
    with open('/usr/local/bin/photon','w') as w:
        w.write(code)

    os.chmod('/usr/local/bin/photon',0o777)
else:
    print('Automatic installation in this system is not supported yet.')
