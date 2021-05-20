from copy import deepcopy

class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.target = target
        self.filename = filename.split('/')[-1].replace('.w','.d')
        self.module = module

        self.operators = ['**','*','%','/','-','+','andnot','and','or','==','!=','>','<','>=','<=','is','in','&', '<<', '>>'] # in order 
        self.instructions = {
            'printFunc': self.printFunc,
            'inputFunc': self.processInput,
            'expr': self.processExpression,
            'assign': self.processAssign,
            'if': self.processIf,
            'while': self.processWhile,
            'for': self.processFor,
            'func': self.processFunc,
            'return': self.processReturn,
            'breakStatement': self.processBreak,
            'comment': self.processComment,
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
        }
        self.terminator = ';'
        self.currentScope = {}
        self.inFunc = None
        self.inClass = None
        self.insertMode = True
        self.source = []
        self.outOfMain = []
        self.nativeTypes = {
            'int':'int',
            'float':'float',
            'void':'void',
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
            if varType == 'array':
                elementType = token['elementType']
                length = token['len']
        elif name in self.currentScope:
            # Already processed
            varType = self.currentScope[name]['type']
            if varType == 'array':
                elementType = self.currentScope[name]['elementType']
                length = self.currentScope[name]['len']
        elif name == self.inFunc and self.returnType:
            for rt in self.returnType:
                if self.typeKnown(rt):
                    varType = rt
                    # If return is an array, get other info
                    if varType == 'array':
                        elementType = self.currentScope[name]['elementType']
                        length = self.currentScope[name]['len']
        else:
            varType = 'unknown'
        if 'modifier' in token:
            token['name'] = token['modifier'].replace('not',self.notOperator) + token['name']
        if varType == 'array':
            return {'value':token['name'], 'type':varType,
            'elementType':elementType, 'len':length}
        return {'value':token['name'], 'type':varType}

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
        # InferType
        types = {}
        elements = []
        if self.typeKnown(token['elementType']):
            # Type was explicit
            varType = token['elementType']
        else:
            # Infer type
            for tok in token['elements']:
                element = self.getValAndType(tok)
                types.add(element['type'])
                elements.append(element)
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
        return {'value':self.formatArray(elements, varType, token['len']), 'type':'array',
        'elements':elements, 'elementType':varType}

    def getValAndType(self, token):
        if 'value' in token and 'type' in token and (self.typeKnown(token['type']) or not self.insertMode):
            if token['type'] == 'str':
                token = self.processFormatStr(token)
            elif token['type'] == 'bool':
                if token['value'] in {'false', 'False'}:
                    token['value'] = self.false
                else:
                    token['value'] = self.true
            if 'modifier' in token:
                token['value'] = token['modifier'] + token['value']
            return token
        elif token['token'] == 'expr':
            return self.processExpr(token)
        elif token['token'] == 'call':
            return self.processCall(token)
        elif token['token'] == 'group':
            return self.processGroup(token)
        elif token['token'] == 'var':
            return self.processVar(token)
        elif token['token'] == 'inputFunc':
            return self.processInput(token)
        elif token['token'] == 'array':
            return self.processArray(token)
        else:
            raise ValueError(f'ValAndType with token {token} not implemented')

    def processExpression(self, token):
        ''' Process the expr token as a standalone code '''
        expr = self.processExpr(token)
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

    def processAssign(self, token):
        target = token['target']
        expr = token['expr']
        if target['token'] == 'var':
            variable = self.processVar(target)
            if variable['type'] == 'array':
                if not self.typeKnown(expr['args'][0]['elementType']):
                    # Add array info into expression
                    expr['args'][0]['elementType'] = variable['elementType']
                    expr['args'][0]['len'] = variable['len']
        else:
            raise SyntaxError(f'Assign with variable {target} no supported yet.')
        expr = self.processExpr(expr)
        inMemory = False
        if variable['value'] in self.currentScope:
            inMemory = True
        elif self.typeKnown(variable['type']):
            self.currentScope[variable['value']] = {'type':variable['type']}
            if variable['type'] == 'array':
                self.currentScope[variable['value']]['elementType'] = variable['elementType']
                self.currentScope[variable['value']]['len'] = variable['len']
                #if not self.typeKnown(expr['elementType']):
                #    expr['elementType'] = variable['elementType']
                #    expr['len'] = variable['len']
        else:
            varType = self.inferType(expr)
            if self.typeKnown(varType):
                self.currentScope[variable['value']] = {'type':varType}
                target['type'] = varType
        self.insertCode(self.formatAssign(target, expr, inMemory=inMemory))

    def processIf(self, token):
        expr = self.processExpr(token['expr'])
        self.insertCode(self.formatIf(expr))
        for c in token['block']:
            self.process(c)
        if 'elifs' in token:
            for elifStatement in token['elifs']:
                expr = self.processExpr(elifStatement['expr'])
                self.insertCode(self.formatElif(expr))
                for c in elifStatement['elifBlock']:
                    self.process(c)
        if 'else' in token:
            self.insertCode(self.formatElse())
            for c in token['else']:
                self.process(c)
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
        variables = [ self.processVar(v) for v in token['vars'] ]
        self.insertCode(self.formatFor(variables, iterable))
        #TODO: Handle dict iteration and multivar for loop
        self.currentScope[variables[-1]['value']] = {'type':iterable['type']}
        for c in token['block']:
            self.process(c)
        self.insertCode(self.formatEndFor())

    def processArgs(self, tokens):
        args = []
        for tok in tokens:
            arg = self.getValAndType(tok)
            # ignore value becauso of the scope
            # Function arguments need explicit type
            args.append( {'type':tok['type'], 'value':arg['value']} )
        return args

    def processCall(self, token):
        args = self.processArgs(token['args'])
        name = self.getValAndType(token['name'])
        val = self.formatCall(name['value'], name['type'],args)
        return {'value':val, 'type':name['type']}

    def startScope(self):
        self.oldScope = deepcopy(self.currentScope)
        # refresh returnType
        self.returnType = set()

    def endScope(self):
        scope = deepcopy(self.currentScope)
        self.currentScope = self.oldScope
        return scope

    def processFunc(self, token):
        #TODO: add support for kwargs
        args = self.processArgs(token['args'])
        name = token['name']
        returnType = token['type']
        self.returnType = returnType
        self.inFunc = name
        # infer return type if not known
        if not self.typeKnown(returnType):
            # Pre process code and get returnType
            # change mode to not insert code on processing
            self.insertMode = False
            self.startScope()
            for arg in args:
                argType = arg['type']
                argVal = arg['value']
                self.currentScope[argVal] = {'type':argType}
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
            # return to normal mode
            self.insertMode = True
            # End pre processing
        self.startScope()
        self.currentScope[name] = {'type':returnType, 'token':'func'}
        index = len(self.outOfMain)
        # put args in scope
        for arg in args:
            argType = arg['type']
            argVal = arg['value']
            self.currentScope[argVal] = {'type':argType}
        for c in token['block']:
            self.process(c)
        self.insertCode(self.formatFunc(name, returnType, args),index)
        self.insertCode(self.formatEndFunc())
        self.inFunc = None
        funcScope = self.endScope()
        self.currentScope[name] = {'token':'func','args':args, 'type':returnType, 'scope':funcScope}

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

    def printFunc(self, token):
        if 'expr' in token:
            value = self.processExpr(token['expr'])
        else:
            value = {'value':'','type':'null'}
        self.insertCode(self.formatPrint(value))

    def add(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
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

    def processGroup(self, token):
        expr = self.processExpr(token['expr'])
        if 'modifier' in token:
            op = token['modifier']
        else:
            op = ''
        return {'value':f'{op}({expr["value"]})', 'type':expr['type']}

    def isBlock(self, line):
        for b in self.block:
            if b in line and not line.startswith(self.commentSymbol):
                return True
        return False

    def run(self):
        print('Running')
