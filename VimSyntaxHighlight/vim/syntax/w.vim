" Wlang syntax highlight for Vim - Version 0.1
" Author: Will - HashLDash

set termguicolors

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
syntax keyword wStatement class def cdef if elif else for in return not while and or break continue del
syntax match wBuiltinFunc "\v(len|print|time|open|collidedRecs|collidedPointRec|uniform|randInt|choose|post|chop|exitApp|localSetItem|localGetItem|localClear|abs|decimal|pass)+\ze(\s?\()"
syntax keyword wBuiltinFunc native import from
syntax keyword wTypes str cstr int float func struct const char double
syntax keyword wPlatforms android Android HTML5 html5 linux Linux Web C c Python python Py py JS js JavaScript

hi def link wVar ModeMsg
hi def link wString String
hi wNumber ctermfg=Magenta guifg=#FFAAFF cterm=bold
hi wComment ctermfg=DarkGray
hi wFuncName ctermfg=Cyan guifg=#33BBCC cterm=bold
hi wStatement ctermfg=Yellow guifg=#FFFF77 cterm=bold
hi wTypes ctermfg=Blue guifg=#8888FF cterm=bold
hi wBuiltinFunc ctermfg=Blue guifg=#4466FF cterm=bold
hi def link wPlatforms Type

let b:current_syntax = 'w'
