from transpilers.baseTranspiler import BaseTranspiler
import os

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.filename = self.filename.replace('.w','.c')
        self.commentSymbol = '//'
        self.imports = {'#include <stdio.h>', '#include <stdlib.h>', '#include <locale.h>'}
        self.funcIdentifier = '/*def*/'
        self.constructorName = 'new'
        self.block = {'typedef ','/*def*/', 'for ','while ','if ','else ', 'int main('}
        self.true = '1'
        self.false = '0'
        self.null = 'NULL'
        self.self = 'self'
        self.listTypes = set()
        self.dictTypes = set()
        self.instanceCounter = 0
        self.nativeTypes = {
            'float':'double',
            'int':'long',
            'str':'char*',
            'bool':'int',
            'unknown':'auto',
        }

    def formatVarInit(self, name, varType):
        return f'{varType} {name};'
    
    def formatAssign(self, target, expr):
        cast = None
        if target['token'] == 'var':
            variable = target['name']
            if variable in self.currentScope:
                if self.typeKnown(target['type']):
                    # Casting to a different type
                    varType = self.nativeType(target['type'])
                    cast = varType
                else:
                    varType = ''
            else:
                if self.typeKnown(target['type']):
                    # Type was explicit
                    varType = self.nativeType(target['type'])
                else:
                    varType = self.nativeType(self.inferType(expr))
        else:
            raise SyntaxError(f'Format assign with variable {target} not implemented yet.')
        formattedExpr = self.formatExpr(expr, cast=cast)
        return f'{varType} {variable} = {formattedExpr};'

    def formatExpr(self, value, cast=None):
        #TODO: implement cast to type
        return value['value']
    
    def div(self, arg1, arg2):
        return {'value':f'({self.nativeType("float")}){arg1["value"]} / {arg2["value"]}', 'type':'float'}

    def formatPrint(self, value):
        if value['type'] == 'int':
            return f'printf("%d\\n", {value["value"]});'
        elif value['type'] == 'float':
            return f'printf("%f\\n", {value["value"]});'
        elif value['type'] == 'str':
            return f'printf("%s\\n", {value["value"]});'
        elif value['type'] == 'bool':
            return f'if ({value["value"]} == 0) {{printf("False\\n");}} else {{printf("True\\n");}}'
        else:
            raise SyntaxError(f'Print function with token {value} not supported yet.')

    def write(self):
        boilerPlateStart = [
            'int main() {',
            'setlocale(LC_ALL, "");',
        ]
        boilerPlateEnd = [
            'return 0;',
            '}'
        ]
        indent = 0
        count = 0
        if not 'Sources' in os.listdir():
            os.mkdir('Sources')
        if not self.module:
            self.filename = 'main.c'
        else:
            self.filename = f'{moduleName}.c'
            boilerPlateStart = []
            boilerPlateEnd = []
            del self.imports[0]
            del self.imports[0]
            del self.imports[0]
        with open(f'Sources/{self.filename}','w') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w','').replace('"','')
                print(f'Importing {module}')
                if f'{module}.c' in os.listdir('Sources'):
                    with open(f'Sources/{module}.c','r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp+'\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line[0] == '}':
                        indent -= 4
                f.write(' '*indent+line+'\n')
                if self.isBlock(line):
                    indent += 4
        print('Generated '+self.filename)

    def run(self):
        from subprocess import call, check_call
        self.write()
        print(f'Running {self.filename}')
        try:
            check_call(['gcc', '-O3', f'Sources/{self.filename}', '-o',
            'Sources/main'])
        except:
            print('Compilation error. Check errors above.')
        else:
            call(['./Sources/main'])
