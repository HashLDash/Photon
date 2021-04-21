" Wlang syntax highlight for Vim - Version 0.1
" Author: Will - HashLDash

" Quit when a syntax file was already loaded.
if exists('b:current_syntax') | finish|  endif

syntax match wVar   "\k\+"
syntax match wNumber "\v<\d+>"
syntax match wNumber "\v<\d+\.\d+>"
syntax match wNumber "\v<\d*\.?\d+([Ee]-?)?\d+>"
syntax match wNumber "\v<0x\x+([Pp]-?)?\x+>"
syntax match wNumber "\v<0b[01]+>"
syntax match wNumber "\v<0o\o+>"
syntax match wNumber " *True"
syntax match wNumber " *False"
syntax match wNumber " *null"
syntax region wString start=/\v"/ skip=/\v(\\[\\"]){-1}/ end=/\v"/
syntax region wString start=/\v'/ end=/\v'/
syntax match wComment " *#.*$"
syntax match wFuncName "\v[[:alpha:]_.]+\ze(\s?\()"
syntax keyword wStatement class def cdef if elif else for in return not while and break continue
syntax match wBuiltinFunc "\v(len|print|time|collidedRecs|collidedPointRec|uniform|randInt|choose|post|chop|exitApp|localSetItem|localGetItem|localClear|abs|decimal|pass)+\ze(\s?\()"
syntax keyword wBuiltinFunc import
syntax keyword wTypes str cstr int float func struct const char double
syntax keyword wPlatforms android, html5, linux

hi def link wVar ModeMsg
hi def link wNumber Number
hi def link wString String
hi def link wStatement Statement
hi wComment ctermfg=DarkGray
hi def link wBuiltinFunc Include
hi def link wFuncName Function
hi def link wTypes Type
hi def link wPlatforms Type

let b:current_syntax = 'w'
