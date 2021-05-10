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
            '+': self.add,
            '-': self.sub,
            '*': self.mul,
            '/': self.div,
            '**': self.exp,
            '==': self.equals,
            '>=': self.greaterEqual,
            '<=': self.lessEqual,
            '!=': self.notEqual,
        }
        self.terminator = ';'
        self.currentScope = {}
        self.source = []
        self.outOfMain = []
        self.nativeTypes = {
            'int':'int',
            'float':'float',
            'unknown':'auto',
        }

    def process(self, token):
        self.instructions[token['opcode']](token)

    def nativeType(self, varType):
        if varType in self.nativeTypes:
            return self.nativeTypes[varType]
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
        self.source.append(self.formatVarInit(name, varType))

    def processVar(self, token):
        name = token['name']
        if self.typeKnown(token['type']):
            varType = token['type']
        elif name in self.currentScope:
            varType = self.currentScope[name]['type']
        else:
            varType = 'unknown'
        if 'modifier' in token:
            token['name'] = token['modifier'] + token['name']
        return {'value':token['name'], 'type':varType}

    def processFormatStr(self, token):
        string, variables = self.formatStr(token['value'])
        if variables:
            # It's a format string
            token['variables'] = variables
            token['format'] = string
        else:
            # Normal string
            token['value'] = string
        return token

    def getValAndType(self, token):
        if 'value' in token and 'type' in token and self.typeKnown(token['type']):
            if token['type'] == 'str':
                token = self.processFormatStr(token)
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
        else:
            raise ValueError(f'ValAndType with token {token} not implemented')

    def processExpression(self, token):
        ''' Process the expr token as a standalone code '''
        expr = self.processExpr(token)
        self.source.append(expr['value']+self.terminator)

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
        if target['token'] == 'var':
            variable = self.processVar(target)
        else:
            raise SyntaxError(f'Assign with variable {target} no supported yet.')
        expr = self.processExpr(token['expr'])
        self.source.append(self.formatAssign(target, expr))
        if self.typeKnown(variable['type']):
            self.currentScope[variable['value']] = {'type':variable['type']}
        else:
            varType = self.inferType(expr)
            if self.typeKnown(varType):
                self.currentScope[variable['value']] = {'type':varType}

    def processIf(self, token):
        expr = self.processExpr(token['expr'])
        self.source.append(self.formatIf(expr))
        for c in token['block']:
            self.process(c)
        if 'elifs' in token:
            for elifStatement in token['elifs']:
                expr = self.processExpr(elifStatement['expr'])
                self.source.append(self.formatElif(expr))
                for c in elifStatement['elifBlock']:
                    self.process(c)
        if 'else' in token:
            self.source.append(self.formatElse())
            for c in token['else']:
                self.process(c)
        self.source.append(self.formatEndIf())

    def processWhile(self, token):
        expr = self.processExpr(token['expr'])
        self.source.append(self.formatWhile(expr))
        for c in token['block']:
            self.process(c)
        self.source.append(self.formatEndWhile())

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
        self.source.append(self.formatFor(variables, iterable))
        for c in token['block']:
            self.process(c)
        self.source.append(self.formatEndFor())

    def processArgs(self, tokens):
        args = []
        for tok in tokens:
            arg = self.getValAndType(tok)
            args.append( {'type':arg['type'], 'value':arg['value']} )
        return args

    def processCall(self, token):
        args = self.processArgs(token['args'])
        name = self.getValAndType(token['name'])
        val = self.formatCall(name['value'], name['type'],args)
        return {'value':val, 'type':name['type']}

    def printFunc(self, token):
        value = self.processExpr(token['expr'])
        self.source.append(self.formatPrint(value))

    def add(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        return {'value':f'{arg1["value"]} + {arg2["value"]}', 'type':varType}

    def sub(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        return {'value':f'{arg1["value"]} - {arg2["value"]}', 'type':varType}

    def mul(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 == 'int' and t2 == 'int':
            varType = 'int'
        elif t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        return {'value':f'{arg1["value"]} * {arg2["value"]}', 'type':varType}

    def div(self, arg1, arg2):
        t1 = arg1['type']
        t2 = arg2['type']
        if t1 in {'float','int'} and t2 in {'float','int'}:
            varType = 'float'
        return {'value':f'{arg1["value"]} / {arg2["value"]}', 'type':varType}

    def exp(self, arg1, arg2):
        self.imports.add('#include <math.h>')
        return {'value':f'pow({arg1["value"]}, {arg2["value"]})', 'type':'float'}

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
