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
        self.funcIdentifier = 'def '
        self.constructorName = '__init__'
        self.block = {'class ','def ', 'for ','while ','if ','elif ','else:'}
        self.true = 'True'
        self.false = 'False'
        self.null = 'None'
        self.self = 'self'
        self.notOperator = 'not '
        self.nativeTypes = {
            'float':'float',
            'int':'int',
            'str':'str',
            'bool':'bool',
            'unknown':'any',
        }
    
    def nativeType(self, varType):
        try:
            return self.nativeTypes[varType]
        except KeyError:
            return 'any'

    def formatVarInit(self, name, varType):
        if varType:
            return f'{name}:{varType} = None'
        return f'{name} = None'

    def formatInput(self, expr):
        message = expr['value']
        return f'input({message})'

    def formatStr(self, string, expressions):
        if not '{' in string:
            return string, []
        string = string[1:-1].replace('"','\"')
        for expr in expressions:
            string = string.replace('{}',f'{{{expr["value"]}}}',1)
        return f'f"{string}"', []

    def formatArray(self, elements, varType, size):
        values = ', '.join(v['value'] for v in elements)
        return f'[{values}]'
    
    def formatIndexAssign(self, target, expr, inMemory=False):
        if target['type'] == 'array':
            index = self.processExpr(target['indexAccess'])['value']
            name = target['name']
            varType = target['elementType']
            if self.typeKnown(expr['type']) and expr['type'] != varType:
                cast = self.nativeType(varType)
            else:
                cast = None
            expr = self.formatExpr(expr, cast=cast)
            return f'{name}[{index}] = {expr}'
        else:
            raise SyntaxError(f'Index assign with type {target["type"]} not implemented in py target.')

    def formatArrayAppend(self, target, expr):
        name = target['value']
        expr = self.formatExpr(expr)
        return f'{name}.append({expr})'

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
        if varType and not inMemory:
            return f'{variable}:{varType} = {formattedExpr}'
        return f'{variable} = {formattedExpr}'

    def formatCall(self, name, returnType, args):
        arguments = ','.join([ arg["value"] for arg in args])
        return f'{name}({arguments})'

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
    
    def formatWhile(self, expr):
        formattedExpr = self.formatExpr(expr)
        return f'while {formattedExpr}:'

    def formatEndWhile(self):
        return '#end'

    def formatFor(self, variables, iterable):
        if 'from' in iterable:
            var = variables[0]['value']
            fromVal = iterable['from']['value']
            step = iterable['step']['value']
            toVal = iterable['to']['value']
            return f'for {var} in range({fromVal}, {toVal}, {step}):'
        else:
            return f'for {variables[0]["value"]} in {iterable["value"]}:'

    def formatEndFor(self):
        return '#end'

    def formatArgs(self, args):
        return ','.join([ f'{arg["value"]}: {self.nativeType(arg["type"])}' for arg in args ])

    def formatFunc(self, name, returnType, args):
        args = self.formatArgs(args)
        return f'def {name}({args}) -> {returnType}:'

    def formatEndFunc(self):
        return '#end'

    def formatReturn(self, expr):
        if expr:
            return f'return {expr["value"]}'
        return 'return'

    def div(self, arg1, arg2):
        return {'value':f'{arg1["value"]} / {arg2["value"]}', 'type':'float'}

    def andOperator(self, arg1, arg2):
        return {'value':f'{arg1["value"]} and {arg2["value"]}', 'type':'bool'}

    def orOperator(self, arg1, arg2):
        return {'value':f'{arg1["value"]} or {arg2["value"]}', 'type':'bool'}

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
                    if line.startswith('#end') or line.startswith('elif ') or line.startswith('else:'):
                        indent -= 4
                f.write(' '*indent+line.replace('#end','')+'\n')
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
