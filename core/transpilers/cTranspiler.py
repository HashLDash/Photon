from transpilers.baseTranspiler import BaseTranspiler
import os
from string import Formatter

def debug(*args):
    #print(*args)
    pass

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
    
    def formatInput(self, expr):
        self.imports.add('#include <string.h>')
        message = self.formatPrint(expr).replace('\\n','',1) if expr else ''
        size = '__internalInputSize__'
        return  f'{message}size_t {size} = 0; {self.nativeType("str")} {{var}}; getline(&{{var}}, &{size}, stdin); c[strlen(c)-1] = 0;'

    def formatStr(self, string):
        string = '"' + string[1:-1].replace('"','\\"') + '"'
        variables = []
        if '{' in string:
            self.imports.add('#include "asprintf.h"')
            variables = [var for _,var,_,_ in Formatter().parse(string) if var]
            for var in variables:
                varType = self.getType(var)
                if varType == 'str':
                    string = string.replace(f'{{{var}}}','%s',1)
                elif varType == 'int':
                    string = string.replace(f'{{{var}}}','%d',1)
                elif varType == 'float':
                    string = string.replace(f'{{{var}}}','%f',1)
                else:
                    raise SyntaxError(f'Cannot format {varType} in formatStr')
        return string, variables

    def formatCall(self, name, returnType, args):
        arguments = ','.join([ f'{arg["value"]}' for arg in args ])
        return f'{name}({arguments})'

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
        if 'format' in expr:
            # It's a format string
            formatstr = expr['format']
            variables = ','.join(expr['variables'])
            return f'{varType} {variable}; asprintf(&{variable}, {formatstr}, {variables});'
        formattedExpr = self.formatExpr(expr, cast=cast)
        try:
            if expr['token'] == 'inputFunc':
                return formattedExpr.format(var=variable)
        except KeyError:
            pass
        return f'{varType} {variable} = {formattedExpr};'

    def formatExpr(self, value, cast=None):
        #TODO: implement cast to type
        return value['value']
    
    def formatIf(self, expr):
        return f'if ({expr["value"]}) {{'

    def formatElif(self, expr):
        return f'}} else if ({expr["value"]}) {{'

    def formatElse(self):
        return '} else {'

    def formatEndIf(self):
        return '}'
    
    def div(self, arg1, arg2):
        return {'value':f'({self.nativeType("float")}){arg1["value"]} / {arg2["value"]}', 'type':'float'}

    def formatPrint(self, value):
        if value['type'] == 'int':
            return f'printf("%d\\n", {value["value"]});'
        elif value['type'] == 'float':
            return f'printf("%f\\n", {value["value"]});'
        elif value['type'] == 'str':
            if 'format' in value:
                # It's a format string
                formatstr = value['format'][:-1] + '\\n' + value['format'][-1:]
                variables = ','.join(value['variables'])
                return f'printf({formatstr}, {variables});'
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
                debug(f'Importing {module}')
                if module in os.listdir(f'{self.standardLibs}/native/c'):
                    from shutil import copyfile
                    copyfile(f'{self.standardLibs}/native/c/{module}',f'Sources/{module}')
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
        debug('Generated '+self.filename)

    def run(self):
        from subprocess import call, check_call
        self.write()
        debug(f'Running {self.filename}')
        try:
            check_call(['gcc', '-O3', f'Sources/{self.filename}', '-o',
            'Sources/main'])
        except:
            print('Compilation error. Check errors above.')
        else:
            call(['./Sources/main'])
