from copy import deepcopy
import photonParser as parser

def inference(value):
    ''' Return the token and infer its properties '''

    try:
        float(value)
        return {'token':'num', 'value': value, 'type':'int'}
    except:
        try:
            input(float(value[0]))
            input('it is something??')
            return {'token':'value','type':'unknown','value':value}
        except:
            if value == 'True' or value == 'False':
                return {'token':'expr','type':'bool','args': [{'token':'bool', 'type':'bool','value':value.lower()}], 'ops':[] }
            elif value == 'null':
                return {'token':'expr','type':'null','args': [{'token':'null', 'type':'null','value':'null'}], 'ops':[] }
            else:
                return {'token':'var', 'type':'unknown', 'name':value}

def comment(i, t):
    ''' Remove comment from token list '''
    for n, token in enumerate(t):
        if token['token'] in {'singleQuote', 'doubleQuote'}:
            # It is part of a string
            return 'continue'
        if token['token'] == 'hashtag':
            # remove all tokens after the hashtag
            if n == 1:
                # It's a line of comments
                t[n]['token'] = 'comment'
                return t[:n+1]
            # There is code and comment. Ignore the comment for now
            return t[:n]

def operator(i, t):
    ''' Combine operators that are compatible '''

    op1 = t[i]['operator'] if 'operator' in t[i] else t[i]['symbol']
    op2 = t[i+1]['operator'] if 'operator' in t[i+1] else t[i+1]['symbol']
    op = op1 + op2
    if op in {'**', '==', '>=', '<=','<<','>>','!='}:
        t[i] = {'token':'operator','operator':op}
    #elif op in {'+=','-=','*=','/='}:
    #    t[i] = {'token':'augEqual','symbol':op}
    else:
        return 'continue'
    del t[i+1] # operator or symbol
    return t

def string(i, t):
    ''' Return a string value token according to tokenList '''
    
    # Maybe there is a doubleQuote before, verify
    for n,token in enumerate(t):
        if token['token'] in {'singleQuote','doubleQuote'}:
            i = n
            break
    if t[i]['token'] == 'singleQuote':
        quote = "'"
        stringQuote = 'singleQuote'
    else:
        quote = '"'
        stringQuote = 'doubleQuote'
    s = ''
    n = 1
    expressions = []
    expression = []
    inExpr = False
    for token in t[i+1:]:
        if inExpr:
            if 'symbol' in token and token['symbol'] == '}':
                s += '}'
                inExpr = False
                expressions.append(deepcopy(expression))
                expression = []
            elif not token['token'] == 'space':
                expression.append(token)
        elif token['token'] == stringQuote:
            break
        elif 'singleQuote' in token:
            s += '"\'"'
        elif 'doubleQuote' in token:
            s += "'\"'"
        elif token['token'] == 'var':
            s += token['name']
        elif token['token'] == 'num':
            s += str(token['value'])
        elif 'operator' in token:
            s += token['operator']
        elif 'symbol' in token:
            if token['symbol'] == '{':
                inExpr = True
                s += '{'
            else:
                s += token['symbol']
        elif token['token'] == 'type':
            s += token['type']
        elif 'Statement' in token['token']:
            s += token['token'].replace('Statement', '')
        else:
            s += token['token']
        n += 1

    processedExpressions = []
    for expression in expressions:
        # process expression. Add a dummy token for index compatibility
        expression = parser.reduceToken([{'token':'indent'}]+expression)[1:][0]
        # verify if it's an expression
        if not expression['token'] == 'expr':
            raise SyntaxError(f'Expected expression in format string, but got {expression[0]["token"]} instead')
        else:
            processedExpressions.append(expression)

    t[i] = {
        'token':'expr',
        'type':'str',
        'args':[{'token':'str',
        'type':'str','value':f'{quote}{s}{quote}','expressions':processedExpressions}],
        'ops':[]
    }
    for _ in range(n):
        del t[i+1]
    return t

def var(i, t):
    return t

def arrayType(i, t):
    ''' 
    Return a type token according to signature.
    (var type) beginBlock num -> array
    '''
    # Verify if it's a valid type token
    if inMap(i, t):
        return 'continue'
    if t[i]['token'] == 'var':
        elementType = t[i]['name']
    elif t[i]['token'] == 'type':
        elementType = t[i]['type']
    else:
        raise SyntaxError('Array type tok {t[i]["token"} not implemented.')

    arraySize = t[i+2]['value']

    t[i] = {'token':'type', 'type':'array', 'elementType':elementType, 'size':arraySize}

    del t[i+1] #beginBlock
    del t[i+1] #num
    return t

def inMap(i, t):
    ''' Checks if the current token is inside a map definition '''
    # If there is an open brace, then it is a keyVal and not a mapType
    braceLevel = 0
    for i in range(i):
        if t[i]['token'] == 'lbrace':
            braceLevel += 1
        elif t[i]['token'] == 'rbrace':
            braceLevel -= 1
    if braceLevel > 0:
        return True
    return False

def mapType(i, t):
    ''' 
    Return a type token according to signature.
    (var type) beginBlock (var type) -> map
    '''
    # Verify if it's a valid type token
    if inMap(i, t):
        return 'continue'
    if t[i]['token'] == 'var':
        keyType = t[i]['name']
    elif t[i]['token'] == 'type':
        keyType = t[i]['type']
    else:
        raise SyntaxError('Map key type tok {t[i]["token"} not implemented.')

    if t[i+2]['token'] == 'var':
        valType = t[i+2]['name']
    elif t[i+2]['token'] == 'type':
        valType = t[i+2]['type']
    else:
        raise SyntaxError('Map val type tok {t[i]["token"} not implemented.')

    t[i] = {'token':'type', 'type':'map', 'keyType':keyType, 'valType':valType}

    del t[i+1] #beginBlock
    del t[i+1] #var or type
    return t

def keyVal(i, t):
    ''' KeyVal token is used to define map elements '''
    key = t[i]
    val = t[i+2]
    t[i] = {'token':'keyVal', 'key':key, 'val':val}
    del t[i+1] # beginBlock
    del t[i+1] # expr
    return t

def keyVals(i, t):
    ''' keyVal beginBlock keyVal '''
    keyVals = []
    for tok in [t[i], t[i+2]]:
        if tok['token'] == 'keyVals':
            keyVals += tok['keyVals']
        elif tok['token'] == 'keyVal':
            keyVals.append(tok)
    t[i] = {'token':'keyVals', 'keyVals':keyVals}
    del t[i+1] # beginBlock
    del t[i+1] # keyVal
    return t

def typeDeclaration(i, t):
    varType = []
    last = ''
    name = ''
    elementType = ''
    arraySize = ''
    keyType = ''
    valType = ''
    if t[i]['token'] in {'type', 'var'}:
        for n, tok in enumerate(t[i:]):
            if tok['token'] == 'type':
                if tok['type'] == 'array':
                    elementType = tok['elementType']
                    arraySize = tok['size']
                elif tok['type'] == 'map':
                    keyType = tok['keyType']
                    valType = tok['valType']
                else:
                    varType.append(tok['type'])
            elif tok['token'] == 'var' and not last == 'var':
                if not tok['type'] == 'unknown':
                    varType.append(tok['type'])
                name = tok['name']
                last = 'var'
            elif tok['token'] == 'var' and last == 'var':
                varType.append(name)
                name = tok['name']
                break
            elif not tok['token'] in {'type','var'}:
                # subtract to not consume the token
                n -= 1
                break
    if not name:
        raise SyntaxError('Type declaration error')
    t[i] = {'token':'var', 'name':name, 'type':' '.join(varType)} 
    if elementType:
        # It's an array, include size and elementType
        t[i]['type'] = 'array'
        t[i]['size'] = arraySize
        t[i]['elementType'] = elementType
    elif valType:
        # It's a map, include keyType and valType
        t[i]['type'] = 'map'
        t[i]['keyType'] = keyType
        t[i]['valType'] = valType
    for _ in range(n):
        del t[i+1] # type and var types
    return t

def floatNumber(i, t):
    ''' Check if it is a floatNumber token and
        Return a float number from the given tokenList
    '''
    try:
        if t[i+2]['token'] == 'dot':
            # Its a range token
            return 'continue'
    except IndexError:
        pass
    try:
        t[i] = {
            'token':'floatNumber',
            'type':'float',
            'value': f"{t[i]['value']}.{t[i+2]['value']}"}
        del t[i+1] #dot
    except:
        t[i] = {
            'token':'floatNumber',
            'type':'float',
            'value': f"{t[i]['value']}."}

    del t[i+1] #dot or decimal
    return t

def convertToExpr(token):
    if token['token'] in {'num', 'floatNumber'}:
        if token['token'] == 'num':
            varType = 'int'
        else:
            varType = 'float'
        return {'token':'expr', 'type':varType, 'args':[token], 'ops':[]}
    elif token['token'] in {'var','group','inputFunc', 'call', 'array', 'dotAccess', 'map'}:
        return {'token':'expr', 'type':token['type'], 'args':[token], 'ops':[]}
    else:
        raise SyntaxError(f'Cant convert token {token} to expr')

def expr(i, t):
    if t[i]['token'] == 'operator' and t[i-1]['token'] == 'rparen':
        # its part of an expression. Not ready to parse this yet.
        return 'continue'
    elif len(t[i:]) > 3 and t[i+1]['token'] == 'operator' and t[i+3]['token'] in {'lparen','lbracket'}:
        # The second argument is probly a function or indexAccess. Not ready to parse
        # this yet.
        return 'continue'
    elif t[i]['token'] == 'operator':
        # check if it's ready
        try:
            if t[i+2]['token'] in {'lparen','lbracket'}:
                # Second argument is probably a func or indexAccess. Not ready
                # to parse this yet.
                return 'continue'
        except IndexError:
            # it is the last element on the line, ready to proceed.
            pass
        try:
            if t[i-1]['token'] in {'rparen','rbracket'}:
                # First argument is probably a func or indexAccess. Not ready
                # to parse this yet
                return 'continue'
        except IndexError:
            # operator is the first token, it is a modifier. Proceed
            pass
        # Modifier operator
        t2 = t[i+1].copy()
        t2['args'][0]['modifier'] = t[i]['operator']
        t[i] = t2
        del t[i+1] # var or num
    elif len(t[i:]) > 1 and t[i+1]['token'] == 'operator' and t[i+2]['token'] in {'num','var','group','expr'}:
        args = []
        ops = []
        for token in t[i:i+3]:
            if token['token'] == 'expr':
                args = args + token['args']
                ops = ops + token['ops']
            elif token['token'] in {'floatNumber', 'num','var','group'}:
                args.append(token)
            elif token['token'] == 'operator':
                ops.append(token['operator'])
            else:
                raise SyntaxError(f'Expression of token {token["token"]} not implemented.')
        t[i] = {'token':'expr', 'type':'unknown', 'args':args, 'ops':ops}
        del t[i+1] # operator
        del t[i+1] # var or num
    elif t[i]['token'] in {'num', 'floatNumber', 'var', 'group', 'dotAccess'}:
        t[i] = convertToExpr(t[i])
    else:
        raise SyntaxError(f'Expression of token {t[i]["token"]} not implemented.')
    return t

def group(i, t):
    ''' Return a group token
    '''
    if t[i-1]['token'] in {'operator','returnStatement'} or 'symbol' in t[i-1]:
        # Its a group
        t[i] = {'token':'group', 'type':t[i+1]['type'], 'expr':t[i+1]}
        del t[i+1] # expr
        del t[i+1] # rparen
        return t
    else:
        # Its a call, redirect
        return 'continue'
        
def args(i, t):
    ''' Return an args token '''
    args = []
    try:
        if t[i+3]['token'] in {'equal', 'lparen'}:
            # Probably a kwargs token. Not ready to proceed.
            return 'continue'
    except IndexError:
        pass
    for tok in [t[i],t[i+2]]:
        if tok['token'] == 'args':
            args += tok['args']
        elif tok['token'] == 'expr':
            # Only valid for self.var
            if 'dotAccess' in tok['args'][0] and len(tok['args'][0]['dotAccess']) == 2:
                tok['attribute'] = True
            args.append(tok)
    t[i] = {'token':'args','args':args}
    del t[i+1] # comma
    del t[i+1] # arg or expr
    return t

def assign2kwarg(tok):
    if tok['target']['token'] == 'dotAccess':
        # Only valid for self.var
        if len(tok['target']['dotAccess']) == 2:
            tok['target'] = tok['target']['dotAccess'][1]
            tok['target']['attribute'] = True
        else:
            raise SyntaxError('Default class attribute initiation is only valid for immediate class attributes. Ex: self.a.b not valid, but self.a is valid.')
    return tok

def kwargs(i, t):
    ''' Return a kwargs token, if valid '''
    kwargs = []
    for tok in [t[i],t[i+2]]:
        if tok['token'] == 'kwargs':
            kwargs += tok['kwargs']
        elif tok['token'] == 'assign':
            kwargs.append(assign2kwarg(tok))
    t[i] = {'token':'kwargs','kwargs':kwargs}
    del t[i+1] # comma
    del t[i+1] # kwargs or assign
    return t

def call(i, t):
    ''' Return a call token if valid '''
    # Verify if it is a valid call
    if not t[i]['args'][0]['token'] in {'var','dotAccess'} or t[i-1]['token'] in {'defStatement','classStatement'}:
        # Not a valid call
        return 'continue'

    arguments = []
    kwargs = []
    if t[i+2]['token'] == 'rparen':
        pass
    elif t[i+2]['token'] == 'args':
        arguments = t[i+2]['args']
        del t[i+1] # args
    elif t[i+2]['token'] == 'expr':
        arguments = [t[i+2]]
        del t[i+1] # expr
    elif t[i+2]['token'] == 'assign':
        kwargs = [t[i+2]]
        del t[i+1] # assign
    elif t[i+2]['token'] == 'kwargs':
        kwargs = t[i+2]['kwargs']
        del t[i+1] # kwargs
    else:
        raise SyntaxError(f'Call with arg {t[i+2]} not supported')
    if t[i+2]['token'] == 'comma':
        if t[i+3]['token'] == 'assign':
            kwargs += [t[i+3]]
            del t[i+3] # assign
        elif t[i+3]['token'] == 'kwargs':
            kwargs += t[i+3]['kwargs']
            del t[i+3] # kwargs
        del t[i+2]

    if t[i]['args'][0]['token'] == 'dotAccess':
        t[i]['args'][0]['dotAccess'][-1] = {
            'token':'call',
            'type':t[i]['args'][0]['dotAccess'][-1]['type'],
            'name':t[i]['args'][0]['dotAccess'][-1],
            'args':arguments,
            'kwargs':kwargs,
        }
    else:
        if t[i]['args'][0]['name'] == 'print':
            tokenName = 'printFunc'
        else:
            tokenName = 'call'
        callToken = {
            'token':tokenName,
            'type':t[i]['args'][0]['type'],
            'name':t[i]['args'][0],
            'args':arguments,
            'kwargs':kwargs,
        }
        if tokenName != 'printFunc':
            t[i] = convertToExpr(callToken)
        else:
            t[i] = callToken
    del t[i+1] # rparen
    del t[i+1] # lparen
    return t

def inputFunc(i, t):
    ''' Return an inputFunc token
    '''
    if t[i+2]['token'] == 'rparen':
        t[i] = convertToExpr({'token':'inputFunc', 'type':'str'})
    elif t[i+2]['token'] == 'expr':
        t[i] = convertToExpr({'token':'inputFunc', 'type':'str', 'expr':t[i+2]})
        del t[i+1] # expr
    else:
        t[i] = convertToExpr({'token':'inputFunc', 'type':'str', 'expr':convertToExpr(t[i+2])})
        del t[i+1] # expr
    del t[i+1] # lparen
    del t[i+1] # rparen
    return t

def augAssign(i, t):
    ''' expr operator equal expr
    '''
    if t[i]['args'][0]['token'] in {'var','dotAccess'}:
        t[i] = {'token':'augAssign', 'target':t[i]['args'][0], 'operator': t[i+1]['operator'], 'expr':t[i+3]}
        del t[i+1] # operator
        del t[i+1] # equal
        del t[i+1] # expr
        return t
    # Not a valid assign, continue
    return 'continue'

def assign(i, t):
    ''' expr equal expr
    '''
    if len(t) > 4 and i == 1:
        # Not parsed the value of the assign yet.
        return 'continue'
    if len(t) > i+3 and t[i+2]['args'][0]['token'] in {'var', 'dotAccess'} and 'symbol' in t[i+3]:
        # Incomplete expression parsing
        if not t[i+3]['token'] == 'rparen':
            return 'continue'
        
    if t[i]['args'][0]['token'] in {'var', 'dotAccess'}:
        t[i] = {'token':'assign', 'target':t[i]['args'][0], 'expr':t[i+2]}
        del t[i+1] # equal
        del t[i+1] # expr
        return t
    # Not a valid assign, continue
    return 'continue'

def ifelif(i, t):
    ''' Create an if or elif token
    '''
    # Token will have a block field

    # Change token to if or elif
    t[i]['token'] = t[i]['token'].replace('Statement','')
    # Add expression
    t[i]['expr'] = t[i+1]

    del t[i+1] # expr
    del t[i+1] # beginBlock
    return t

def rangeExpr(i, t):
    ''' Return a range token '''

    token = {'token':'range', 'from':t[i]}
    if t[i+4]['token'] == 'dot' and t[i+5]['token'] == 'dot':
        token['step'] = t[i+3]
        token['to'] = t[i+6]
        del t[i+1] # dot
        del t[i+1] # dot
        del t[i+1] # step
    else:
        token['to'] = t[i+3]
    t[i] = token
    del t[i+1] # dot
    del t[i+1] # dot
    del t[i+1] # to
    return t

def forLoop(i, t):
    ''' Check if its a valid for token and return the token if it is '''
    #token will have a block field
    #TODO: include args for key val unpacking
    t[i]['token'] = 'for'
    if t[i+1]['token'] == 'expr':
        if t[i+1]['args'][0]['token'] == 'var':
            t[i]['vars'] = [t[i+1]['args'][0]]
        else:
            raise SyntaxError("Iteration variable cannot be {t[i+1]['args'][0]['token']}")
    elif t[i+1]['token'] == 'args':
        t[i]['vars'] = []
        for expr in t[i+1]['args']:
            if expr['args'][0]['token'] == 'var':
                t[i]['vars'].append(expr['args'][0])
            else:
                raise SyntaxError("Iteration variable cannot be {expr['args'][0]['token']}")
    t[i]['iterable'] = t[i+3]
    del t[i+1] # var
    del t[i+1] # in
    del t[i+1] # iterable
    del t[i+1] # beginBlock
    return t

def forTarget(i, t):
    ''' Check if its a valid for target token and return it if it is '''
    if not t[i+1]['args'][0]['token'] == 'var':
        # not valid for target
        raise SyntaxError("The token {t[i+1]['args'][0]['token']} is not a valid target token.")
    t[i]['token'] = 'forTarget'
    t[i]['target'] = t[i+1]['args'][0]['name']
    del t[i+1] # target
    del t[i+1] # beginBlock
    return t
    
def whileLoop(i, t):
    ''' Create a while token '''
    # token will have a block field

    t[i]['token'] = 'while'
    t[i]['expr'] = t[i+1]
    del t[i+1] # expr
    del t[i+1] # beginBlock
    return t

def function(i, t):
    ''' Check if its a function definition and return a function token if it is '''
    
    # token will have a block field

    if not t[i+1]['args'][0]['token'] == 'var':
        # Invalid function definition
        return 'continue'

    t[i]['token'] = 'func'
    t[i]['name'] = t[i+1]['args'][0]['name']
    t[i]['type'] = t[i+1]['args'][0]['type']
    t[i]['args'] = []
    t[i]['kwargs'] = []
    if t[i+3]['token'] == 'args':
        t[i]['args'] = t[i+3]['args']
        del t[i+1] # args
    elif t[i+3]['token'] == 'expr':
        t[i]['args'] = [t[i+3]]
        del t[i+1] # expr
    elif t[i+3]['token'] == 'assign':
        t[i]['kwargs'] = [assign2kwarg(t[i+3])]
        del t[i+1] # assign
    elif t[i+3]['token'] == 'kwargs':
        t[i]['kwargs'] = t[i+3]['kwargs']
        del t[i+1] # kwargs
    elif t[i+3]['token'] == 'rparen':
        # no args no kwargs, but valid definition
        pass
    else:
        raise SyntaxError(f'function arg with token {t[i+3]} not supported.')
    if t[i+3]['token'] == 'kwargs':
        t[i]['kwargs'] = t[i+3]['kwargs']
        del t[i+1] # kwargs
    del t[i+1] # var
    del t[i+1] # lparen
    del t[i+1] # rparen
    del t[i+1] # beginBlock
    return t

def funcReturn(i, t):
    ''' Return a return token '''
    if i == len(t)-1:
        t[i]['token'] = 'return'
        t[i]['type'] = 'void'
    else:
        t[i]['token'] = 'return'
        t[i]['type'] = t[i+1]['type'],
        t[i]['expr'] = t[i+1]
        del t[i+1] # expr
    return t

def imports(i, t):
    ''' Return an import token if valid '''

    t[i]['token'] = 'import'
    t[i]['expr'] = t[i+1]
    del t[i+1] # expr
    return t

def array(i, t):
    ''' Verify if its an array and return an array token if it is '''
    if t[i-1]['token'] in {'var','expr'}:
        # Its an index access
        return 'continue'
    # Its an array
    if t[i+1]['token'] == 'args':
        elements = t[i+1]['args']
        del t[i+1] # args
    elif t[i+1]['token'] == 'expr':
        elements = [t[i+1]]
        del t[i+1] # expr
    else:
        elements = []
    t[i] = convertToExpr({'token':'array','type':'array','elementType':'unknown',
        'len':len(elements), 'size':'unknown', 'elements':elements})
    del t[i+1] # rbracket
    return t

def hashmap(i, t):
    ''' Verify if its a valid hashmap and return a map token if it is '''
    elements = []
    if t[i+1]['token'] == 'keyVal':
        elements.append(t[i+1])  
        del t[i+1] # keyVal
    elif t[i+1]['token'] == 'keyVals':
        elements = t[i+1]['keyVals']
        del t[i+1] # keyVals
    t[i] = convertToExpr({'token':'map','type':'map','valType':'unknown','keyType':'unknown',
        'elements':elements})
    del t[i+1] # rbrace
    return t

def indexAccess(i, t):
    ''' Verify if its an indexAccess and return an indexAccess token
        if it is
    '''
    if not t[i]['args'][-1]['token'] in {'var','dotAccess'}:
        # Not a valid indexAccess
        return 'continue'
    if t[i]['args'][-1]['token'] == 'var':
        t[i]['args'][-1]['indexAccess'] = t[i+2]
    elif t[i]['args'][-1]['token'] == 'dotAccess':
        t[i]['args'][-1]['dotAccess'][-1]['indexAccess'] = t[i+2]
    del t[i+1] # lbracket
    del t[i+1] # expr
    del t[i+1] # rbracket
    return t

def classDefinition(i, t):
    ''' Return a class token '''
    # token will have a block field

    if not t[i+1]['args'][0]['token'] == 'var':
        # Invalid function definition
        return 'continue'

    t[i]['token'] = 'class'
    t[i]['name'] = t[i+1]['args'][0]['name']
    if t[i+3]['token'] == 'rparen':
        t[i]['args'] = []
    elif t[i+3]['token'] == 'args':
        t[i]['args'] = t[i+3]['args']
        del t[i+1] # expr or args
    elif t[i+3]['token'] == 'expr':
        t[i]['args'] = [t[i+3]]
        del t[i+1] # expr or args
    else:
        raise SyntaxError(f'Class arg with token {t[i+3]} not supported.')
    del t[i+1] # var
    del t[i+1] # lparen
    del t[i+1] # rparen
    del t[i+1] # beginBlock
    return t

def dotAccess(i, t):
    ''' Verify if its a dotAccess and return a dotAccess token
        if it is.
    '''
    varType = 'unknown'
    if t[i]['token'] == 'dot':
        if not t[i-1]['token'] in {'dot', 'var', 'dotAccess'}\
                and t[i+1]['args'][0]['token'] in {'var', 'dotAccess'}:
            # Its a self. shorthand notation
            names = [{'token':'var', 'type':'unknown', 'name':'self'}]
            t[i] = convertToExpr(names[0])
            secondToken = t[i+1]
        else:
            # not a valid shorthand for self.
            return 'continue'
    else:
        if t[i+1]['token'] == 'space':
            # First arg is the type and second is self. shorthand notation
            names = [{'token':'var', 'type':'unknown', 'name':'self'}]
            if t[i]['token'] == 'var':
                varType = t[i]['args'][0]['name']
            elif t[i]['token'] == 'type':
                varType = t[i]['type']
            else:
                raise SyntaxError('Type token {t[i]["token"]} not supported')
            t[i] = convertToExpr(names[0])
            secondToken = t[i+3]
            del t[i+1] # space

        if not t[i]['args'][-1]['token'] in {'var','dotAccess', 'type'}\
            or not t[i+2]['args'][0]['token'] in {'var', 'dotAccess'}:
            # Not a valid dotAccess
            return 'continue'

        if t[i]['args'][-1]['token'] == 'dotAccess':
            names = t[i]['args'][-1]['dotAccess']
        elif t[i]['args'][-1]['token'] == 'var':
            names = [t[i]['args'][-1]]

        secondToken = t[i+2]
        del t[i+1] # dot

    if secondToken['args'][0]['token'] == 'dotAccess':
        names += secondToken['args'][0]['dotAccess']
    elif secondToken['args'][0]['token'] == 'var':
        names += [secondToken['args'][0]]

    # Get the args and ops from the previous expr
    args = deepcopy(t[i]['args'])
    ops = deepcopy(t[i]['ops'])
    # The last arg is where the junction occurs and it must be converted to a dotAccess token
    args[-1] = {'token':'dotAccess', 'type':'unknown', 'dotAccess':names}
    # Now join the args from the other expr, removing the first because it was joined
    args = args + deepcopy(secondToken['args'][1:])
    ops = ops + deepcopy(secondToken['ops'])
    # Update the current expression token
    t[i]['args'] = args
    t[i]['ops'] = ops
    t[i]['type'] = varType
    t[i]['args'][0]['type'] = varType
    del t[i+1] # var or dotAccess
    return t

def delete(i, t):
    t[i] = {'token':'delete', 'expr':t[i+1]}
    del t[i+1]
    return t
