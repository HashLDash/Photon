from interpreter import Interpreter
from copy import deepcopy
import os
from pprint import pprint
from .tokens import *

class CurrentScope():
    def __init__(self):
        self.currentScope = {}
        self.localScope = {}
        self.local = False

    def startLocalScope(self):
        self.local = True
        self.localScope = {}

    def endLocalScope(self):
        self.local = False
        self.localScope = {}

    def add(self, token):
        if not isinstance(token, Var) and token.index is not None:
            print(f'adding {token.index} with type {token.type.type}')
            if self.local:
                self.localScope[token.index] = token
            else:
                self.currentScope[token.index] = token

    def __repr__(self):
        s = 'SCOPE DUMP\n'
        for i, t in {**self.currentScope, **self.localScope}.items():
            s += f'"{i}" {t.type}\n'
        return s

    def get(self, index):
        return {**self.currentScope, **self.localScope}[index]
        
    def typeOf(self, obj):
        print('GET')
        print(obj)
        print(obj.index in self.currentScope)
        print(obj.index in {**self.currentScope, **self.localScope})
        print(self)
        #print(obj.index, self.currentScope[obj.index].type)
        #TODO CLASS INSTANCE IS NOT BEING FOUND
        return {**self.currentScope, **self.localScope}[obj.index].type

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
            'dotAccess': self.processDotAccess,
            'range': self.processRange,
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
        pprint(token)
        if token is not None:
            processedToken = self.instructions[token['opcode']](token)
            if processedToken is not None:
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
        self.currentScope.startLocalScope()
        oldNamespace = self.currentNamespace
        self.currentNamespace = ''
        #TODO WARNING: Global variables cannot be called inside
        #because the namespace will be different
        #in the local scope
        #use global syntax or try to infer global variables
        args = self.processTokens(token['vars'])
        iterable = self.preprocess(token['iterable'])
        if isinstance(iterable, Range):
            if len(args) == 1:
                args[0].type = iterable.type
            elif len(args) == 2:
                args[0].type = Type('int')
                args[1].type = iterable.type
            else:
                raise SyntaxError('For with range cannot have more than 2 variables')
        for t in args:
            self.currentScope.add(Assign(target=t, value=Num(0, t.type)))
        input(self.currentScope)
        code=self.processTokens(token['block'])
        self.currentNamespace = oldNamespace
        self.currentScope.endLocalScope()
        return For(
            code=code,
            args=args,
            iterable=iterable,
        )

    def processForTarget(self, token):
        pass

    def processCall(self, token, className=None):
        callType = self.preprocess(token['name']).type
        if callType.isClass:
            scope = self.currentScope.get(callType.type).parameters
            #args = [f for f in scope]
        return Call(
            name=self.processVar(token['name']),
            args=self.processTokens(token['args']),
            kwargs=self.processTokens(token['kwargs']),
        )

    def processDotAccess(self, token):
        initialType = self.preprocess(token['dotAccess'][0]).type
        oldNamespace = self.currentNamespace
        self.currentNamespace = ''
        chain = self.processTokens(token['dotAccess'])
        chain[0].type = initialType
        currentType = initialType
        for c in chain:
            if currentType.isClass:
                scope = self.currentScope.get(initialType.type).__dict__
                if c.index in scope['parameters']:
                    c.type = scope['parameters'][c.index].type
                else:
                    pass
                    #TODO check methods too
        for c in chain:
            print(c.type)
        input('Correct?')
        self.currentNamespace = oldNamespace
        return DotAccess(
            chain,
            namespace=oldNamespace,
        )

    def processClass(self, token):
        return Class(
            name=Var(token['name'], namespace=self.currentNamespace),
            args=self.processTokens(token['args']),
            code=self.processTokens(token['block'])
        )

    def processFunc(self, token):
        self.currentScope.startLocalScope()
        oldNamespace = self.currentNamespace
        self.currentNamespace = ''
        #TODO WARNING: Global variables cannot be called inside
        #because the namespace will be different
        #in the local scope
        #use global syntax or try to infer global variables
        args=self.processTokens(token['args'])
        kwargs=self.processTokens(token['kwargs'])
        for t in args + kwargs:
            self.currentScope.add(t)
        code=self.processTokens(token['block'])
        self.currentNamespace = oldNamespace
        self.currentScope.endLocalScope()
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

    def processRange(self, token):
        return Range(
            initial=self.preprocess(token['from']),
            final=self.preprocess(token['to']),
            step=self.preprocess(token['step']) if 'step' in token else Num(1, 'int'),
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
            arg.mode = 'format'
            #if arg.type.type == 'array':
            #    arg.mode = 'format'
        return Call(
            name = Var('printf', 'unknown', namespace=''),
            args = args,
        )

    def run(self):
        print('Running')
