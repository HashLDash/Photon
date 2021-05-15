#!/usr/bin/env python3
''' Photon command-line interface. '''

def lang(defineLang = None):
    import os
    import json
    import pathlib
    home = pathlib.Path.home()
    if not '.photon' in os.listdir(home):
        os.mkdir(f'{home}/.photon')
    if 'photon.conf' in os.listdir(f'{home}/.photon'):
        with open(f'{home}/.photon/photon.conf', 'r') as conf:
            defaultConfig = json.load(conf)
    else:
        defaultConfig = {}
        defineLang = 'c'
    if defineLang != '' and defineLang != None:
        defaultConfig['lang'] = defineLang
        with open(f'{home}/.photon/photon.conf', 'w') as conf:
            json.dump(defaultConfig, conf)
    return defaultConfig['lang']

if __name__ == "__main__":
    import sys
    import os
    langs = ['c', 'd', 'js', 'dart', 'haxe', 'py']
    PHOTON_INSTALL_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, PHOTON_INSTALL_PATH)
    from interpreter import Interpreter
    from builder import Builder
    from dependencies import haveDependencies, resolveDependencies
    __version__ = '0.0.1'
    try:
        first = sys.argv[1]
    except IndexError:
        print(f'Photon - {__version__} - pyEngine')
        Interpreter().run()
        sys.exit()
    if first == '--version' or first == '-v' :
        print(f'Photon Version {__version__}')
    elif first == '--build' or first == '-b':
        try:
            Builder(platform = sys.argv[2], standardLibs = os.path.join(PHOTON_INSTALL_PATH, 'libs/'))
        except IndexError:
            print('Welcome to Photon builder!')
            print('')
            print('Usage:')
            print('  photon --build [platform]')
            print('Available platforms: web, linux, flutter-android')
    elif first == '--lang' or first == '-l':
        command = ' '.join(sys.argv[2:])    
        command = command.lower()
        if command in langs:
            command = lang(command)
            print(f'Setting default lang to: {command.upper()}')
            if not haveDependencies(command, sys.platform):
                resolveDependencies(command, sys.platform)
                print('Dependencies successfuly installed.')
        elif command == '':
            command = lang()
            index = langs.index(command)
            langs[index] = f'({langs[index].upper()})'
            print(f'List of languages: {(", ".join(langs))}')
            print('-' * 49)
            print(f'The current language is: {command.upper()}')
        else:
            print(f'ERROR: It was not possible to select the language ({command.upper()}).')
    elif first == '--help' or first == '-h':
        print('Available commands:')
        print('    photon [file.w] Runs the script using the default lang')
        print('    photon --build [platform] Builds and runs the project for the target platform')
        print('    photon --lang Lists available languages')
        print(f'    photon --lang [{(", ".join(langs))}] Sets the default language')
        print('    photon --version Shows the the current version')
    elif first == '--update' or first == '-u':
        os.system(f'git -C {PHOTON_INSTALL_PATH} pull')
    elif first == '--android-logcat' or first == '-al':
        try:
            packageName = sys.argv[2]
            os.system(f"adb shell 'logcat --pid=$(pidof -s {packageName})'")
        except IndexError:
            print('Please provide the package name. Ex:\n    photon logcat com.photon.example')
    elif first == '--android-view' or first == '-av':
        os.system('adb exec-out screenrecord --output-format=h264 - | ffplay -framerate 60 -probesize 32 -sync video  -')
    else:
        Interpreter(filename = first, lang = lang(), standardLibs = os.path.join(PHOTON_INSTALL_PATH, 'libs/')).run()
