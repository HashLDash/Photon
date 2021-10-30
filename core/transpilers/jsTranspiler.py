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
        self.lang = 'js'
        self.commentSymbol = '//'
        self.imports = set()
        self.funcIdentifier = 'function '
        self.constructorName = 'constructor'
        self.block = {'/*def*/', 'class ','function ', 'for ','while ','if ','elif ','else'}
        self.true = 'true'
        self.false = 'false'
        self.null = 'null'
        self.self = 'this'
        self.notOperator = '!'
        self.iterVar = []
        self.tempVarCounter = 0
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

    def formatSystemLibImport(self, expr):
        module = self.getValAndType(expr)['value']
        self.imports.add(f'import {{*}} from "{module}";')
        return ''

    def formatVarInit(self, name, varType):
        return f'var {name} = {self.null}'

    def formatDotAccess(self, tokens):
        currentType = None
        names = []
        for tok in tokens:
            v = self.getValAndType(tok) 
            if currentType == 'map':
                if v['value'] == 'len':
                    names = [f"Object.keys({'.'.join(names)}).length"]
                else:
                    names.append(v['value'])
            elif currentType == 'array':
                if v['value'] == 'len':
                    names = [f"{'.'.join(names)}.length"]
                else:
                    names.append(v['value'])
            else:
                currentType = v['type']
                names.append(v['value'])

        return '.'.join(names).replace('self.','this.')
    
    def formatInput(self, expr):
        if not self.target == 'web':
            self.imports.add("prompt = require('prompt-sync')()")
            self.links.add('prompt-sync')
        message = expr['value']
        return f'prompt({message})'

    def formatStr(self, string, expressions):
        if not '{' in string:
            return string, []
        string = string[1:-1].replace('"','\"')
        for expr in expressions:
            string = string.replace('{}',f'${{{expr["value"]}}}',1)
        return f'`{string}`', []

    def formatArray(self, elements, varType, size):
        values = ', '.join(v['value'] for v in elements)
        return f'[{values}]'

    def formatMap(self, elements, varType, size):
        # the [] in the key is used to evaluate the variable, else the key won't be the value
        # and will produce errors.
        values = ', '.join(f"[{k['value']}]:{v['value']}" for k, v in elements)
        return f'{{{values}}}'
    
    def formatIndexAccess(self, token):
        if token['type'] in {'array', 'map'}:
            index = self.processExpr(token['indexAccess'])['value']
            #TODO: Optimize for constants and remove the if else test. The same applies to C
            name = token['name']
            return f'{name}[{index} >= 0 ? {index} : {name}.length + {index}]'
        else:
            raise SyntaxError(f'IndexAccess with type {token["type"]} not implemented yet')
    
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
        return f'{name}.push({expr});'

    def formatArrayIncrement(self, target, index, expr):
        name = target['name']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        index = f'{index} >= 0 ? {index} : {name}.length + {index}'
        return f'{name}[{index}] += {expr};'

    def formatIncrement(self, target, expr):
        name = target['value']
        varType = target['type']
        expr = self.formatExpr(expr)
        return f'{name} += {expr};'

    def formatAssign(self, variable, varType, cast, expr, inMemory=False):
        formattedExpr = self.formatExpr(expr, cast=cast)
        if inMemory:
            return f'{variable} = {formattedExpr};'
        return f'var {variable} = {formattedExpr};'

    def formatCall(self, name, returnType, args, kwargs, className):
        arguments = ', '.join([ arg["value"] for arg in args+kwargs])
        return f'{name}({arguments})'

    def formatExpr(self, value, cast=None):
        if value['type'] in self.classes:
            return f'new {value["value"]}'
        elif cast == 'int':
            return f'parseInt({value["value"]})'
        elif cast == 'float':
            return f'parseFloat({value["value"]})'
        elif cast == 'str':
            return f'{value["value"]}.toString()'
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
        self.step = 0
        self.iterVar.append(variables)
        if 'from' in iterable:
            fromVal = iterable['from']['value']
            self.step = iterable['step']['value']
            toVal = iterable['to']['value']
            if len(variables) == 2:
                return f'var {self.iterVar[-1][0]}; var {self.iterVar[-1][-1]}; for ({self.iterVar[-1][-1]} = {fromVal}, {self.iterVar[-1][0]} = 0; {self.iterVar[-1][-1]} < {toVal}; {self.iterVar[-1][-1]} += {self.step}, {self.iterVar[-1][0]} += 1) {{'
            return f'var {self.iterVar[-1][-1]}; for ({self.iterVar[-1][-1]} = {fromVal}; {self.iterVar[-1][-1]} < {toVal}; {self.iterVar[-1][-1]} += {self.step}) {{'
        elif iterable['type'] == 'array':
            if len(variables) == 2:
                return f'var {self.iterVar[-1][-1]}; for ([{self.iterVar[-1][0]}, {self.iterVar[-1][-1]}] of {iterable["value"]}.entries()) {{'
            iteration = f'__tempVar{self.tempVarCounter}__'
            self.tempVarCounter += 1
            return f'var {self.iterVar[-1][-1]}; for (var {iteration} = 0; {iteration} < {iterable["value"]}.length; {iteration}++) {{ {self.iterVar[-1][-1]} = {iterable["value"]}[{iteration}];'
        elif iterable['type'] == 'str':
            if len(variables) == 2:
                return f'var {self.iterVar[-1][-1]}; for ([{self.iterVar[-1][0]}, {self.iterVar[-1][-1]}] of Array.from({iterable["value"]}).entries()) {{'
            iteration = f'__tempVar{self.tempVarCounter}__'
            self.tempVarCounter += 1
            return f'var {self.iterVar[-1][-1]}; for (var {iteration} = 0; {iteration} < {iterable["value"]}.length; {iteration}++) {{ {self.iterVar[-1][-1]} = {iterable["value"]}[{iteration}];'
        else:
            raise SyntaxError(f'For loop with token {iterable} not implemented yet.')

    def formatEndFor(self):
        if self.step:
            return f'}} {self.iterVar.pop()[-1]} -= {self.step};'
        # consume iter var for this loop
        self.iterVar.pop()
        return '}'

    def formatArgs(self, args):
        return ', '.join([ f'{arg["value"]}' for arg in args if not arg['value'] == 'self'])

    def formatFunc(self, name, returnType, args, kwargs):
        if name == 'new':
            name = self.constructorName
        kwargs = [{'value':kw['name'], 'type':kw['type']} for kw in kwargs]
        args = self.formatArgs(args+kwargs)
        if self.inClass:
            func = '/*def*/'
        else:
            func = 'function '
        return f'{func}{name}({args}) {{'

    def formatEndFunc(self):
        return '}'

    def formatClass(self, name, args):
        self.className = name
        return f'class {self.className} {{'

    def formatEndClass(self):
        return '}'

    def formatClassDefaultValue(self, kwarg):
        name = kwarg['name']
        value = kwarg['value']
        return f'{self.self}.{name} = {value};'

    def formatClassAttribute(self, attr):
        if 'returnType' in attr:
            return
        variable = attr['variable']
        expr = attr['expr']
        varType = variable['type']
        name = variable['value']
        expr = self.formatExpr(expr)
        return f'{name} = {expr};'

    def formatReturn(self, expr):
        if expr:
            return f'return {expr["value"]};'
        return 'return;'

    def exp(self, arg1, arg2):
        if arg1['type'] == 'int' and arg2['type'] == 'int':
            varType = 'int'
        else:
            varType = 'float'
        return {'value':f'Math.pow({arg1["value"]}, {arg2["value"]})', 'type':varType}

    def formatDelete(self, expr, name, varType):
        if varType == 'array':
            return f'{name}.splice({expr["indexAccess"]["value"]}, 1)'
        return f'delete {expr["value"]}'

    def formatPrint(self, value, terminator='\\n'):
        if value['value']:
            if terminator == '\\n':
                return f'console.log({value["value"]});'
            return f'process.stdout.write(JSON.stringify({value["value"]})+"{terminator}");'
        return f'process.stdout.write("{terminator}");'

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
            self.filename = f'{moduleName}.js'
            boilerPlateStart = []
            boilerPlateEnd = []
            del self.imports[0]
            del self.imports[0]
            del self.imports[0]
        # Force utf8 on windows
        with open(f'Sources/js/{self.filename}', 'w', encoding='utf8') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w', '').replace('"',  '')
                debug(f'Importing {module}')
                if f'{module}.js' in os.listdir('Sources/js'):
                    with open(f'Sources/js/{module}.js', 'r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp + '\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line.startswith('}'):
                        indent -= 4
                    f.write(' ' * indent + line.replace('/*def*/', '') + '\n')
                    if self.isBlock(line):
                        indent += 4
        debug('Generated ' + self.filename)

    def run(self):
        from subprocess import call, check_call
        self.write()
        debug(f'Running {self.filename}')
        try:
            if not 'node_modules' in os.listdir():
                debug('Linking libraries. This will only run once per project.')
                for module in self.links:
                    check_call(['npm', 'link', module])
            check_call(['node', f'Sources/js/{self.filename}'])
        except Exception as e:
            print(f'Compilation error {e}. Check errors above.')
