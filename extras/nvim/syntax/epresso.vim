" Vim syntax file
" Language:     epresso (.ep) — Python frontmatter + Jinja2/HTML body
" Maintainer:   epresso
" Home:         extras/nvim/syntax/epresso.vim in the epresso repository
"
" A .ep file is:
"   ---                                <- Python frontmatter (route logic, Props,
"   from pydantic import BaseModel         helpers) delimited by --- ... ---
"   class Props(BaseModel): ...
"   ---                                <- end frontmatter
"   {% extends "layouts/base.ep" %}
"   <div class="x">{{ props.title }}</div>
"   <style>.x { color: red; }</style>  <- CSS inside <style>
"   <script>console.log(1)</script>    <- JS  inside <script>
"
" Highlighting:
"   * frontmatter -> Python (the --- ... --- region contains @epressoPython only,
"                    so HTML/Jinja below do not leak into it)
"   * body        -> HTML, loaded top-level via html.vim which already includes
"                    css.vim (for <style>) and javascript.vim (for <script>),
"                    plus Jinja for template tags/expressions.

if exists("b:current_syntax")
  finish
endif

let s:save_cpo = &cpo
set cpo&vim

" 1) Python into a cluster (used for the frontmatter block).
syn include @epressoPython syntax/python.vim
unlet b:current_syntax

" 2) HTML top-level — brings CSS and JavaScript for <style>/<script>.
"    Loaded with :runtime! (not :syn include) so html.vim's internal regions
"    (javaScript/cssStyle) keep working exactly as with :set ft=html.
runtime! syntax/html.vim
unlet b:current_syntax

" 3) Jinja top-level — template tags/expressions ({% %}, {{ }}, {# #}).
runtime! syntax/jinja.vim
unlet b:current_syntax

" Frontmatter: --- ... ---. contains=@epressoPython only, so HTML/Jinja top-level
" items do not match inside it; the --- delimiters get a subdued color.
syn region epressoFrontmatter
      \ start=/\m\%^---$/
      \ end=/\m^---$/
      \ matchgroup=epressoFrontmatterDelim
      \ contains=@epressoPython
      \ keepend

hi def link epressoFrontmatterDelim Comment

let b:current_syntax = "epresso"

let &cpo = s:save_cpo
