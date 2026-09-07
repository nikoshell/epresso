" ftplugin/epresso.vim
" File-type settings for epresso (.ep) files.
if exists("b:did_ftplugin")
  finish
endif
let b:did_ftplugin = 1

" The frontmatter is Python, the body is Jinja; pick Python's marker for
" `gcc`/comment ops (most comments target the logic block).
setlocal commentstring=#\ %s

" Sane editing options for a code file.
setlocal expandtab
setlocal softtabstop=4
setlocal shiftwidth=4

let b:undo_ftplugin = "setlocal commentstring< expandtab< softtabstop< shiftwidth<"
