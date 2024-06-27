from transpilers.baseTranspiler import BaseTranspiler
import os

def debug(*args):
    #print(*args)
    pass

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        self.lang = 'javascript'
        self.loadTokens('js')
        super().__init__(filename, **kwargs)
        self.filename = self.filename.replace('.w','.js')
        self.libExtension = 'js'
        self.imports = set()
        self.links = set()
        self.listTypes = set()
        self.dictTypes = set()
        self.classes = {}
        self.nativeTypes = {
            'float':'float',
            'int':'int',
            'str':'str',
            'bool':'bool',
            'array':'list',
            'unknown':'any',
            'void':'None',
        }
        self.builtins = {
            'open':{'type':'file', 'value':'open'},
        }
    
    def write(self):
        boilerPlateStart = [
        ]
        boilerPlateEnd = [
        ]
        indent = 0
        count = 0
        if not 'Sources' in os.listdir():
            os.mkdir('Sources')
        if not 'js' in os.listdir('Sources'):
           os.mkdir('Sources/js')
        if not self.module:
            self.filename = 'main.js'
        else:
            boilerPlateStart = []
            boilerPlateEnd = []
        with open(f'Sources/js/{self.filename}', 'w') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w', '').replace('"', '')
                debug(f'Importing {module}')
                if f'{module}.js' in os.listdir('Sources/js'):
                    with open(f'Sources/js/{module}.js', 'r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp + '\n')
            for line in [''] + boilerPlateStart + [self.sequence] + boilerPlateEnd:
                f.write(f'{line}\n')
        debug('Generated ' + self.filename)

    def run(self):
        from subprocess import call, check_call
        self.write()
        debug(f'Running {self.filename}')
        try:
            check_call(['node', f'Sources/js/{self.filename}'])
        except:
            print('Compilation error. Check errors above.')
