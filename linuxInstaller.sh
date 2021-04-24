#!/bin/bash
green='\033[0;32m'
normal='\033[0m'
DISTRO=$(grep '^NAME' /etc/os-release | cut -d'"' -f 2)
if [ "$DISTRO" = "Arch Linux" ]; then
    printf "${green}Let's install photon depencies. We need your permission to continue.\n${normal}"
    sudo pacman -S python nodejs haxe dmd gcc dart && sudo python3 install.py
fi

# TODO: implement for other distros
