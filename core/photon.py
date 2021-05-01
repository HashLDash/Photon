#!/usr/bin/env python3

# Photon command-line interface

if __name__ == "__main__":
    import sys
    import os
    PHOTON_INSTALL_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, PHOTON_INSTALL_PATH)
    from interpreter import Interpreter
    from builder import Builder
    from dependencies import haveDependencies, resolveDependencies
    try:
        first = sys.argv[1]
    except IndexError:
        print('Interpreter mode not implemented yet. Please try executing a source file instead')
        print('Or try:')
        print('    photon --help')
        print('To see more options')
        sys.exit()
    if first == 'build':
        try:
            platform = sys.argv[2]
            Builder(platform, standardLibs=os.path.join(PHOTON_INSTALL_PATH, 'Libs/'))
        except IndexError:
            print('Welcome to Photon builder!')
            print('')
            print('Usage:')
            print('  photon build [platform]')
            print('Available platforms: web, linux, flutter-android')
    elif first == 'logcat':
        try:
            packageName = sys.argv[2]
            os.system(f"adb shell 'logcat --pid=$(pidof -s {packageName})'")
        except IndexError:
            print('Please provide the package name. Ex:\n    photon logcat com.photon.example')
    elif first == 'set':
        command = ' '.join(sys.argv[2:])
        import json
        import pathlib
        home = pathlib.Path.home()
        if not '.photon' in os.listdir(home):
            os.mkdir(f'{home}/.photon')
        if 'photon.conf' in os.listdir(f'{home}/.photon'):
            with open(f'{home}/.photon/photon.conf','r') as conf:
                defaultConfig = json.load(conf)
        else:
            defaultConfig = {}
        try:
            variable, value = command.split('=')
        except ValueError:
            # On Windows '=' is ignored on argv
            variable, value = sys.argv[2:]
        vairable, value = variable.strip(), value.strip()
        if variable in ['lang']:
            if value in ['c', 'd', 'dart', 'haxe', 'js']:
                print(f'Setting default lang to {value}')
                if not haveDependencies(value, sys.platform):
                    resolveDependencies(value, sys.platform)
                    print('Dependencies successfuly installed.')
                    exit()
                defaultConfig['lang'] = value
            else:
                print('Error: Invalid lang. Available langs are: c, d, dart, haxe and js')
        else:
            print('This setting is not available. Available parameters are:\n    defaultLang')
        with open(f'{home}/.photon/photon.conf','w') as conf:
            json.dump(defaultConfig, conf)
    elif first == '--help' or first == '-h':
        print('Available commands:')
        print('    photon [file.w] Runs the script using the default lang')
        print('    photon build [platform] Builds and runs the project for the target platform')
        print('    photon set lang=[lang] Set the default language to [lang]')
        print('    photon --version Shows the the current version')
    elif first == 'update':
        os.system(f'git -C {PHOTON_INSTALL_PATH} pull')
    elif first == 'android-view':
        os.system('adb exec-out screenrecord --output-format=h264 - | ffplay -framerate 60 -probesize 32 -sync video  -')
    elif first == '--version' or first == '-v' :
        print('Photon Version 0.0.1')
    else:
        try:
            filename = first
            from pathlib import Path
            import json
            with open(f'{Path.home()}/.photon/photon.conf','r') as conf:
                lang = json.load(conf)['lang']
        except Exception as e:
            #print(f'Error: {e} loading default lang. Using c')
            #print(f'You can change that using "photon set defaultLang=lang"')
            lang = 'c'
        Interpreter(filename, lang=lang, standardLibs=os.path.join(PHOTON_INSTALL_PATH, 'Libs/')).run()
