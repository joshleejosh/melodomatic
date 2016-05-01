" Vim syntax file
" Language:	Melodomatic

" Quit when a syntax file was already loaded
"if exists("b:current_syntax")
"  finish
"endif

" Get this mostly for comments
"runtime! syntax/conf.vim

syn match	MelodomaticComment	     "^#.*"
syn match	MelodomaticComment	     "\s#.*"ms=s+1
syn match MelodomaticPreprocessing "\!\S\+.*$"
syn match MelodomaticDirective     "\:\S\+"
syn match MelodomaticCommand       "\.\S\+"
syn match MelodomaticMacro         "@\S\+"
syn match MelodomaticGenerator     "\$\S\+"

hi def link MelodomaticComment       Comment
hi def link MelodomaticDirective     Keyword
hi def link MelodomaticCommand       Statement
hi def link MelodomaticMacro         PreProc
hi def link MelodomaticGenerator     Type
hi def link MelodomaticPreprocessing PreProc

let b:current_syntax="melodomatic"

