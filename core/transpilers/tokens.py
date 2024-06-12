# Basic Types
from copy import deepcopy
from pprint import pprint

class Comment():
    def __repr__(self):
        return ''

    @property
    def index(self):
        return None

class Null():
    imports = []
    def __init__(self):
        self.namespace = ''
        self.type = Type('void')
    
    def prepare(self):
        pass

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        return None

class Module():
    def __init__(self, expr, name, namespace, native=False, scope=None):
        self.expr = expr
        self.name = name
        self.namespace = namespace
        self.type = Type('module', name=name, native=native)
        self.native = native
        self.links = []
        self.imports = []
        self.scope = scope

    def __repr__(self):
        return f'#module {self.name}'

    @property
    def index(self):
        return self.expr.index

class Group():
    imports = []
    def __init__(self, expr):
        self.expr = expr
        self.namespace = expr.namespace
        self.type = expr.type

    def prepare(self):
        pass

    def __repr__(self):
        return f'({self.expr})'

class Scope():
    beginSymbol = '{'
    endSymbol = '}'
    def __init__(self, obj, indent=4):
        if isinstance(obj, Scope):
            self.sequence = obj.sequence
        else:
            if not isinstance(obj, Sequence):
                self.sequence = Sequence(obj)
            else: 
                self.sequence = obj
        self.indent = ' '*indent

    def __len__(self):
        return len(self.sequence)

    def __repr__(self):
        return f'{self.beginSymbol}\n' + '\n'.join(
            [self.indent + r 
                for r in repr(self.sequence).split('\n')]
        ) + f'\n{self.endSymbol}'

    def extend(self, scope):
        self.sequence = self.sequence + scope.sequence

    def __iter__(self):
        return iter(self.sequence)

class NativeCode():
    imports = []
    def __init__(self, line):
        self.line = line

    def prepare(self):
        pass

    def __repr__(self):
        return self.line

class Obj():
    def __init__(self, value='', type='', namespace='', mode='expr'):
        self.value = value
        self.type = Type(type)
        self.namespace = namespace
        self.mode = mode
        self.imports = []

    def prepare(self):
        pass

    def expression(self):
        return 'Obj-expr'

    def declaration(self):
        return 'Obj-expr'

    def format(self):
        return 'Obj-expr'

    def method(self):
        return 'Obj-method'

    def __repr__(self):
        self.prepare()
        if self.mode == 'expr':
            return self.expression()
        elif self.mode == 'declaration':
            return self.declaration()
        elif self.mode == 'format':
            return self.format()
        elif self.mode == 'method':
            return self.method()
        elif self.mode == 'types':
            return self.types()
        elif self.mode == 'empty':
            return ''
        else:
            raise ValueError(f'Mode {self.mode} not implemented.')

    @property
    def index(self):
        return None

class Bool(Obj):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = Type('bool')

    def format(self):
        return f'{self.expression()} ? "true": "false"'

    def expression(self):
        return '1' if self.value == 'true' else '0'

class Num(Obj):
    def __repr__(self):
        return str(self.value)

class String(Obj):
    imports = []
    def __init__(self, expressions='', **kwargs):
        kwargs['type'] = 'str'
        super().__init__(**kwargs)
        self.value = '"' + self.value[1:-1].replace('"', '\\"') + '"'
        self.expressions = expressions if expressions else []

    def __repr__(self):
        if self.expressions:
            raise NotImplemented 
        return self.value

class Var(Obj):
    imports = []
    def __init__(self, *args, indexAccess=None, attribute=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.indexAccess = indexAccess
        self.attribute = attribute
        self.prepare()

    def prepare(self):
        if self.namespace:
            self.name = f'{self.namespace}__{self.value}'
        else:
            self.name = self.value

    def declaration(self):
        if self.type.type == 'func':
            self.type.funcName = self.value
            return f'{self.type}'
        return f'{self.type} {self.value}'

    def format(self):
        if self.type.type in ['map', 'array']:
            if not self.indexAccess:
                call = repr(self.type).replace("*","").replace('struct ','')
                return f'{call}_str({self.name})'
            return self.expression()
        if self.type.type == 'bool':
            return f'{self.name} ? "true" : "false"'
        if self.type.type not in ['str','int','float', 'bool']:
            if self.type.isClass:
                return f'"<class {self.type.type}>"'
            call = repr(self.type).replace("*","").replace('struct ','')
            return f'{call}_str({self.name})'
        return self.name

    def method(self):
        return f'{self.name}'

    def expression(self):
        if self.indexAccess:
            if self.type.type == 'array':
                return f'list_{self.type.elementType.type}_get({self.name}, {self.indexAccess})'
            if self.type.type == 'map':
                return f'dict_{self.type.keyType.type}_{self.type.valType.type}_get({self.name}, {self.indexAccess})'
            else:
                return f'{self.name}[{self.indexAccess}]'
        return self.name

    def types(self):
        return f'{self.type}'

    def __hash__(self):
        self.prepare()
        return hash(self.name)

    @property
    def index(self):
        if self.namespace:
            return f'{self.namespace}__{self.value}'
        return f'{self.value}'

class Expr(Obj):
    operatorOrder = [
        'not','**','*','%','/','-','+','==','!=','>','<','>=','<=',
        'is','in','andnot','and','or','&', '<<', '>>'
    ]
    opConversions = {
        'and': '&&',
        'or': '||',
        'not': '!',
    }
    def __init__(self, *elements, ops=None, **kwargs):
        super().__init__(**kwargs)
        self.elements = list(elements)
        self.ops = ops if ops else []
        if not self.value:
            self.process()
        else:
            # Already processed, so it's native code
            self.value = NativeCode(self.value)

    def prepare(self):
        self.value.mode = self.mode
        self.value.type = self.type
        self.value.namespace = self.namespace
        self.value.prepare()
        self.imports = self.value.imports

    def process(self):
        ops = self.ops.copy()
        elements = deepcopy(self.elements)
        if len(elements) == 1 and len(self.ops) == 1:
            if self.ops[0] == 'not':
                elements[0] = Expr(value=f'{self.opConversions["not"]} {elements[0]}', type=Type('bool'))
                self.ops = []
            elif self.ops[0] == '-':
                elements[0] = Expr(value=f'-{elements[0]}', type=elements[0].type)
                self.ops = []
        else:
            self.type = 'unknown'
            for op in self.operatorOrder:
                while op in ops:
                    index = ops.index(op)
                    arg1 = elements[index]
                    arg2 = elements[index+1]
                    elements[index] = self.operations(op, arg1, arg2)
                    del ops[index]
                    del elements[index+1]
        self.value = elements[0]
        self.namespace = elements[0].namespace
        self.type = elements[0].type
        self.indexAccess = getattr(elements[0], 'indexAccess', None)

    def operations(self, op, arg1, arg2):
        t = None
        intOrFloat = [Type('int'), Type('float')]
        if op in ['+', '-','*','**']:
            if arg1.type == arg2.type:
                t = arg1.type
            elif arg1.type in intOrFloat or arg2.type in intOrFloat:
                t = Type('float')
            else:
                t = Type('unknown')
        elif op == '/':
            t = Type('float')
        elif op == '%':
            t = Type('int')
        elif op in ['not','==','!=','>','<','>=','<=','in','and','or']:
            t = Type('bool')
        if op in self.opConversions:
            op = self.opConversions[op]
        if arg1.type == Type('str') and op == '+':
            if arg1.type == arg2.type:
                return self.concatenate(arg1, arg2, t)
            raise RuntimeError(f'Sum of str with {arg2.type.type} not supported')
        return Expr(value=f'{arg1} {op} {arg2}', type=t)

    def concatenate(self, arg1, arg2, t):
        return Expr(value=f'__photon_format_str("%s%s", {arg1}, {arg2})', type=t)

    def __repr__(self):
        self.prepare()
        return repr(self.value)

    @property
    def index(self):
        self.prepare()
        if len(self.elements) == 1:
            return self.value.index
        return super().index

class Delete():
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        self.expr.mode = 'method'
        if self.expr.type.type in ['array', 'map']:
            call = f'{self.expr.type}'.replace('*','')
            return f'{call}_del({self.expr}, {self.expr.value.indexAccess})'
        if isinstance(self.expr.value, DotAccess):
            return repr(self.expr.value).replace('_get(', '_del(', 1)
        raise SyntaxError(f'Delete not supported for type {type(self.expr.value)}')

    @property
    def index(self):
        return None

class DotAccess():
    imports = []
    def __init__(self, chain=None, type=None, namespace='', mode='expr'):
        self.chain = chain
        self.namespace = namespace
        self.chain[0].namespace = namespace
        self.type = type
        self.indexAccess = getattr(chain[-1], 'indexAccess', None)
        self.mode = mode
        self.processed = False

    def prepare(self):
        pass

    def format(self):
        call = repr(self.type).replace("*","")#.replace("struct ", '')
        if self.type.isClass or self.type.type in ['array', 'map']:
            return f'{call}_str({self.value})'
        return self.value

    def expression(self):
        chain = [repr(self.chain[0])]
        currentType = self.chain[0].type
        for n, c in enumerate(self.chain[1:]):
            if currentType.native:
                chain.append('.')
                chain.append(repr(c))
            elif currentType.type == 'file':
                if isinstance(c, Call):
                    fileName = ''.join(chain)
                    if repr(c.name) == 'write':
                        chain = [f'fprintf({fileName}, {c.args})']
                    elif repr(c.name) == 'close':
                        chain = [f'fclose({fileName})']
                    elif repr(c.name) == 'read':
                        chain = [f'photonRead({fileName})']
                    else:
                        raise SyntaxError(f'File object has no method {c.name}')
                else:
                    raise SyntaxError(f'File object has no attribute {c}')
            elif currentType.type == 'array' and isinstance(c, Call):
                instanceName = ''.join(chain)
                chain = [f'list_{currentType.elementType.type}']
                chain.append('_')
                c.args.args.insert(0, Var(instanceName, currentType))
                chain.append(repr(c))
            elif c.type.type == 'array' and getattr(c, 'indexAccess', None):
                chain.append('->')
                chain.append(c.name)
                instanceName = ''.join(chain)
                chain.append('_')
                c.value = instanceName
                chain = [repr(c)]
                c.type = c.type.elementType
            elif currentType.isClass and isinstance(c, Call):
                instanceName = ''.join(chain)
                if instanceName == 'super':
                    del c.args.args[0]
                    c.args.args.insert(0, Cast(Var('self', currentType), castTo=currentType))
                    chain = [f'{currentType.type}__{repr(c)}']
                else:
                    chain = [instanceName]
                    chain.append('->')
                    chain.append(repr(c))
            elif currentType.isModule:
                chain[n-1] = ''
                chain.append(repr(c))
            else:
                chain.append('->')
                chain.append(repr(c))
            currentType = c.type
        if self.mode == 'method':
            self.chain[-1].mode = 'method'
            chain[-1] = repr(self.chain[-1])
            self.chain[-1].mode = 'expr'
        self.processed = True
        return ''.join(chain)

    def __repr__(self):
        if not self.processed:
            self.value = self.expression()
            if self.mode == 'format':
                self.value = self.format()
        return self.value

    @property
    def index(self):
        return None

class Return():
    def __init__(self, expr=None):
        self.expr = expr
        self.type = expr.type

    def __repr__(self):
        return f'return {self.expr}'

    @property
    def index(self):
        return None

class Array():
    def __init__(self, *elements, type=None, mode='expr'):
        self.elements = elements
        self.type = type
        self.prepare()
        self.namespace = ''
        self.mode = mode

    def prepare(self):
        self.len = len(self.elements)
        self.size = 8 if self.len < 8 else self.len
        self.imports = []

    def expression(self):
        raise NotImplemented

    def __repr__(self):
        raise NotImplemented

class KeyVal():
    def __init__(self, key='', val=''):
        self.key = key
        self.val = val

    def __repr__(self):
        return f'{self.key},{self.val}'

class Map():
    def __init__(self, *keyVals, type=None):
        self.keyVals = keyVals
        self.type = type
        self.namespace = ''
        self.prepare()
    
    def prepare(self):
        self.imports = []

    def __repr__(self):
        raise NotImplemented

class Open():
    imports = []
    def __init__(self, args=None, namespace=''):
        self.args = Args(args)
        self.type = Type('file')
        self.namespace = namespace

    def prepare(self):
        pass

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        return None

class Input():
    def __init__(self, expr=None, namespace=''):
        self.expr = expr
        self.imports = []
        self.type = Type('str')
        self.namespace = namespace

    def prepare(self):
        pass

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        return None

class Break():
    def __repr__(self):
        return f'break'

    @property
    def index(self):
        return None

# Representation Types

class Sequence():
    def __init__(self, objs=None, terminator=';', apply=None):
        self.terminator = terminator
        self.sequence = [] if objs is None else objs
        self.apply = apply

    def add(self, obj):
        self.sequence.append(obj)

    def __add__(self, sequence):
        if isinstance(sequence, Sequence):
            return Sequence(self.sequence + sequence.sequence)
        raise ValueError(f'Object of type {type(sequence)} cannot be added to Sequence.')

    def __repr__(self):
        representation = ''
        for obj in self.sequence:
            if isinstance(obj, Expr):
                obj.mode = 'declaration'
            if self.apply:
                obj = self.apply(obj)
            representation += f'{obj}{self.terminator}\n'
        return representation

    def __len__(self):
        return len(self.sequence)

    def __getitem__(self, index):
        return self.sequence[index]

    def __iter__(self):
        return iter(self.sequence)

    @property
    def index(self):
        return None

class Cast():
    imports = []
    conversion = {
        'int':{
            'str': 'castToIntFromStr',
        },
    }

    def __init__(self, expr, castTo):
        if isinstance(expr, Cast):
            self.expr = expr.expr
        else:
            self.expr = expr
        self.castTo = castTo
        self.type = self.castTo
        self.namespace = self.expr.namespace

    def prepare(self):
        pass

    @property
    def value(self):
        return self

    def __repr__(self):
        self.expr.namespace = self.namespace
        castFrom = self.expr.type.type
        castTo = self.castTo.type
        if castTo == 'map':
            castTo = self.castTo.valType.type
        elif castTo == 'array' and castFrom == 'array':
            return f'({self.castTo}) {self.expr}'
        elif castTo == 'array':
            castTo = self.castTo.elementType.type
        if castFrom == 'map' and self.expr.indexAccess is not None:
            castFrom = self.expr.type.valType
        elif castFrom == 'array' and self.expr.indexAccess is not None:
            castFrom = self.expr.type.elementType
        try:
            if self.castTo.isClass:
                return f'({self.castTo}) {self.expr}'
            elif castTo != castFrom and castTo in self.conversion:
                return self.conversion[castTo][castFrom].format(self=self)
            return repr(self.expr)
        except KeyError as e:
            raise SyntaxError(f'Cast not implemented for type {castTo} from {castFrom} {e}')

class Assign(Obj):
    def __init__(self, target='', inMemory=False, cast=None, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.namespace = target.namespace
        self.inMemory = inMemory
        self.type = self.target.type
        self.cast = cast
        if self.cast is not None:
            self.value = Cast(self.value, self.cast)

    def prepare(self):
        self.target.namespace = self.namespace

    def declaration(self):
        raise NotImplemented

    def expression(self):
        raise NotImplemented

    def types(self):
        return f'{self.type}'

    @property
    def index(self):
        self.prepare()
        return self.target.index

class Args():
    def __init__(self, args, mode='expr'):
        if isinstance(args, Args):
            self.args = args.args
            self.mode = args.mode
        else:
            self.args = args if args else []
            self.mode = mode

    def prepare(self):
        for arg in self.args:
            arg.mode = self.mode
    
    def __bool__(self):
        return True if repr(self) else False

    def __getitem__(self, index):
        return self.args[index]

    def __repr__(self):
        self.prepare()
        return ', '.join([repr(arg) for arg in self.args])

class Kwargs():
    def __init__(self, kwargs, mode='expr'):
        if isinstance(kwargs, Kwargs):
            self.kwargs = kwargs.kwargs
            self.mode = kwargs.mode
        else:
            self.kwargs = kwargs
            self.mode = mode

    def prepare(self):
        mode = self.mode
        if mode == 'value':
            # value mode is exclusive for kwarg
            mode = 'expr'
        for kwarg in self.kwargs:
            kwarg.mode = mode

    def __bool__(self):
        return True if repr(self) else False

    def __repr__(self):
        self.prepare()
        if self.mode == 'value':
            return ', '.join([repr(kwarg.value) for kwarg in self.kwargs])
        return ', '.join([repr(kwarg) for kwarg in self.kwargs])

class Call(Obj):
    def __init__(self, name='', args='', kwargs='', signature='', namespace='', **defaults):
        super().__init__(**defaults)
        self.name = name
        self.type = self.name.type
        self.args = Args(args)
        self.kwargs = Kwargs(kwargs)
        self.signature = signature
        self.namespace = namespace

    def prepare(self):
        self.name.namespace = self.namespace

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
            return f'{self.name}__new({args}{separator}{kwargs})'
        else:
            return f'{self.name}({args}{separator}{kwargs})'

class Print():
    def __init__(self, args=None):
        self.args = Args(args)

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        return

class Function(Obj):
    def __init__(self, name='', args='', kwargs='', code=None, signature=None, **defaults):
        super().__init__(**defaults)
        self.name = name
        self.namespace = name.namespace
        self.type = name.type
        self.args = Args(args, mode='declaration')
        self.kwargs = Kwargs(kwargs, mode='declaration')
        self.code = Scope(code)
        self.signature = signature if signature is not None else []

    def prepare(self):
        self.name.namespace = self.namespace
        self.separator = ', ' if self.args and self.kwargs else ''

    def declaration(self):
        raise NotImplemented 

    def expression(self):
        raise NotImplemented

    @property
    def index(self):
        self.prepare()
        return self.name.index

class Class():
    def __init__(self, name='', args=None, code=None, parameters=None, methods=None, new=None):
        self.name = name
        self.namespace = name.namespace
        self.args = Args(args)
        self.code = Scope(code)
        self.type = Type(repr(self.name))
        self.parameters = parameters
        self.methods = methods if methods is not None else {}
        self.new = new
        self.formatNewMethod()
        self.postCode = ''

    def prepare(self):
        self.name.namespace = self.namespace

    def formatNewMethod(self):
        raise NotImplemented

    def declarationMode(self):
        for _, t in self.parameters.items():
            t.mode = 'declaration'
    
    def writeMode(self):
        for _, t in self.parameters.items():
            t.mode = 'expr'

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        self.prepare()
        return self.name.index

class Elif():
    def __init__(self, expr, block):
        self.expr = expr
        self.block = Scope(block)

    def __repr__(self):
        raise NotImplemented

class Else():
    def __init__(self, block):
        self.block = Scope(block)

    def __repr__(self):
        raise NotImplemented

class If():
    def __init__(self, expr, ifBlock, elifs=None, elseBlock=None):
        self.expr = expr
        self.ifBlock = Scope(ifBlock)
        self.elifs = elifs
        self.elseBlock = Else(elseBlock) if elseBlock is not None else ''

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        return None

class While():
    def __init__(self, expr, block=None):
        self.expr = expr
        self.block = Scope(block)

    def __repr__(self):
        raise NotImplemented

    @property
    def index(self):
        return None

class For():
    def __init__(self, args=None, iterable=None, code=None):
        self.args = Args(args)
        self.iterable = iterable
        self.code = Scope(code)
        self.imports = []

    def __repr__(self):
        #TODO break each type of for into different methods
        # so this logic won't be replicated to different targets
        if isinstance(self.iterable, Range):
            if len(self.args.args) == 1:
                raise NotImplemented
            if len(self.args.args) == 2:
                raise NotImplemented
        elif isinstance(self.iterable, Expr):
            if self.iterable.type.type == 'array':
                if len(self.args.args) == 1:
                    raise NotImplemented
                if len(self.args.args) == 2:
                    raise NotImplemented
            if self.iterable.type.type == 'map':
                if len(self.args.args) == 1:
                    raise NotImplemented
                if len(self.args.args) == 2:
                    raise NotImplemented
            if self.iterable.type.type == 'str':
                if len(self.args.args) == 1:
                    raise NotImplemented
                if len(self.args.args) == 2:
                    raise NotImplemented
            else:
                raise TypeError('Iterable type is unknown')
        else:
            raise ValueError(f'Iterable of type {type(self.iterable)} no supported in for.')

    @property
    def index(self):
        return None

class Range():
    def __init__(self, initial=None, final=None, step=None):
        self.initial = initial
        self.final = final
        self.step = step
        if self.initial.type.type == 'int' and self.step.type.type == 'int':
            self.type = Type('int')
        else:
            self.type = Type('float')

class AugAssign():
    def __init__(self, target=None, expr=None, operator=None):
        self.target = target
        self.expr = expr
        self.operator = operator

    def __repr__(self):
        if self.operator in ['+','-','*','/','%','&']:
            return repr(Assign(
                target=self.target,
                value=Expr(self.target, self.expr, ops=[self.operator]),
                inMemory=True))
        raise NotImplemented('operator not implemented')

    @property
    def index(self):
        return None
