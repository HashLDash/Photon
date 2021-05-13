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
        self.notOperator = '!'
        self.listTypes = set()
        self.dictTypes = set()
        self.instanceCounter = 0
        self.nativeTypes = {
            'float':'double',
            'int':'long',
            'str':'char*',
            'bool':'int',
            'void':'void',
            'unknown':'auto',
        }

        self.initInternal = False

    def formatVarInit(self, name, varType):
        return f'{varType} {name};'
    
    def formatInput(self, expr):
        self.imports.add('#include <string.h>') # strlen
        if self.target in {'win32', 'cygwin', 'msys'}:
            self.imports.add('#include "getline.h"') # getline
        message = self.formatPrint(expr).replace('\\n','',1) if expr['value'] else ''
        size = '__internalInputSize__'
        if not self.initInternal:
            initInternal = f'size_t {size} = 0; char* __inputStr__;'
            self.initInternal = True
        else:
            initInternal = f'{size} = 0;'
        #return  f'{message}{initInternal}{self.nativeType("str")} {{var}}; getline(&{{var}}, &{size}, stdin); {{var}}[strlen({{var}})-1] = 0;'
        return  f'{message}{initInternal} getline(&__inputStr__, &{size}, stdin); __inputStr__[strlen(__inputStr__)-1] = 0;'

    def formatStr(self, string):
        string = '"' + string[1:-1].replace('"','\\"').replace('%','%%') + '"'
        variables = []
        if '{' in string:
            if self.target in {'win32', 'cygwin', 'msys'}:
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
        if target['token'] == 'var':
            variable = target['name']
            if variable in self.currentScope:
                varType = self.currentScope[variable]['type']
            elif self.typeKnown(target['type']):
                # Type was explicit
                varType = self.nativeType(target['type'])
            else:
                varType = self.nativeType(self.inferType(expr))

            #if variable in self.currentScope:
            #    if self.typeKnown(target['type']):
            #        if not target['type'] == self.currentScope[variable]['type']:
            #            # Casting to a different type
            #            varType = self.nativeType(target['type'])
            #        else:
            #            # Doesnt need cast here
            #            varType = self.nativeType(self.currentScope[variable]['type'])
            #        cast = varType
            #    else:
            #        varType = ''
            #else:
            #    if self.typeKnown(target['type']):
            #        # Type was explicit
            #        varType = self.nativeType(target['type'])
            #    else:
            #        varType = self.nativeType(self.inferType(expr))
        else:
            raise SyntaxError(f'Format assign with variable {target} not implemented yet.')
        if 'format' in expr:
            # It's a format string
            formatstr = expr['format']
            variables = ','.join(expr['variables'])
            return f'{varType} {variable}; asprintf(&{variable}, {formatstr}, {variables});'
        if expr['type'] != varType:
            cast = self.nativeType(varType)
        else:
            cast = None
        formattedExpr = self.formatExpr(expr, cast=cast, var=variable)
        varType = self.nativeType(varType)
        try:
            if expr['token'] == 'inputFunc' and not cast is None:
                return formattedExpr
            elif expr['token'] == 'inputFunc':
                input(cast)
                return formattedExpr + f'{varType} {variable}; {variable} = __inputStr__;'
        except KeyError:
            pass
        return f'{varType} {variable} = {formattedExpr};'

    def formatExpr(self, value, cast=None, var=None):
        #TODO: implement cast to type
        if not cast is None:
            if cast == 'long':
                if value['token'] == 'inputFunc':
                    return f'{value["value"]} {cast} {var} = strtol(__inputStr__,NULL,10);'
            else:
                raise SyntaxError(f'Cast not implemented for type {cast}')
        return value['value']
    
    def formatIf(self, expr):
        return f'if ({expr["value"]}) {{'

    def formatElif(self, expr):
        return f'}} else if ({expr["value"]}) {{'

    def formatElse(self):
        return '} else {'

    def formatEndIf(self):
        return '}'
    
    def formatWhile(self, expr):
        formattedExpr = self.formatExpr(expr)
        return f'while ({formattedExpr}) {{'

    def formatEndWhile(self):
        return '}'

    def formatFor(self, variables, iterable):
        if 'from' in iterable:
            # For with range
            iterVar = variables[0]['value']
            varType = iterable['type']
            fromVal = iterable['from']['value']
            step = iterable['step']['value']
            toVal = iterable['to']['value']
            return f'for ({varType} {iterVar}={fromVal};{iterVar}<{toVal}; i+={step}) {{'
        else:
            raise SyntaxError(f'Format for with unpacking not suported yet.')
    
    def formatEndFor(self):
        return '}'

    def formatArgs(self, args):
        return ','.join([ f'{self.nativeType(arg["type"])} {arg["value"]}' for arg in args])

    def formatFunc(self, name, returnType, args):
        args = self.formatArgs(args)
        return f'/*def*/{self.nativeType(returnType)} {name}({args}) {{'

    def formatEndFunc(self):
        return '}'

    def formatReturn(self, expr):
        if expr:
            return f'return {expr["value"]};'
        return 'return;'
    
    def div(self, arg1, arg2):
        return {'value':f'({self.nativeType("float")}){arg1["value"]} / {arg2["value"]}', 'type':'float'}

    def equals(self, arg1, arg2):
        if arg1['type'] == 'str' or arg2['type'] == 'str':
            self.imports.add('#include <string.h>')
            return {'value':f'!strcmp({arg1["value"]}, {arg2["value"]})', 'type':'bool'}
        else:
            return {'value':f'{arg1["value"]} == {arg2["value"]}', 'type':'bool'}

    def formatPrint(self, value):
        if value['type'] == 'int':
            return f'printf("%ld\\n", {value["value"]});'
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
                f.write(' '*indent+line.replace('/*def*/','')+'\n')
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
