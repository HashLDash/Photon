# Install all dependencies for running projects with the
# corresponding language on the target platform

solver = {
    ('c', 'win32'): resolveCWin32,
    ('d', 'win32'): resolveDWin32
    ('haxe', 'win32'): resolveHaxeWin32
    ('js', 'win32'): resolveJsWin32
    ('dart', 'win32'): resolveDartWin32
}

def haveDependencies(lang, platform):
    ''' Return True if all dependencies are installed
        for the corresponding lang and platform or
        False otherwise. '''
    raise NotImplemented

def resolveDependencies(lang, platform):
    ''' Run the corresponding dependency solver '''
    solver[(lang, platform)]()
    #TODO: Check if the installation was successful
    # or print the error message and terminate the program

def resolveCWin32():
    ''' Install gcc '''
    pass

def resolveDWin32():
    ''' Install dmd '''
    pass

def resolveHaxeWin32():
    ''' Install haxe '''
    pass

def resolveJsWin32():
    ''' Install nodejs '''
    pass

def resolveDartWin32():
    ''' Install dart '''
    pass
