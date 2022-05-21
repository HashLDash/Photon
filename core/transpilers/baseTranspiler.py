from interpreter import Interpreter
from copy import deepcopy
import os
from pprint import pprint

class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs='', debug=False):
        self.debug = debug # make this a global variable instead, inseide the debug module
        self.standardLibs = standardLibs
        self.target = target
        self.lang = 'photon'
        self.libExtension = 'photonExt'
        self.filename = filename.split('/')[-1].replace('.w','.photon')
        self.header = []
        self.module = module

        self.operators = ['**','*','%','/','-','+','==','!=','>','<','>=','<=','is','in','andnot','and','or','&', '<<', '>>'] # in order 
        self.instructions = {
            'printFunc': self.processPrint,
            'inputFunc': self.processInput,
            'expr': self.processExpression,
            'assign': self.processAssign,
            'augAssign': self.processAugAssign,
            'if': self.processIf,
            'while': self.processWhile,
            'for': self.processFor,
            'forTarget': self.processForTarget,
            'func': self.processFunc,
            'class': self.processClass,
            'return': self.processReturn,
            'breakStatement': self.processBreak,
            'comment': self.processComment,
            'import': self.processImport,
            '+': self.add,
            '-': self.sub,
            '*': self.mul,
            '/': self.div,
            '%': self.mod,
            '**': self.exp,
            '<': self.lessThan,
            '>': self.greaterThan,
            '==': self.equals,
            '>=': self.greaterEqual,
            '<=': self.lessEqual,
            '!=': self.notEqual,
            'and': self.andOperator,
            'or': self.orOperator,
            'delete': self.delete,
        }
        self.builtins = {
            'open':{'type':'file', 'value':'open'},
        }
        self.terminator = ';'
        self.currentScope = {}
        # Old scope is a list because of nested scopes.
        # E.g. methods of a class have the classScope and the method scope
        self.oldScope = []
        self.classes = {}
        self.oldClasses = []
        self.links = set()
        self.inFunc = None
        self.inClass = None
        self.methodsInsideClass = True
        self.insertMode = True
        self.source = []
        self.outOfMain = []
        self.nativeTypes = {
            'int':'int',
            'float':'float',
            'void':'void',
            'array':'array',
            'unknown':'auto',
        }

    def insertCode(self, line, index=None):
        if self.insertMode:
            if self.inFunc or self.inClass:
                if not index is None:
                    self.outOfMain.insert(index, line)
                else:
                    self.outOfMain.append(line)
            else:
                if not index is None:
                    self.source.insert(index, line)
                else:
                    self.source.append(line)

    def process(self, token):
        self.instructions[token['opcode']](token)

    def nativeType(self, varType):
        if varType in self.nativeTypes:
            return self.nativeTypes[varType]
        elif self.typeKnown(varType):
            return varType
        else:
            raise NotImplemented

    def getType(self, name):
        try:
            return self.currentScope[name]['type']
        except KeyError:
            pass
        try:
            if '.' in name:
                float(name)
                return 'float'
            else:
                int(name)
                return 'int'
        except ValueError:
            pass
        return 'unknown'


    def inferType(self, expr):
        if self.typeKnown(expr['type']):
            return expr['type']
        else:
            print('Infering type')
            input(expr)
            return 'unknown'
            raise NotImplemented

    def typeKnown(self, varType):
        if varType in {'unknown', self.nativeType('unknown')}:
            return False
        return True

    def processInput(self, token):
        if 'expr' in token:
            expr = self.processExpr(token['expr'])
        else:
            expr = {'type':'null', 'value':''}
        return {'token':'inputFunc', 'type':'str', 'value':self.formatInput(expr)}

    def processVarInit(self, token):
        name = token['args'][0]['name']
        varType = token['args'][0]['type']
        if self.typeKnown(varType):
            self.currentScope[name] = {'type':varType}
        self.insertCode(self.formatVarInit(name, varType))

    def processVar(self, token):
        name = token['name']
        if self.typeKnown(token['type']):
            # Type was explicit
            varType = token['type']
        elif name in self.currentScope:
            # Already processed
            varType = self.currentScope[name]['type']
            if varType == 'array':
                token['elementType'] = self.currentScope[name]['elementType']
                token['size'] = self.currentScope[name]['size']
            elif varType == 'map':
                token['keyType'] = self.currentScope[name]['keyType']
                token['valType'] = self.currentScope[name]['valType']
        elif name == self.inFunc and self.returnType:
            for rt in self.returnType:
                if self.typeKnown(rt):
                    varType = rt
                    # If return is an array, get other info
                    if varType == 'array':
                        token['elementType'] = self.currentScope[name]['elementType']
                        token['size'] = self.currentScope[name]['size']
                    elif varType == 'map':
                        token['keyType'] = self.currentScope[name]['keyType']
                        token['valType'] = self.currentScope[name]['valType']
        else:
            varType = 'unknown'
        if 'modifier' in token:
            #TODO: This should go after indexAccess
            token['name'] = token['modifier'].replace('not',self.notOperator) + token['name']
        if varType == 'array':
            if 'indexAccess' in token:
                # Accessing an element of the array
                token['type'] = varType
                v = self.processIndexAccess(token)
                return {'value':v['value'],
                    'indexAccess':token['indexAccess'], 'type':v['type']}
            return {'value':token['name'], 'type':varType,
                'elementType':token['elementType'], 'size':token['size']}
        if varType == 'map':
            if 'indexAccess' in token:
                # Accessing an element of the map
                token['type'] = varType
                v = self.processIndexAccess(token)
                return {'value':v['value'],
                    'indexAccess':token['indexAccess'], 'type':v['type']}
            return {'value':token['name'], 'type':varType,
                'keyType':token['keyType'], 'valType':token['valType']}
        if varType == 'str':
            if 'indexAccess' in token:
                # Accessing an element of string
                token['type'] = varType
                v = self.processIndexAccess(token)
                return {'value':v['value'],
                    'indexAccess':token['indexAccess'], 'type':v['type']}
        return {'value':token['name'], 'type':varType}

    def processIndexAccess(self, token):
        if token['type'] == 'array':
            varType = token['elementType']
            return {'value':self.formatIndexAccess(token),
                'type':varType}
        elif token['type'] == 'map':
            varType = token['valType']
            return {'value':self.formatIndexAccess(token),
                'type':varType}
        elif token['type'] == 'str':
            varType = 'char'
            return {'value':self.formatIndexAccess(token),
                'type':varType}
        else:
            raise SyntaxError(f'IndexAccess with type {token["type"]} not implemented yet')

    def processFormatStr(self, token):
        expressions = [self.processExpr(expr) for expr in token['expressions']]
        string, expressions = self.formatStr(token['value'], expressions)
        if expressions:
            # It's a format string
            token['values'] = expressions
            token['format'] = string
        else:
            # Normal string
            token['value'] = string
        return token

    def processArray(self, token):
        types = set()
        elements = []
        for tok in token['elements']:
            element = self.getValAndType(tok)
            types.add(element['type'])
            elements.append(element)
        if self.typeKnown(token['elementType']):
            # Type was explicit
            varType = token['elementType']
        else:
            # Infer type
            if len(types) == 0:
                varType = 'unknown'
            elif len(types) == 1:
                varType = types.pop()
            elif len(types) == 2:
                t1 = types.pop()
                t2 = types.pop()
                if t1 in {'int','float'} and t2 in {'int','float'}:
                    varType = 'float'
                else:
                    raise SyntaxError(f'Type inference in array with types {t1} and {t2} not implemented yet.')
            else:
                raise SyntaxError(f'Type inference in array with types {types} not implemented yet.')
        return {'value':self.formatArray(elements, varType, token['size']), 'type':'array',
        'elements':elements, 'elementType':varType, 'size':'unknown'}

    def processMap(self, token):
        keyTypes = set()
        valTypes = set()
        elements = []
        for keyVal in token['elements']:
            key, val = self.getValAndType(keyVal['key']), self.getValAndType(keyVal['val'])
            keyTypes.add(key['type'])
            valTypes.add(val['type'])
            elements.append((key, val))
        if self.typeKnown(token['keyType']) and self.typeKnown(token['valType']):
            # Type was explicit
            keyType = token['keyType']
            valType = token['valType']
        else:
            # Infer type
            if len(keyTypes) == 0:
                keyType = 'unknown'
                valType = 'unknown'
            elif len(keyTypes) == 1:
                keyType = keyTypes.pop()
                valType = valTypes.pop()
            else:
                raise SyntaxError('Map with dynamic types not implemented yet.')
        return {'value':self.formatMap(elements, keyType, valType),
            'type':'map', 'elements':elements, 'valType':valType,
            'keyType':keyType, 'size':'unknown'}

    def getValAndType(self, token):
        if 'value' in token and 'type' in token and (self.typeKnown(token['type']) or not self.insertMode):
            if token['type'] == 'str':
                token = self.processFormatStr(token)
            elif token['type'] == 'bool':
                if token['value'].lower() == 'false':
                    token['value'] = self.false
                elif token['value'].lower() == 'true':
                    token['value'] = self.true
            if 'modifier' in token:
                token['value'] = token['modifier'].replace('not', self.notOperator) + token['value']
                del token['modifier']
            return token
        elif token['token'] == 'expr':
            return self.processExpr(token)
        elif token['token'] == 'call':
            return self.processCall(token)
        elif token['token'] == 'printFunc':
            return self.processPrint(token)
        elif token['token'] == 'group':
            return self.processGroup(token)
        elif token['token'] == 'var':
            return self.processVar(token)
        elif token['token'] == 'dotAccess':
            return self.processDotAccess(token)
        elif token['token'] == 'inputFunc':
            return self.processInput(token)
        elif token['token'] == 'array':
            return self.processArray(token)
        elif token['token'] == 'map':
            return self.processMap(token)
        else:
            raise ValueError(f'ValAndType with token {token} not implemented')

    def processExpression(self, token):
        ''' Process the expr token as a standalone code '''
        expr = self.processExpr(token)
        if 'token' in token['args'][0] and token['args'][0]['token'] == 'var':
            self.insertCode(self.formatVarInit(expr['value'], expr['type']))
        else:
            self.insertCode(expr['value']+self.terminator)

    def processExpr(self, token):
        ''' Process expr tokens as values, returning its type and value '''
        args = token['args']
        ops = token['ops']
        if not ops:
            tok = args[0]
            return self.getValAndType(tok)
        elif len(args) == 1 and len(ops) == 1:
            # modifier operator
            if self.typeKnown(token['type']):
                return {'value':ops[0]+token['args'][0]['value'],'type':token['type']}
            else:
                raise NotImplemented
        else:
            for op in self.operators:
                while op in ops:
                    index = ops.index(op)
                    arg1 = args[index]
                    arg2 = args[index+1]
                    arg1 = self.getValAndType(arg1)
                    arg2 = self.getValAndType(arg2)
                    result = self.instructions[op](arg1, arg2)
                    args[index] = result
                    del ops[index]
                    del args[index+1]
            return args[0]

        return token['args'][0]

    def processClassAttribute(self, token):
        if 'default' in token:
            # positional default argument
            initVals = {
                'int': '0',
                'str': '""',
                'float': '0.0',
            }
            self.classes[self.inClass]['scope'][token['value']] = {'type': token['type']}
            expr = {'value': initVals[token['type']],'type':token['type']}
            self.classes[self.inClass]['attributes'].append({'variable':token, 'expr':expr})
            return

        if 'token' in token and token['token'] == 'expr':
            variable = self.processExpr(token)
            expr = {'value':'{}', 'type':'unknown'}
        else:
            variable = self.processVar(token['target'])
            expr = token['expr']
            
            for attr in self.classes[self.inClass]['attributes']:
                if 'returnType' in attr:
                    continue
                if variable['value'] == attr['variable']['value']:
                    # Attribute already defined, skip
                    return

            if self.typeKnown(variable['type']) and expr['args'][0]['type'] == 'array':
                # The type declaration is for the elementType
                variable['elementType'] = variable['type']
                expr['args'][0]['elementType'] = variable['type']
                variable['type'] = 'array'
                if not 'size' in variable:
                    variable['size'] = expr['args'][0]['size']
            expr = self.processExpr(expr)
            if not self.typeKnown(variable['type']):
                variable['type'] = expr['type']
        self.classes[self.inClass]['scope'][variable['value']] = {'type': variable['type']}
        if variable['type'] == 'array':
            if not 'elementType' in variable:
                variable['elementType'] = expr['elementType']
                variable['size'] = expr['size']
            self.classes[self.inClass]['scope'][variable['value']]['elementType'] = variable['elementType']
            self.classes[self.inClass]['scope'][variable['value']]['size'] = variable['size']
        self.classes[self.inClass]['attributes'].append({'variable':variable, 'expr':expr})

    def processAssign(self, token):
        target = token['target']
        expr = token['expr']
        if target['token'] in {'var', 'dotAccess'}:
            #variable = self.processVar(target)
            variable = self.getValAndType(target)
            if variable['type'] == 'array':
                if not self.typeKnown(expr['args'][0]['elementType']):
                    # Add array info into expression
                    expr['args'][0]['elementType'] = variable['elementType']
                    expr['args'][0]['size'] = variable['size']
            elif variable['type'] == 'map':
                if not self.typeKnown(expr['args'][0]['valType']):
                    # Add map info into expression
                    expr['args'][0]['keyType'] = variable['keyType']
                    expr['args'][0]['valType'] = variable['valType']
            elif self.typeKnown(variable['type']) and expr['args'][0]['type'] == 'array':
                # The type declaration is for the elementType
                expr['args'][0]['elementType'] = variable['type']
        else:
            raise SyntaxError(f'Assign with variable {target} no supported yet.')
        expr = self.processExpr(expr)
        inMemory = False
        if variable['value'] in self.currentScope or target['token'] == 'dotAccess':
            inMemory = True
        elif self.typeKnown(variable['type']):
            self.currentScope[variable['value']] = {'type':variable['type']}
            if variable['type'] == 'array':
                self.currentScope[variable['value']]['elementType'] = variable['elementType']
                self.currentScope[variable['value']]['size'] = variable['size']
                #if not self.typeKnown(expr['elementType']):
                #    expr['elementType'] = variable['elementType']
                #    expr['len'] = variable['len']
            elif expr['type'] == 'array':
                self.currentScope[variable['value']]['elementType'] = expr['elementType']
                self.currentScope[variable['value']]['size'] = expr['size']
                # We have to change the type to array because the type declaration was intended
                # for the elementType
                self.currentScope[variable['value']]['type'] = 'array'

            if variable['type'] == 'map':
                self.currentScope[variable['value']]['keyType'] = variable['keyType']
                self.currentScope[variable['value']]['valType'] = variable['valType']
            elif expr['type'] == 'map':
                self.currentScope[variable['value']]['keyType'] = expr['keyType']
                self.currentScope[variable['value']]['valType'] = expr['valType']
                # We have to change the type to array because the type declaration was intended
                # for the elementType
                self.currentScope[variable['value']]['type'] = 'map'

        else:
            varType = self.inferType(expr)
            if self.typeKnown(varType):
                self.currentScope[variable['value']] = {'type':varType}
                if varType == 'array':
                    if self.typeKnown(expr['elementType']):
                        self.currentScope[variable['value']]['elementType'] = expr['elementType']
                    elif self.typeKnown(variable['type']):
                        self.currentScope[variable['value']]['elementType'] = variable['type']
                    else:
                        raise SyntaxError(f'Array with unknown type not implemented yet.')
                    self.currentScope[variable['value']]['size'] = expr['size']
                elif varType == 'map':
                    if self.typeKnown(expr['valType']) and self.typeKnown(expr['keyType']):
                        self.currentScope[variable['value']]['keyType'] = expr['keyType']
                        self.currentScope[variable['value']]['valType'] = expr['valType']
                    elif self.typeKnown(variable['type']):
                        self.currentScope[variable['value']]['keyType'] = variable['keyType']
                        self.currentScope[variable['value']]['valType'] = variable['valType']
                    else:
                        raise SyntaxError(f'Array with unknown type not implemented yet.')
                    self.currentScope[variable['value']]['size'] = expr['size']
                target['type'] = varType

        if target['token'] == 'var':
            variableName = target['name']
            if variableName in self.currentScope:
                varType = self.currentScope[variableName]['type']
            elif self.typeKnown(target['type']):
                # Type was explicit
                varType = self.nativeType(target['type'])
            else:
                varType = self.nativeType(self.inferType(expr))
        elif target['token'] == 'dotAccess':
            v = self.getValAndType(target)
            variableName = v['value']
            varType = v['type']
        else:
            raise SyntaxError(f'Format assign with variableName {target} not implemented yet.')

        if expr['type'] == 'array' and expr['elementType'] != self.currentScope[variableName]['elementType']:
            cast = self.nativeType(varType)
        elif self.typeKnown(expr['type']) and expr['type'] != varType and self.typeKnown(varType):
            cast = self.nativeType(varType)
        else:
            cast = None

        if 'indexAccess' in target:
            target['type'] = varType
            self.insertCode(self.formatIndexAssign(target, expr, inMemory=inMemory))
        else:
            self.insertCode(self.formatAssign(variableName, varType, cast, expr, inMemory=inMemory))

    def processAugAssign(self, token):
        op = token['operator']
        expr = self.processExpr(token['expr'])
        if token['target']['token'] in {'var','dotAccess'}:
            variable = self.getValAndType(token['target'])
            if op == '+':
                if variable['type'] == 'array':
                    self.insertCode(self.formatArrayAppend(variable, expr))
                elif 'indexAccess' in variable:
                    indexVal = variable['indexAccess']['args'][0]
                    index = indexVal['value'] if 'value' in indexVal else indexVal['name']
                    self.insertCode(self.formatArrayIncrement(token['target'], index, expr))
                elif variable['type'] in {'int', 'float', 'str'}:
                    self.insertCode(self.formatIncrement(variable, expr))
                else:
                    raise SyntaxError(f'AugAssign with type {variable["type"]} not implemented yet.')
            if op == '-':
                if variable['type'] == 'array':
                    self.insertCode(self.formatArrayRemoveAll(variable, expr))
                else:
                    raise NotImplemented
        else:
            raise SyntaxError(f'AugAssign with variable {token["target"]} not supported yet.')

    def formatIndexAccess(self, token):
        if token['type'] in {'array', 'map'}:
            indexAccess = self.processExpr(token['indexAccess'])['value']
            name = token['name']
            return f'{name}[{indexAccess}]'
        else:
            raise SyntaxError(f'IndexAccess with type {token["type"]} not implemented yet')

    def processIf(self, token):
        expr = self.processExpr(token['expr'])
        self.insertCode(self.formatIf(expr))
        self.startScope()
        for c in token['block']:
            self.process(c)
        self.endScope()
        if 'elifs' in token:
            for elifStatement in token['elifs']:
                expr = self.processExpr(elifStatement['expr'])
                self.insertCode(self.formatElif(expr))
                self.startScope()
                for c in elifStatement['elifBlock']:
                    self.process(c)
                self.endScope()
        if 'else' in token:
            self.insertCode(self.formatElse())
            self.startScope()
            for c in token['else']:
                self.process(c)
            self.endScope()
        self.insertCode(self.formatEndIf())

    def processWhile(self, token):
        expr = self.processExpr(token['expr'])
        self.insertCode(self.formatWhile(expr))
        for c in token['block']:
            self.process(c)
        self.insertCode(self.formatEndWhile())

    def processRange(self, token):
        rangeType = 'unknown'
        fromVal = self.processExpr(token['from'])
        if 'step' in token:
            step = self.processExpr(token['from'])
        else:
            step = {'type':'int', 'value':'1'}
        toVal = self.processExpr(token['to'])
        types = {fromVal['type'], step['type'], toVal['type']}
        if len(types) == 1:
            rangeType = types.pop()
        elif len(types) == 2 and 'float' in types and 'int' in types:
            rangeType = 'float'
        return {'type':rangeType, 'from':fromVal, 'step':step, 'to':toVal}

    def processFor(self, token):
        if token['iterable']['token'] == 'expr':
            iterable = self.processExpr(token['iterable'])
        else:
            iterable = self.processRange(token['iterable'])
        variables = [ self.processVar(v)['value'] for v in token['vars'] ]
        self.insertCode(self.formatFor(variables, iterable))
        if iterable['type'] == 'array':
            if len(variables) == 2:
                self.currentScope[variables[0]] = {'type':'int'}
            self.currentScope[variables[-1]] = {'type':iterable['elementType']}
        elif iterable['type'] == 'str' or 'from' in iterable:
            if len(variables) == 2:
                self.currentScope[variables[0]] = {'type':'int'}
            self.currentScope[variables[-1]] = {'type':iterable['type']}
        elif iterable['type'] == 'map':
            if len(variables) == 2:
                self.currentScope[variables[0]] = {'type':iterable['keyType']}
                self.currentScope[variables[1]] = {'type':iterable['valType']}
            elif len(variables) == 3:
                self.currentScope[variables[0]] = {'type':'int'}
                self.currentScope[variables[1]] = {'type':iterable['keyType']}
                self.currentScope[variables[2]] = {'type':iterable['valType']}
            else:
                self.currentScope[variables[0]] = {'type':iterable['keyType']}
        else:
            self.currentScope[variables[-1]] = {'type':iterable['type']}
        for c in token['block']:
            self.process(c)
        self.insertCode(self.formatEndFor())

    def processForTarget(self, token):
        var = token['target'].lower().replace('python', 'py')
        lang = self.lang.lower().replace('python', 'py')
        target = self.target.lower()
        if var == lang or var == target:
            for tok in token['block']:
                self.process(tok)

    def processArgs(self, tokens, inferType=False):
        args = []
        for tok in tokens:
            arg = self.getValAndType(tok)
            if inferType:
                args.append( {'type':arg['type'], 'value':arg['value']} )
            else:
                # ignore value type because of the scope
                # Function arguments need explicit type
                attr = {'type':tok['type'], 'value':arg['value']}
                if 'attribute' in tok:
                    attr['default'] = True
                    attr['value'] = tok['args'][0]['dotAccess'][-1]['name']
                args.append(attr)
        return args

    def processKwargs(self, tokens, inferType=False):
        kwargs = []
        for tok in tokens:
            if tok['expr']['type'] == 'array' and not self.typeKnown(tok['expr']['args'][0]['elementType']):
                tok['expr']['args'][0]['elementType'] = tok['target']['type']
            kw = self.getValAndType(tok['expr'])
            if self.typeKnown(tok['target']['type']) and tok['target']['type'] == 'func':
                # It's a callback
                kw['type'] = tok['target']['type']
            name = tok['target']['name']
            kw['name'] = name
            if 'attribute' in tok['target']:
                kw['default'] = True
            kwargs.append(kw)
        return kwargs

    def processCall(self, token, className=None):
        name = self.getValAndType(token['name'])
        args = self.processArgs(token['args'], inferType=True)
        if name['value'] in self.builtins:
            callType = self.builtins[name['value']]['type']
            name['value'] = self.builtins[name['value']]['value']
        else:
            callType = name['type']
        callback = False
        # Put kwargs in the right order
        if token['type'] == 'func':
            # It'a a callback
            kws = self.processKwargs(token['kwargs'], inferType=True)
            ags = args
        elif className is not None:
            kws = self.classes[className]['methods'][name['value']]['kwargs']
            ags = self.classes[className]['methods'][name['value']]['args']
        elif name['value'] in self.classes:
            callType = name['value']
            if 'new' in self.classes[callType]['methods']:
                kws = self.classes[callType]['methods']['new']['kwargs']
                ags = self.classes[callType]['methods']['new']['args']
            else:
                kws = []
                ags = []
        elif name['value'] in self.currentScope:
            if self.currentScope[name['value']]['token'] == 'nativeFunc':
                kws = []
                ags = args
            elif 'func' in self.currentScope[name['value']]['type']:
                # Its a callback
                callback = True
                kws = self.processKwargs(token['kwargs'], inferType=True)
                ags = args
            else:
                kws = self.currentScope[name['value']]['kwargs']
                ags = self.currentScope[name['value']]['args']
        else:
            # Call signature not defined, use the order it was passed
            kws = self.processKwargs(token['kwargs'], inferType=True)
            ags = args

        kwargs = []
        # If the kwarg was passed, use it. Otherwise use the default value
        for kw in kws:
            for a in self.processKwargs(token['kwargs']):
                if kw['name'] == a['name']:
                    kwargs.append(a)
                    break
            else:
                kwargs.append(kw)

        arguments = []
        for arg, a in zip(args, ags):
            if arg['type'] != a['type']:
                arg['cast'] = a['type']
            arguments.append(arg)
                
        val = self.formatCall(name['value'], name['type'], arguments, kwargs, className, callback)
        if 'modifier' in token:
            val = token['modifier'].replace('not',self.notOperator) + val
        return {'value':val, 'type':callType}

    def processDotAccess(self, token):
        tokens = token['dotAccess']
        varType = self.getValAndType(tokens[0])['type']
        currentType = varType
        tokens[0]['type'] = varType
        for n, v in enumerate(tokens[1:], 1):
            if currentType in self.classes:
                if v['token'] == 'call':
                    name = v['name']['name']
                else:
                    name = v['name']
                if name in self.classes[varType]['scope']:
                    currentType = self.classes[varType]['scope'][name]['type']
                    if currentType == 'array':
                        size = self.classes[varType]['scope'][name]['size']
                        varType = self.classes[varType]['scope'][name]['elementType']
                        tokens[n]['type'] = currentType
                        tokens[n]['elementType'] = varType
                        tokens[n]['size'] = size
                    else:
                        varType = currentType
                        tokens[n]['type'] = varType
            elif currentType in {'array', 'map'} and v['name'] == 'len':
                tokens[n]['type'] = 'int'
                currentType = 'int'
                varType = 'int'
            else:
                varType = v['type']
                currentType = varType
        value = self.formatDotAccess(tokens)
        
        # pass other arguments to be compatible with processVar method
        if currentType == 'array':
            if 'indexAccess' in tokens[-1]:
                # Accessing an element of the array
                #tokens[-1]['type'] = varType
                return {'value': value, #tokens[-1]['name'],
                    'indexAccess':tokens[-1]['indexAccess'],
                    'type':varType}
            return {'value':value, 'type':currentType,
                'elementType':tokens[-1]['elementType'], 'size':'unknown'}
        #TODO: Implement map with indexAccess

        return {'value':value, 'type':varType}

    def startClassScope(self):
        self.oldClasses.append(deepcopy(self.classes))

    def endClassScope(self):
        self.classes = self.oldClasses.pop()

    def startScope(self):
        self.oldScope.append(deepcopy(self.currentScope))
        # refresh returnType
        self.returnType = set()

    def endScope(self):
        scope = deepcopy(self.currentScope)
        self.currentScope = self.oldScope.pop()
        return scope

    def processClass(self, token):
        name = token['name']
        inheritedClasses = [v['value'] for v in self.processArgs(token['args'])]
        if len(inheritedClasses) > 1:
            raise SyntaxError('Multiple Inheritance is not allowed yet.')
        self.classes[name] = {'scope':{}, 'attributes':[],'methods':{}, 'inherited':[]}
        self.inClass = name
        self.startScope()
        index = len(self.outOfMain)
        newDefined = False
        for c in token['block']:
            if c['token'] == 'func':
                if c['name'] == 'new':
                    newDefined = True
                    break
        for inherited in inheritedClasses:
            if inherited in self.classes:
                self.classes[name] = deepcopy(self.classes[inherited])
                self.classes[name]['inherited'] = [inherited]
                for methodName in self.classes[name]['methods']:
                    self.classes[name]['scope'][methodName]['args'][0]['type'] = name
                    self.classes[name]['methods'][methodName]['scope']['self']['type'] = name
                    if inherited:
                        self.classes[name]['methods'][methodName]['scope']['super'] = {'type': inherited}
                    self.classes[name]['methods'][methodName]['args'][0]['type'] = name
                    definition = self.classes[name]['methods'][methodName]['code'][0]
                    self.reformatInheritedMethodDefinition(definition, methodName, name, inherited)
                for n, attr in enumerate(self.classes[name]['attributes']):
                    if 'returnType' in attr:
                        self.classes[name]['attributes'][n]['args'][0]['type'] = name

        for c in token['block']:
            if c['token'] in {'assign', 'expr'}:
                self.processClassAttribute(c)
            elif c['token'] == 'func':
                self.processClassMethod(c)
            elif c['token'] == 'comment':
                self.processComment(c)
            else:
                raise SyntaxError(f'Cannot use {c["token"]} inside a class')
        classScope = self.endScope()
        # Include methods, args/kwargs
        args = self.processArgs(token['args'])
        self.insertCode(self.formatClass(name, args), index)
        for attr in self.classes[name]['attributes']:
            self.insertCode(self.formatClassAttribute(attr))
        if not self.methodsInsideClass:
            # Close class definition before writing methods
            self.insertCode(self.formatEndClass())
            self.classHeader(index)
        # Write methods code
        for methodName, info in self.classes[name]['methods'].items():
            self.insertCode('')
            self.classes[name]['scope'][methodName] = info['scope'][methodName]
            for c in info['code']:
                self.insertCode(c)
        if self.methodsInsideClass:
            # Close class definition after writing methods
            self.insertCode(self.formatEndClass())
        self.inClass = None

    def reformatInheritedMethodDefinition(self, definition, methodName, className, inheritedName):
        pass

    def classHeader(self, index):
        ''' Construct the main header if it needs '''
        self.header.append(f'typedef struct {self.inClass} {self.inClass};')

    def processClassMethod(self, token):
        selfArg = {
            'token': 'expr',
            'type': self.inClass,
            'args': [{'token': 'var', 'name': 'self', 'type': self.inClass}], 'ops': []}
        token['args'] = [selfArg] + token['args']
        index = len(self.outOfMain)
        name = token['name']
        if name == "new":
            # Only change the name for transpilation
            #token['name'] = self.constructorName
            # add kwargs from inherited class
            try:
                inherited = self.classes[self.inClass]['inherited'][0]
            except IndexError:
                pass
            else:
                inheritedKwargs = self.classes[inherited]['methods']['new']['tokens']['kwargs']
                # Check if it's an inherited new method
                # to avoid duplicating the attributes
                if not inheritedKwargs == token['kwargs']:
                    token['kwargs'] = inheritedKwargs + token['kwargs']
        self.processFunc(token)
        # delete self, because the next inheritance will insert it
        del token['args'][0]
        methodCode = self.outOfMain[index:]
        del self.outOfMain[index:]
        self.classes[self.inClass]['methods'][name] = deepcopy(self.currentScope[name])
        self.classes[self.inClass]['methods'][name]['code'] = methodCode
        self.classes[self.inClass]['methods'][name]['tokens'] = token

        methodInfo = self.classes[self.inClass]['methods'][name]['scope'][name] 
        attrData = {
            'returnType':methodInfo['type'],
            'name':name,
            'args':methodInfo['args'],
            'kwargs':methodInfo['kwargs']}
        # Check if this method overrides other inherited method
        for n, attr in enumerate(self.classes[self.inClass]['attributes']):
            if 'returnType' in attr and attr['name'] == name:
                # It is overriding this attr
                self.classes[self.inClass]['attributes'][n] = attrData
                break
        else:
            self.classes[self.inClass]['attributes'].append(attrData)
        del self.currentScope[name]

    def processFunc(self, token):
        args = self.processArgs(token['args'])
        kwargs = self.processKwargs(token['kwargs'])
        functionName = token['name']
        returnType = token['type']
        self.returnType = returnType
        self.inFunc = functionName
        # infer return type if not known
        if not self.typeKnown(returnType):
            # Pre process code and get returnType
            # change mode to not insert code on processing
            self.insertMode = False
            self.startScope()
            if self.inClass:
                self.startClassScope()
                inherited = self.classes[self.inClass]['inherited']
                if inherited:
                    self.currentScope['super'] = {'type':inherited[0]}
            # put args in scope
            for arg in args:
                argType = arg['type']
                argVal = arg['value']
                self.currentScope[argVal] = {'type':argType}
                if self.inClass and 'default' in arg:
                    self.processClassAttribute(arg)
            # put kwargs in scope
            for kw in kwargs:
                kwType = kw['type']
                kwVal = kw['name']
                self.currentScope[kwVal] = {'type':kwType}
                if kwType == 'array':
                    self.currentScope[kwVal]['elementType'] = kw['elementType']
                    self.currentScope[kwVal]['size'] = kw['size']
                    
                if 'default' in kw:
                    attribute = {
                        'target':{
                            'name':kw['name'],
                            'type':kw['type']
                        },
                        'expr':{
                            'args':[
                                self.getValAndType(kw)
                            ],
                            'ops':[]
                        }
                    }
                    if kw['type'] == 'array':
                        attribute['target']['type'] = kw['elementType']
                        attribute['target']['elementType'] = kw['elementType']
                        attribute['target']['size'] = kw['size']
                        attribute['expr']['args'][0]['elementType'] = kw['elementType']
                        attribute['expr']['args'][0]['size'] = kw['size']
                        attribute['expr']['args'][0]['elements'] = kw['elements']
                    if self.inClass:
                        self.processClassAttribute(attribute)
            # get a deepcopy or it will corrupt the block
            block = deepcopy(token['block'])
            for c in block:
                self.process(c)
            for rt in self.returnType:
                if self.typeKnown(rt):
                    returnType = rt
                    break
            else:
                returnType = 'void'
            self.endScope()
            if self.inClass:
                self.endClassScope()
            # return to normal mode
            self.insertMode = True
            # End pre processing
        self.startScope()
        scopeName = 'new' if functionName == self.constructorName else functionName
        self.currentScope[scopeName] = {'type':returnType, 'token':'func', 'args':args, 'kwargs':kwargs}
        # put args in scope
        if self.inClass:
            inherited = self.classes[self.inClass]['inherited']
            if inherited:
                self.currentScope['super'] = {'type':inherited[0]}
        index = len(self.outOfMain)
        for arg in args:
            argType = arg['type']
            argVal = arg['value']
            self.currentScope[argVal] = {'type':argType}
            if self.inClass and 'default' in arg:
                self.insertCode(self.formatClassDefaultValue(arg))
                self.processClassAttribute(arg)
        # put kwargs in scope
        for kw in kwargs:
            kwType = kw['type']
            kwVal = kw['name']
            self.currentScope[kwVal] = {'type':kwType}
            if kwType == 'array':
                self.currentScope[kwVal]['elementType'] = kw['elementType']
                self.currentScope[kwVal]['size'] = kw['size']
            if 'default' in kw:
                if self.inClass:
                    self.insertCode(self.formatClassDefaultValue(kw))
                attribute = {
                    'target':{
                        'name':kw['name'],
                        'type':kw['type']
                    },
                    'expr':{
                        'args':[
                            self.getValAndType(kw)
                        ],
                        'ops':[]
                    }
                }
                if kw['type'] == 'array':
                    attribute['target']['type'] = kw['elementType']
                    attribute['target']['elementType'] = kw['elementType']
                    attribute['target']['size'] = kw['size']
                    attribute['expr']['args'][0]['elementType'] = kw['elementType']
                    attribute['expr']['args'][0]['size'] = kw['size']
                    attribute['expr']['args'][0]['elements'] = kw['elements']
                if self.inClass:
                    self.processClassAttribute(attribute)
        for c in token['block']:
            self.process(c)
        self.insertCode(self.formatFunc(functionName, returnType, args, kwargs),index)
        self.insertCode(self.formatEndFunc())
        self.inFunc = None
        funcScope = self.endScope()
        self.currentScope[scopeName] = {'scope':funcScope, 'type':returnType, 'token':'func', 'args':args, 'kwargs':kwargs}

    def processReturn(self, token):
        if 'expr' in token:
            expr = self.processExpr(token['expr'])
            self.returnType.add(expr['type'])
        else:
            expr = None
            self.returnType.add('void')
        self.insertCode(self.formatReturn(expr))

    def processBreak(self, token):
        self.insertCode('break'+self.terminator)

    def processComment(self, token):
        # Do nothing for now
        pass

    def processImport(self, token):
        folder = None
        if token['expr']['args'][0]['token'] == 'var':
            name = token['expr']['args'][0]['name']
            if f"{name}.w" in os.listdir(folder) + os.listdir(self.standardLibs):
                if f"{name}.w" in os.listdir(self.standardLibs):
                    # Photon module import
                    if name == 'wui':
                        # Inject assets folder
                        os.makedirs(f'Sources/{self.lang}', exist_ok=True)
                        assetsPath = os.path.realpath(self.standardLibs+'../assets')
                        os.system(f'cp -r {assetsPath} Sources/{self.lang}/')
                    filename = f'{self.standardLibs}{name}.w'
                else:
                    # Local module import
                    filename = f'{name}.w'
                interpreter = Interpreter(
                        filename=filename,
                        lang=self.lang,
                        target=self.target,
                        module=True,
                        standardLibs=self.standardLibs,
                        transpileOnly=True,
                        debug=self.debug)
                interpreter.run()
                self.classes.update(interpreter.engine.classes)
                self.currentScope.update(interpreter.engine.currentScope)
                self.imports = self.imports.union(interpreter.engine.imports)
                self.links = self.links.union(interpreter.engine.links)
                self.outOfMain += interpreter.engine.outOfMain
                self.source += interpreter.engine.source
                self.header += interpreter.engine.header
            elif f"{name}.{self.libExtension}" in os.listdir(self.standardLibs + f'/native/{self.lang}/'):
                # Native Photon lib module import
                self.insertCode(self.formatNativeLibImport(token['expr']))
            elif f"{name}.{self.libExtension}" in os.listdir():
                # Native Photon local module import
                raise SyntaxError('Native Photon local module import not implemented yet.')
            else:
                # System library import
                self.insertCode(self.formatSystemLibImport(token['expr']))

    def processPrint(self, token):
        if token['args']:
            value = self.getValAndType(token['args'][0])
        else:
            value = {'value':'','type':'null'}
        terminator = '\\n'
        if token['kwargs']:
            kwargs = self.processKwargs(token['kwargs'])
            if kwargs[0]['name'] == 'end':
                if kwargs[0]['type'] == 'str':
                    terminator = kwargs[0]['value'][1:-1]
                else:
                    raise ValueError('end parameter on print can only be of type str.')
        self.insertCode(self.formatPrint(value, terminator=terminator))

    def add(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        elif t1 == 'str' or t2 == 'str':
            varType = 'str'
            return {'value':f'{arg1["value"]} + {arg2["value"]}', 'type':varType, 'expressions':[]}
        else:
            varType = 'unknown'
        return {'value':f'{arg1["value"]} + {arg2["value"]}', 'type':varType}

    def sub(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        else:
            varType = 'unknown'
        return {'value':f'{arg1["value"]} - {arg2["value"]}', 'type':varType}

    def mul(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        else:
            varType = 'unknown'
        return {'value':f'{arg1["value"]} * {arg2["value"]}', 'type':varType}

    def div(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        else:
            varType = 'unknown'
        return {'value':f'{arg1["value"]} / {arg2["value"]}', 'type':varType}
    
    def mod(self, arg1, arg2):
        return {'value':f'{arg1["value"]} % {arg2["value"]}', 'type':'int'}

    def exp(self, arg1, arg2):
        if arg1['type'] == 'int' and arg2['type'] == 'int':
            varType = 'int'
        else:
            varType = 'float'
        return {'value':f'pow({arg1["value"]}, {arg2["value"]})', 'type':'float'}

    def lessThan(self, arg1, arg2):
        return {'value':f'{arg1["value"]} < {arg2["value"]}', 'type':'bool'}

    def greaterThan(self, arg1, arg2):
        return {'value':f'{arg1["value"]} > {arg2["value"]}', 'type':'bool'}

    def equals(self, arg1, arg2):
        return {'value':f'{arg1["value"]} == {arg2["value"]}', 'type':'bool'}

    def greaterEqual(self, arg1, arg2):
        return {'value':f'{arg1["value"]} >= {arg2["value"]}', 'type':'bool'}
    
    def lessEqual(self, arg1, arg2):
        return {'value':f'{arg1["value"]} <= {arg2["value"]}', 'type':'bool'}

    def notEqual(self, arg1, arg2):
        return {'value':f'{arg1["value"]} != {arg2["value"]}', 'type':'bool'}

    def andOperator(self, arg1, arg2):
        return {'value':f'{arg1["value"]} && {arg2["value"]}', 'type':'bool'}

    def orOperator(self, arg1, arg2):
        return {'value':f'{arg1["value"]} || {arg2["value"]}', 'type':'bool'}

    def processGroup(self, token):
        expr = self.processExpr(token['expr'])
        if 'modifier' in token:
            op = token['modifier'].replace('not',self.notOperator)
        else:
            op = ''
        return {'value':f'{op}({expr["value"]})', 'type':expr['type']}

    def delete(self, token):
        t = deepcopy(token['expr'])
        if 'indexAccess' in t['args'][-1]:
            del t['args'][-1]['indexAccess']
            v = self.processExpr(t)
            name, varType = v['value'], v['type']
            expr = self.processExpr(token['expr'])
            expr['indexAccess'] = self.processExpr(expr['indexAccess'])
        self.insertCode(self.formatDelete(expr, name, varType))

    def isBlock(self, line):
        for b in self.block:
            # remove comment
            try:
                line = line[:line.index('#')]
            except ValueError:
                pass
            if b in line:
                if b == 'for ' or b == 'if ':
                    if ('[' in line and ']' in line) and (line.index('[') < line.index('for ') < line.index(']')):
                        # its a list comprehension
                        continue
                    else:
                        return True
                return True
        return False

    def run(self):
        print('Running')
