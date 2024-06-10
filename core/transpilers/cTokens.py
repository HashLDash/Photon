# Basic Types
from copy import deepcopy
from pprint import pprint
from .baseType import BaseType

class Type(BaseType):
    nativeTypes = {
        'int':'long',
        'str':'char*',
        'float':'double',
        'bool':'int',
        'unknown':'void',
        '':'void',
        'obj':'obj',
        'file':'FILE*',
    }

    def __repr__(self):
        if self.native:
            return self.type
        elif self.type == 'array':
            return f'list_{self.elementType.type}*'
        elif self.type == 'map':
            return f'dict_{self.keyType.type}_{self.valType.type}*'
        elif self.type == 'func':
            return f'{self.returnType} (*{self.funcName})({", ".join(self.argsTypes)})'
        elif self.type in self.nativeTypes:
            return self.nativeTypes[self.type] 
        elif self.isClass:
            return f'struct {self.type}*'
        else:
            return f'{self.type}'

exec(open(__file__.rsplit('/', 1)[0]+"/tokens.py").read())

class Comment(Comment):
    pass

class Null(Null):
    def __repr__(self):
        return 'NULL'

class Module(Module):
    def __init__(self, expr, name, namespace, native=False):
        super().__init__(expr, name, namespace, native=native)
        if self.native:
            self.imports = [f'#include "{self.name}.h"']
            if self.name not in ['time']:
                self.links = [f'-l{self.name}']

    def __repr__(self):
        return f'//module {self.name}'

class Group(Group):
    pass

class Scope(Scope):
    beginSymbol = '{'
    endSymbol = '}'

class NativeCode(NativeCode):
    pass

class Bool(Bool):
    def format(self):
        return f'{self.expression()} ? "true": "false"'

    def expression(self):
        return '1' if self.value == 'true' else '0'

class Num(Num):
    pass

class String(String):
    imports = ['#include "asprintf.h"']
    types = {
        'str':'%s',
        'int':'%ld',
        'float':'%g',
        'bool':'%s',
    }
    def getFormat(self, valType):
        if valType in self.types:
            return self.types[valType]
        return '%s'
        
    def __init__(self, expressions='', **kwargs):
        super().__init__(expressions=expressions, **kwargs)
        for expr in self.expressions:
            expr.mode = 'format'
            valType = expr.type.type
            if 'func' in valType:
                valType = valType.replace(' func','').strip()
            if valType in self.types:
                self.value = self.value.replace('{}', self.getFormat(valType), 1)
            elif valType == 'array':
                if expr.indexAccess:
                    self.value = self.value.replace('{}', self.getFormat(expr.type.elementType.type), 1)
                else:
                    self.value = self.value.replace('{}', '%s', 1)
            elif valType == 'map':
                if expr.indexAccess:
                    self.value = self.value.replace('{}', self.getFormat(expr.type.valType.type), 1)
                else:
                    self.value = self.value.replace('{}', '%s', 1)
            elif expr.type.isClass:
                self.value = self.value.replace('{}', '%s', 1)
            else:
                raise SyntaxError(f'Cannot format {valType} in formatStr')

    def __repr__(self):
        if self.expressions:
            return f'__photon_format_str({self.value}, {", ".join([repr(expr) for expr in self.expressions])})'
        return self.value

class Var(Var):
    imports = []
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

class Expr(Expr):
    operatorOrder = [
        'not','**','*','%','/','-','+','==','!=','>','<','>=','<=',
        'is','in','andnot','and','or','&', '<<', '>>'
    ]
    opConversions = {
        'and': '&&',
        'or': '||',
        'not': '!',
    }

class Delete(Delete):
    def __repr__(self):
        self.expr.mode = 'method'
        if self.expr.type.type in ['array', 'map']:
            call = f'{self.expr.type}'.replace('*','')
            return f'{call}_del({self.expr}, {self.expr.value.indexAccess})'
        if isinstance(self.expr.value, DotAccess):
            return repr(self.expr.value).replace('_get(', '_del(', 1)
        raise SyntaxError(f'Delete not supported for type {type(self.expr.value)}')

class DotAccess(DotAccess):
    imports = ['#include "photonInput.h"']
    def format(self):
        call = repr(self.type).replace("*","")
        if self.type.isClass or self.type.type in ['array', 'map']:
            return f'{call}_str({self.value})'
        return self.value

    def expression(self):
        chain = [repr(self.chain[0])]
        currentType = self.chain[0].type
        for n, c in enumerate(self.chain[1:]):
            if currentType.native:
                if currentType.isModule:
                    chain = [repr(c)]
                else:
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
                        self.imports = ['#include "photonInput.h"']
                    else:
                        raise SyntaxError(f'File object has no method {c.name}')
                else:
                    raise SyntaxError(f'File object has no attribute {c}')
            elif currentType.type == 'array' and isinstance(c, Call):
                instanceName = ''.join(chain)
                chain = [f'list_{currentType.elementType.type}']
                chain.append('_')
                c.args.args.insert(0, Var(instanceName, currentType))
                if repr(c.name) == 'append':
                    if c.args.args[1].type != currentType.elementType:
                        c.args.args[1] = Cast(deepcopy(c.args.args[1]), currentType.elementType)
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

class Return(Return):
    def __repr__(self):
        return f'return {self.expr}'

class Array(Array):
    def prepare(self):
        self.len = len(self.elements)
        self.size = 8 if self.len < 8 else self.len
        if self.type.known:
            self.imports = ['#include "asprintf.h"']
            if not self.type.elementType.isClass:
                self.imports.append(f'#include "list_{self.type.elementType.type}.h"')
        else:
            self.imports = []

    def expression(self):
        if self.elements:
            return f'list_{self.type.elementType.type}_constructor({self.len}, {self.size}, ' + ','.join([repr(e) for e in self.elements])+')'
        return f'list_{self.type.elementType.type}_constructor({self.len}, {self.size})'

    def __repr__(self):
        self.prepare()
        value = self.expression()
        if self.mode == 'format':
            return f'list_{self.type.elementType.type}_str({value})'
        return value

class KeyVal(KeyVal):
    pass

class Map(Map):
    def prepare(self):
        if self.type.known:
            self.imports = [
                f'#include "dict_{self.type.keyType.type}_{self.type.valType.type}.h"',
                '#include "asprintf.h"']
        else:
            self.imports = []

    def __repr__(self):
        self.prepare()
        size = 8 if (l:=len(self.keyVals)) < 8 else l
        if self.keyVals:
            return f'dict_{self.type.keyType.type}_{self.type.valType.type}_constructor({len(self.keyVals)},{size},' + ', '.join([repr(kv) for kv in self.keyVals])+')'
        return f'dict_{self.type.keyType.type}_{self.type.valType.type}_constructor({len(self.keyVals)},{size})'

class Open(Open):
    def __repr__(self):
        return f'fopen({self.args})'

class Input(Input):
    imports = ['#include "photonInput.h"']

    def __repr__(self):
        return f'photonInput({self.expr})'

class Break(Break):
    def __repr__(self):
        return f'break'

# Representation Types

class Sequence(Sequence):
    pass

class Cast(Cast):
    conversion = {
        'int':{
            'str': 'strtol({self.expr}, NULL, 10)',
            'float': '(long)({self.expr})',
        },
        'float':{
            'str': 'strtod({self.expr}, NULL)',
            'int': '(double)({self.expr})',
        },
        'str':{
            'int': '__photon_format_str("%ld", {self.expr})',
            'float': '__photon_format_str("%lf", {self.expr})',
        },
    }

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

class Assign(Assign):
    def declaration(self):
        if self.type.type == 'func':
            self.type.funcName = self.target.value
            return f'{self.type}'
        return f'{self.target.type} {self.target}'

    def expression(self):
        if self.inMemory or isinstance(self.target, DotAccess):
            if self.target.indexAccess:
                if self.target.type.type == 'array':
                    return f'list_{self.target.type.elementType.type}_set({self.target.name}, {self.target.indexAccess}, {self.value})'
                if self.target.type.type == 'map':
                    return f'dict_{self.type.keyType.type}_{self.type.valType.type}_set({self.target.name}, {self.target.indexAccess}, {self.value})'
                if isinstance(self.target, DotAccess) and self.target.chain[-1].type.type == 'array':
                    return repr(self.target).replace('_get(', '_set(', 1)[:-1] + f', {self.value})'
                else:
                    return f'{self.target.name}[{self.target.indexAccess}] = {self.value}'
            return f'{self.target} = {self.value}'
        else:
            return f'{self.target.type} {self.target} = {self.value}'

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
            return f'{self.name}__new({args}{separator}{kwargs})'
        else:
            return f'{self.name}({args}{separator}{kwargs})'

class Print(Print):
    def __repr__(self):
        formats = {
            'str': '%s',
            'int': '%ld',
            'float': '%g',
            'array': '%s',
            'map': '%s',
            'bool': '%s',
        }
        types = []
        for arg in self.args:
            argType = arg.type
            if argType.type == 'map':
                if getattr(arg, 'indexAccess', None) is not None:
                    argType = argType.valType
            elif argType.type == 'array':
                if getattr(arg, 'indexAccess', None) is not None:
                    argType = argType.elementType
            elif argType.type == 'func':
                argType = argType.returnType
                argType.funcName = arg.value
            elif argType.isClass:
                argType = Type('str')
            types.append(argType)
        template = String(value='"'+" ".join([formats[t.type] for t in types])+'\\n"')
        args = Args([template] + self.args.args, mode='format')
        return f'printf({args})'

class Function(Function):
    def declaration(self):
        oldMode = self.args.mode
        self.args.mode = 'types'
        result = f'{self.name.type} (*{self.name.value})({self.args}{self.separator}{self.kwargs})'
        self.args.mode = oldMode
        return result

    def expression(self):
        return f'{self.name.type} {self.name}({self.args}{self.separator}{self.kwargs}) {self.code}'

class Class(Class):
    def formatNewMethod(self):
        paramsInit = [
            NativeCode(f'{self.new.name.type} self = malloc(sizeof({self.name}))')]
        for p in self.parameters.values():
            if isinstance(p, Assign):
                if not p.target.attribute:
                    paramsInit.append(
                        NativeCode(f'self->{p.target} = {p.value}'))
                else:
                    paramsInit.append(
                        NativeCode(f'self->{p.target} = {p.target}'))
            elif isinstance(p, Function):
                paramsInit.append( 
                    NativeCode(f'self->{p.name.value} = {p.name}'))
        code = paramsInit + self.new.code.sequence.sequence
        code.append(NativeCode(f'return self'))
        self.new.code = Scope(code)

    def __repr__(self):
        self.declarationMode()
        declarations = Scope(
            list(self.parameters.values())
        )
        value = f'typedef struct {self.name} {declarations} {self.name};\n'
        self.writeMode()
        for method in self.methods.values():
            if method.name.value == 'new':
                continue
            value += f'{method}\n'
        value += f'{self.new}\n'
        return value+self.postCode

class Elif(Elif):
    def __repr__(self):
        return f'else if ({self.expr}) {self.block}'

class Else(Else):
    def __repr__(self):
        return f'else {self.block}'

class If(If):
    def __repr__(self):
        return f'if ({self.expr}) {self.ifBlock} {"".join(repr(e) for e in self.elifs)} {self.elseBlock}'

class While(While):
    def __repr__(self):
        return f'while ({self.expr}) {self.block}'

class For(For):
    def __init__(self, args=None, iterable=None, code=None):
        super().__init__(args=args, iterable=iterable, code=code)
        if self.iterable.type.type == 'str':
            self.imports.append('#include <string.h>')

    def __repr__(self):
        if isinstance(self.iterable, Range):
            if len(self.args.args) == 1:
                return f'for ({self.args[0].type} {self.args[0]}={self.iterable.initial}; {self.args[0]} < {self.iterable.final}; {self.args[0]} += {self.iterable.step}) {self.code}'
            if len(self.args.args) == 2:
                return f'{{{self.args[0].type} {self.args[0]}=0; for ({self.args[1].type} {self.args[1]}={self.iterable.initial}; {self.args[1]} < {self.iterable.final}; {self.args[0]}++, {self.args[1]} += {self.iterable.step}) {self.code}}}'
        elif isinstance(self.iterable, Expr):
            if self.iterable.type.type == 'array':
                if len(self.args.args) == 1:
                    iterableVar = f'__iterable_{self.args[0]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[0].type} {self.args[0]} = {iterableVar}->values[0]; for (long __forIndex=0; __forIndex < {iterableVar}->len; __forIndex++, {self.args[0]} = {iterableVar}->values[__forIndex]) {self.code}}}'
                if len(self.args.args) == 2:
                    iterableVar = f'__iterable_{self.args[1]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[1].type} {self.args[1]} = {iterableVar}->values[0]; for ({self.args[0].type} {self.args[0]}=0; {self.args[0]} < {iterableVar}->len; {self.args[0]}++, {self.args[1]} = {iterableVar}->values[{self.args[0]}]) {self.code}}}'
            if self.iterable.type.type == 'map':
                if len(self.args.args) == 1:
                    iterableVar = f'__iterable_{self.args[0]}'
                    iterableIndex = f'__iterable_index_{self.args[0]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[0].type} {self.args[0]} = {iterableVar}->entries[0].key; for (long {iterableIndex}=0; {iterableIndex} < {iterableVar}->len; {iterableIndex}++, {self.args[0]} = {iterableVar}->entries[{iterableIndex}].key) {self.code}}}'
                if len(self.args.args) == 2:
                    iterableVar = f'__iterable_{self.args[1]}'
                    iterableIndex = f'__iterable_index_{self.args[1]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[0].type} {self.args[0]} = {iterableVar}->entries[0].key;\n{self.args[1].type} {self.args[1]} = {iterableVar}->entries[0].val;\nfor (long {iterableIndex}=0; {iterableIndex} < {iterableVar}->len; {iterableIndex}++, {self.args[0]} = {iterableVar}->entries[{iterableIndex}].key, {self.args[1]} = {iterableVar}->entries[{iterableIndex}].val) {self.code}}}'
            if self.iterable.type.type == 'str':
                if len(self.args.args) == 1:
                    iterableVar = f'__iterable_{self.args[0]}'
                    return f'''{{{self.iterable.type} {iterableVar} = {self.iterable};\n;long __i = 0;char {self.args[0]}[] = " ";\nwhile({iterableVar}[__i] != '\\0') {{
                        int __len = mblen({iterableVar}+__i, 2);
                        for (int __j = 0; __j<__len;__j++) {{
                            {self.args[0]}[__j] = {iterableVar}[__i+__j];
                        }}
                        {self.args[0]}[__len] = '\\0';
                        {self.code}
                        __i += __len;
                    }}}}
                    '''
                if len(self.args.args) == 2:
                    iterableVar = f'__iterable_{self.args[1]}'
                    iterableIndex = f'{self.args[0]}'
                    return f'''{{{self.iterable.type} {iterableVar} = {self.iterable};\nlong {iterableIndex} = 0;long __i = 0; char {self.args[1]}[] = " ";\nwhile({iterableVar}[__i] != '\\0') {{
                        int __len = mblen({iterableVar}+__i, 2);
                        for (int __j = 0; __j<__len;__j++) {{
                            {self.args[1]}[__j] = {iterableVar}[__i+__j];
                        }}
                        {self.args[1]}[__len] = '\\0';
                        {self.code}
                        __i += __len;
                        {iterableIndex} += 1;
                    }}}}
                    '''
            else:
                raise TypeError('Iterable type is unknown')
        else:
            raise ValueError(f'Iterable of type {type(self.iterable)} no supported in for.')

class Range(Range):
    pass

class AugAssign(AugAssign):
    pass
