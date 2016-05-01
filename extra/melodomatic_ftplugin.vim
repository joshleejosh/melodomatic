" Vim filetype plugin file
" Language: Melodomatic

if exists ("b:did_ftplugin")
   finish
endif
let b:did_ftplugin = 1

setlocal comments=:# commentstring=#\ %s formatoptions-=t formatoptions+=croql
setlocal et ai ts=8 sw=0

