from transpilers.baseTranspiler import BaseTranspiler
import os

def debug(*args):
    #print(*args)
    pass

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.filename = self.filename.replace('.w','.py')
        self.lang = 'py'
        self.libExtension = 'py'
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
            'array':'list',
            'unknown':'any',
            'void':'None',
        }
    
    def nativeType(self, varType):
        try:
            return self.nativeTypes[varType]
        except KeyError:
            return 'any'

    def formatSystemLibImport(self, expr):
        module = self.getValAndType(expr)['value']
        self.imports.add(f'from {module} import *')
        return

    def formatVarInit(self, name, varType):
        if varType:
            return f'{name}:{varType} = None'
        return f'{name} = None'

    def formatDotAccess(self, tokens):
        currentType = None
        names = []
        for tok in tokens:
            v = self.getValAndType(tok) 
            if 'indexAccess' in tok:
                if 'elementType' in tok:
                    tok['type'] = 'array'
                elif 'keyType' in tok:
                    tok['type'] = 'map'
                value = self.processIndexAccess(tok)
                names.append(value['value'])
                currentType = value['type']
            elif currentType in {'array', 'map'}:
                if v['value'] == 'len':
                    names = [f"len({'.'.join(names)})"]
                    currentType = 'int'
                else:
                    names.append(v['value'])
                    currentType = v['type']
            else:
                names.append(v['value'])
                currentType = v['type']

        return '.'.join(names)

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

    def formatMap(self, elements, varType, size):
        values = ', '.join(f"{k['value']}:{v['value']}" for k, v in elements)
        return f'{{{values}}}'
    
    def formatIndexAssign(self, target, expr, inMemory=False):
        target = self.getValAndType(target)
        varType = target['type']
        if self.typeKnown(expr['type']) and expr['type'] != varType:
            cast = self.nativeType(varType)
        else:
            cast = None
        expr = self.formatExpr(expr, cast=cast)
        return f'{target["value"]} = {expr}'

    def formatArrayAppend(self, target, expr):
        name = target['value']
        expr = self.formatExpr(expr)
        return f'{name}.append({expr})'

    def formatArrayIncrement(self, target, index, expr):
        name = self.getValAndType(target)['value']
        varType = target['type']
        if self.typeKnown(expr['type']) and expr['type'] != varType:
            cast = self.nativeType(varType)
        else:
            cast = None
        expr = self.formatExpr(expr, cast=cast)
        return f'{name} += {expr}'

    def formatIncrement(self, target, expr):
        name = target['value']
        varType = target['type']
        if self.typeKnown(expr['type']) and expr['type'] != varType:
            cast = self.nativeType(varType)
        else:
            cast = None
        expr = self.formatExpr(expr, cast=cast)
        return f'{name} += {expr}'

    def formatArrayRemoveAll(self, target, expr):
        name = target['value']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        return f'{name} = [x for x in {name} if x != {expr}]'

    def formatAssign(self, variable, varType, cast, expr, inMemory=False):
        formattedExpr = self.formatExpr(expr, cast=cast)
        if varType and not inMemory:
            varType = self.nativeType(varType)
            return f'{variable}:{varType} = {formattedExpr}'
        return f'{variable} = {formattedExpr}'

    def formatCall(self, name, returnType, args, kwargs, className):
        arguments = ','.join([ arg["value"] for arg in args+kwargs])
        return f'{name}({arguments})'

    def formatExpr(self, value, cast=None):
        if cast is None:
            return value['value']
        elif cast in {'str', 'int', 'float'}:
            return f"{cast}({value['value']})"
        else:
            raise NotImplemented
    
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
            var = ', '.join(variables)
            fromVal = iterable['from']['value']
            step = iterable['step']['value']
            toVal = iterable['to']['value']
            if len(variables) == 2:
                return f'for {var} in enumerate(range({fromVal}, {toVal}, {step})):'
            return f'for {var} in range({fromVal}, {toVal}, {step}):'
        else:
            if len(variables) == 2:
                var = ', '.join(variables)
                return f'for {var} in enumerate({iterable["value"]}):'
            return f'for {variables[0]} in {iterable["value"]}:'

    def formatEndFor(self):
        return "#end"

    def formatArgs(self, args):
        return ','.join([ f'{arg["value"]}: {self.nativeType(arg["type"])}' for arg in args ])

    def formatFunc(self, name, returnType, args, kwargs):
        if name == 'new':
            name = self.constructorName
        kwargs = [{'value':kw['name'], 'type':kw['type']} for kw in kwargs]
        args = self.formatArgs(args+kwargs)
        returnType = self.nativeType(returnType)
        return f'def {name}({args}) -> {returnType}:'

    def formatEndFunc(self):
        if self.inFunc or self.inClass:
            if 'def ' in self.outOfMain[-1]:
                self.insertCode("pass")
        elif 'def ' in self.source[-1]:
            self.insertCode("pass")
        return "#end"

    def formatClass(self, name, args):
        self.className = name
        return f'class {self.className}():'

    def formatEndClass(self):
        return f'#end'

    def formatClassDefaultValue(self, arg):
        if 'name' in arg:
            # it's a kwarg
            name = arg['name']
            value = arg['value']
        else:
            # it's an arg
            name = arg['value']
        return f'{self.self}.{name} = {name}'

    def formatClassAttribute(self, attr):
        if 'returnType' in attr:
            # It's a method, do nothing
            return
        variable = attr['variable']
        expr = attr['expr']
        varType = self.nativeType(variable['type'])
        name = variable['value']
        expr = self.formatExpr(expr)
        return f'{name}:{varType} = {expr}'

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

    def formatDelete(self, expr, name, varType):
        return f'del {expr["value"]}'

    def formatPrint(self, value, terminator='\\n'):
        if value['value']:
            return f'print({value["value"]}, end="{terminator}")'
        return f'print(end="{terminator}")'

    def write(self):
        boilerPlateStart = [
        ]
        boilerPlateEnd = [
        ]
        indent = 0
        count = 0
        if not 'Sources' in os.listdir():
            os.mkdir('Sources')
        if not 'py' in os.listdir('Sources'):
           os.mkdir('Sources/py')
        if not self.module:
            self.filename = 'main.py'
        else:
            #self.filename = f'{moduleName}.py'
            boilerPlateStart = []
            boilerPlateEnd = []
        with open(f'Sources/py/{self.filename}', 'w') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w', '').replace('"', '')
                debug(f'Importing {module}')
                if f'{module}.c' in os.listdir('Sources/py'):
                    with open(f'Sources/py/{module}.py', 'r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp + '\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line.startswith('#end') or line.startswith('elif ') or line.startswith('else:'):
                        indent -= 4
                    f.write(' ' * indent + line.replace('#end', '') + '\n')
                    if self.isBlock(line):
                        indent += 4
        debug('Generated ' + self.filename)

    def run(self):
        from subprocess import call, check_call
        self.write()
        debug(f'Running {self.filename}')
        try:
            check_call(['python', f'Sources/py/{self.filename}'])
        except:
            print('Compilation error. Check errors above.')
