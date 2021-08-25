# Photon builder
# This script is used to generate a Photon project
# according to the target platform and preferences
# Each target is handled by its Toolchain

import sys

class Builder():
    def __init__(self, platform, standardLibs='', **kwargs):
        print(f'Platform: {platform}')
        if platform == 'shared':
            from toolchains.shared import Toolchain
        else:
            print('This platform is not supported yet.')
            sys.exit()
        Toolchain(platform, standardLibs=standardLibs).getBuildFiles()
        Toolchain(platform, standardLibs=standardLibs).transpile()
        Toolchain(platform, standardLibs=standardLibs).prepare()
        Toolchain(platform, standardLibs=standardLibs).make()
        Toolchain(platform, standardLibs=standardLibs).runProject()
