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
        self.iterVar = []
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
        if name == 'math':
            # the link name is different
            name = 'm'
        self.links.add(f"-l{name}")
        return ''

    def formatVarInit(self, name, varType):
        return f'{varType} {name};'

    def formatDotAccess(self, tokens):
        dotAccess = []
        currentType = None
        for n, v in enumerate(tokens):
            if 'indexAccess' in v:
                # The value should be the dotAccess up to now
                v['name'] = '.'.join(dotAccess + [v['name']]).replace('->.','->')
                value = self.processIndexAccess(v)
                currentType = value['type']
                # Now the result is just this dotAccess
                dotAccess = [value['value']]
            elif v['token'] == 'call':
                if currentType in self.classes:
                    instance = dotAccess.pop()
                    v['args'] = [{'value':instance, 'type':currentType, 'pointer':True}] + v['args']
                    value = self.processCall(v, className=currentType)
                    dotAccess.append(f'{currentType}_{value["value"]}')
                else:
                    value = self.processCall(v)
                    dotAccess.append(value['value'])
            elif 'name' in v:
                currentType = v['type']
                if 'name' in v and v['type'] in self.classes:
                    if self.inFunc or self.inClass or n > 0:
                        dotAccess.append(f'{v["name"]}->')
                    else:
                        # Outside functions and classes, instances are not pointers
                        dotAccess.append(f'{v["name"]}')
                else:
                    dotAccess.append(v['name'])
        return '.'.join(dotAccess).replace('->.','->')
    
    def formatArray(self, elements, elementType, size):
        self.listTypes.add(elementType)
        className = f'list_{elementType.replace("*", "ptr")}'
        if elementType in {'int', 'float', 'str'}:
            self.imports.add(f'#include "{className}.h"')
            if elementType == 'str':
                self.imports.add('#include "asprintf.h"')
        else:
            raise SyntaxError(f'Array of type {elementType} not implemented yet.')
        if size == 'unknown':
            size = 10
        if elements:
            initValues = ';'.join(f'{{var}}.values[{i}] = {v["value"]}' for i, v in enumerate(elements))
        else:
            initValues = ''
        elementType = self.nativeType(elementType)
        return f"{className} {{var}} = {{{{ {len(elements)}, {size}, malloc(sizeof({elementType})*{size}) }}}};{initValues};"

    def formatMap(self, elements, keyType, valType):
        className = f'dict_{keyType.replace("*", "ptr")}_{valType.replace("*", "ptr")}'
        self.dictTypes.add(className)
        self.listTypes.add(keyType)
        self.listTypes.add(valType)
        if keyType in {'int', 'float', 'str'} and valType in {'int', 'float', 'str'}:
            self.imports.add(f'#include "{className}.h"')
            self.imports.add(f'#include "list_{keyType.replace("*", "ptr")}.h"')
            self.imports.add(f'#include "list_{valType.replace("*", "ptr")}.h"')
        else:
            raise SyntaxError(f'Dict of type {className} not implemented yet.')
        size = 10
        if elements:
            initValues = ';'.join(f'{{var}}.keys.values[{i}] = {v[0]["value"]}; {{var}}.values.values[{i}] = {v[1]["value"]}' for i, v in enumerate(elements))
        else:
            initValues = ''
        keyType = self.nativeType(keyType)
        valType = self.nativeType(valType)
        return f"{className} {{var}} = {{{{ {{{{ {len(elements)}, {size}, malloc(sizeof({keyType})*{size}) }}}}, {{{{ {len(elements)}, {size}, malloc(sizeof({valType})*{size}) }}}} }}}}; {initValues};"

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
            self.imports.add('#include "asprintf.h"')
            for expr in expressions:
                valType = expr['type']
                val = expr['value']
                exprs.append(val)
                if valType == 'str':
                    string = string.replace('{}', '%s', 1)
                elif valType == 'int':
                    string = string.replace('{}', '%ld', 1)
                elif valType == 'float':
                    string = string.replace('{}', '%f', 1)
                else:
                    raise SyntaxError(f'Cannot format {valType} in formatStr')
        return string, exprs

    def formatCall(self, name, returnType, args, kwargs):
        # Handle function arguments. Kwargs are in the right order
        if name in self.classes:
            args.append({'value':'{var}', 'type':name})
        arguments = ''
        permanentVars = ''
        tempVars = ''
        freeVars = ''
        for arg in args+kwargs:
            n = 0
            if arg['type'] == 'array':
                if '{var}' in arg['value']:
                    tempVars += f"{arg['value'].format(var=f'__tempVar{n}__')}; "
                    arguments += f'__tempVar{n}__, '
                    freeVars += f'free(__tempVar{n}__.values); '
                    n += 1
                else:
                    arguments += f"{arg['value']}, "
                
            elif arg['type'] in self.classes:
                if f"{arg['type']}_new(" in arg['value']:
                    permanentVars += f"{arg['type']} __permVar{self.instanceCounter}__ = {self.formatClassInit(arg['type'], f'__permVar{self.instanceCounter}__')[1]};"
                    arguments += f"&__permVar{self.instanceCounter}__, "
                    self.instanceCounter += 1
                else:
                    arguments += f"&{arg['value']}, "
            else:
                arguments += f"{arg['value']}, "
        arguments = arguments[:-2]
        if name in self.classes:
            name = f'{name}_new'
        if tempVars or permanentVars:
            return f'{permanentVars} {{ {tempVars}{name}({arguments}); {freeVars} }}'
        return f'{name}({arguments})'
    
    def formatIndexAccess(self, token):
        if token['type'] == 'array':
            varType = token['elementType']
            indexAccess = self.processExpr(token['indexAccess'])['value']
            name = token['name']
            return f'list_{varType}_get(&{name}, {indexAccess})'
        elif token['type'] == 'map':
            keyType = token['keyType']
            valType = token['valType']
            indexAccess = self.processExpr(token['indexAccess'])['value']
            name = token['name']
            return f'dict_{keyType}_{valType}_get(&{name}, {indexAccess})'
        else:
            raise SyntaxError(f'IndexAccess with type {token["type"]} not implemented yet')

    def formatIndexAssign(self, target, expr, inMemory=False):
        assignType = None
        if target['type'] == 'array':
            assignType = 'array'
            index = self.processExpr(target['indexAccess'])['value']
            name = target['name']
            varType = target['elementType']
        elif 'dotAccess' in target and target['dotAccess'][-1]['type'] == 'array':
            assignType = 'array'
            index = self.processExpr(target['dotAccess'][-1]['indexAccess'])['value']
            name = target['dotAccess'][-1]['name']
            varType = target['dotAccess'][-1]['elementType']
        elif target['type'] == 'map':
            assignType = 'map'
            index = self.processExpr(target['indexAccess'])['value']
            name = target['name']
            varType = target['valType']
            keyType = target['keyType']
        else:
            raise SyntaxError(f'Index assign with type {target["type"]} not implemented in c target.')

        if self.typeKnown(expr['type']) and expr['type'] != varType:
            cast = self.nativeType(varType)
        else:
            cast = None
        expr = self.formatExpr(expr, cast = cast, var = name)

        if assignType == 'array':
            return f'list_{varType}_set(&{name}, {index}, {expr});'
        elif assignType == 'map':
            return f'dict_{keyType}_{varType}_set(&{name}, {index}, {expr});'
        else:
            raise SyntaxError('This assign type for indexAssign is not implemented yet.')

    def formatArrayAppend(self, target, expr):
        name = target['value']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        return f'list_{varType}_append(&{name}, {expr});'

    def formatArrayIncrement(self, target, index, expr):
        if 'name' in target:
            name = target['name']
            varType = target['elementType']
        else:
            # dotAccess
            name = target['dotAccess'][-1]['name']
            varType = target['dotAccess'][-1]['elementType']
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
        elif target['token'] == 'dotAccess':
            v = self.getValAndType(target)
            variable = v['value']
            varType = v['type']
        else:
            raise SyntaxError(f'Format assign with variable {target} not implemented yet.')
        if 'format' in expr:
            # It's a format string
            formatstr = expr['format']
            values = ','.join(expr['values'])
            varType = self.nativeType(varType)
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
        if expr['type'] in {'array', 'map'}:
            return formattedExpr.format(var=variable)
        elif expr['type'] in self.classes:
            className = expr["type"]
            permanentVars, classInit = self.formatClassInit(className, variable)
            initMethod = expr['value'].replace('{var}',variable) + ';'
            return f'{permanentVars}; {className} {variable} = {classInit};{initMethod}'
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
                    return f'(long)({value["value"]})'
                else:
                    raise SyntaxError(f'Convert from type {value["type"]} to type {cast} not implemented')
            elif cast == 'double':
                if 'token' in value and value['token'] == 'inputFunc':
                    return f'{value["value"]} {cast} {var} = strtod(__inputStr__, NULL);'
                elif value['type'] == 'str':
                    return f'strtod({value["value"]}, NULL)'
                elif value['type'] == 'int':
                    return f'(double)({value["value"]})'
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
            self.iterVar.append(variables[0]['value'])
            varType = iterable['type']
            fromVal = iterable['from']['value']
            self.step = iterable['step']['value']
            toVal = iterable['to']['value']
            if self.iterVar[-1] in self.currentScope:
                varType = ''
            else:
                varType = varType + ' '
            return f'{varType}{self.iterVar[-1]} = {fromVal}; for (; {self.iterVar[-1]} < {toVal}; {self.iterVar[-1]} += {self.step}) {{'
        elif iterable['type'] == 'array':
            varType = iterable['elementType']
            self.iterVar.append(variables[0]['value'])
            if self.iterVar[-1] in self.currentScope:
                varType = ''
            else:
                varType = varType
            if '{var}' in iterable['value']:
                # Temp array, must be initialized first
                tempArray = iterable['value'].format(var="__tempArray__")
                self.freeTempArray = 'free(__tempArray__.values); }'
                beginScope = '{ '
                iterable["value"] = "__tempArray__"
                self.listTypes.add(varType)
            else:
                tempArray = ''
                beginScope = ''
            # tempArray is inside a scope block, must end that when closing the loop
            return f'{self.nativeType(varType)} {self.iterVar[-1]}; {beginScope}{tempArray}; for (int __iteration__=0; __iteration__ < {iterable["value"]}.len; __iteration__++) {{ {self.iterVar[-1]}={iterable["value"]}.values[__iteration__];'
        else:
            raise SyntaxError(f'Format for with iterable {iterable["type"]} not suported yet.')
    
    def formatEndFor(self):
        if self.step:
            # Must also close the tempArray scope block
            return f'}} {self.iterVar.pop()} -= {self.step};{self.freeTempArray}'
        else:
            # consume the iterVar of this loop
            self.iterVar.pop()
            # Must also close the tempArray scope block
            return f'}}{self.freeTempArray}'

    def formatArgs(self, args):
        newArgs = []
        for arg in args:
            if arg['type'] == '%{className}%':
                arg['type'] = self.inClass
            elif arg['type'] == 'array':
                arg['type'] = f"list_{arg['elementType']}"
            newArgs.append(arg)
        args = newArgs

        return ', '.join([ 
            f'{self.nativeType(arg["type"])} {arg["value"]}' if not arg['type'] in self.classes
            else f'{self.nativeType(arg["type"])}* {arg["value"]}' for arg in args])

    def formatFunc(self, name, returnType, args, kwargs):
        # convert kwargs to args
        newKwargs = []
        for kw in kwargs:
            kwarg = {'value':kw['name'], 'type':kw['type']}
            if kw['type'] == 'array':
                kwarg['elementType'] = kw['elementType']
            newKwargs.append(kwarg)
        kwargs = newKwargs
        args = self.formatArgs(args+kwargs)
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

    def formatClassDefaultValue(self, kwarg):
        name = kwarg['name']
        value = kwarg['value']
        return f'{self.self}->{name} = {name};'

    def formatClassInit(self, className, variable):
        attrs = self.classes[className]['attributes']
        defaultValues = []
        permanentVars = ''
        initVals = ''
        for a in attrs:
            if a['variable']['type'] in self.classes:
                attrClassName = a['variable']['type']
                #defaultValues.append(f'malloc(sizeof({attrClassName}))')
                defaultValues.append(f'&__permVar{self.instanceCounter}__')
                # Get initVals of the attribute class
                permanentVar = ';'.join(self.formatClassInit(a['variable']['type'], f'{variable}.{a["variable"]["value"]}')[1].split(';'))
                permanentVars += f"{a['variable']['type']} __permVar{self.instanceCounter}__ = {permanentVar}; "
                self.instanceCounter += 1
            elif a['variable']['type'] == 'array':
                defaultValues.append(self.formatArrayInit(a['expr']))
                initVals += ';'.join(v.format(var=f"{variable}.{a['variable']['value']}") for v in a['expr']['value'].split(';')[1:]) + ';'
            else:
                defaultValues.append(a['expr']['value'])
        defaultValues = ', '.join(defaultValues)
        # TODO: Initialize dict values
        return permanentVars, f'{{ {defaultValues} }}; {initVals}'

    def formatClassAttribute(self, variable, expr):
        varType = variable['type']
        if varType == 'array':
            elementType = expr['elementType']
            varType = f'list_{elementType}'
        name = variable['value']
        expr = self.formatExpr(expr)
        varType = self.nativeType(varType)
        if varType in self.classes:
            return f'{varType}* {name};'
        else:
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
            return f'printf("%s\\n", ({value["value"]}) ? "True" : "False");'
        elif value['type'] == 'null':
            return 'printf("\\n");'
        else:
            raise SyntaxError(f'Print function with token {value} not supported yet.')

    def sortedImports(self):
        ''' Imports must be sorted to avoid definition errors or conflicts '''
        # Lists must be imported before dicts
        imports = sorted(list(self.imports), reverse=True)
        try:
            index = imports.index('#include "list_str.h"')
        except ValueError:
            pass
        else:
            aspIndex = imports.index('#include "asprintf.h"')
            # asprintf must come before list_str. Switch if not
            if aspIndex > index:
                imports[index], imports[aspIndex] = imports[aspIndex], imports[index]
        return imports
                
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
            moduleName = self.filename.split('.')[0]    
            self.filename = f'{moduleName}.c'
            boilerPlateStart = []
            boilerPlateEnd = []
        with open(f'Sources/c/{self.filename}', 'w') as f:
            for imp in self.sortedImports():
                module = imp.split(' ')[-1].replace('.w', '').replace('"', '')
                debug(f'Importing {module}')
                if module in os.listdir(f'{self.standardLibs}/native/c'):
                    from shutil import copyfile
                    copyfile(f'{self.standardLibs}/native/c/{module}', f'Sources/c/{module}')
                if not f'{module}.c' in os.listdir('Sources/c'):
                    # native import
                    f.write(imp + '\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line[0] == '}':
                        indent -= 4
                if self.debug:
                    # pretty output
                    for l in line.replace('/*def*/','').split(';'):
                        l = l.strip()
                        if l:
                            f.write(' ' * indent + l + ';\n')
                    f.write('\n')
                else:
                    # Ugly, but faster
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
