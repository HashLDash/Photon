#!/bin/bash
red='\033[0;31m'
green='\033[0;32m'
normal='\033[0m'

printf "${green}Linux Installer - Photon${normal}\n"


SUDO=''
if [ $(id -u) -ne 0 ] ; then
    SUDO='sudo'
fi


if [ -f '/etc/debian_version' ]; then
    $SUDO apt update && $SUDO apt install python3 build-essential git
elif [ -f '/etc/arch-release' ]; then
    $SUDO pacman -Syy python gcc git glibc
elif [ -f '/etc/gentoo-release' ]; then
    $SUDO emerge --sync && $SUDO emerge dev-lang/python sys-devel/gcc dev-vcs/git
elif [ -f '/etc/SuSE-release' ]; then
    $SUDO zypper refresh && $SUDO zypper install python3 gcc git
elif [ -f '/etc/redhat-release' ]; then
    ($SUDO dnf check-update && $SUDO dnf install python3 gcc git) ||
    ($SUDO yum check-update && $SUDO yum install python3 gcc git)
else
    printf "${red}Automatic installation in this system is not supported yet.\n${normal}"
    exit 1
fi

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

if command -v python3; then
    $SUDO python3 "$SCRIPTPATH/install.py"
elif command -v python; then
    $SUDO python "$SCRIPTPATH/install.py"
else
    printf "${red}Was not possible to install Python >= 3.6, please do it manually\n${normal}"
    exit 1
fi

