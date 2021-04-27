class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.target = target
        self.filename = filename.split('/')[-1].replace('.w','.d')
        self.module = module

        self.instructions = {
            'printFunc': self.printFunc,
            'expr': self.processVarInit,
            'assign': self.processAssign,
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
        return {'value':token['name'], 'type':varType}

    def processExpr(self, token):
        #TODO: To be implemented
        if not token['ops']:
            tok = token['args'][0]
            if tok['token'] == 'var':
                return self.processVar(tok)

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

    def printFunc(self, token):
        value = self.processExpr(token['expr'])
        self.source.append(self.formatPrint(value))

    def isBlock(self, line):
        for b in self.block:
            if b in line and not line.startswith(self.commentSymbol):
                return True
        return False

    def run(self):
        print('Running')
