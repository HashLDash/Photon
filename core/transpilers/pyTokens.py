# Basic Types
from copy import deepcopy
from pprint import pprint
from .baseType import BaseType

class Type(BaseType):
    nativeTypes = {
        'int':'int',
        'str':'str',
        'float':'float',
        'bool':'bool',
        'unknown':'None',
        '':'None',
        'obj':'obj',
        'file':'TypeVar("file")',
    }

    def __repr__(self):
        if self.native:
            return f'TypeVar("{self.type}")'
        elif self.type == 'array':
            return f'list[{self.elementType.type}]'
        elif self.type == 'map':
            return f'dict[{self.keyType.type}, {self.valType.type}]'
        elif self.type == 'func':
            return f'Callable[[{", ".join(self.argsTypes)}], {self.returnType}]'
        elif self.type in self.nativeTypes:
            return self.nativeTypes[self.type] 
        elif self.isClass:
            return f'TypeVar("{self.type}")'
        else:
            return f'TypeVar("{self.type}")'

exec(open(__file__.rsplit('/', 1)[0]+"/tokens.py").read())

class Comment(Comment):
    pass

class Null(Null):
    def __repr__(self):
        return 'None'

class Module(Module):
    def __init__(self, expr, name, namespace, native=False):
        super().__init__(expr, name, namespace, native=native)
        if self.native:
            self.imports = [f'import {self.name}']

    def __repr__(self):
        return f'#module {self.name}'

class Group(Group):
    pass

class Scope(Scope):
    beginSymbol = ':'
    endSymbol = ''
    def __repr__(self):
        if repr(self.sequence).strip():
            return super().__repr__()
        else:
            return f':\n{self.indent}pass\n'

class NativeCode(NativeCode):
    pass

class Bool(Bool):
    def format(self):
        return f'"true" if {self.expression()} else "false"'

    def expression(self):
        return '1' if self.value == 'true' else '0'

class Num(Num):
    pass

class String(String):
    imports = []
    def __repr__(self):
        if self.expressions:
            return f'{self.value}.format({", ".join([repr(expr) for expr in self.expressions])})'
        return self.value

class Var(Var):
    imports = []
    def prepare(self):
        if self.namespace:
            self.name = f'{self.namespace}__{self.value}'
        else:
            self.name = self.value

    def declaration(self):
        return f'{self.value}:{self.type}'

    def format(self):
        if self.type.type in ['map', 'array']:
            if not self.indexAccess:
                return f'str({self.name})'
            return self.expression()
        if self.type.type == 'bool':
            return f'"true" if {self.name} else "false"'
        if self.type.type not in ['str','int','float', 'bool']:
            if self.type.isClass:
                return f'"<class {self.type.type}>"'
            return f'str({self.name})'
        return self.name

    def method(self):
        return f'{self.name}'

    def expression(self):
        if self.indexAccess:
            if self.type.type == 'array':
                return f'{self.name}[{self.indexAccess}]'
            if self.type.type == 'map':
                return f'{self.name}[{self.indexAccess}]'
            else:
                return f'{self.name}[{self.indexAccess}]'
        return self.name

class Expr(Expr):
    operatorOrder = [
        'not','**','*','%','/','-','+','==','!=','>','<','>=','<=',
        'is','in','andnot','and','or','&', '<<', '>>'
    ]
    opConversions = {
        'and': 'and',
        'or': 'or',
        'not': 'not',
    }
    def concatenate(self, arg1, arg2, t):
        return Expr(value=f'{arg1} + {arg2}', type=t)

class Delete(Delete):
    def __repr__(self):
        self.expr.mode = 'method'
        if self.expr.type.type in ['array', 'map']:
            return f'del {self.expr}[{self.expr.value.indexAccess}]'
        if isinstance(self.expr.value, DotAccess):
            return f'del {self.expr}[{self.expr.value.indexAccess}]'
        raise SyntaxError(f'Delete not supported for type {type(self.expr.value)}')

class DotAccess(DotAccess):
    imports = []
    def format(self):
        if self.type.isClass or self.type.type in ['array', 'map']:
            return f'str({self.value})'
        return self.value

    def expression(self):
        if self.chain[0].type.isModule:
            self.chain[0].namespace = ''
        chain = [repr(self.chain[0])]
        currentType = self.chain[0].type
        for n, c in enumerate(self.chain[1:]):
            if currentType.native:
                chain.append('.')
                chain.append(repr(c))
            elif currentType.type == 'file':
                if isinstance(c, Call):
                    if repr(c.name) in ['write', 'close', 'read']:
                        if repr(c.name) == 'read' and not c.args:
                            c.name.value = 'readline'
                        chain.append('.')
                        chain.append(repr(c))
                    else:
                        raise SyntaxError(f'File object has no method {c.name}')
                else:
                    raise SyntaxError(f'File object has no attribute {c}')
            elif currentType.type == 'array' and isinstance(c, Call):
                chain.append('.')
                chain.append(repr(c))
            elif currentType.type == 'array' and isinstance(c, Var):
                if repr(c) == 'len':
                    varName = ''.join(chain)
                    chain = [f'len({varName})']
                else:
                    chain.append('.')
                    chain.append(c.name)
            elif c.type.type == 'array' and getattr(c, 'indexAccess', None):
                chain.append('.')
                chain.append(repr(c))
                c.type = c.type.elementType
            elif currentType.isClass and isinstance(c, Call):
                instanceName = ''.join(chain)
                #TODO this fails sometimes but a method
                # always should have the self...
                if c.signature:
                    del c.signature[0]
                if c.args.args:
                    del c.args.args[0]
                if instanceName == 'super':
                    chain.append('().')
                    chain.append(repr(c))
                else:
                    chain.append('.')
                    chain.append(repr(c))
            elif currentType.isModule:
                if currentType.native:
                    input(f'Is native {c}')
                else:
                    chain = [repr(c)]
            else:
                chain.append('.')
                chain.append(repr(c))
            currentType = c.type
        if self.mode == 'method':
            self.chain[-1].mode = 'method'
            chain[-1] = repr(self.chain[-1])
            self.chain[-1].mode = 'expr'
        self.processed = True
        return ''.join(chain)

class Return(Return):
    def __repr__(self):
        return f'return {self.expr}'

class Array(Array):
    imports = []
    def prepare(self):
        self.len = len(self.elements)
        self.size = 8 if self.len < 8 else self.len

    def expression(self):
        return '[' + ','.join([repr(e) for e in self.elements]) + ']'

    def __repr__(self):
        self.prepare()
        value = self.expression()
        if self.mode == 'format':
            return f'str({value})'
        return value

class KeyVal(KeyVal):
    pass

class Map(Map):
    def __repr__(self):
        return '{' + ', '.join([repr(kv) for kv in self.keyVals])+ '}'

class Open(Open):
    def __repr__(self):
        return f'open({self.args})'

class Input(Input):
    imports = []
    def __repr__(self):
        return f'input({self.expr})'

class Break(Break):
    def __repr__(self):
        return f'break'

# Representation Types

class Sequence(Sequence):
    def __init__(self, objs=None, terminator='', apply=None):
        super().__init__(objs=objs, terminator=terminator, apply=apply)

class Cast(Cast):
    conversion = {
        'int':{
            'str': 'int({self.expr})',
            'float': 'int({self.expr})',
        },
        'float':{
            'str': 'float({self.expr})',
            'int': 'float({self.expr})',
        },
        'str':{
            'int': 'str({self.expr})',
            'float': 'str({self.expr})',
        },
    }

    def __repr__(self):
        self.expr.namespace = self.namespace
        castFrom = self.expr.type.type
        castTo = self.castTo.type
        if castTo == 'map':
            castTo = self.castTo.valType.type
        elif castTo == 'array' and castFrom == 'array':
            return f'{self.expr}'
        elif castTo == 'array':
            castTo = self.castTo.elementType.type
        if castFrom == 'map' and self.expr.indexAccess is not None:
            castFrom = self.expr.type.valType
        elif castFrom == 'array' and self.expr.indexAccess is not None:
            castFrom = self.expr.type.elementType
        try:
            if self.castTo.isClass:
                return f'{self.expr}'
            elif castTo != castFrom and castTo in self.conversion:
                return self.conversion[castTo][castFrom].format(self=self)
            return repr(self.expr)
        except KeyError as e:
            raise SyntaxError(f'Cast not implemented for type {castTo} from {castFrom} {e}')

class Assign(Assign):
    def declaration(self):
        return f'{self.target}:{self.target.type}'

    def expression(self):
        if self.inMemory or isinstance(self.target, DotAccess):
            if self.target.indexAccess:
                if self.target.type.type == 'array':
                    return f'{self.target.name}[{self.target.indexAccess}] = {self.value}'
                if self.target.type.type == 'map':
                    return f'{self.target.name}[{self.target.indexAccess}] = {self.value}'
                else:
                    # indexAccess already processed in self.target
                    return f'{self.target} = {self.value}'
            return f'{self.target} = {self.value}'
        else:
            return f'{self.target}:{self.target.type} = {self.value}'

class Args(Args):
    pass

class Kwargs(Kwargs):
    def __repr__(self):
        self.prepare()
        if self.mode == 'value':
            return ', '.join([repr(kwarg.value) for kwarg in self.kwargs])
        return ', '.join([repr(kwarg) for kwarg in self.kwargs])

class Call(Call):
    def __repr__(self):
        if self.mode == 'format' and self.type.isClass:
            return f'"<class {self.type.type}>"'
        if self.signature:
            kwargs = []
            args = []
            # allocate args then sort kwargs
            for s in self.signature[len(self.args.args):]:
                for kwarg in self.kwargs.kwargs:
                    if isinstance(s, Assign):
                        kwarg.target.namespace = ''
                        if s.target.index == kwarg.target.index:
                            if kwarg.type != s.type:
                                kwarg = Cast(Expr(kwarg.value), s.type)
                            kwargs.append(kwarg)
                            break
                else:
                    kwargs.append(s)
            kwargs = Kwargs(kwargs, mode='value')
            for arg, sig in zip(self.args, self.signature):
                if arg.type != sig.type:
                    args.append(Cast(arg, sig.type))
                else:
                    args.append(arg)
            args = Args(args, mode='expr')
        else:
            kwargs = []
            for kwarg in self.kwargs.kwargs:
                kwarg.namespace = ''
                kwargs.append(kwarg)
            kwargs = Kwargs(kwargs, mode='value')
            args = self.args
        separator = ', ' if args and kwargs else ''
        if self.type.isClass:
            return f'{self.name}({args}{separator}{kwargs})'
        else:
            return f'{self.name}({args}{separator}{kwargs})'

class Print(Print):
    def __repr__(self):
        return f'print({self.args})'

class Function(Function):
    def expression(self):
        return f'def {self.name}({self.args}{self.separator}{self.kwargs}) -> {self.name.type} {self.code}'

class Class(Class):
    def formatNewMethod(self):
        paramsInit = []
        for p in self.parameters.values():
            if isinstance(p, Assign):
                if not p.target.attribute:
                    paramsInit.append(
                        NativeCode(f'self.{p.target} = {p.value}'))
                else:
                    paramsInit.append(
                        NativeCode(f'self.{p.target} = {p.target}'))
            elif isinstance(p, Expr):
                paramsInit.append(
                    NativeCode(f'self.{p} = None'))
        code = paramsInit + self.new.code.sequence.sequence
        self.new.code = Scope(code)

    def __repr__(self):
        value = f'class {self.name}({self.args}):\n'
        self.writeMode()
        for method in self.methods.values():
            if method.name.value == 'new':
                method = deepcopy(method)
                method.name.value = '__init__'
                method.name.type = Type('unknown')
                if not method.args.args or not repr(method.args.args[0].name) != "self":
                    method.args.args.insert(0, Var('self', repr(self.name)))
            method.namespace = ''
            method.code.indent = ' '*8
            value += f'    {method}\n'
        return value+self.postCode

class Elif(Elif):
    def __repr__(self):
        return f'elif {self.expr} {self.block}'

class Else(Else):
    def __repr__(self):
        return f'else {self.block}'

class If(If):
    def __repr__(self):
        return f'if {self.expr} {self.ifBlock}{"".join(repr(e) for e in self.elifs)}{self.elseBlock}'

class While(While):
    def __repr__(self):
        return f'while {self.expr} {self.block}'

class For(For):
    def __repr__(self):
        if isinstance(self.iterable, Range):
            if len(self.args.args) == 1:
                return f'for {self.args[0]} in range({self.iterable.initial}, {self.iterable.final}, {self.iterable.step}) {self.code}'
            if len(self.args.args) == 2:
                return f'for {self.args[0]}, {self.args[1]} in enumerate(range({self.iterable.initial}, {self.iterable.final}, {self.iterable.step})) {self.code}'
        elif isinstance(self.iterable, Expr):
            if self.iterable.type.type == 'array':
                if len(self.args.args) == 1:
                    return f'for {self.args[0]} in {self.iterable} {self.code}'
                if len(self.args.args) == 2:
                    return f'for {self.args[0]}, {self.args[1]} in enumerate({self.iterable}) {self.code}'
            if self.iterable.type.type == 'map':
                if len(self.args.args) == 1:
                    return f'for {self.args[0]} in {self.iterable} {self.code}'
                if len(self.args.args) == 2:
                    return f'for {self.args[0]}, {self.args[1]} in {self.iterable}.items() {self.code}'
            if self.iterable.type.type == 'str':
                if len(self.args.args) == 1:
                    return f'for {self.args[0]} in {self.iterable} {self.code}'
                if len(self.args.args) == 2:
                    return f'for {self.args[0]}, {self.args[1]} in enumerate({self.iterable}) {self.code}'
            else:
                raise TypeError('Iterable type is unknown')
        else:
            raise ValueError(f'Iterable of type {type(self.iterable)} no supported in for.')

class Range(Range):
    pass

class AugAssign(AugAssign):
    pass
