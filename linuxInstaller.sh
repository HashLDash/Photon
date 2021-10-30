#!/bin/bash
red='\033[0;31m'
green='\033[0;32m'
normal='\033[0m'

printf "${green}Linux Installer - Photon${normal}\n"

printf "Checking Photon dependencies...\n"

installDeps="false";

if ! command -v gita &> /dev/null
then
    echo "git could not be found"
    installDeps="true";
else
    echo "You already have git installed."
fi
if ! command -v gcc &> /dev/null
then
    echo "gcc could not be found"
    installDeps="true";
else
    echo "You already have gcc installed."
fi
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found"
    installDeps="true";
else
    echo "You already have python3 installed."
fi

SUDO=''
if [ $(id -u) -ne 0 ] ; then
    SUDO='sudo'
fi
if [ "$installDeps" == "true" ]; then
    echo "Preparing to install dependencies..."


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
    elif [ "$(uname)" == "Darwin" ]; then
        $SUDO /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
        $SUDO brew install gcc git python3
    else
        printf "${red}Automatic installation in this system is not supported yet.\n${normal}"
        printf "Photon needs Python>=3.6, gcc and git on your PATH to work properly."
        exit 1
    fi
fi
echo "Dependencies installed. Installing Photon command-line interface..."

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

