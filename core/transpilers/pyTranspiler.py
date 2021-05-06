from transpilers.baseTranspiler import BaseTranspiler
import os

def debug(*args):
    #print(*args)
    pass

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.filename = self.filename.replace('.w','.py')
        self.commentSymbol = '#'
        self.imports = set()
        self.funcIdentifier = 'def'
        self.constructorName = '__init__'
        self.block = {'class ','def ', 'for ','while ','if ','else '}
        self.true = 'True'
        self.false = 'False'
        self.null = 'None'
        self.self = 'self'
        self.nativeTypes = {
            'float':'float',
            'int':'int',
            'str':'str',
            'bool':'bool',
            'unknown':'',
        }

    def formatVarInit(self, name, varType):
        if varType:
            return f'{name}:{varType} = None'
        return f'{name} = None'

    def formatStr(self, string):
        string = string[1:-1].replace('"','\"')
        return f'f"{string}"'
    
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
        if varType:
            return f'{variable}:{varType} = {formattedExpr}'
        return f'{variable} = {formattedExpr}'

    def formatExpr(self, value, cast=None):
        #TODO: implement cast to type
        return value['value']
    
    def formatIf(self, expr):
        return f'if {expr["value"]}:'

    def formatElif(self, expr):
        return f'elif {expr["value"]}:'

    def formatElse(self):
        return 'else:'

    def formatEndIf(self):
        return '#end'
    
    def div(self, arg1, arg2):
        return {'value':f'({arg1["value"]} / {arg2["value"]}', 'type':'float'}

    def formatPrint(self, value):
        return f'print({value["value"]})'

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
            self.filename = 'main.py'
        else:
            self.filename = f'{moduleName}.py'
            boilerPlateStart = []
            boilerPlateEnd = []
            del self.imports[0]
            del self.imports[0]
            del self.imports[0]
        with open(f'Sources/{self.filename}','w') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w','').replace('"','')
                debug(f'Importing {module}')
                if f'{module}.c' in os.listdir('Sources'):
                    with open(f'Sources/{module}.py','r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp+'\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line.startswith('#end'):
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
            check_call(['python', f'Sources/{self.filename}'])
        except:
            print('Compilation error. Check errors above.')
