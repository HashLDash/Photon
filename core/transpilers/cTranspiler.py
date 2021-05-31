from transpilers.baseTranspiler import BaseTranspiler
import os
from string import Formatter

def debug(*args):
    #print(*args)
    pass

class Transpiler(BaseTranspiler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.lang = 'c'
        self.libExtension = 'h'
        self.filename = self.filename.replace('.w', '.c')
        self.commentSymbol = '//'
        self.imports = {'#include <stdio.h>', '#include <stdlib.h>', '#include <locale.h>'}
        self.funcIdentifier = '/*def*/'
        self.constructorName = 'new'
        self.block = {'struct ','/*def*/', 'for ','while ','if ','else ', 'int main('}
        self.true = '1'
        self.false = '0'
        self.null = 'NULL'
        self.self = 'self'
        self.methodsInsideClass = False
        self.notOperator = '!'
        self.links = set()
        self.listTypes = set()
        self.dictTypes = set()
        self.instanceCounter = 0
        self.nativeTypes = {
            'float': 'double',
            'int': 'long',
            'str': 'char*',
            'bool': 'int',
            'void': 'void',
            'unknown': 'auto',
        }
        self.initInternal = False

    def formatSystemLibImport(self, expr):
        # TODO: Handle dotAccess imports
        name = expr['args'][0]['name']
        self.imports.add(f'#include "{name}.h"')
        self.links.add(f"-l{name}")
        return ''

    def formatVarInit(self, name, varType):
        return f'{varType} {name};'

    def formatDotAccess(self, tokens):
        dotAccess = []
        currentType = None
        for v in tokens:
            if 'indexAccess' in v:
                # The value should be the dotAccess up to now
                v['name'] = '.'.join(dotAccess + [v['name']])
                value = self.processIndexAccess(v)
                currentType = value['type']
                # Now the result is just this dotAccess
                dotAccess = [value['value']]
            elif v['token'] == 'call':
                if currentType in self.classes:
                    instance = dotAccess.pop()
                    v['args'] = [{'value':instance, 'type':currentType, 'pointer':True}] + v['args']
                    value = self.processCall(v)
                    dotAccess.append(f'{currentType}_{value["value"]}')
                else:
                    value = self.processCall(v)
                    dotAccess.append(value['value'])
            elif 'name' in v:
                currentType = v['type']
                if v['name'] == 'self' and self.inClass:
                    # self is always a pointer
                    dotAccess.append('self->')
                else:
                    dotAccess.append(v['name'])
        return '.'.join(dotAccess).replace('->.','->')
    
    def formatArray(self, elements, elementType, size):
        self.listTypes.add(elementType)
        className = f'list_{elementType.replace("*", "ptr")}'
        if elementType in {'int', 'float', 'str'}:
            self.imports.add(f'#include "{className}.h"')
        else:
            raise SyntaxError(f'Array of type {elementType} not implemented yet.')
        values = ','.join(e['value'] for e in elements)
        if size == 'unknown':
            size = 10
        if elements:
            initValues = ';'.join(f'{{var}}.values[{i}] = {v["value"]}' for i, v in enumerate(elements))
        else:
            initValues = ''
        elementType = self.nativeType(elementType)
        return f"{className} {{var}} = {{{{ {len(elements)}, {size}, malloc(sizeof({elementType})*{size}) }}}};{initValues};"

    def formatInput(self, expr):
        self.imports.add('#include "photonInput.h"')
        message = self.formatPrint(expr).replace('\\n', '', 1) if expr['value'] else ''
        if not self.initInternal:
            initInternal = ' char* __inputStr__;'
            self.initInternal = True
        else:
            initInternal = ''
        return  f'{message}{initInternal} __inputStr__ = photonInput();'

    def formatStr(self, string, expressions):
        string = '"' + string[1:-1].replace('"', '\\"').replace('%', '%%') + '"'
        exprs = []
        if '{' in string:
            if self.target in {'win32', 'cygwin', 'msys'}:
                self.imports.add('#include "asprintf.h"')
            for expr in expressions:
                valType = expr['type']
                val = expr['value']
                exprs.append(val)
                if valType == 'str':
                    string = string.replace('{}', '%s', 1)
                elif valType == 'int':
                    string = string.replace('{}', '%d', 1)
                elif valType == 'float':
                    string = string.replace('{}', '%f', 1)
                else:
                    raise SyntaxError(f'Cannot format {valType} in formatStr')
        return string, exprs

    def formatCall(self, name, returnType, args):
        # Handle function arguments
        arguments = ', '.join(f'{arg["value"]}' if not arg['type'] in self.classes
            else f'&{arg["value"]}' for arg in args)
        return f'{name}({arguments})'
    
    def formatIndexAccess(self, token):
        if token['type'] == 'array':
            varType = token['elementType']
            indexAccess = self.processExpr(token['indexAccess'])['value']
            name = token['name']
            return f'list_{varType}_get(&{name}, {indexAccess})'
        else:
            raise SyntaxError(f'IndexAccess with type {token["type"]} not implemented yet')

    def formatIndexAssign(self, target, expr, inMemory=False):
        if target['type'] == 'array':
            index = self.processExpr(target['indexAccess'])['value']
            name = target['name']
            varType = target['elementType']
            if self.typeKnown(expr['type']) and expr['type'] != varType:
                cast = self.nativeType(varType)
            else:
                cast = None
            expr = self.formatExpr(expr, cast = cast, var = name)
            return f'list_{varType}_set(&{name}, {index}, {expr});'
        else:
            raise SyntaxError(f'Index assign with type {target["type"]} not implemented in c target.')

    def formatArrayAppend(self, target, expr):
        name = target['value']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        return f'list_{varType}_append(&{name}, {expr});'

    def formatArrayIncrement(self, target, index, expr):
        name = target['name']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        return f'list_{varType}_inc(&{name}, {index}, {expr});'

    def formatIncrement(self, target, expr):
        name = target['value']
        varType = target['type']
        expr = self.formatExpr(expr)
        return f'{name} += {expr};'

    def formatAssign(self, target, expr, inMemory = False):
        if target['token'] == 'var':
            variable = target['name']
            if variable in self.currentScope:
                varType = self.currentScope[variable]['type']
            elif self.typeKnown(target['type']):
                # Type was explicit
                varType = self.nativeType(target['type'])
            else:
                varType = self.nativeType(self.inferType(expr))
        else:
            raise SyntaxError(f'Format assign with variable {target} not implemented yet.')
        if 'format' in expr:
            # It's a format string
            formatstr = expr['format']
            values = ','.join(expr['values'])
            return f'{varType} {variable}; asprintf(&{variable}, {formatstr},{values});'
        if expr['type'] == 'array' and expr['elementType'] != self.currentScope[variable]['elementType']:
            cast = self.nativeType(varType)
        elif self.typeKnown(expr['type']) and expr['type'] != varType:
            cast = self.nativeType(varType)
        else:
            cast = None
        formattedExpr = self.formatExpr(expr, cast = cast, var = variable)
        # Check if type declaration is needed
        if inMemory:
            # Already defined, definition is not needed
            varType = ''
        else:
            varType = self.nativeType(varType) + ' '
        try:
            if expr['token'] == 'inputFunc' and not cast is None:
                return formattedExpr
            elif expr['token'] == 'inputFunc':
                return formattedExpr + f'{varType}{variable}; {variable} = __inputStr__;'
        except KeyError:
            pass
        if expr['type'] == 'array':
            return formattedExpr.format(var=variable)
        elif expr['type'] in self.classes:
            className = expr["type"]
            classInit = self.formatClassInit(className).format(var=variable)
            return f'{className} {variable} = {classInit};'
        return f'{varType}{variable} = {formattedExpr};'

    def formatExpr(self, value, cast=None, var=None):
        #TODO: implement cast to type
        if not cast is None:
            if cast == 'long':
                if 'token' in value and value['token'] == 'inputFunc':
                    return f'{value["value"]} {cast} {var} = strtol(__inputStr__, NULL, 10);'
                elif value['type'] == 'str':
                    return f'strtol({value["value"]}, NULL, 10)'
                elif value['type'] == 'float':
                    return f'(long) {value["value"]}'
                else:
                    raise SyntaxError(f'Convert from type {value["type"]} to type {cast} not implemented')
            elif cast == 'double':
                if 'token' in value and value['token'] == 'inputFunc':
                    return f'{value["value"]} {cast} {var} = strtod(__inputStr__, NULL);'
                elif value['type'] == 'str':
                    return f'strtod({value["value"]}, NULL)'
                elif value['type'] == 'int':
                    return f'(double) {value["value"]}'
                else:
                    raise SyntaxError(f'Convert from type {value["type"]} to type {cast} not implemented')
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
        self.step = 0
        self.freeTempArray = ''
        if 'from' in iterable:
            # For with range
            self.iterVar = variables[0]['value']
            varType = iterable['type']
            fromVal = iterable['from']['value']
            self.step = iterable['step']['value']
            toVal = iterable['to']['value']
            if self.iterVar in self.currentScope:
                varType = ''
            else:
                varType = varType + ' '
            return f'{varType}{self.iterVar} = {fromVal}; for (; {self.iterVar} < {toVal}; {self.iterVar} += {self.step}) {{'
        elif iterable['type'] == 'array':
            varType = iterable['elementType']
            self.iterVar = variables[0]['value']
            if self.iterVar in self.currentScope:
                varType = ''
            else:
                varType = varType + ' '
            if '{var}' in iterable['value']:
                # Temp array, must be initialized first
                tempArray = iterable['value'].format(var="__tempArray__")
                self.freeTempArray = 'free(__tempArray__.values); }'
                beginScope = '{{ '
                iterable["value"] = "__tempArray__"
                self.listTypes.add(varType)
            else:
                tempArray = ''
                beginScope = ''
            # tempArray is inside a scope block, must end that when closing the loop
            return f'{varType}{self.iterVar}; {beginScope}{tempArray}; for (int __iteration__=0; __iteration__ < {iterable["value"]}.len; __iteration__++) {{ {self.iterVar}={iterable["value"]}.values[__iteration__];'
        else:
            raise SyntaxError(f'Format for with iterable {iterable["type"]} not suported yet.')
    
    def formatEndFor(self):
        if self.step:
            # Must also close the tempArray scope block
            return f'}} {self.iterVar} -= {self.step};{self.freeTempArray}'
        else:
            # Must also close the tempArray scope block
            return f'}}{self.freeTempArray}'

    def formatArgs(self, args):
        return ', '.join([ 
            f'{self.nativeType(arg["type"])} {arg["value"]}' if not arg['type'] in self.classes
            else f'{self.nativeType(arg["type"])}* {arg["value"]}' for arg in args])

    def formatFunc(self, name, returnType, args):
        args = self.formatArgs(args)
        if self.inClass:
            # Its a method
            return f'/*def*/{self.nativeType(returnType)} {self.inClass}_{name}({args}) {{'
        else:
            return f'/*def*/{self.nativeType(returnType)} {name}({args}) {{'

    def formatEndFunc(self):
        return '}\n'

    def formatClass(self, name, args):
        self.className = name
        return f'typedef struct {self.className} {{'

    def formatEndClass(self):
        return f'}} {self.className};'

    def formatArrayInit(self, array):
        elements = array['elements']
        elementType = array['elementType']
        elementType = self.nativeType(elementType)
        size = array['size']
        if size == 'unknown':
            size = 10
        return f"{{ {len(elements)}, {size}, malloc(sizeof({elementType})*{size}) }}"

    def formatClassInit(self, className):
        attrs = self.classes[className]['attributes']
        defaultValues = ', '.join(
            a['value']['value'] if a['value']['type'] != 'array' else
            self.formatArrayInit(a['value']).replace('{','{{').replace('}','}}') for a in attrs)
        # Initialize array values
        # TODO: Initialize dict values
        initVals = ''
        for attr in self.classes[className]['attributes']:
            if attr['type'] == 'array':
                initVals += ';'.join(v.format(var=f"{{var}}.{attr['name']}") for v in attr['value']['value'].split(';')[1:]) + ';'
        return f'{{{{ {defaultValues} }}}}; {initVals}'

    def formatClassAttribute(self, variable, expr):
        varType = variable['type']
        if varType == 'array':
            elementType = expr['elementType']
            varType = f'list_{elementType}'
        name = variable['value']
        expr = self.formatExpr(expr)
        varType = self.nativeType(varType)
        return f'{varType} {name};'

    def formatReturn(self, expr):
        if expr:
            return f'return {expr["value"]};'
        return 'return;'

    def div(self, arg1, arg2):
        return {'value':f'({self.nativeType("float")}){arg1["value"]} / {arg2["value"]}', 'type':'float'}

    def exp(self, arg1, arg2):
        self.imports.add('#include <math.h>')
        self.links.add('-lm')
        return {'value':f'pow((double) {arg1["value"]}, (double) {arg2["value"]})', 'type':'float'}
    
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
                values = ', '.join(value['values'])
                return f'printf({formatstr}, {values});'
            return f'printf("%s\\n", {value["value"]});'
        elif value['type'] == 'bool':
            return f'if ({value["value"]} == 0) {{printf("False\\n");}} else {{printf("True\\n");}}'
        elif value['type'] == 'null':
            return 'printf("\\n");'
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
        if not 'c' in os.listdir('Sources'):
           os.mkdir('Sources/c')
        if not self.module:
            self.filename = 'main.c'
        else:
            self.filename = f'{moduleName}.c'
            boilerPlateStart = []
            boilerPlateEnd = []
            del self.imports[0]
            del self.imports[0]
            del self.imports[0]
        with open(f'Sources/c/{self.filename}', 'w') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w', '').replace('"', '')
                debug(f'Importing {module}')
                if module in os.listdir(f'{self.standardLibs}/native/c'):
                    from shutil import copyfile
                    copyfile(f'{self.standardLibs}/native/c/{module}', f'Sources/c/{module}')
                if f'{module}.c' in os.listdir('Sources/c'):
                    with open(f'Sources/c/{module}.c', 'r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp + '\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line[0] == '}':
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
            debug(' '.join(['gcc', '-O2', '-std=c99', f'Sources/c/{self.filename}'] + list(self.links) + ['-o', 'Sources/c/main']))
            check_call(['gcc', '-O2', '-std=c99', f'Sources/c/{self.filename}'] + list(self.links) + ['-o', 'Sources/c/main'])
        except Exception as e:
            print(e)
            print('Compilation error. Check errors above.')
        else:
            call(['./Sources/c/main'])
