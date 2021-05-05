class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.target = target
        self.filename = filename.split('/')[-1].replace('.w','.d')
        self.module = module

        self.operators = ['**','*','%','/','-','+','andnot','and','or','==','!=','>','<','>=','<=','is','in','&', '<<', '>>'] # in order 
        self.instructions = {
            'printFunc': self.printFunc,
            'expr': self.processVarInit,
            'assign': self.processAssign,
            'if': self.processIf,
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

    def getValAndType(self, token):
        if 'value' in token and 'type' in token and self.typeKnown(token['type']):
            if token['type'] == 'str':
                token['value'] = self.formatStr(token['value'])
            # Already processed, return
            if 'modifier' in token:
                token['value'] = token['modifier'] + token['value']
            return token
        elif token['token'] == 'group':
            return self.processGroup(token)
        elif token['token'] == 'var':
            return self.processVar(token)
        else:
            raise ValueError(f'ValAndType with token {token} not implemented')

    def processExpr(self, token):
        #TODO: To be implemented
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
