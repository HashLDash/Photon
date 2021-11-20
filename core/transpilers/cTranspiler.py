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
        self.imports = {'#include <stdio.h>', '#include <stdlib.h>', '#include <locale.h>', '#include "main.h"'}
        self.funcIdentifier = '/*def*/'
        self.constructorName = 'new'
        self.block = {'typedef ','/*def*/', 'for ','while ','if ','else ', 'int main('}
        self.true = '1'
        self.false = '0'
        self.null = 'NULL'
        self.self = 'self'
        self.methodsInsideClass = False
        self.notOperator = '!'
        self.links = set()
        if self.debug:
            # compile with debug symbols for gdb
            self.links.add('-g')
            self.links.add('-Wall')
        self.expressionBuffer = None
        self.listTypes = set()
        self.dictTypes = set()
        self.permVarCounter = 0
        self.tempVarCounter = 0
        self.iterVar = []
        self.nativeTypes = {
            'float': 'double',
            'int': 'long',
            'str': 'char*',
            'bool': 'int',
            'void': 'void',
            'func': 'void',
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
        if name not in {'time'}:
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
                if 'elementType' in v:
                    baseType = 'array'
                elif 'keyType' in v:
                    baseType = 'map'
                else:
                    raise TypeError(f'Base type of {v} not implemented yet.')
                v['type'] = baseType
                value = self.processIndexAccess(v)
                currentType = value['type']
                # Now the result is just this dotAccess
                if currentType in self.classes:
                    # arrays and dicts with classes are all pointers
                    dotAccess = [value['value']+'->']
                else:
                    dotAccess = [value['value']]
            elif v['token'] == 'call':
                if currentType in self.classes:
                    instance = dotAccess.pop()
                    # include instance as the first arg in the call
                    v['args'] = [{'value':instance.replace('->',''), 'type':currentType, 'pointer':True}] + v['args']
                    value = self.processCall(v, className=currentType)
                    if self.inFunc:
                        if self.inClass and instance == 'super->':
                            # Call the method only without a dot access
                            call = value['value'].replace('!@instance@!', '').replace(f'{v["name"]["name"]}(super', f'{v["name"]["name"]}(({currentType}*)self')

                            value['value'] = f'{currentType}_{call}'
                        else:
                            call = value['value'].replace('!@instance@!', '')
                            value['value'] = '.'.join(dotAccess + [instance, call]).replace('->.','->')
                    else:
                        # if outside, use . instead
                        value['value'] = value['value'].replace('!@instance@!', instance + '.')
                    dotAccess = [value['value']]
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
        if not self.typeKnown(elementType):
            raise SyntaxError(f'Array with elements of type {elementType} not supported yet.')
        if not elementType in self.listTypes:
            self.listTypes.add(elementType)
            if elementType in self.classes:
                self.insertCode(f'#include "list_{elementType}.h"')
                self.insertCode(f'#include "list_{elementType}.c"')
        className = f'list_{elementType.replace("*", "ptr")}'
        if elementType == 'str' or elementType not in {'int', 'float'}:
            self.imports.add('#include "asprintf.h"')
        self.imports.add(f'#include "{className}.h"')
        if size == 'unknown':
            size = 10
        if elements:
            initValues = []
            for i, v in enumerate(elements):
                if v['type'] in self.classes:
                    permVars, init = self.formatClassInit(v['type'], f'{{var}}.values[{i}]')
                    init = init.replace('{','{{').replace('}','}}')
                    newMethod = v['value'].format(var=f'__permVar{self.permVarCounter}__')
                    initValues.append(f'{v["type"]} __permVar{self.permVarCounter}__ = {init};{newMethod}')
                    if elementType != v['type']:
                        cast = f'({elementType}*)'
                    else:
                        cast = ''
                    initValues.append(f'{{var}}.values[{i}] = {cast}&__permVar{self.permVarCounter}__')
                    self.permVarCounter += 1
                else:
                    initValues.append(f'{{var}}.values[{i}] = {v["value"]}')
            initValues = ';'.join(initValues)
        else:
            initValues = ''
        elementType = self.nativeType(elementType)
        return f"{className} {{var}} = {{{{ {len(elements)}, {size}, malloc(sizeof({elementType})*{size}) }}}};{initValues};"

    def formatMap(self, elements, keyType, valType):
        className = f'dict_{keyType.replace("*", "ptr")}_{valType.replace("*", "ptr")}'
        self.dictTypes.add((keyType, valType))
        if keyType in {'int', 'float', 'str'}:
            if valType in {'int', 'float', 'str'}:
                self.imports.add(f'#include "{className}.h"')
            elif valType in self.classes:
                self.imports.add(f'#include "{className}.h"')
            else:
                raise SyntaxError(f'Dict of type {className} not implemented yet.')
        else:
            raise SyntaxError(f'Dict of type {className} not implemented yet.')
        size = 10
        if elements:
            initValues = ';'.join(f'dict_{keyType}_{valType}_set(&{{var}}, {v[0]["value"]}, {v[1]["value"]})' for v in elements) + ';'
        else:
            initValues = ''
        return f"{className} {{var}} = {{{{ 0, {size}, malloc(sizeof(int)*{size}), malloc(sizeof(dict_{keyType}_{valType}_entry)*{size}) }}}}; for(int i=0; i<{size}; i++) {{{{ {{var}}.indices[i]=-1; }}}} {initValues};{initValues}"

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
        if string[0] in {'"', "'"}:
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
                    string = string.replace('{}', '%g', 1)
                elif valType == 'bool':
                    string = string.replace('{}', '%s', 1)
                    exprs[-1] = f'({exprs[-1]}) ? "True" : "False"'
                elif valType == 'array':
                    string = string.replace('{}', '%s', 1)
                    exprs[-1] = f'list_{expr["elementType"]}_str(&{exprs[-1]})'
                elif valType == 'map':
                    string = string.replace('{}', '%s', 1)
                    exprs[-1] = f'dict_{expr["keyType"]}_{expr["valType"]}_str(&{exprs[-1]})'
                else:
                    raise SyntaxError(f'Cannot format {valType} in formatStr')
        return string, exprs

    def formatCall(self, name, returnType, args, kwargs, className, callback):
        # Handle function arguments. Kwargs are in the right order
        if name in self.classes:
            args.insert(0, {'value':'{var}', 'type':name})
        arguments = ''
        permanentVars = ''
        tempVars = ''
        for arg in args+kwargs:
            if arg['type'] == 'array':
                if '{var}' in arg['value']:
                    permanentVars += f"{arg['value'].format(var=f'__permVar{self.permVarCounter}__')}; "
                    arguments += f'__permVar{self.permVarCounter}__, '
                    self.permVarCounter += 1
                else:
                    arguments += f"{arg['value']}, "
                
            elif arg['type'] in self.classes:
                if 'cast' in arg:
                    cast = f"({arg['cast']}*)"
                else:
                    cast = ''
                if f"{arg['type']}_new(" in arg['value']:
                    argPermVars, argInit = self.formatClassInit(arg['type'], f'__permVar{self.permVarCounter}__')
                    arg['value'] = arg['value'].format(var=f'__permVar{self.permVarCounter}__')
                    permanentVars += f"{argPermVars} {arg['type']} __permVar{self.permVarCounter}__ = {argInit}; {arg['value']};"
                    arguments += f"{cast}&__permVar{self.permVarCounter}__, "
                    self.permVarCounter += 1
                elif self.inFunc:
                    arguments += f"{cast}{arg['value']}, "
                else:
                    arguments += f"{cast}&{arg['value']}, "
            else:
                arguments += f"{arg['value']}, "
        arguments = arguments[:-2]
        if name in self.classes:
            # only call new if it exists
            if 'new' in self.classes[name]['methods']:
                name = f'{name}_new'
            else:
                return ''
        instance = '' if className is None else f'!@instance@!'
        if tempVars or permanentVars:
            self.insertCode(permanentVars)
            self.insertCode(tempVars)
            if callback:
                return f'(*{name})({arguments})'
            return f'{instance}{name}({arguments})'
        if callback:
            return f'(*{name})({arguments})'
        return f'{instance}{name}({arguments})'
    
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
        preparation = ''
        if expr['type'] in self.classes:
            variable = f'__permVar{self.permVarCounter}__'
            self.permVarCounter += 1
            className = expr["type"]
            permanentVars, classInit = self.formatClassInit(className, variable)
            initMethod = expr['value'].replace('{var}',variable) + ';'
            if inMemory:
                preparation = f'{permanentVars};{initMethod};'
            preparation = f'{permanentVars}; {className} {variable} = {classInit};{initMethod};'
            expr = f'&{variable}'
        else:
            expr = self.formatExpr(expr, cast = cast, var = name)

        if assignType == 'array':
            return f'{preparation}list_{varType}_set(&{name}, {index}, {expr});'
        elif assignType == 'map':
            return f'{preparation}dict_{keyType}_{varType}_set(&{name}, {index}, {expr});'
        else:
            raise SyntaxError('This assign type for indexAssign is not implemented yet.')

    def formatArrayAppend(self, target, expr):
        name = target['value']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        if varType in self.classes and not (self.inFunc or self.inClass):
            return f'list_{varType}_append(&{name}, &{expr});'
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
        if varType == 'str':
            self.imports.add('#include "asprintf.h"')
            self.imports.add('#include <string.h>')
            return f'asprintf(&{name}, "%s%s", {name}, {expr});'
        return f'{name} += {expr};'

    def formatArrayRemoveAll(self, target, expr):
        name = target['value']
        varType = target['elementType']
        expr = self.formatExpr(expr)
        return f'list_{varType}_removeAll(&{name}, {expr});'

    def formatAssign(self, variable, varType, cast, expr, inMemory = False):
        if 'format' in expr:
            # It's a format string
            formatstr = expr['format']
            values = ','.join(expr['values'])
            varType = self.nativeType(varType)
            return f'{varType} {variable}; asprintf(&{variable}, {formatstr},{values});'
        formattedExpr = self.formatExpr(expr, cast = cast, var = variable)
        # Check if type declaration is needed
        if inMemory:
            # Already defined, definition is not needed
            varType = ''
        else:
            varType = self.nativeType(varType) + ' '
        try:
            if expr['token'] == 'inputFunc' and cast is not None:
                return formattedExpr.format(cast=varType, var=variable)
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
            if inMemory:
                return f'{permanentVars};{initMethod}'
            return f'{permanentVars}; {className} {variable} = {classInit};{initMethod}'
        if varType == self.nativeType('str') + ' ':
            # if defined with char* it cannot be modified
            if '__tempVar' in formattedExpr:
                # Already allocated memory, just reassign
                return f'char* {variable} = {formattedExpr};'
            else:
                return f'char* {variable} = {formattedExpr};'
        return f'{varType}{variable} = {formattedExpr};'

    def formatExpr(self, value, cast=None, var=None):
        if cast is not None and self.nativeType(value['type']) != cast:
            if cast == 'long':
                if 'token' in value and value['token'] == 'inputFunc':
                    return f'{value["value"]} {{cast}} {var} = strtol(__inputStr__, NULL, 10);'
                elif value['type'] == 'str':
                    return f'strtol({value["value"]}, NULL, 10)'
                elif value['type'] == 'float':
                    return f'(long)({value["value"]})'
                else:
                    raise SyntaxError(f'Convert from type {value["type"]} to type {cast} not implemented')
            elif cast == 'double':
                if 'token' in value and value['token'] == 'inputFunc':
                    return f'{value["value"]} {{cast}} {var} = strtod(__inputStr__, NULL);'
                elif value['type'] == 'str':
                    return f'strtod({value["value"]}, NULL)'
                elif value['type'] == 'int':
                    return f'(double)({value["value"]})'
                elif value['type'] == 'float':
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
        self.iterVar.append(variables)
        if 'from' in iterable:
            # For with range
            varType = iterable['type']
            fromVal = iterable['from']['value']
            self.step = iterable['step']['value']
            toVal = iterable['to']['value']
            if self.iterVar[-1][-1] in self.currentScope:
                varType = ''
            else:
                varType = self.nativeType(varType) + ' '
            if len(variables) == 2:
                counterVar = variables[0]
                return f'{varType}{self.iterVar[-1][-1]} = {fromVal}; for (long {counterVar}=-1; {self.iterVar[-1][-1]} < {toVal}; {self.iterVar[-1][-1]} += {self.step}) {{ {counterVar}++;'
            else:
                return f'{varType}{self.iterVar[-1][-1]} = {fromVal}; for (; {self.iterVar[-1][-1]} < {toVal}; {self.iterVar[-1][-1]} += {self.step}) {{'
        elif iterable['type'] == 'array':
            varType = iterable['elementType']
            if self.iterVar[-1][-1] in self.currentScope:
                varType = ''
            else:
                if varType in self.classes:
                    varType = self.nativeType(varType) + "*"
                else:
                    varType = self.nativeType(varType)
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
            if len(variables) == 2:
                counterVar = variables[0]
            else:
                counterVar = f'__tempVar{self.tempVarCounter}__'
                self.tempVarCounter += 1
            return f'{varType} {self.iterVar[-1][-1]}; {beginScope}{tempArray}; for (long {counterVar}=0; {counterVar} < {iterable["value"]}.len; {counterVar}++) {{ {self.iterVar[-1][-1]}={iterable["value"]}.values[{counterVar}];'
        elif iterable['type'] == 'map':
            varType = iterable['keyType']
            if '{var}' in iterable['value']:
                # Temp array, must be initialized first
                #TODO: create dict in memory
                tempArray = iterable['value'].format(var="__tempArray__")
                self.freeTempArray = 'free(__tempArray__.values); }'
                iterable["value"] = "__tempArray__"
            else:
                tempArray = ''
            if len(variables) == 3:
                counterVar, keyVar, valVar = variables
                if counterVar in self.currentScope:
                    counterVarType = ''
                else:
                    counterVarType = 'long'
            else:
                if len(variables) == 2:
                    keyVar, valVar = variables
                else:
                    keyVar = variables[0]
                counterVar = f'__tempVar{self.tempVarCounter}__'
                self.tempVarCounter += 1
                counterVarType = 'long'
            if keyVar in self.currentScope:
                varType = ''
            else:
                varType = self.nativeType(varType)
            if len(variables) >= 2:
                if self.iterVar[-1][-1] in self.currentScope:
                    valVarType = ''
                else:
                    if varType in self.classes:
                        valVarType = self.nativeType(varType) + "*"
                    else:
                        valVarType = self.nativeType(varType)
                return f'{varType} {keyVar};{valVarType} {valVar}; {tempArray}; for ({counterVarType} {counterVar}=0; {counterVar} < {iterable["value"]}.len; {counterVar}++) {{ {keyVar}={iterable["value"]}.entries[{counterVar}].key; {valVar}={iterable["value"]}.entries[{counterVar}].val;'
            else:
                return f'{varType} {keyVar}; {tempArray}; for (long {counterVar}=0; {counterVar} < {iterable["value"]}.len; {counterVar}++) {{ {keyVar}={iterable["value"]}.entries[{counterVar}].key;'
        elif iterable['type'] == 'str':
            varType = 'str'
            self.imports.add('#include <string.h>')
            if self.iterVar[-1][-1] in self.currentScope:
                varCreation = f''
            else:
                varCreation = f'char {self.iterVar[-1][-1]}[] = \" \";'
            if len(variables) == 2:
                counterVar = f'{variables[0]}'
                if variables[0] in self.currentScope:
                    counterVarType = ''
                else:
                    counterVarType = self.nativeType('int')
            else:
                counterVar = f'__tempVar{self.tempVarCounter}'
                self.tempVarCounter += 1
                counterVarType = self.nativeType('int')
            charLen = f'__tempVar{self.tempVarCounter}__'
            self.tempVarCounter += 1
            if iterable['value'].startswith('"'):
                iterableVar = f'__tempVar{self.tempVarCounter}__'
                self.tempVarCounter += 1
                iterableVarCreation = f"char* {iterableVar}  = {iterable['value']};"
            else:
                iterableVarCreation = "";
                iterableVar = iterable['value']
            pos = f'__tempVar{self.tempVarCounter}__'
            self.tempVarCounter += 1
            temp = f'__tempVar{self.tempVarCounter}__'
            self.tempVarCounter += 1
            return f"""{iterableVarCreation}
    long {pos} = 0;
    int {charLen};
    {varCreation}
    {counterVarType} {counterVar} = -1;
    while ({iterableVar}[{pos}] != '\\0' && ({charLen} = mblen({iterableVar}+{pos}, 2))) {{
        for (int {temp} = 0; {temp}<{charLen}; {temp}++) {{
            {self.iterVar[-1][-1]}[{temp}] = {iterableVar}[{pos}+{temp}];
        }}
        {self.iterVar[-1][-1]}[{charLen}] = '\\0';
        {pos} += {charLen};
        {counterVar}++;"""
        else:
            raise SyntaxError(f'Format for with iterable {iterable["type"]} not suported yet.')
    
    def formatEndFor(self):
        if self.step:
            # Must also close the tempArray scope block
            return f'}} {self.iterVar.pop()[-1]} -= {self.step};{self.freeTempArray}'
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
            elif 'func' in arg['type']:
                #callback
                #TODO: implement return types
                arg['value'] = f"(*{arg['value']})()"
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

    def reformatInheritedMethodDefinition(self, definition, methodName, className, inheritedName):
        definition = definition.replace(
            f'{inheritedName}_{methodName}({inheritedName}',
            f'{className}_{methodName}({className}')
        self.classes[className]['methods'][methodName]['code'][0] = definition

    def formatEndClass(self):
        return f'}} {self.className};'

    def formatArrayInit(self, array):
        elements = array['elements']
        elementType = array['elementType']
        elementType = self.nativeType(elementType)
        size = array['size']
        if size == 'unknown':
            size = 8
        return f"{{ {len(elements)}, {size}, malloc(sizeof({elementType})*{size}) }}"

    def formatClassDefaultValue(self, arg):
        if 'name' in arg:
            # its a kwarg
            name = arg['name']
            value = arg['value']
        else:
            # its an arg
            name = arg['value']
        return f'{self.self}->{name} = {name};'

    def formatClassInit(self, className, variable):
        attrs = self.classes[className]['attributes']
        defaultValues = []
        permanentVars = ''
        initVals = ''
        for a in attrs:
            if 'returnType' in a:
                defaultValues.append(f'&{className}_{a["name"]}')
            elif a['variable']['type'] in self.classes:
                attrClassName = a['variable']['type']
                #defaultValues.append(f'malloc(sizeof({attrClassName}))')
                # Get initVals of the attribute class
                argPermVars, argInit = self.formatClassInit(a['variable']['type'], f'{variable}.{a["variable"]["value"]}')
                permanentVars += f"{argPermVars} {a['variable']['type']} __permVar{self.permVarCounter}__ = {argInit}; "
                defaultValues.append(f'&__permVar{self.permVarCounter}__')
                self.permVarCounter += 1
            elif a['variable']['type'] == 'array':
                defaultValues.append(self.formatArrayInit(a['expr']))
                initVals += ';'.join(v.format(var=f"{variable}.{a['variable']['value']}") for v in a['expr']['value'].split(';')[1:]) + ';'
            else:
                defaultValues.append(a['expr']['value'])
        defaultValues = ', '.join(defaultValues)
        # TODO: Initialize dict values
        return permanentVars, f'{{ {defaultValues} }}; {initVals}'

    def formatClassAttribute(self, attr):
        if 'returnType' in attr:
            # Its a method
            methodReturnType = self.nativeType(attr['returnType'])
            method = attr['name']
            args = attr['args'] + attr['kwargs']
            argsTypes = []
            for a in args:
                attrType = self.nativeType(a['type'])
                if attrType == 'array':
                    argsTypes.append(f"list_{a['elementType']}")
                elif a['type'] in self.classes:
                    argsTypes.append(f'struct {attrType}*')
                elif a['type'] == 'func':
                    #TODO: Add real return type
                    argsTypes.append(f'void (*)()')
                else:
                    argsTypes.append(attrType)

            argsTypes = ', '.join(argsTypes)
            return f'{methodReturnType} (*{method})({argsTypes});'
        else:
            # Its a variable
            variable = attr['variable']
            expr = attr['expr']
            varType = variable['type']
            if varType == 'array':
                elementType = expr['elementType']
                varType = f'list_{elementType}'
            name = variable['value']
            expr = self.formatExpr(expr)
            varType = self.nativeType(varType)
            if varType in self.classes:
                return f'{varType}* {name};'
            elif variable['type'] == 'func':
                # Its a callback
                #TODO: Handle real type
                return f'{varType} (*{name})();'
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

    def formatPrint(self, value, terminator='\\n'):
        if value['type'] == 'int':
            return f'printf("%ld{terminator}", {value["value"]});'
        elif value['type'] == 'float':
            return f'printf("%g{terminator}", {value["value"]});'
        elif value['type'] == 'str':
            if 'format' in value:
                # It's a format string
                formatstr = value['format'][:-1] + terminator + value['format'][-1:]
                values = ', '.join(value['values'])
                return f'printf({formatstr}, {values});'
            return f'printf("%s{terminator}", {value["value"]});'
        elif value['type'] == 'bool':
            return f'printf("%s{terminator}", ({value["value"]}) ? "True" : "False");'
        elif value['type'] == 'null':
            return f'printf("{terminator}");'
        elif value['type'] == 'array':
            elementType = value['elementType']
            return f'list_{elementType}_repr(&{value["value"]});'
        elif value['type'] == 'map':
            keyType = value['keyType']
            valType = value['valType']
            return f'dict_{keyType}_{valType}_repr(&{value["value"]});'
        elif value['type'] in self.classes:
            if 'repr' in self.classes[value['type']]['methods']:
                if self.inFunc or self.inClass:
                    return f'printf("%s{terminator}", {value["type"]}_repr({value["value"]}));'
                else:
                    return f'printf("%s{terminator}", {value["type"]}_repr(&{value["value"]}));'
            else:
                return f'printf("<class {value["type"]}>{terminator}");'
        else:
            raise SyntaxError(f'Print function with token {value} not supported yet.')

    def add(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'str' or t2 == 'str':
            self.imports.add('#include "asprintf.h"')
            self.imports.add('#include <string.h>')
            self.insertCode(f'char* __tempVar{self.tempVarCounter}__ = malloc(strlen({arg1["value"]}) + strlen({arg2["value"]}) + 1);')
            self.insertCode(f'asprintf(&__tempVar{self.tempVarCounter}__, "%s%s", {arg1["value"]}, {arg2["value"]});')
            self.tempVarCounter += 1

            return {'value':f'__tempVar{self.tempVarCounter - 1}__', 'type':'str', 'expressions':[]}
        else:
            return super().add(arg1, arg2)
                
    def formatDelete(self, expr, name, varType):
        valType = expr['type']
        keyType = expr['indexAccess']['type']
        if varType == 'array':
            return expr['value'].replace(f'list_{valType}_get(', f'list_{valType}_del(') + ';'
        elif varType == 'map':
            return expr['value'].replace(f'dict_{keyType}_{valType}_get(', f'dict_{keyType}_{valType}_del(') + ';'
        else:
            raise NotImplemented

    def renderDictTemplate(self, keyType, valType):
        formatCodes = {'int':'%ld', 'str':'\\"%s\\"', 'float':'%lf'}
        with open(f'{self.standardLibs}/native/c/dict_{keyType}.template') as template:
            dictLib = template.read()
        valNativeType = self.nativeType(valType)
        if valType in self.classes:
            valNativeType += "*"
        #TODO: Call instance repr if it exists instead of the placeholder
        dictLib = dictLib.replace('!@valType@!', valType).replace('!@valNativeType@!', valNativeType).replace('!@formatCode@!', formatCodes[valType] if valType in formatCodes else f'<class {valType}>')
        with open(f'Sources/c/dict_{keyType}_{valType}.h', 'w') as lib:
            lib.write(dictLib)

    def renderListTemplate(self, valType):
        if not valType in {'str', 'int', 'float'}:
            with open(f'{self.standardLibs}/native/c/list_template.h') as template:
                listLib = template.read()
            listLib = listLib.replace('!@valType@!', valType)
            with open(f'Sources/c/list_{valType}.h', 'w') as lib:
                lib.write(listLib)
            with open(f'{self.standardLibs}/native/c/list_template.c') as template:
                listLib = template.read()
            listLib = listLib.replace('!@valType@!', valType)
            with open(f'Sources/c/list_{valType}.c', 'w') as lib:
                lib.write(listLib)

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
        with open(f'Sources/c/main.h', 'w') as f:
            indent = 0
            f.write('#ifndef __main_h\n#define __main_h\n')
            listTypeHints = []
            for listType in self.listTypes:
                if listType in self.classes:
                    listTypeHints.append(f'typedef struct list_{listType} list_{listType};')
            #TODO: do the same type hint for dicts
            for line in listTypeHints + self.header:
                if '}' in line:
                    indent -= 4
                f.write(' '*indent + line+'\n')
                if self.isBlock(line) and not ';' in line[-1]:
                    indent += 4
            f.write('#endif')
        indent = 0
        with open(f'Sources/c/{self.filename}', 'w') as f:
            f.write('#ifndef __main\n#define __main\n')
            for imp in sorted(self.imports):
                module = imp.split(' ')[-1].replace('.w', '').replace('"', '')
                debug(f'Importing {module}')
                if module in os.listdir(f'{self.standardLibs}/native/c'):
                    from shutil import copyfile
                    copyfile(f'{self.standardLibs}/native/c/{module}', f'Sources/c/{module}')
                if not f'{module}.c' in os.listdir('Sources/c'):
                    # native import
                    f.write(imp + '\n')
                for valType in self.listTypes:
                    self.renderListTemplate(valType)
                for keyType, valType in self.dictTypes:
                    self.renderDictTemplate(keyType, valType)
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
            f.write('#endif')
        debug('Generated ' + self.filename)

    def run(self):
        from subprocess import call, check_call
        import sys
        self.write()
        debug(f'Running {self.filename}')
        try:
            if sys.platform == 'darwin':
                optimizationFlags = ['-Ofast']
            else:
                optimizationFlags = ['-Ofast', '-frename-registers', '-funroll-loops']
            debug(' '.join(['gcc', '-O2', '-std=c99', f'Sources/c/{self.filename}'] + list(self.links) + ['-o', 'Sources/c/main']))
            check_call(['gcc'] + optimizationFlags + ['-std=c99', f'Sources/c/{self.filename}'] + list(self.links) + ['-o', 'Sources/c/main'])
        except Exception as e:
            print(e)
            print('Compilation error. Check errors above.')
            exit()
        else:
            if self.target in {'linux', 'darwin'}:
                call('./main', cwd='Sources/c')
            else:
                call('main', cwd='Sources/c', shell=True)
