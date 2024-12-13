from transpilers.baseTranspiler import BaseTranspiler
from copy import deepcopy
import os
from string import Formatter

def debug(*args):
    #print(*args)
    pass

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        self.lang = 'c'
        self.loadTokens(self.lang)
        super().__init__(filename, **kwargs)
        self.libExtension = 'h'
        self.filename = self.filename.replace('.w', '.c')
        self.imports = {'#include <stdio.h>', '#include <stdlib.h>', '#include <locale.h>', '#include "main.h"'}
        self.links = set()
        if self.debug:
            # compile with debug symbols for gdb
            self.links.add('-g')
            self.links.add('-Wall')
        self.listTypes = set()
        self.dictTypes = set()
        self.classes = {}
        self.nativeTypes = {
            'float': 'double',
            'int': 'long',
            'str': 'char*',
            'bool': 'int',
            'void': 'void',
            'func': 'void',
            'unknown': 'auto',
            'file': 'FILE*'
        }
        self.builtins = {
            'open':{'type':'file', 'value':'fopen'},
        }

    def renderDictTemplate(self, keyType, valType):
        formatCodes = {'int':'%ld', 'str':'\\"%s\\"', 'float':'%lf'}
        with open(f'{self.standardLibs}/native/c/dict_{keyType}.template') as template:
            dictLib = template.read()
        if valType in self.classes:
            valNativeType = f"{valType}*"
        else:
            valNativeType = self.nativeTypes[valType]
        #TODO: Call instance repr if it exists instead of the placeholder
        dictLib = dictLib.replace('!@valType@!', valType).replace('!@valNativeType@!', valNativeType).replace('!@formatCode@!', formatCodes[valType] if valType in formatCodes else f'<class {valType}>')
        with open(f'Sources/c/dict_{keyType}_{valType}.h', 'w') as lib:
            lib.write(dictLib)

    def renderListTemplate(self, valType):
        if not valType in {'str', 'int', 'float'}:
            with open(f'{self.standardLibs}/native/c/list_template.h') as template:
                listLib = template.read()
            listLib = listLib.replace('!@valType@!', valType)
            with open(f'Sources/c/list_{valType}.h', 'w') as lib:
                lib.write(listLib)

    def write(self):
        boilerPlateStart = [
            'int main() {',
            'setlocale(LC_ALL, "");',
        ]
        boilerPlateEnd = [
            'return 0;',
            '}'
        ]
        if not 'Sources' in os.listdir():
            os.mkdir('Sources')
        if not 'c' in os.listdir('Sources'):
           os.mkdir('Sources/c')
        if not self.module:
            self.filename = 'main.c'
        else:
            moduleName = self.filename.split('.')[0]    
            self.filename = f'{moduleName}.c'
            boilerPlateStart = []
            boilerPlateEnd = []
        with open(f'Sources/c/main.h', 'w') as f:
            indent = 0
            f.write('#ifndef __main_h\n#define __main_h\n')
            if self.listTypes or self.dictTypes:
                self.imports.add('#include "asprintf.h"')
            listTypeHints = []
            dictTypeHints = []
            for listType in self.listTypes:
                if listType in self.classes:
                    listTypeHints.append(f'typedef struct list_{listType} list_{listType};')
                    self.classes[listType].postCode=f'\n#include "list_{listType}.h"\n'
            for keyType, valType in self.dictTypes:
                if valType in self.classes:
                    dictTypeHints.append(f'typedef struct dict_{keyType}_{valType} dict_{keyType}_{valType};')
                    self.classes[valType].postCode+=f'\n#include "dict_{keyType}_{valType}.h"\n'
            #TODO: do the same type hint for dicts
            for line in listTypeHints + dictTypeHints:
                #if '}' in line:
                #    indent -= 4
                f.write(' '*indent + line+'\n')
                #if self.isBlock(line) and not ';' in line[-1]:
                #    indent += 4
            f.write('#endif')
        with open(f'Sources/c/{self.filename}', 'w') as f:
            f.write('#ifndef __main\n#define __main\n')
            for imp in sorted(self.imports):
                module = imp.split(' ')[-1].replace('.w', '').replace('"', '')
                debug(f'Importing {module}')
                if module in os.listdir(f'{self.standardLibs}/native/c'):
                    from shutil import copyfile
                    copyfile(f'{self.standardLibs}/native/c/{module}', f'Sources/c/{module}')
                if not f'{module}.c' in os.listdir('Sources/c'):
                    # native import
                    f.write(imp + '\n')
                for valType in self.listTypes:
                    self.renderListTemplate(valType)
                for keyType, valType in self.dictTypes:
                    self.renderDictTemplate(keyType, valType)
            for line in [''] + boilerPlateStart + [''] + [self.sequence] + boilerPlateEnd:
                f.write(f'{line}\n')
            f.write('#endif')
        debug('Generated ' + self.filename)

    def run(self):
        from subprocess import call, check_call
        import sys
        self.write()
        debug(f'Running {self.filename}')
        try:
            if self.debug:
                optimizationFlags = ['-ggdb']
            elif sys.platform == 'darwin':
                optimizationFlags = ['-Ofast']
            else:
                optimizationFlags = ['-Ofast', '-frename-registers', '-funroll-loops']
            debug(' '.join(['gcc', '-O2', '-std=c99', f'Sources/c/{self.filename}'] + list(self.links) + ['-o', 'Sources/c/main']))
            check_call(['gcc'] + optimizationFlags + ['-std=c99', f'Sources/c/{self.filename}'] + list(self.links) + ['-o', 'Sources/c/main'])
        except Exception as e:
            print(e)
            print('Compilation error. Check errors above.')
            exit()
        else:
            if self.platform in {'linux', 'darwin'}:
                # don't call on Sources/c folder because of file paths
                call('./Sources/c/main')
                #call('./main', cwd='Sources/c')
            else:
                call('main', cwd='Sources/c', shell=True)
