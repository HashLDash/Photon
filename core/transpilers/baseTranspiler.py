class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.target = target
        self.filename = filename.split('/')[-1].replace('.w','.d')
        self.module = module

        self.instructions = {
            'printFunction': self.printFunction,
            'expr': self.processVarInit,
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
        if name in self.currentScope:
            varType = self.currentScope[name]['type']
        else:
            varType = 'unknown'
        return {'value':token['name'], 'type':varType}

    def processExpression(self, token):
        #TODO: To be implemented
        if not token['ops']:
            tok = token['args'][0]
            if tok['token'] == 'var':
                return self.processVar(tok)

        return token['args'][0]

    def printFunction(self, token):
        value = self.processExpression(token['expr'])
        self.source.append(self.formatPrint(value))

    def isBlock(self, line):
        for b in self.block:
            if b in line and not line.startswith(self.commentSymbol):
                return True
        return False

    def run(self):
        print('Running')