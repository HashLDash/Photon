import os

local = '/usr/local/bin/photon'

try:
    if os.path.isfile(local):
        print(f'Removing the file {local}.')
        os.remove(local)
        print('Successfully removed!')

    else:
        print("It has nothing to be removed!")
except PermissionError:
    print(
        " Please run this script with the 'sudo' command\n",
        "Example:\n   'sudo python3 uninstall.py'")
