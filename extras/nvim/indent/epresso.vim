" indent/epresso.vim
" Indent epresso (.ep) files like Python (the frontmatter dominates the
" indentation structure; Jinja blocks align to their enclosing Python).
if exists("b:did_indent")
  finish
endif

" Provide GetPythonIndent().
runtime! indent/python.vim

let b:did_indent = 1

setlocal indentexpr=GetEpressoIndent()
setlocal indentkeys=o,O,*<Return>,:,:!,\#,*),0),#,=elif,=else,=except,=finally

function! GetEpressoIndent()
  if exists('*GetPythonIndent')
    return GetPythonIndent()
  endif
  return -1
endfunction

let b:undo_indent = "setlocal indentexpr< indentkeys<"
