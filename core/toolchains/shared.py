from toolchains.toolchain import BaseToolchain
from photonParser import debug

class Toolchain(BaseToolchain):
    def transpile(self):
        self.interpreter.run()

    def make(self):
        from subprocess import call, check_call
        debug(f'Compiling shared library...')
        links = list(self.interpreter.engine.links)
        filename = self.interpreter.engine.filename.split('.')[0] + '.c'
        libraryName = self.interpreter.filename.split('.')[0] + '.so'
        try:
            debug(' '.join(['gcc', '-O2', '-std=c99', f'Sources/c/{filename}'] + links + ['-o', 'Sources/c/main']))
            check_call(['gcc', '-O2', '-std=c99', '-fPIC', '-shared', f'Sources/c/{filename}'] + links + ['-o', libraryName])
        except Exception as e:
            print(e)
            print('Compilation error. Check errors above.')
