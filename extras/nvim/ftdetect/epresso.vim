" ftdetect/epresso.vim
" Detect .ep files (Python frontmatter + Jinja2 body) as filetype 'epresso'.
autocmd BufRead,BufNewFile *.ep setfiletype epresso
