#!/usr/bin/env python3
''' Photon command-line interface. '''

import os, sys
from pattern_cli import cli, flags, kwargs, cli_help

PHOTON_INSTALL_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, PHOTON_INSTALL_PATH)

__version__ = '0.0.10'

allowed_kwargs = {
    'lang': ['c', 'd', 'js', 'ts', 'dart', 'haxe', 'python'],
    'platform': ['linux', 'windows', 'mac', 'android', 'web'],
    'framework': ['raylib', 'html5', 'flutter', 'opengl', 'canvas'],
}

def get_home():
    import json
    import pathlib
    return pathlib.Path.home()

def get_conf():
    import json
    try:
        with open(f'{get_home()}/.photon/photon.conf') as c:
            return json.load(c)
    except FileNotFoundError:
        createConfFolder()
        return {'lang':'c'}

def set_conf(**kwargs):
    import json
    data = get_conf()
    for key, val in kwargs.items():
        if key in allowed_kwargs:
            if val in allowed_kwargs[key]:
                data[key] = val
                if key == 'lang':
                    from dependencies import haveDependencies, resolveDependencies
                    if not haveDependencies(val, sys.platform):
                        resolveDependencies(val, sys.platform)
                        print('Dependencies successfuly installed.')
            else:
                print(f'Value {val} is not allowed. You can try these: {", ".join(allowed_kwargs[key])}')
        else:
            print(f'Value {key} or {val} is not allowed. You can try these:')
            print(f'{"\n  ".join([""] + allowed_kwargs)}')
    with open(f'{get_home()}/.photon/photon.conf', 'w') as c:
        json.dump(data, c)

def getParameters():
    parameters = get_conf()
    parameters.update(kwargs)
    return parameters

def createConfFolder():
    home = get_home()
    if not '.photon' in os.listdir(home):
        os.mkdir(f'{home}/.photon')

@cli('version')
def version():
    'Show photon version'
    print(f'Photon {__version__}')        

@cli('update')
def update():
    'Update photon'
    os.system(f'git -C {PHOTON_INSTALL_PATH} pull')

@cli('set')
def set_config(**kwargs):
    'Set a default parameter in the photon config'
    set_conf(**kwargs)

@cli('<str:filename>')
def run(filename, **kwargs):
    'Run a script'
    from interpreter import Interpreter
    DEBUG = '-d' in flags or '--debug' in flags
    Interpreter(
        filename=filename,
        standardLibs=os.path.join(
            PHOTON_INSTALL_PATH, 'libs'),
        debug=DEBUG,
        **getParameters()).run()

@cli('')
def interpreter():
    'Open the interpreter'
    if flags:
        if '-v' in flags or '--version' in flags:
            version()
        elif '-h' in flags or '--help' in flags:
            cli_help()
        else:
            print(f'Flag {flags[0]} not valid here')
    else:
        from interpreter import Interpreter
        DEBUG = '-d' in flags or '--debug' in flags
        print(f'Photon - {__version__} - pyEngine')
        Interpreter(
            standardLibs=os.path.join(
                PHOTON_INSTALL_PATH, 'libs'),
            debug=DEBUG).run()
