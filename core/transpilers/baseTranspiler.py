class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.target = target
        self.filename = filename.split('/')[-1].replace('.w','.d')
        self.module = module

        self.instructions = {
            'printFunction': self.printFunction,
        }
        self.source = []
        self.outOfMain = []

    def process(self, token):
        self.instructions[token['opcode']](token)

    def processExpression(self, token):
        #TODO: To be implemented
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
