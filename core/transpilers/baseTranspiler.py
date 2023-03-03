from interpreter import Interpreter
from copy import deepcopy
import os
from pprint import pprint
from .tokens import *

class CurrentScope():
    def __init__(self):
        self.currentScope = {}

    def add(self, token):
        if not isinstance(token, Var) and token.index is not None:
            print(f'adding {token.index} with type {token.type.type}')
            self.currentScope[token.index] = token

    def __repr__(self):
        s = 'SCOPE DUMP\n'
        for i, t in self.currentScope.items():
            s += f'"{i}" {t.type}\n'
        return s

    def typeOf(self, obj):
        print('GET', obj)
        print(obj.index in self.currentScope)
        print(obj.index, self.currentScope[obj.index].type)
        #TODO CLASS INSTANCE IS NOT BEING FOUND
        return self.currentScope[obj.index].type

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
            'floatNumber': self.processNum,
            'str': self.processString,
            'call': self.processCall,
            'array': self.processArray,
        }

        self.sequence = Sequence()
        self.currentScope = CurrentScope()
        self.currentNamespace = self.moduleName

    def typeOf(self, obj):
        if obj.type.known:
            return obj.type
        if isinstance(obj, String):
            return Type('str')
        try:
            return self.currentScope.typeOf(obj)
        except Exception as e:
            print(e)
            return Type('unknown')

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

    def processString(self, token):
        for i in String.imports:
            self.imports.add(i)
        return String(
            value=token['value'],
            expressions=self.processTokens(token['expressions'])
        )

    def processInput(self, token):
        pass

    def processVar(self, token):
        #print(self.currentScope)
        var = Var(
            value=token['name'],
            type=token['type'],
            namespace=self.currentNamespace,
        )
        var.type = self.typeOf(var)
        print(var, var.type)
        return var

    def processArray(self, token):
        array = Array(
            *self.processTokens(token['elements'])
        )
        for i in array.imports:
            self.imports.add(i)
        self.listTypes.add(array.elementType)
        return array

    def processMap(self, token):
        pass

    def processExpr(self, token):
        print('here2')
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
        return Call(
            name=self.processVar(token['name']),
            args=self.processTokens(token['args']),
            kwargs=self.processTokens(token['kwargs']),
        )

    def processDotAccess(self, token):
        pass

    def processClass(self, token):
        return Class(
            name=Var(token['name'], namespace=self.currentNamespace),
            args=self.processTokens(token['args']),
            code=self.processTokens(token['block'])
        )

    def processFunc(self, token):
        args=self.processTokens(token['args'])
        kwargs=self.processTokens(token['kwargs'])
        for t in args + kwargs:
            print(t)
            self.currentScope.add(t)
        code=self.processTokens(token['block'])
        return Function(
            name=Var(
                token['name'],
                type=token['type'],
                namespace=self.currentNamespace,
            ),
            args=args,
            kwargs=kwargs,
            code=code,
        )

    def processReturn(self, token):
        pass

    def processBreak(self, token):
        pass

    def processComment(self, token):
        pass

    def processImport(self, token):
        pass

    def processTokens(self, tokens):
        return [self.preprocess(t) for t in tokens]

    def processPrint(self, token):
        print(self.currentScope)
        formats = {
            'str': '%s',
            'int': '%ld',
            'float': '%g',
            'array': '%s',
            'map': '%s',
        }
        args = self.processTokens(token['args'])
        template = String(value='"'+" ".join([formats[self.typeOf(arg).type] for arg in args])+'\\n"')
        args.insert(0, template)
        for arg in args:
            if arg.type.type == 'array':
                arg.format = True
        return Call(
            name = Var('printf', 'unknown', namespace=''),
            args = args,
        )

    def run(self):
        print('Running')
