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
                return {'token':'expr','type':'bool','args': [{'type':'bool','value':value.lower()}], 'ops':[] }
            elif value == 'null':
                return {'token':'expr','type':'null','args': [{'type':'null','value':'null'}], 'ops':[] }
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
            t[n]['token'] = 'comment'
            return t[:n+1]

def operator(i, t):
    ''' Combine operators that are compatible '''

    op1 = t[i]['operator'] if 'operator' in t[i] else t[i]['symbol']
    op2 = t[i+1]['operator'] if 'operator' in t[i+1] else t[i]['symbol']
    op = op1 + op2
    if op in {'**', '==', '>=', '<=','<<','>>','!='}:
        t[i] = {'token':'operator','operator':op}
    elif op in {'+=','-=','*=','/='}:
        t[i] = {'token':'augEqual','symbol':op}
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
    for token in t[i+1:]:
        if token['token'] == stringQuote:
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
            s += token['symbol']
        elif token['token'] == 'type':
            s += token['type']
        else:
            tok = token['token']
            if 'Statement' in tok:
                s += tok.replace('Statement', '')
            else:
                s += tok
        n += 1

    t[i] = {
        'token':'expr',
        'args':[{'token':'str', 'type':'str','value':f'{quote}{s}{quote}'}],
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
    if t[i]['token'] == 'var':
        elementType = t[i]['name']
    elif t[i]['token'] == 'type':
        elementType = t[i]['type']
    else:
        raise SyntaxError('Array type tok {t[i]["token"} not implemented.')

    arrayLen = t[i+2]['value']

    t[i] = {'token':'type', 'type':'array', 'elementType':elementType, 'len':arrayLen}

    del t[i+1] #beginBlock
    del t[i+1] #num
    return t

def mapType(i, t):
    ''' 
    Return a type token according to signature.
    (var type) beginBlock (var type) -> map
    '''
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

def typeDeclaration(i, t):
    varType = []
    last = ''
    name = ''
    elementType = ''
    arrayLen = ''
    keyType = ''
    valType = ''
    if t[i]['token'] in {'type', 'var'}:
        for n, tok in enumerate(t[i:]):
            if tok['token'] == 'type':
                if tok['type'] == 'array':
                    elementType = tok['elementType']
                    arrayLen = tok['len']
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
    if arrayLen:
        # It's an array, include len and elementType
        t[i]['type'] = 'array'
        t[i]['len'] = arrayLen
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
    if t[i+2]['token'] == 'dot':
        # Its a range token
        return 'continue'
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
    elif token['token'] in {'var','group','inputFunc','call'}:
        return {'token':'expr', 'type':token['type'], 'args':[token], 'ops':[]}
    else:
        raise SyntaxError(f'Cant convert token {token} to expr')

def expr(i, t):
    if t[i]['token'] == 'operator':
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
            elif token['token'] in {'num','var','group'}:
                args.append(token)
            elif token['token'] == 'operator':
                ops.append(token['operator'])
            else:
                raise SyntaxError(f'Expression of token {token["token"]} not implemented.')
        t[i] = {'token':'expr', 'type':'unknown', 'args':args, 'ops':ops}
        del t[i+1] # operator
        del t[i+1] # var or num
    elif t[i]['token'] in {'num', 'floatNumber', 'var', 'group'}:
        t[i] = convertToExpr(t[i])
    else:
        raise SyntaxError(f'Expression of token {t[i]["token"]} not implemented.')
    return t

def group(i, t):
    ''' Return a group token
    '''
    if t[i-1]['token'] == 'operator' or 'symbol' in t[i-1]:
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
    t[i] = {'token':'args','args':[t[i], t[i+2]]}
    del t[i+1] # comma
    del t[i+1] # arg
    return t

def call(i, t):
    ''' Return a call token if valid '''
    # Verify if it is a valid call
    if not t[i]['args'][0]['token'] in {'var'} or t[i-1]['token'] == 'defStatement':
        # Not a valid call
        return 'continue'
    if t[i+2]['token'] == 'rparen':
        arguments = []
    elif t[i+2]['token'] == 'args':
        arguments = t[i+2]['args']
        del t[i+1] # args
    elif t[i+2]['token'] == 'expr':
        arguments = [t[i+2]]
        del t[i+1] # expr
    else:
        raise SyntaxError('Call with arg {t[i+2]} not supported')
    callToken = {
        'token':'call',
        'type':t[i]['args'][0]['type'],
        'name':t[i]['args'][0],
        'args':arguments,
        'kwargs':[],
    }
    t[i] = convertToExpr(callToken)
    del t[i+1] # rparen
    del t[i+1] # lparen
    return t

def printFunc(i, t):
    ''' Return a printFunc token
    '''
    if t[i+2]['token'] == 'expr':
        t[i] = {'token':'printFunc', 'expr':t[i+2]}
    else:
        t[i] = {'token':'printFunc', 'expr':convertToExpr(t[i+2])}
    del t[i+1] # lparen
    del t[i+1] # expr
    del t[i+1] # rparen
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

def assign(i, t):
    ''' expr equal expr
    '''
    if t[i]['args'][0]['token'] == 'var':
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
    if not t[i+1]['args'][0]['token'] == 'var':
        # not valid for loop
        return 'continue'
    t[i]['token'] = 'for'
    t[i]['vars'] = [t[i+1]['args'][0]]
    t[i]['iterable'] = t[i+3]
    del t[i+1] # var
    del t[i+1] # in
    del t[i+1] # iterable
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
    if t[i+3]['token'] == 'rparen':
        t[i]['args'] = []
    elif t[i+3]['token'] == 'args':
        t[i]['args'] = t[i+3]['args']
        del t[i+1] # expr or args
    elif t[i+3]['token'] == 'expr':
        t[i]['args'] = [t[i+3]]
        del t[i+1] # expr or args
    else:
        raise SyntaxError(f'function arg with token {t[i+3]} not supported.')
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
    return t

