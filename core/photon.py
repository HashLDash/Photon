#!/usr/bin/env python3
''' Photon command-line interface. '''

import os
import sys

def photonConfigLang(defineLang = None):
    import json
    import pathlib
    home = pathlib.Path.home()
    if not '.photon' in os.listdir(home):
        os.mkdir(f'{home}/.photon')
    if 'photon.conf' in os.listdir(f'{home}/.photon'):
        try:
            with open(f'{home}/.photon/photon.conf', 'r') as conf:
                defaultConfig = json.load(conf)
        except json.decoder.JSONDecodeError:
            print('Seems like your photon.conf is corrupted. Please fix it and try again.')
            exit(-1)
    else:
        defaultConfig = {}
        if defineLang != '' and defineLang != None:
            defineLang = 'c'
    if not os.path.isfile(f'{home}/.photon/photon.conf'):
        defineLang = 'c'
    if defineLang != '' and defineLang != None:
        defaultConfig['lang'] = defineLang
        with open(f'{home}/.photon/photon.conf', 'w') as conf:
            json.dump(defaultConfig, conf)
    return defaultConfig['lang']

if __name__ == "__main__":
    langs = ['c', 'd', 'js', 'ts', 'dart', 'haxe', 'py']
    platforms = ['web', 'linux', 'flutter-android']
    PHOTON_INSTALL_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, PHOTON_INSTALL_PATH)
    from interpreter import Interpreter
    from builder import Builder
    from dependencies import haveDependencies, resolveDependencies
    __version__ = '0.0.9'
    try:
        if '-d' in sys.argv:
            sys.argv.remove('-d')
            DEBUG = True
        elif '--debug' in sys.argv:
            sys.argv.remove('--debug')
            DEBUG = True
        else:
            DEBUG = False
        first = sys.argv[1]
    except IndexError:
        print(f'Photon - {__version__} - pyEngine')
        Interpreter(standardLibs = os.path.join(PHOTON_INSTALL_PATH, 'libs'), debug = DEBUG).run()
        sys.exit()
    if first == '--version' or first == '-v' :
        print(f'Photon Version {__version__}')
    elif first == '--build' or first == '-b':
        try:
            filename = "main.w"
            if "shared" != sys.argv[-1] and (sys.argv[-1][-2] + sys.argv[-1][-1]) == ".w":
                filename = sys.argv[-1]
            Builder(platform = sys.argv[2], filename = filename, standardLibs = os.path.join(PHOTON_INSTALL_PATH, 'libs'), debug = DEBUG)
        except IndexError:
            print(f'ERROR: Platform [{(", ".join(platforms))}] not informed.')
    elif first == '--lang' or first == '-l':
        command = ' '.join(sys.argv[2:])    
        command = command.lower()
        if command in langs:
            command = photonConfigLang(command)
            print(f'Setting default lang to: {command.upper()}')
            if not haveDependencies(command, sys.platform):
                resolveDependencies(command, sys.platform)
                print('Dependencies successfuly installed.')
        elif command == '':
            command = photonConfigLang()
            index = langs.index(command)
            langs[index] = f'({langs[index].upper()})'
            print(f'List of languages: {(", ".join(langs))}')
            print('-' * 49)
            print(f'The current language is: {command.upper()}')
        else:
            print(f'ERROR: It was not possible to select the language ({command.upper()}).')
    elif first == '--help' or first == '-h' or first == '-?':
        print('Available commands:\r\n')
        print('# Runs the script using the default lang')
        print('>> photon [file.w]\r\n')
        print('# Builds and runs the project for the target platform')
        print(f'>> photon --build [{(", ".join(platforms))}]')
        print(f'>> photon -b [{(", ".join(platforms))}]\r\n')
        print('# Lists available languages')
        print('>> photon --lang')
        print('>> photon -l\r\n')
        print('# Sets the default language')
        print(f'>> photon --lang [{(", ".join(langs))}]')
        print(f'>> photon -l [{(", ".join(langs))}]\r\n')
        print('# Shows the the current version')
        print('>> photon --version')
        print('>> photon -v\r\n')
        print('# Updates the version of Photon (Git is required)')
        print('>> photon --update')
        print('>> photon -u')
    elif first == '--update' or first == '-u':
        os.system(f'git -C {PHOTON_INSTALL_PATH} pull')
    elif first == '--android-logcat' or first == '-al':
        try:
            packageName = sys.argv[2]
            os.system(f"adb shell 'logcat --pid=$(pidof -s {packageName})'")
        except IndexError:
            print('Please provide the package name. Example:')
            print('>> photon --android-logcat com.photon.example')
            print('>> photon -al com.photon.example')
    elif first == '--android-view' or first == '-av':
        os.system('adb exec-out screenrecord --output-format=h264 - | ffplay -framerate 60 -probesize 32 -sync video  -')
    else:
        lang = photonConfigLang()
        """ Performs the transpilation process for the language provided;
            without changing the language defined in the photon.conf file
        """
        otherParams = sys.argv[2:]
        if len(otherParams) > 1 and \
            (otherParams[0] == '-l' or otherParams[0] == '--lang') and \
            (otherParams[1].lower() in langs):
            lang = otherParams[1].lower()
            if not haveDependencies(lang, sys.platform):
                resolveDependencies(lang, sys.platform)
                print('Dependencies successfuly installed.')
        Interpreter(filename = first, lang = lang, standardLibs = os.path.join(PHOTON_INSTALL_PATH, 'libs'), debug = DEBUG).run()
