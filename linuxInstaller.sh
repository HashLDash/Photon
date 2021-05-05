#!/bin/bash
red='\033[0;31m'
green='\033[0;32m'
normal='\033[0m'

printf "${green}Linux Installer - Photon${normal}\n"

if [ -f '/etc/debian_version' ]; then
    sudo apt-get update && sudo apt-get install python3 build-essential git
elif [ -f '/etc/arch-release' ]; then
    sudo pacman -Syy python gcc git glibc
elif [ -f '/etc/gentoo-release' ]; then
    sudo emerge --sync && sudo emerge dev-lang/python sys-devel/gcc dev-vcs/git
elif [ -f '/etc/SuSE-release' ]; then
    sudo zypper refresh && sudo zypper install python3 gcc git
elif [ -f '/etc/redhat-release' ]; then
    (sudo dnf check-update && sudo dnf install python3 gcc git) ||
    (sudo yum check-update && sudo yum install python3 gcc git)
else
    printf "${red}Automatic installation in this system is not supported yet.\n${normal}"
    exit 1
fi

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

if command -v python3; then
    sudo python3 "$SCRIPTPATH/install.py"
elif command -v python; then
    sudo python "$SCRIPTPATH/install.py"
else
    printf "${red}Was not possible to install Python >= 3.6, please do it manually\n${normal}"
    exit 1
fi

