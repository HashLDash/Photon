from transpilers.baseTranspiler import BaseTranspiler
import os
from string import Formatter

def debug(*args):
    #print(*args)
    pass

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.filename = self.filename.replace('.w','.js')
        self.commentSymbol = '//'
        self.imports = set()
        self.funcIdentifier = 'function '
        self.constructorName = 'new'
        self.block = {'class ','function ', 'for ','while ','if ','elif ','else'}
        self.true = 'true'
        self.false = 'false'
        self.null = 'null'
        self.self = 'this'
        self.notOperator = '!'
        self.nativeTypes = {
            'float':'float',
            'int':'int',
            'str':'str',
            'bool':'bool',
            'any':'var',
            'unknown':'var',
        }
    
    def nativeType(self, varType):
        try:
            return self.nativeTypes[varType]
        except KeyError:
            return 'any'

    def formatVarInit(self, name, varType):
        return f'var {name} = {self.null}'

    def formatInput(self, expr):
        if not self.target == 'web':
            self.imports.add("prompt = require('prompt-sync')()")
        message = expr['value']
        return f'prompt({message})'

    def formatStr(self, string):
        string = string[1:-1].replace('"','\"')
        variables = [var for _,var,_,_ in Formatter().parse(string) if var]
        for var in variables:
            string = string.replace(f'{{{var}}}',f'${{{var}}}',1)
        return f'`{string}`', []
    
    def formatAssign(self, target, expr, inMemory=False):
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
        return f'var {variable} = {formattedExpr};'

    def formatCall(self, name, returnType, args):
        arguments = ','.join([ arg["value"] for arg in args])
        return f'{name}({arguments})'

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
    
    def formatWhile(self, expr):
        formattedExpr = self.formatExpr(expr)
        return f'while ({formattedExpr}) {{'

    def formatEndWhile(self):
        return '}'

    def formatFor(self, variables, iterable):
        if 'from' in iterable:
            self.var = variables[0]['value']
            fromVal = iterable['from']['value']
            self.step = iterable['step']['value']
            toVal = iterable['to']['value']
            return f'for (var {self.var}={fromVal};{self.var}<{toVal}; {self.var}+={self.step}) {{'

    def formatEndFor(self):
        return f'}} {self.var} -= {self.step};'

    def formatArgs(self, args):
        return ','.join([ f'{arg["value"]}' for arg in args ])

    def formatFunc(self, name, returnType, args):
        args = self.formatArgs(args)
        return f'function {name}({args}) {{'

    def formatEndFunc(self):
        return '}'

    def formatReturn(self, expr):
        if expr:
            return f'return {expr["value"]};'
        return 'return;'

    def formatPrint(self, value):
        return f'console.log({value["value"]});'

    def write(self):
        boilerPlateStart = [
        ]
        boilerPlateEnd = [
        ]
        indent = 0
        count = 0
        if not 'Sources' in os.listdir():
            os.mkdir('Sources')
        if not self.module:
            self.filename = 'main.js'
        else:
            self.filename = f'{moduleName}.js'
            boilerPlateStart = []
            boilerPlateEnd = []
            del self.imports[0]
            del self.imports[0]
            del self.imports[0]
        with open(f'Sources/{self.filename}','w') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w','').replace('"','')
                debug(f'Importing {module}')
                if f'{module}.js' in os.listdir('Sources'):
                    with open(f'Sources/{module}.js','r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp+'\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line.startswith('}'):
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
            check_call(['node', f'Sources/{self.filename}'])
        except:
            print('Compilation error. Check errors above.')
