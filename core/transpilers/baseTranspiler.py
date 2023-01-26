from interpreter import Interpreter
from copy import deepcopy
import os
from pprint import pprint
from .tokens import Sequence, Num, String, Var, Expr, Assign, Call, Args, Kwargs

class CurrentScope():
    def __init__(self):
        self.currentScope = {}

    def add(self, token):
        if isinstance(token, Assign):
            self.currentScope[repr(token.target)] = token
        elif isinstance(token, Call):
            pass
        else:
            raise NotImplemented

    def __repr__(self):
        s = 'SCOPE DUMP\n'
        for i in self.currentScope:
            s += f'"{i}" \n'
        return s

    def typeOf(self, obj):
        return self.currentScope[repr(obj.value)].type.type

class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs='', debug=False):
        self.debug = debug
        self.standardLibs = standardLibs
        self.target = target
        self.lang = 'photon'
        self.libExtension = 'photonExt'
        self.filename = filename.split('/')[-1].replace('.w','.photon')
        self.moduleName = self.filename.replace('.photon','')
        self.module = module

        self.instructions = {
            'printFunc': self.processPrint,
            'inputFunc': self.processInput,
            'expr': self.processExpr,
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
            'num': self.processNum,
            'var': self.processVar,
        }

        self.sequence = Sequence()
        self.currentScope = CurrentScope()
        self.currentNamespace = self.moduleName

    def typeOf(self, obj):
        return self.currentScope.typeOf(obj)

    def process(self, token):
        print('Processing:')
        print(token)
        if token is not None:
            processedToken = self.instructions[token['opcode']](token)
            self.currentScope.add(processedToken)
            self.sequence.add(processedToken)

    def preprocess(self, token, inferType=True):
        processedToken = self.instructions[token['token']](token)
        return processedToken

    def processNum(self, token):
        return Num(value=token['value'], type=token['type'])

    def processInput(self, token):
        pass

    def processVar(self, token):
        return Var(
            value=token['name'],
            type=token['type'],
            namespace=self.currentNamespace,
        )

    def processArray(self, token):
        pass

    def processMap(self, token):
        pass

    def processExpr(self, token):
        return Expr(
            *[self.preprocess(t) for t in token['args']],
            ops = token['ops']
        )

    def processAssign(self, token):
        assign = Assign(
            target = self.processVar(token['target']),
            value = self.processExpr(token['expr']),
            namespace=self.currentNamespace,
        )
        return assign

    def processAugAssign(self, token):
        pass

    def processIf(self, token):
        pass

    def processWhile(self, token):
        pass

    def processRange(self, token):
        pass

    def processFor(self, token):
        pass

    def processForTarget(self, token):
        pass

    def processCall(self, token, className=None):
        pass

    def processDotAccess(self, token):
        pass

    def processClass(self, token):
        pass

    def processFunc(self, token):
        pass

    def processReturn(self, token):
        pass

    def processBreak(self, token):
        pass

    def processComment(self, token):
        pass

    def processImport(self, token):
        pass

    def processPrint(self, token):
        print(self.currentScope)
        formats = {
            'str': '%s',
            'int': '%ld',
            'float': '%g',
        }
        args = [self.preprocess(t) for t in token['args']]
        template = String(value='"'+" ".join([formats[self.typeOf(arg)] for arg in args])+'\\n"')
        args.insert(0, template)
        return Call(
            name = Var('printf', 'unknown'),
            args = args,
        )

    def run(self):
        print('Running')
