# ruff: noqa: E501
"""Dev-toolbar — a floating overlay injected by the development server.

Only ``epresso dev`` injects it (never ``epresso build`` output). It offers app
buttons in a bottom/top bar: inspect (hover/click an element to see its component
source), routes & collections, a page **audit** (a11y/quality checks), a project
menu with debug info, and settings (persisted in localStorage). The bar also
shows toasts for dev-server rebuild/error events. Controlled by ``[dev.toolbar]``
in ``site.toml``.
"""

from __future__ import annotations

import json
from html import escape as h
from pathlib import Path

_PANEL_ROUTES = 400  # cap routes shown in the panel

_TEMPLATE = r"""<div id="__epresso_toolbar" style="@TBSTYLE@" data-placement="@PLACEMENT@">
<style>
#__epresso_toolbar{font:12px/1.5 system-ui,sans-serif;background:#0f1117;color:#e8ecf1;z-index:9999}
#__epresso_toolbar *{box-sizing:border-box}
#__epresso_toolbar .tb-inner{display:flex;gap:10px;align-items:center;padding:5px 12px;flex-wrap:wrap}
#__epresso_toolbar code{background:#262a33;padding:1px 5px;border-radius:4px;color:#9fd6ff}
#__epresso_toolbar a{color:#9fd6ff}
#__epresso_toolbar .tb-label{opacity:.55;text-transform:uppercase;letter-spacing:.06em;font-size:10px}
#__epresso_toolbar .tb-btn{background:#262a33;color:#e8ecf1;border:1px solid #3a4150;border-radius:5px;padding:2px 8px;cursor:pointer;font:inherit;position:relative}
#__epresso_toolbar .tb-btn:hover{background:#343b49}
#__epresso_toolbar .tb-btn.tb-icon{display:inline-flex;align-items:center;justify-content:center;padding:2px 6px;line-height:0}
#__epresso_toolbar .tb-btn.tb-icon svg{width:13px;height:13px;display:block}
#__epresso_toolbar .tb-right{margin-left:auto;display:flex;align-items:center;gap:10px}
#__epresso_toolbar .tb-btn.on{background:#1457a6;border-color:#3d8fe0}
#__epresso_toolbar .tb-btn a{color:inherit}
#__epresso_toolbar a.tb-btn{color:inherit;text-decoration:none}
#__epresso_toolbar .tb-badge{position:absolute;top:-5px;right:-5px;min-width:15px;height:15px;border-radius:8px;background:#e5534b;color:#fff;font-size:10px;line-height:15px;text-align:center;padding:0 3px;display:none}
#__epresso_toolbar .tb-panels{display:none;border-top:1px solid #2a2f3a;padding:10px 16px;max-height:52vh;overflow:auto;background:#0c0e12}
#__epresso_toolbar.open .tb-panels{display:block}
#__epresso_toolbar .tb-panels section{display:none}
#__epresso_toolbar .tb-panels section.active{display:block}
#__epresso_toolbar ul{margin:0;columns:3;column-gap:24px;list-style:none;padding:0}
#__epresso_toolbar li{break-inside:avoid;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#__epresso_toolbar h4{margin:0 0 4px 0;font-size:10px;opacity:.5;text-transform:uppercase;letter-spacing:.06em}
#__epresso_toolbar .tb-audit{margin:0;padding:0;list-style:none;columns:1}
#__epresso_toolbar .tb-audit li{margin:2px 0;cursor:pointer;color:#e8ecf1}
#__epresso_toolbar .tb-audit li.warn::before{content:"\26a0";color:#f0b429;margin-right:6px}
#__epresso_toolbar .tb-audit li.ok::before{content:"\2713";color:#7ee787;margin-right:6px}
#__epresso_toolbar .tb-cs{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr);gap:10px}
#__epresso_toolbar .tb-cs-left,#__epresso_toolbar .tb-cs-right{min-height:0;overflow:auto}
#__epresso_toolbar .tb-cs ul{margin:0;padding:0 0 0 4px;list-style:none}
#__epresso_toolbar .tb-cs summary{cursor:pointer}
#__epresso_toolbar .tb-cs .tb-coll{margin:4px 0}
#__epresso_toolbar .tb-cs .tb-centry{display:block;width:100%;text-align:left;background:none;border:none;color:#e8ecf1;font:12px/1.5 monospace;padding:2px 4px;border-radius:4px;cursor:pointer}
#__epresso_toolbar .tb-cs .tb-centry:hover,#__epresso_toolbar .tb-cs .tb-centry.active{background:#262a33}
#__epresso_toolbar .tb-cs .tb-centry.active{color:#7ee787}
#__epresso_toolbar .tb-cview h4{margin:0 0 4px 0;font-size:10px;opacity:.5;text-transform:uppercase;letter-spacing:.06em}
#__epresso_toolbar .tb-cview pre{background:#161a22;padding:6px;border-radius:4px;overflow:auto;white-space:pre-wrap;margin:0 0 8px}
#__epresso_toolbar .tb-hint{opacity:.5}
#__epresso_toolbar .tb-debug pre{background:#161a22;padding:8px;border-radius:6px;white-space:pre-wrap;max-width:100%}
#__epresso_toolbar .tb-field{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:4px 0;max-width:32rem}
#__epresso_toolbar kbd{font:inherit;font-size:11px;border:1px solid currentColor;border-radius:3px;padding:0 3px;opacity:.7}
#__epresso_toolbar .tb-toast{position:fixed;top:12px;right:12px;background:#0f1117;border:1px solid #3a4150;border-left:3px solid #7ee787;color:#e8ecf1;border-radius:6px;padding:7px 11px;display:none;max-width:70vw;z-index:10000}
#__epresso_toolbar .tb-toast.err{border-left-color:#e5534b}
#__epresso_toolbar .tb-toast.tb-toast-layout{align-items:center;flex-wrap:wrap;gap:2px;border-left-color:#9fd6ff}
#__epresso_toolbar .tb-lcrumb{background:none;border:0;color:#9fd6ff;font:inherit;cursor:pointer;padding:2px 3px}
#__epresso_toolbar .tb-lcrumb:hover{text-decoration:underline}
#__epresso_toolbar .tb-lsep{opacity:.5}
#__epresso_toolbar .tb-lc-edit{background:none;border:0;color:inherit;opacity:.8;cursor:pointer;padding:2px;display:inline-flex;align-items:center}
#__epresso_toolbar .tb-lc-edit svg{width:11px;height:11px;display:block}
#__epresso_toolbar .tb-lc-edit:hover{opacity:1;color:#7ee787}
#__epresso_tb_status{position:fixed;right:14px;bottom:44px;background:#0f1117;border-radius:999px;padding:4px 11px;font:600 10px/1 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.07em;border:1px solid;z-index:10001;box-shadow:0 2px 8px rgba(0,0,0,.45)}
#__epresso_tb_status.tb-draft{color:#7a5a00;background:#f7d469;border-color:#e3b93e}
#__epresso_tb_status.tb-private{color:#e8ecf1;background:#565b66;border-color:#6a6f7a}
#__epresso_toolbar .tb-env{display:inline-flex;align-items:center;gap:6px;text-transform:uppercase;letter-spacing:.06em;font-size:10px;opacity:.95}
#__epresso_toolbar .tb-env .tb-dot{width:0.55rem;height:0.55rem;border-radius:50%}
#__epresso_toolbar .tb-dot.tb-dot-dev{background:#a78bfa}
#__epresso_toolbar .tb-dot.tb-dot-preview{background:#ff922b}
#__epresso_toolbar .tb-dot.tb-dot-prod{background:var(--accent,#8b949e)}
#__epresso_toolbar [hidden]{display:none !important}
#__epresso_toolbar .tb-pop{position:fixed;left:50%;transform:translateX(-50%);@POPPOS@;display:flex;align-items:center;gap:8px;background:#0f1117;color:#e8ecf1;border:1px solid #3a4150;border-radius:6px;padding:5px 8px;font:12px/1.5 system-ui,sans-serif;max-width:70vw}
#__epresso_toolbar .tb-pop .tb-info{min-width:0}
#__epresso_toolbar .tb-pop .tb-open{color:inherit;background:none;border:none;cursor:pointer;padding:2px;display:inline-flex;align-items:center;margin-left:auto}
#__epresso_toolbar .tb-pop .tb-open svg,#__epresso_toolbar .tb-pop .tb-closebtn svg{width:13px;height:13px}
#__epresso_toolbar .tb-pop .tb-closebtn{background:none;border:none;color:inherit;cursor:pointer;padding:2px;display:inline-flex;align-items:center}
#__epresso_toolbar .tb-pop .tb-comp{color:#7ee787}
body.ep-inspect{cursor:crosshair}
.ep-inspect-link{outline:2px solid #4cc2ff !important;outline-offset:1px}
.ep-audit-hit{outline:2px dashed #f0b429 !important;outline-offset:1px}
#__epresso_tb_layout{position:fixed;inset:0;z-index:9998;pointer-events:none;font:12px/1.4 system-ui,sans-serif}
.tb-lbox{box-sizing:border-box;pointer-events:auto;cursor:pointer}
.tb-lbox:hover{outline:2px solid #fff}
.tb-lbox-bg{cursor:default}
.tb-lbox-bg:hover{outline:none}
#__epresso_toolbar .tb-pcomp,#__epresso_toolbar .tb-pcontent{display:block;width:100%;text-align:left;background:none;border:none;color:#e8ecf1;font:12px/1.6 monospace;padding:2px 4px;border-radius:4px;cursor:pointer}
#__epresso_toolbar .tb-pcomp:hover,#__epresso_toolbar .tb-pcontent:hover{background:#262a33}
#__epresso_toolbar .tb-pcomp.on,#__epresso_toolbar .tb-pcontent.on{color:#7ee787}
.tb-comp-highlight{outline:2px solid #7ee787 !important;outline-offset:2px}
/* normal-flow spacer at the document end; JS only ever grows it (never below) */
#__epresso_tb_space{height:64px}
html{scroll-padding-bottom:64px}
</style>
<div class="tb-inner">
  <span class="tb-env" title="Build environment"><span class="tb-dot @ENVDOT@"></span> @ENV@</span>
  <button class="tb-btn tb-icon" id="__epresso_tb_theme" aria-pressed="false" title="Colour scheme: system" aria-label="Emulate colour scheme"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M1.75 2.5A1.75 1.75 0 0 0 0 4.25v5.5c0 .966.784 1.75 1.75 1.75h4.5v1.5H4a.75.75 0 0 0 0 1.5h8a.75.75 0 0 0 0-1.5h-2.25v-1.5h4.5A1.75 1.75 0 0 0 16 9.75v-5.5A1.75 1.75 0 0 0 14.25 2.5H1.75Zm0 1.5h12.5a.25.25 0 0 1 .25.25v5.5a.25.25 0 0 1-.25.25H1.75a.25.25 0 0 1-.25-.25v-5.5a.25.25 0 0 1 .25-.25Z"/></svg></button>
  <button class="tb-btn tb-icon" data-app="inspect" title="Inspect elements (Shift+Alt+I)" aria-label="Inspect elements"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5.5 1.5c-.41 0-.75.34-.75.75v11.35c0 .9 1.09 1.35 1.72.71l2.78-2.86 1.59 4.09c.14.36.55.53.91.38l.24-.09c.33-.13.51-.49.38-.82L12 11.5h3.48c.9 0 1.35-1.09.72-1.72l-9.23-8.79C6.52 1.56 6.02 1.5 5.5 1.5Z"/></svg></button>
  <button class="tb-btn tb-icon" data-app="layout" title="Component layout (Shift+Alt+L)" aria-label="Component layout"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="1.25" y="1.25" width="13.5" height="13.5" rx="1.5"/><path d="M1.25 6.25h13.5M6.25 6.25v8.5"/></svg></button>
  <button class="tb-btn" data-app="routes">routes</button>
  <button class="tb-btn" data-app="content" title="Explore content">content</button>
  <button class="tb-btn" data-app="page" title="Content this page depends on">page</button>
  <button class="tb-btn" data-app="audit" title="Run checks">audit<span class="tb-badge" data-audit-badge></span></button>
  <button class="tb-btn" data-app="project" title="Project info">project</button>
  <button class="tb-btn" data-app="settings" title="Settings">settings</button>
  <span class="tb-right">
    <code>@FILE@</code>
    @EDITOR@
    <button class="tb-btn tb-icon" data-tb-dismiss title="Hide toolbar (Shift+Alt+D)" aria-label="Hide toolbar"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"/></svg></button>
  </span>
</div>
<div class="tb-panels">
  <section data-panel="routes"><h4>Routes</h4><ul>@ROUTES@</ul></section>
  <section data-panel="content">
    <div class="tb-cs">
      <div class="tb-cs-left">@CLEFT@</div>
      <div class="tb-cs-right"><div class="tb-cview" id="__epresso_tb_cview"><p class="tb-hint">pick an entry</p></div></div>
    </div>
  </section>
  <section data-panel="page"><h4>Content on this page</h4>@PAGEDEPS@<h4>Components on this page</h4><div id="__epresso_tb_pcomps"></div></section>
  <section data-panel="audit"><ul class="tb-audit" data-audit-list></ul></section>
  <section data-panel="project"><h4>epresso @VERSION@</h4><p>@DESC@</p><p><button class="tb-btn" data-copy-debug>copy debug info</button> @LINKS@</p><h4>Debug info</h4><div class="tb-debug"><pre>@DEBUG@</pre></div></section>
  <section data-panel="settings">
    <div class="tb-field"><span>shortcuts</span><span class="tb-hint"><kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>D</kbd> toolbar · <kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>I</kbd> inspect · <kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>L</kbd> layout</span></div>
    <div class="tb-field"><span>placement</span><select data-opt="placement"><option value="bottom">bottom</option><option value="top">top</option></select></div>
    <div class="tb-field"><span>editor</span><select data-opt="editor"><option value="vscode">vscode</option><option value="nvim">nvim</option></select></div>
    <div class="tb-field"><label><input type="checkbox" data-opt="notify"> notifications</label></div>
    <div class="tb-field"><label><input type="checkbox" data-opt="verbose"> verbose logging</label></div>
    <div class="tb-field"><button class="tb-btn" data-save>save</button><button class="tb-btn" data-tb-dismiss>close</button></div>
  </section>
</div>
<div class="tb-toast" id="__epresso_tb_toast"></div>
<div class="tb-pop" id="__epresso_tb_pop" hidden>
  <span id="__epresso_tb_info" class="tb-info"></span>
  <button type="button" id="__epresso_tb_open" class="tb-open tb-editor" title="Open source in editor" aria-label="Open source in editor"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M11.013 1.427a1.75 1.75 0 0 1 2.474 0l1.086 1.086a1.75 1.75 0 0 1 0 2.474l-8.61 8.61c-.21.21-.47.364-.756.445a6.03 6.03 0 0 1-1.68.441l-1.026.146a.75.75 0 0 1-.863-.863l.146-1.026c.055-.34.207-.677.441-1.68a1.75 1.75 0 0 1 .445-.755l8.61-8.61Z"/></svg></button>
  <button id="__epresso_tb_close" class="tb-closebtn" title="Close" aria-label="Close"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"/></svg></button>
</div>
<script>
(function(){
  var tb=document.getElementById('__epresso_toolbar');if(!tb)return;
  var map=@SCOPE_MAP@;var mode=false,last=null;var pageFile=@PAGE@;var layoutMode=false;
  var pop=document.getElementById('__epresso_tb_pop');
  var toast=document.getElementById('__epresso_tb_toast');
  var panels=document.querySelector('.tb-panels');
  var btns=tb.querySelectorAll('[data-app]');
  var dismiss=tb.querySelector('[data-tb-dismiss]');
  var url=(location.protocol==='https:'?'wss://':'ws://')+location.host+'/__epresso_reload';
  var prefs=loadPrefs();
  function loadPrefs(){try{return JSON.parse(localStorage.getItem('epresso-toolbar')||'{}')||{};}catch(e){return {};}}
  function savePrefs(){try{localStorage.setItem('epresso-toolbar',JSON.stringify(prefs));}catch(e){}}
  function vlog(){ if(prefs.verbose&&window.console&&console.debug){console.debug.apply(console,arguments);} }
  // --- app switching (non-inspect apps open a panel) ---
  function inspBtn(){for(var i=0;i<btns.length;i++){if(btns[i].getAttribute('data-app')==='inspect')return btns[i];}return null;}
  function layoutBtn(){for(var i=0;i<btns.length;i++){if(btns[i].getAttribute('data-app')==='layout')return btns[i];}return null;}
  function open(app){
    deactivateInspect();               // opening a panel exits inspect mode
    deactivateLayout();                // ...and the layout view
    if(pop){pop.hidden=true;clearOutline();}
    tb.classList.add('open');
    try{sessionStorage.setItem('__epresso_app',app);}catch(e){}
    btns.forEach(function(b){if(b===inspBtn()||b===layoutBtn())return;b.classList.toggle('on',b.getAttribute('data-app')===app);});
    Array.prototype.forEach.call(panels.querySelectorAll('section'),function(s){s.classList.toggle('active',s.getAttribute('data-panel')===app);});
    if(app==='audit')runAudit();
    if(app==='settings')loadSettingsUI();
    positionStatus();
    fitBodyPad();   // reserve space for the (taller) open panel
  }
  function close(){tb.classList.remove('open');try{sessionStorage.removeItem('__epresso_app');}catch(e){}btns.forEach(function(b){if(b===inspBtn()||b===layoutBtn())return;b.classList.remove('on');});positionStatus();fitBodyPad();}
  function deactivateInspect(){
    mode=false;var ib=inspBtn();if(ib)ib.classList.remove('on');
    document.body.classList.remove('ep-inspect');
  }
  function toggleInspect(){
    var ib=inspBtn();
    if(mode){deactivateInspect();}
    else{mode=true;document.body.classList.add('ep-inspect');if(ib)ib.classList.add('on');close();deactivateLayout();}
  }
  btns.forEach(function(b){b.onclick=function(){
    var app=b.getAttribute('data-app');
    if(app==='inspect'){toggleInspect();return;}
    if(app==='layout'){toggleLayout();return;}
    if(tb.classList.contains('open')&&b.classList.contains('on')){close();}
    else{open(app);}
  };});
  if(dismiss)dismiss.onclick=function(){tb.style.display='none';fitBodyPad();};
  function toggleToolbar(){
    if(tb.style.display==='none'){tb.style.display='';}
    else{tb.style.display='none';close();deactivateInspect();if(pop)pop.hidden=true;clearOutline();}
    positionStatus();fitBodyPad();
  }
  /* Keyboard shortcuts — this toolbar only exists in development builds, so
     they are dev-only by construction. Shift+Alt rather than Ctrl+Shift to
     stay clear of browser-reserved combos (Ctrl+Shift+D/I). Matched on e.code
     so it works on non-QWERTY layouts too. */
  (function(){
    var keys={KeyD:toggleToolbar,KeyI:toggleInspect,KeyL:toggleLayout};
    document.addEventListener('keydown',function(e){
      if(!e.shiftKey||!e.altKey||e.ctrlKey||e.metaKey)return;
      var fn=keys[e.code];if(!fn)return;
      var t=e.target;
      if(t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.tagName==='SELECT'||t.isContentEditable))return;
      e.preventDefault();
      fn();
    },true);
  })();
  // --- colour-scheme emulation (dev only: the site follows the OS) ---
  // Cycles system -> dark -> light, remembered in the toolbar prefs. Setting
  // data-theme on <html> pins color-scheme, so every light-dark() on the page —
  // design tokens and code palette alike — follows. "system" removes it.
  var themeBtn=document.getElementById('__epresso_tb_theme');
  var THEME_MODES=['system','dark','light'];
  var THEME_ICONS={system:'<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M1.75 2.5A1.75 1.75 0 0 0 0 4.25v5.5c0 .966.784 1.75 1.75 1.75h4.5v1.5H4a.75.75 0 0 0 0 1.5h8a.75.75 0 0 0 0-1.5h-2.25v-1.5h4.5A1.75 1.75 0 0 0 16 9.75v-5.5A1.75 1.75 0 0 0 14.25 2.5H1.75Zm0 1.5h12.5a.25.25 0 0 1 .25.25v5.5a.25.25 0 0 1-.25.25H1.75a.25.25 0 0 1-.25-.25v-5.5a.25.25 0 0 1 .25-.25Z"/></svg>',dark:'<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M9.598 1.591a.749.749 0 0 1 .785-.175 7.001 7.001 0 1 1-8.967 8.967.75.75 0 0 1 .961-.96 5.5 5.5 0 0 0 7.046-7.046.75.75 0 0 1 .175-.786Zm1.616 1.945a7 7 0 0 1-7.678 7.678 5.499 5.499 0 1 0 7.678-7.678Z"/></svg>',light:'<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 12a4 4 0 1 1 0-8 4 4 0 0 1 0 8Zm0-1.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Zm5.657-8.157a.75.75 0 0 1 0 1.061l-1.061 1.06a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734l1.06-1.06a.75.75 0 0 1 1.06 0Zm-9.193 9.193a.75.75 0 0 1 0 1.06l-1.06 1.061a.75.75 0 1 1-1.061-1.06l1.06-1.061a.75.75 0 0 1 1.061 0ZM8 0a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0V.75A.75.75 0 0 1 8 0ZM3 8a.75.75 0 0 1-.75.75H.75a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 3 8Zm13 0a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 16 8Zm-8 5a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 8 13Zm3.536-1.464a.75.75 0 0 1 1.06 0l1.061 1.06a.75.75 0 0 1-1.06 1.061l-1.061-1.06a.75.75 0 0 1 0-1.061ZM2.343 2.343a.75.75 0 0 1 1.061 0l1.06 1.061a.751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018l-1.06-1.06a.75.75 0 0 1 0-1.06Z"/></svg>'};
  function themeMode(){return THEME_MODES.indexOf(prefs.theme)>0?prefs.theme:'system';}
  function applyThemeMode(){
    var mode=themeMode();
    var root=document.documentElement;
    if(mode==='system')root.removeAttribute('data-theme');
    else root.setAttribute('data-theme',mode);
    if(themeBtn){
      themeBtn.innerHTML=THEME_ICONS[mode];
      themeBtn.title='Colour scheme: '+mode;
      themeBtn.setAttribute('aria-label','Emulate colour scheme (now '+mode+')');
      themeBtn.setAttribute('aria-pressed',mode==='system'?'false':'true');
    }
    vlog('theme mode',mode);
  }
  if(themeBtn){
    themeBtn.onclick=function(){
      prefs.theme=THEME_MODES[(THEME_MODES.indexOf(themeMode())+1)%THEME_MODES.length];
      savePrefs();
      applyThemeMode();
      toastMsg('colour scheme: '+prefs.theme);
    };
    applyThemeMode();
  }
  var editorSchemes={vscode:'vscode://file/',nvim:'nvim://file/'};
  function openEditor(file){var sc=editorSchemes[prefs.editor]||editorSchemes.vscode;if(file)location.href=sc+file;}
  document.addEventListener('click',function(e){var a=e.target&&e.target.closest?e.target.closest('.tb-editor'):null;if(a&&!e.defaultPrevented){e.preventDefault();openEditor(a.getAttribute('data-file'));}},true);
  function positionStatus(){var el=document.getElementById('__epresso_tb_status');if(!el)return;if(tb.style.display==='none'){el.style.bottom='12px';return;}var t=tb.getBoundingClientRect().top;var b=(window.innerHeight-t)+8;el.style.bottom=(b>8?b:8)+'px';}
  if(document.readyState!=='loading'){positionStatus();}else{document.addEventListener('DOMContentLoaded',positionStatus);}
  window.addEventListener('resize',positionStatus);
  // --- inspect ---
  var infoEl=document.getElementById('__epresso_tb_info');
  var openBtn=document.getElementById('__epresso_tb_open');
  var closeBtn=document.getElementById('__epresso_tb_close');
  function inTb(el){return tb.contains(el);}
  function fileOf(el){
    for(var n=el;n&&n!==document.body;n=n.parentElement){
      var atts=n.attributes||[];for(var i=0;i<atts.length;i++){
        var a=atts[i].name;
        if(a.indexOf('data-epresso-')===0){var hh=a.slice('data-epresso-'.length);if(map[hh])return map[hh];}
      }
    }
    return null;
  }
  function clearOutline(){if(last){last.classList.remove('ep-inspect-link');last=null;}}
  function showInfo(el){
    if(last&&last!==el)last.classList.remove('ep-inspect-link');
    last=el;el.classList.add('ep-inspect-link');
    var tag=el.tagName?el.tagName.toLowerCase():'';var id=el.id?('#'+el.id):'';
    var cls=(typeof el.className==='string'&&el.className)?'.'+el.className.trim().split(/\s+/).join('.'):'';
    var file=fileOf(el)||pageFile;
    if(openBtn){if(file){openBtn.setAttribute('data-file',file);openBtn.style.display='';}else{openBtn.style.display='none';}}
    if(infoEl)infoEl.innerHTML='<code>'+tag+id+cls+'</code>'+(file?(' <span class="tb-comp">'+file.split('/').pop()+'</span>'):'');
    pop.hidden=false;
  }
  document.addEventListener('mouseover',function(e){if(mode&&e.target&&!inTb(e.target)&&e.target!==document.body)showInfo(e.target);},true);
  document.addEventListener('mouseout',function(e){if(mode&&e.target===last){e.target.classList.remove('ep-inspect-link');last=null;}},true);
  document.addEventListener('click',function(e){if(mode&&!inTb(e.target)){e.stopPropagation();var a=e.target.closest?e.target.closest('a'):null;if(a)e.preventDefault();showInfo(e.target);deactivateInspect();}},true);
  if(closeBtn)closeBtn.onclick=function(){pop.hidden=true;clearOutline();};
  // --- layout: colour-coded rectangles over each component, click to drill in ---
  // Rendered size only (getBoundingClientRect) — no build-time data needed, since
  // `map` (hash -> source file) is already here for the inspector above.
  var layoutRoot=null,layoutStack=[],layoutChildren=[];
  var EDIT_ICON='<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M11.013 1.427a1.75 1.75 0 0 1 2.474 0l1.086 1.086a1.75 1.75 0 0 1 0 2.474l-8.61 8.61c-.21.21-.47.364-.756.445a6.03 6.03 0 0 1-1.68.441l-1.026.146a.75.75 0 0 1-.863-.863l.146-1.026c.055-.34.207-.677.441-1.68a1.75 1.75 0 0 1 .445-.755l8.61-8.61Z"/></svg>';
  function scopeOf(el){
    var atts=el.attributes||[];
    for(var i=0;i<atts.length;i++){
      var a=atts[i].name;
      if(a.indexOf('data-epresso-')===0){var hh=a.slice('data-epresso-'.length);if(map[hh])return {hash:hh,file:map[hh]};}
    }
    return null;
  }
  /* The topmost component boundary under `root` that isn't `root` itself: walk
     down, and the moment an element carries a *different* component's scope,
     record it and stop descending — its own children are the next drill-in
     level, not this one. Elements still carrying `ownHash` (root's own markup)
     are transparent and get walked through. */
  function directChildComponents(root,ownHash){
    var out=[];
    (function walk(el){
      var kids=el.children;
      for(var i=0;i<kids.length;i++){
        var c=kids[i],s=scopeOf(c);
        if(s&&s.hash!==ownHash)out.push({hash:s.hash,file:s.file,el:c});
        else walk(c);
      }
    })(root);
    return out;
  }
  function hueFor(file){var hh=0;for(var i=0;i<file.length;i++)hh=(hh*31+file.charCodeAt(i))>>>0;return hh%360;}
  function fileName(file){return file.slice(file.lastIndexOf('/')+1).replace(/\.ep$/,'');}
  function ensureLayoutRoot(){
    if(layoutRoot)return layoutRoot;
    layoutRoot=document.createElement('div');
    layoutRoot.id='__epresso_tb_layout';
    document.body.appendChild(layoutRoot);
    /* Same info pill the inspector uses (#__epresso_tb_pop): hover a box, see
       its name/size + the same "open in editor" button, no per-box markup. */
    layoutRoot.addEventListener('mouseover',function(e){
      var box=e.target.closest?e.target.closest('.tb-lbox'):null;
      if(!box)return;
      showLayoutInfo(box);
    });
    layoutRoot.addEventListener('mouseout',function(e){
      var box=e.target.closest?e.target.closest('.tb-lbox'):null;
      if(box&&(!e.relatedTarget||!box.contains(e.relatedTarget)))pop.hidden=true;
    });
    layoutRoot.addEventListener('click',function(e){
      var box=e.target.closest?e.target.closest('.tb-lbox'):null;
      if(!box)return;
      if(box.classList.contains('tb-lbox-bg')){layoutStack.pop();renderLayout();return;}
      var idx=+box.getAttribute('data-i');
      if(layoutChildren[idx]){layoutStack.push(layoutChildren[idx]);renderLayout();}
    });
    return layoutRoot;
  }
  /* Breadcrumb trail lives in the same notification pill as everything else
     (#__epresso_tb_toast) instead of its own fixed bar — no bar to overlap the
     boxes underneath it, and it disappears the same way any other toast does. */
  function editBtn(file,name){
    return file?(' <button type="button" class="tb-editor tb-lc-edit" data-file="'+esc(file)+'" title="Edit '+esc(name)+'" aria-label="Edit '+esc(name)+'">'+EDIT_ICON+'</button>'):'';
  }
  function renderLayoutCrumb(){
    var parts=['<button type="button" class="tb-lcrumb" data-i="-1">page</button>'+editBtn(pageFile,'page')];
    layoutStack.forEach(function(s,i){
      var name=fileName(s.file);
      parts.push('<span class="tb-lsep">/</span><button type="button" class="tb-lcrumb" data-i="'+i+'">'+esc(name)+'</button>'+editBtn(s.file,name));
    });
    clearTimeout(toastTimer);
    toast.innerHTML=parts.join('');
    toast.className='tb-toast tb-toast-layout';
    toast.style.display='flex';
  }
  toast.addEventListener('click',function(e){
    if(!layoutMode)return;
    var crumb=e.target.closest?e.target.closest('.tb-lcrumb'):null;
    if(crumb){layoutStack.length=+crumb.getAttribute('data-i')+1;renderLayout();}
  });
  function showLayoutInfo(box){
    var file=box.getAttribute('data-file'),name=box.getAttribute('data-name'),size=box.getAttribute('data-size');
    if(openBtn){if(file){openBtn.setAttribute('data-file',file);openBtn.style.display='';}else{openBtn.style.display='none';}}
    if(infoEl)infoEl.innerHTML='<code>'+esc(name)+'</code> <span class="tb-comp">'+esc(size)+'</span>';
    pop.hidden=false;
  }
  function layoutBoxHtml(item,idx,isBg){
    var r=item.el.getBoundingClientRect();
    /* Some elements (e.g. a skip-link parked at top:-100% until focused) have
       real dimensions but sit entirely off-screen — nothing to draw a box over. */
    if(r.width<=0||r.height<=0||r.bottom<=0||r.right<=0||r.top>=innerHeight||r.left>=innerWidth)return '';
    var hue=hueFor(item.file),name=fileName(item.file);
    var size=Math.round(r.width)+'\u00d7'+Math.round(r.height);
    var style='position:fixed;left:'+r.left+'px;top:'+r.top+'px;width:'+r.width+'px;height:'+r.height+'px;'+
      'background:hsl('+hue+',60%,'+(isBg?'22%':'32%')+');border:1px solid hsl('+hue+',70%,60%);z-index:'+(isBg?1:2)+';';
    return '<div class="tb-lbox'+(isBg?' tb-lbox-bg':'')+'" data-i="'+idx+'" data-file="'+esc(item.file)+'" data-name="'+esc(name)+'" data-size="'+size+'" style="'+style+'"></div>';
  }
  function renderLayout(){
    var root=ensureLayoutRoot();
    pop.hidden=true;   // the hovered box (if any) no longer exists post-render
    var current=layoutStack.length?layoutStack[layoutStack.length-1]:null;
    var rootEl=current?current.el:document.body,ownHash=current?current.hash:null;
    renderLayoutCrumb();
    var html='';
    if(current)html+=layoutBoxHtml(current,-1,true);
    layoutChildren=directChildComponents(rootEl,ownHash);
    layoutChildren.forEach(function(item,i){html+=layoutBoxHtml(item,i,false);});
    root.innerHTML=html;
  }
  function deactivateLayout(){
    layoutMode=false;var lb=layoutBtn();if(lb)lb.classList.remove('on');
    if(layoutRoot){layoutRoot.remove();layoutRoot=null;}
    layoutStack=[];
    pop.hidden=true;
    clearTimeout(toastTimer);
    toast.style.display='none';
    toast.className='tb-toast';
    toast.innerHTML='';
    document.documentElement.style.overflow='';
  }
  function toggleLayout(){
    var lb=layoutBtn();
    if(layoutMode){deactivateLayout();}
    else{
      layoutMode=true;if(lb)lb.classList.add('on');close();deactivateInspect();
      /* Boxes are positioned from getBoundingClientRect() once per render; lock
         scroll while the view is open rather than recomputing continuously. */
      document.documentElement.style.overflow='hidden';
      renderLayout();
    }
  }
  window.addEventListener('resize',function(){if(layoutMode)renderLayout();});
  document.addEventListener('keydown',function(e){if(layoutMode&&e.key==='Escape')toggleLayout();});
  // --- audit ---
  function issues(){
    var out=[];
    if(!document.documentElement.getAttribute('lang'))out.push({m:'<html> has no lang attribute',el:document.documentElement});
    if(!document.querySelector('meta[name="viewport"]'))out.push({m:'missing viewport <meta>',el:document.head});
    Array.prototype.forEach.call(document.querySelectorAll('img'),function(i){if(i.getAttribute('alt')===null)out.push({m:'img missing alt: '+srcOf(i),el:i});});
    function srcOf(i){var s=i.getAttribute('src')||'';return s.length>40?s.slice(0,40)+'…':s;}
    Array.prototype.forEach.call(document.querySelectorAll('a'),function(a){var t=(a.textContent||'').trim();if(!t&&!a.getAttribute('aria-label'))out.push({m:'link has no text: '+a.getAttribute('href'),el:a});else if(a.getAttribute('href')==='#'||a.getAttribute('href')==='')out.push({m:'link href is empty/#: '+t,el:a});});
    var seen={};Array.prototype.forEach.call(document.querySelectorAll('[id]'),function(el){var id=el.id;if(seen[id])out.push({m:'duplicate id: #'+id,el:el});seen[id]=1;});
    Array.prototype.forEach.call(document.querySelectorAll('button'),function(b){if(!b.textContent.trim()&&!b.getAttribute('aria-label'))out.push({m:'button has no accessible name',el:b});});
    return out;
  }
  function srcOf(i){var s=i.getAttribute('src')||'';return s.length>40?s.slice(0,40)+'…':s;}
  function runAudit(){
    var list=document.querySelector('[data-audit-list]');if(!list)return;
    var iss=issues();var badge=document.querySelector('[data-audit-badge]');
    if(badge){badge.style.display=iss.length?'block':'none';badge.textContent=iss.length;}
    if(iss.length===0){list.innerHTML='<li class="ok">no issues found</li>';return;}
    list.innerHTML='';
    iss.forEach(function(it,i){
      var li=document.createElement('li');li.className='warn';li.innerHTML=it.m;
      li.onclick=function(){document.querySelectorAll('.ep-audit-hit').forEach(function(x){x.classList.remove('ep-audit-hit');});it.el.classList.add('ep-audit-hit');it.el.scrollIntoView({block:'center',behavior:'smooth'});};
      list.appendChild(li);
    });
    vlog('audit:',iss.length,'issues');
  }
  // --- settings ---
  function loadSettingsUI(){
    var sel=tb.querySelector('[data-opt="placement"]');if(sel)sel.value=prefs.placement||tb.getAttribute('data-placement')||'bottom';
    var ed=tb.querySelector('[data-opt="editor"]');if(ed)ed.value=prefs.editor||'vscode';
    var nt=tb.querySelector('[data-opt="notify"]');if(nt)nt.checked=prefs.notify!==false;
    var vb=tb.querySelector('[data-opt="verbose"]');if(vb)vb.checked=!!prefs.verbose;
  }
  var save=tb.querySelector('[data-save]');
  if(save)save.onclick=function(){
    prefs.placement=(tb.querySelector('[data-opt="placement"]')||{}).value||'bottom';
    prefs.editor=(tb.querySelector('[data-opt="editor"]')||{}).value||'vscode';
    prefs.notify=!!(tb.querySelector('[data-opt="notify"]')||{}).checked;
    prefs.verbose=!!(tb.querySelector('[data-opt="verbose"]')||{}).checked;
    savePrefs();applyPrefs();toastMsg('settings saved');vlog('prefs',prefs);
  };
  function applyPrefs(){if(prefs.placement){tb.setAttribute('data-placement',prefs.placement);var css=prefs.placement==='top'?'top:0;border-bottom:1px solid #2a2f3a':'bottom:0;border-top:1px solid #2a2f3a';tb.style.cssText=prefs.placement==='top'?'position:fixed;left:0;right:0;top:0;border-bottom:1px solid #2a2f3a':'position:fixed;left:0;right:0;bottom:0;border-top:1px solid #2a2f3a';}}
  applyPrefs();
  // --- notifications + ws ---
  var toastTimer=null;
  function toastMsg(msg,isErr){if(prefs.notify===false)return;toast.textContent=msg;toast.className='tb-toast'+(isErr?' err':'');toast.style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(function(){toast.style.display='none';},isErr?6000:2000);}
  try{
    if(!@LIVE@)throw 0;      // no live-reload when serving a static build
    var ws=new WebSocket(url);
    ws.onmessage=function(e){var d=e.data||'';vlog('ws',d);if(d.indexOf('error:')===0){toastMsg(d.slice(6),true);}else if(d==='reload'){toastMsg('rebuilt — reloading');location.reload();}};
    ws.onclose=function(){setTimeout(function(){if(ws.readyState>1)location.reload();},2000);};
  }catch(e){}
  // --- project: copy debug ---
  var copy=tb.querySelector('[data-copy-debug]');
  if(copy)copy.onclick=function(){
    var pre=tb.querySelector('.tb-debug pre');var txt=pre?pre.textContent:'';
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){toastMsg('debug info copied');});}
    else{toastMsg('clipboard unavailable');}
  };
  var CDATA=@CDATA@;
  function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function showEntry(c,e){var v=document.getElementById('__epresso_tb_cview');var it=CDATA&&CDATA[c]&&CDATA[c][e];if(!v||!it)return;v.innerHTML='<h4>'+esc(e)+'</h4>'+(it.file?'<div class="tb-ccrumb">'+esc(it.file)+'</div>':'')+'<pre>'+esc(it.data)+'</pre>'+(it.body?'<h4>body</h4><pre>'+esc(it.body)+'</pre>':'');}
  function markEntry(c,e){
    if(e&&CDATA&&CDATA[c]&&CDATA[c][e])showEntry(c,e);
    var t=null;document.querySelectorAll('.tb-centry').forEach(function(x){if(x.getAttribute('data-c')===c&&x.getAttribute('data-e')===e)t=x;});
    if(t){
      document.querySelectorAll('.tb-centry.active').forEach(function(x){x.classList.remove('active');});
      t.classList.add('active');
      var d=t.closest('details');while(d){d.open=true;d=d.parentElement?d.parentElement.closest('details'):null;}
    }
  }
  document.addEventListener('click',function(e){var b=e.target&&e.target.closest?e.target.closest('.tb-centry'):null;if(b)markEntry(b.getAttribute('data-c'),b.getAttribute('data-e'));},true);
  var PCOMPS=document.getElementById('__epresso_tb_pcomps');
  function compOf(el){var atts=el&&el.attributes||[];for(var i=0;i<atts.length;i++){var a=atts[i].name;if(a.indexOf('data-epresso-')===0){var hh=a.slice('data-epresso-'.length);if(map[hh])return map[hh];}}return null;}
  function compHasAncestor(el,f){for(var n=el&&el.parentElement;n&&n!==document.body&&n!==document.documentElement;n=n.parentElement){if(compOf(n)===f)return true;}return false;}
  function pageComponents(){var used={},all=document.querySelectorAll('*');for(var i=0;i<all.length;i++){var el=all[i];var f=compOf(el);if(!f||compHasAncestor(el,f))continue;(used[f]=used[f]||[]).push(el);}return used;}
  function clearCompHighlights(){document.querySelectorAll('.tb-comp-highlight').forEach(function(x){x.classList.remove('tb-comp-highlight');});document.querySelectorAll('.tb-pcomp.on').forEach(function(x){x.classList.remove('on');});}
  function renderPageComponents(){
    if(!PCOMPS)return;var used=pageComponents();var files=Object.keys(used).sort();
    if(!files.length){PCOMPS.innerHTML='<p class="tb-hint">no scoped components on this page</p>';return;}
    var rows=files.map(function(f){var n=f.slice(f.lastIndexOf('/')+1);return '<li><button type="button" class="tb-pcomp" data-f="'+esc(f)+'">'+esc(n)+' <span>('+used[f].length+')</span></button></li>';}).join('');
    PCOMPS.innerHTML='<details class="tb-coll" open><summary>components <span>('+files.length+')</span></summary><ul>'+rows+'</ul></details>';
  }
  document.addEventListener('click',function(e){var b=e.target&&e.target.closest?e.target.closest('.tb-pcomp'):null;if(!b)return;var f=b.getAttribute('data-f');var on=b.classList.contains('on');clearCompHighlights();if(on)return;var inst=(pageComponents()[f])||[];inst.forEach(function(el){el.classList.add('tb-comp-highlight');});if(inst[0])inst[0].scrollIntoView({block:'center',behavior:'smooth'});b.classList.add('on');},true);
  // Clicking a collection/entry in the page tab opens the content tab's viewer on it.
  document.addEventListener('click',function(e){var b=e.target&&e.target.closest?e.target.closest('.tb-pcontent'):null;if(!b)return;var c=b.getAttribute('data-c');if(!c)return;open('content');var id=b.getAttribute('data-e');if(!id){var col=CDATA&&CDATA[c];if(col)id=Object.keys(col)[0]||'';}if(id)markEntry(c,id);},true);
  function fitBodyPad(){
    // Reserve the toolbar's CURRENT full height (bar, or bar + whichever panel is
    // open), so bottom content (footer/Pager) is never hidden behind it. Panels
    // differ in height, so we re-measure on open/close/resize.
    var h=(tb?tb.offsetHeight:0)||0;
    var se=document.scrollingElement||document.documentElement;
    if(se&&h>0)se.style.scrollPaddingBottom=h+'px';
    var sp=document.getElementById('__epresso_tb_space');if(sp)sp.style.height=h+'px';
  }
  fitBodyPad();window.addEventListener('resize',fitBodyPad);
  renderPageComponents();
  runAudit();   // surface the audit badge immediately on page load
  positionStatus();
  (function(){try{var st=sessionStorage.getItem('__epresso_app');if(st&&st!=='inspect'&&document.querySelector('[data-app="'+st+'"]'))open(st);}catch(e){}})();
})();
</script>
</div>"""


def _is_content_entry(obj) -> bool:
    """True if ``obj`` looks like a content Entry (has id/data/rendered)."""
    return obj is not None and hasattr(obj, "id") and hasattr(obj, "data") and hasattr(obj, "rendered")


def _entry_collection(site, entry) -> str | None:
    """The name of the collection holding ``entry`` (by identity), or None."""
    store = getattr(site, "store", None)
    if not store:
        return None
    for name, col in store.collections.items():
        if any(e is entry for e in col.all()):
            return name
    return None


def _content_deps(site, path: str) -> tuple[list[str], dict[str, set[str]], str | None]:
    """Content a page depends on: (whole collections, {collection: entry ids},
    current-route entry's collection or None). Drawn from the build graph edges a
    render recorded (``collection:<name>`` / ``<col>:<id>``), plus the route's own
    data entry so docs-style content pages show even without template reads."""
    edges = set(site.graph.edges_for(path)) if getattr(site, "graph", None) else set()
    collections: list[str] = sorted(k.split(":", 1)[1] for k in edges if k.startswith("collection:"))
    entries: dict[str, set[str]] = {}
    for k in edges:
        if ":" in k and not k.startswith("collection:"):
            col, eid = k.split(":", 1)
            entries.setdefault(col, set()).add(eid)
    # A route whose data is a content Entry contributes its own entry (docs pages).
    current_col = None
    route = _find_route(site, path)
    data = getattr(route, "data", None) if route is not None else None
    if _is_content_entry(data):
        col = _entry_collection(site, data)
        if col:
            current_col = col
            entries.setdefault(col, set()).add(str(getattr(data, "id", "")))
    return collections, entries, current_col


def _page_panel(site, path: str) -> str:
    """Render the 'Page' panel: which collections/entries this page uses."""
    collections, entries, current_col = _content_deps(site, path)
    parts: list[str] = []
    if current_col is not None:
        parts.append(f'<p class="tb-hint">this page is a <b>{h(current_col)}</b> entry</p>')
    if not collections and not entries:
        return "".join(parts) or '<p class="tb-hint">no content dependencies for this page</p>'
    if collections:
        parts.append("<h4>Collections (read in full)</h4>")
        lis = "".join(
            f'<li><button type="button" class="tb-pcontent" data-c="{h(c)}">{h(c)}</button></li>'
            for c in collections
        )
        parts.append(f"<ul>{lis}</ul>")
    for col in sorted(entries):
        ids = sorted(entries[col])
        lis = "".join(
            f'<li><button type="button" class="tb-pcontent" data-c="{h(col)}" data-e="{h(i)}">{h(i)}</button></li>'
            for i in ids
        )
        parts.append(
            f'<details class="tb-coll"><summary>{h(col)} <span>({len(ids)})</span></summary>'
            f"<ul>{lis}</ul></details>"
        )
    return "".join(parts)


def _toolbar_html(site, path: str, *, live: bool = True) -> str:
    placement = (site.config.dev.toolbar.placement or "bottom").lower()
    env_name, env_dot = _env_info(site)
    edge = "top:0;border-bottom:1px solid #2a2f3a" if placement == "top" else "bottom:0;border-top:1px solid #2a2f3a"
    tstyle = f"position:fixed;left:0;right:0;z-index:9999;{edge}"
    poppos = "top:44px" if placement == "top" else "bottom:44px"

    route = _find_route(site, path)
    entry = getattr(route, "data", None)
    src = (getattr(entry, "file_path", None) or (route.source if route is not None else None))
    editor = f'<button type="button" class="tb-btn tb-icon tb-editor" data-file="{str(src)}" title="Open source in editor" aria-label="Open source in editor"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M11.013 1.427a1.75 1.75 0 0 1 2.474 0l1.086 1.086a1.75 1.75 0 0 1 0 2.474l-8.61 8.61c-.21.21-.47.364-.756.445a6.03 6.03 0 0 1-1.68.441l-1.026.146a.75.75 0 0 1-.863-.863l.146-1.026c.055-.34.207-.677.441-1.68a1.75 1.75 0 0 1 .445-.755l8.61-8.61Z"/></svg></button>' if src else ""

    routes = sorted(r.path for r in site.resolve_routes() if r.content_type == "text/html" and not r.redirect_to)[:_PANEL_ROUTES]
    rows = "".join(f'<li><a href="{h(r)}" title="{h(r)}">{h(r)}</a></li>' for r in routes) or "<li><em>none</em></li>"

    links = ""
    repo = (site.config.site.repository or "").strip()
    if repo:
        links += f'<button class="tb-btn"><a href="{h(repo)}">repo</a></button> '
    debug = _debug_info(site)
    desc = "content-first static site generator — dev toolbar"
    return (
        _TEMPLATE.replace("@TBSTYLE@", tstyle)
        .replace("@PLACEMENT@", h(placement))
        .replace("@POPPOS@", poppos)
        .replace("@ENV@", env_name)
        .replace("@ENVDOT@", env_dot)
        .replace("@FILE@", h(src.name if src else path))
        .replace("@PAGE@", json.dumps(str(src) if src else ""))
        .replace("@EDITOR@", editor)
        .replace("@ROUTES@", rows)
        .replace("@CLEFT@", _content_left(site))
        .replace("@CDATA@", _content_data(site))
        .replace("@PAGEDEPS@", _page_panel(site, path))
        .replace("@SCOPE_MAP@", json.dumps(_scope_map(site)))
        .replace("@VERSION@", _version())
        .replace("@DESC@", h(desc))
        .replace("@LINKS@", links)
        .replace("@LIVE@", "true" if live else "false")
        .replace("@DEBUG@", h(debug))
    )


def _content_left(site) -> str:
    """Left pane: a tree of collections -> entries."""
    store = getattr(site, "store", None)
    if not store or not store.collections:
        return '<p class="tb-hint">no collections</p>'
    cap = 200
    parts: list[str] = []
    for name in sorted(store.collections):
        entries = sorted(store.collection(name).all(), key=lambda e: e.id)
        lis = "".join(
            f'<li><button type="button" class="tb-centry" data-c="{h(name)}" data-e="{h(e.id)}">{h(e.id)}</button></li>'
            for e in entries[:cap]
        )
        more = f'<li class="tb-more">… {len(entries) - cap} more</li>' if len(entries) > cap else ""
        parts.append(
            f'<details class="tb-coll"><summary>{h(name)} <span>({len(entries)})</span></summary>'
            f"<ul>{lis}{more}</ul></details>"
        )
    return "".join(parts)


def _content_data(site) -> str:
    """JSON of {collection: {id: {data, body, file}}} for the viewer."""
    import json

    store = getattr(site, "store", None)
    out: dict = {}
    if store:
        for name in sorted(store.collections):
            out[name] = {}
            for e in sorted(store.collection(name).all(), key=lambda x: x.id)[:200]:
                fp = getattr(e, "file_path", None)
                out[name][e.id] = {
                    "data": _dump_data(e.data),
                    "body": (e.body or "")[:1500],
                    "file": str(fp) if fp else "",
                }
    return json.dumps(out, ensure_ascii=False).replace("</", "<\\/")


def _dump_data(data) -> str:
    import json

    obj = data.model_dump() if hasattr(data, "model_dump") else data
    return json.dumps(obj, indent=1, default=str, ensure_ascii=False)


def _debug_info(site) -> str:
    lines = [
        f"epresso {_version()}",
        f"root: {site.config.root}",
        f"env: {site.config.env or 'default'}",
    ]
    store = getattr(site, "store", None)
    if store is not None:
        for name, col in store.collections.items():
            lines.append(f"collection {name}: {len(col.all())} entries")
    lines.append(f"routes: {len(list(site.resolve_routes()))}")
    return "\n".join(lines)


def _version() -> str:
    try:
        from . import __version__  # type: ignore[attr-defined]

        return __version__
    except Exception:  # noqa: BLE001
        return "?"


def _scope_map(site) -> dict[str, str]:
    from .components import _scope_hash  # noqa: PLC0415

    out: dict[str, str] = {}
    roots = []
    for attr in ("dir_components", "dir_layouts"):
        fn = getattr(site.config, attr, None)
        if fn is not None:
            roots.append(fn())
    for root in roots:
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.ep")):
            out.setdefault(_scope_hash(f.stem), str(f.resolve()))
    return out


def _rel(site, src: Path) -> str:
    try:
        return src.relative_to(site.config.root).as_posix()
    except Exception:  # noqa: BLE001
        return str(src)


def _find_route(site, path: str):
    for r in site.resolve_routes():
        if r.path == path and r.source:
            return r
    return None


def _page_status(route) -> dict:
    """Return the current page's visibility status (private/draft) from its entry."""
    entry = getattr(route, "data", None)
    d = getattr(entry, "data", None)
    if d is None:
        return {"label": "", "cls": ""}
    g = (lambda k: d.get(k)) if isinstance(d, dict) else (lambda k: getattr(d, k, None))
    if g("private"):
        return {"label": "private", "cls": "tb-private"}
    if g("draft"):
        return {"label": "draft", "cls": "tb-draft"}
    return {"label": "", "cls": ""}



def _env_info(site) -> tuple[str, str]:
    """Return ``(name, dot_class)`` for the active build environment."""
    env = (getattr(site, "env_name", None) or "development").lower()
    dot = {"development": "tb-dot-dev", "preview": "tb-dot-preview", "production": "tb-dot-prod"}.get(
        env, "tb-dot-prod"
    )
    return env, dot


def _env_override(site) -> str:
    """A tiny non-scoped style tinting a theme's nav/brand dot to the active
    environment. Themes opt in via ``var(--epresso-env-dot, <default>)``. Only
    emitted for non-production (development/preview); a production serve leaves
    the theme's normal accent untouched.
    """
    env = (getattr(site, "env_name", None) or "").lower()
    color = {"development": "#a78bfa", "preview": "#ff922b"}.get(env)
    if not color:
        return ""
    return f'<style data-epresso-env-dot>:root{{--epresso-env-dot:{color}}}</style>'


def _status_html(site, path: str) -> str:
    """Independent bottom-right pill shown when the current page is private/draft."""
    status = _page_status(_find_route(site, path))
    if not status["label"]:
        return ""
    return f'<div id="__epresso_tb_status" class="tb-status {status["cls"]}">this page is {status["label"]}</div>'

def inject(html: str, site, path: str, *, live: bool = True) -> str:
    """Inject the dev toolbar into a rendered HTML page (no-op otherwise).

    ``live`` toggles the live-reload WebSocket wiring; pass ``live=False`` when
    injecting into a statically served build (e.g. ``epresso preview``) so it
    doesn't try to reload over a non-existent WS.

    The toolbar is a development/preview aid only: it is never injected into a
    **production** build (the env ``epresso docs`` and ``epresso preview``
    default to), so a previewed production site stays clean.
    """
    if not site.config.dev.toolbar.enabled:
        return html
    if (getattr(site, "env_name", None) or "").lower() == "production":
        return html
    marker = "</body>"
    if marker not in html:
        return html
    return html.replace(
        marker,
        # A normal-flow spacer right before the (fixed) toolbar reserves room at
        # the bottom of the document, so the last content (e.g. Pager) can scroll
        # above the bar and stays inspectable. Its height is set to the bar's real
        # height in JS (fitBodyPad); this attribute is just a stable hook.
        '<div id="__epresso_tb_space" aria-hidden="true"></div>'
        + _toolbar_html(site, path, live=live)
        + _env_override(site)
        + _status_html(site, path)
        + marker,
        1,
    )
