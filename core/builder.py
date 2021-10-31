# Photon builder
# This script is used to generate a Photon project
# according to the target platform and preferences
# Each target is handled by its Toolchain

import sys

class Builder():
    def __init__(self, platform, filename="main.w", standardLibs='', **kwargs):
        print(f'Platform: {platform}')
        print(f'Filename: {filename}')
        if platform == 'shared':
            from toolchains.shared import Toolchain
        else:
            print('This platform is not supported yet.')
            sys.exit()
        Toolchain(platform, filename=filename, standardLibs=standardLibs).getBuildFiles()
        Toolchain(platform, filename=filename, standardLibs=standardLibs).transpile()
        Toolchain(platform, filename=filename, standardLibs=standardLibs).prepare()
        Toolchain(platform, filename=filename, standardLibs=standardLibs).make()
        Toolchain(platform, filename=filename, standardLibs=standardLibs).runProject()
