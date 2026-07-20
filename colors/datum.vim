" datum.vim -- a 256-color vim colorscheme, light and dark
" Maintainer: datum

hi clear
if exists('syntax_on')
  syntax reset
endif

let g:colors_name = 'datum'

if !has('gui_running') && &t_Co < 256
  finish
endif

" Palette -----------------------------------------------------------------
" Accent hue angles are anchored on the Okabe-Ito color-vision-deficiency-
" safe qualitative set; 'cyan' is a teal placed between string-green and
" keyword-blue. Derived in OKLCH, verified for WCAG 2.2 (>=4.5:1) and APCA,
" validated against protan/deutan/tritan simulation. Hue angle is shared
" across both modes (hue identity); only lightness and chroma differ per
" background. Each entry is [cterm256, guihex]. See docs/ideas.html for
" the full methodology, per-color L/C/H, and measured contrast numbers.

if &background ==# 'light'
  " off-white ground (never pure white -- avoids glare)
  let s:bg0    = ['231', '#f1f6fd']  " canvas       L 0.97
  let s:bg1    = ['255', '#e7ecf2']  " cursorline   L 0.94
  let s:bg2    = ['252', '#ced3d9']  " selection    L 0.86
  let s:fg1    = ['242', '#616a76']  " comments     L 0.52  WCAG 5.1
  let s:fg0    = ['236', '#292e35']  " normal text  L 0.30  WCAG 12.6
  " tier 1 -- saturated mid-tones: the sparse reference points
  let s:red    = ['130', '#a44602']  " h 47   error     WCAG 5.6
  let s:orange = ['94',  '#976700']  " h 77   number    WCAG 4.5
  let s:yellow = ['94',  '#756f1d']  " h 105  constant  WCAG 4.8
  let s:green  = ['29',  '#107c5a']  " h 165  string    WCAG 4.8
  let s:cyan   = ['30',  '#0b7b80']  " h 200  type      WCAG 4.7
  let s:blue   = ['25',  '#0068a4']  " h 244  keyword   WCAG 5.5
  let s:purple = ['95',  '#983472']  " h 346  function  WCAG 6.3
  " tier 2 -- the glue: same hue as its tier-1 sibling, equally saturated,
  " split by lightness (the one channel that survives every kind of CVD).
  " On the light ground the glue goes *darker* -- it is the body text, so it
  " keeps the higher contrast; the accents keep the saturated mid-tones.
  let s:var    = ['236', '#4d3919']  " h 77   variable  WCAG 10.1
  let s:op     = ['239', '#2f516c']  " h 244  operator  WCAG 7.7
  let s:call   = ['239', '#633750']  " h 346  fn call   WCAG 8.8
  let s:param  = ['23',  '#154b4e']  " h 200  parameter WCAG 9.0
else
  " soft near-black ground (never pure black -- avoids halation)
  let s:bg0    = ['233', '#0f1318']  " canvas       L 0.18
  let s:bg1    = ['234', '#181c21']  " cursorline   L 0.22
  let s:bg2    = ['236', '#2b2f35']  " selection    L 0.30
  let s:fg1    = ['246', '#8f98a3']  " comments     L 0.68  WCAG 6.4
  let s:fg0    = ['254', '#dbe0e8']  " normal text  L 0.91  WCAG 14.1
  " tier 1 -- saturated mid-tones: the sparse reference points
  let s:red    = ['209', '#ef844a']  " h 47   error     WCAG 7.2
  let s:orange = ['179', '#e6ac4c']  " h 77   number    WCAG 9.2
  let s:yellow = ['185', '#d8cf58']  " h 105  constant  WCAG 11.5
  let s:green  = ['79',  '#51daa7']  " h 165  string    WCAG 10.6
  let s:cyan   = ['80',  '#5ddae0']  " h 200  type      WCAG 11.2
  let s:blue   = ['75',  '#66b6f4']  " h 244  keyword   WCAG 8.5
  let s:purple = ['175', '#db78b1']  " h 346  function  WCAG 6.5
  " tier 2 -- the glue: same hue as its tier-1 sibling, equally saturated,
  " split by lightness (the one channel that survives every kind of CVD)
  let s:var    = ['223', '#fcdcad']  " h 77   variable  WCAG 14.2
  let s:op     = ['153', '#b2dafb']  " h 244  operator  WCAG 12.7
  let s:call   = ['218', '#f5b9d9']  " h 346  fn call   WCAG 11.4
  let s:param  = ['159', '#a5f5f9']  " h 200  parameter WCAG 15.1
endif

" hi group fg [bg] [attr] [sp] ----------------------------------------------
" sp sets guisp -- the undercurl/underline color, which diagnostics need so
" the squiggle can be colored while the text keeps its syntax color. cterm
" has no equivalent, so it is gui-only.
function! s:hi(group, fg, ...) abort
  let l:bg   = a:0 >= 1 ? a:1 : []
  let l:attr = a:0 >= 2 ? a:2 : 'NONE'
  let l:sp   = a:0 >= 3 ? a:3 : []
  let l:cmd  = 'hi ' . a:group
  if !empty(a:fg)
    let l:cmd .= ' ctermfg=' . a:fg[0] . ' guifg=' . a:fg[1]
  endif
  if !empty(l:bg)
    let l:cmd .= ' ctermbg=' . l:bg[0] . ' guibg=' . l:bg[1]
  endif
  let l:cmd .= ' cterm=' . l:attr . ' gui=' . l:attr
  if !empty(l:sp)
    let l:cmd .= ' guisp=' . l:sp[1]
  endif
  execute l:cmd
endfunction

call s:hi('Normal',      s:fg0, s:bg0)
call s:hi('NonText',     s:bg2, s:bg0)
call s:hi('EndOfBuffer', s:bg0, s:bg0)

" Chroma-tiered highlighting: everything carries a hue, but *saturation* is
" inverse to token prevalence -- the frequency-inverse principle applied to
" chroma rather than to the presence of color. Sparse reference points
" (strings, numbers, constants, functions) run at full chroma; the ubiquitous
" glue (variables, operators) is tinted but quiet; pure punctuation and
" comments stay neutral. Warm = values, cool = grammar, purple = what you
" defined, red = what's broken. See docs/ideas.html for the rationale.

call s:hi('Comment', s:fg1, [], 'italic')

" full-chroma tier -- the sparse reference points
call s:hi('Constant', s:yellow)
call s:hi('Boolean',  s:yellow)
call s:hi('String',   s:green)
call s:hi('Character',s:green)
call s:hi('Number',   s:orange)
call s:hi('Float',    s:orange)

" low-chroma tier -- variables are ~75% of code, so they whisper
call s:hi('Identifier', s:var)
call s:hi('Function',   s:purple)

call s:hi('Statement',  s:blue)
call s:hi('Conditional',s:blue)
call s:hi('Repeat',     s:blue)
call s:hi('Label',      s:blue)
" Operators get a quiet low-chroma blue -- a search cue for = == |> etc.
" without shouting. Delimiters (, ; {}) are dimmed to fg1 instead: pure
" punctuation is the one thing that earns *less* than plain, which is what
" lets the color around it read louder.
" (Identifier/Operator/Delimiter are mostly visible under Tree-sitter; base
" regex syntax under-populates all three groups.)
call s:hi('Operator',   s:op)
call s:hi('Keyword',    s:blue)
call s:hi('Exception',  s:red)

call s:hi('PreProc',   s:orange)
call s:hi('Include',   s:orange)
call s:hi('Define',    s:orange)
call s:hi('Macro',     s:orange)
call s:hi('PreCondit', s:orange)

call s:hi('Type',         s:cyan)
call s:hi('StorageClass', s:cyan)
call s:hi('Structure',    s:cyan)
call s:hi('Typedef',      s:cyan)

call s:hi('Special',        s:purple)
call s:hi('SpecialChar',    s:purple)
call s:hi('Tag',            s:purple)
call s:hi('Delimiter',      s:fg1)
call s:hi('SpecialComment', s:fg1, [], 'italic')
call s:hi('Debug',          s:red)

call s:hi('Underlined', s:blue, [], 'underline')
call s:hi('Ignore',     s:bg2)
call s:hi('Error',      s:red, s:bg0, 'bold')
call s:hi('Todo',       s:bg0, s:yellow, 'bold')

" UI ----------------------------------------------------------------------
call s:hi('Cursor',       s:bg0, s:fg0)
call s:hi('CursorLine',   [],    s:bg1)
call s:hi('CursorLineNr', s:yellow, s:bg1, 'bold')
call s:hi('CursorColumn', [],    s:bg1)
call s:hi('LineNr',       s:bg2, s:bg0)
call s:hi('SignColumn',   s:bg2, s:bg0)
call s:hi('ColorColumn',  [],    s:bg1)
call s:hi('VertSplit',    s:bg2, s:bg0)
call s:hi('StatusLine',   s:fg0, s:bg2)
call s:hi('StatusLineNC', s:fg1, s:bg1)
call s:hi('TabLine',      s:fg1, s:bg1)
call s:hi('TabLineFill',  s:bg2, s:bg0)
call s:hi('TabLineSel',   s:fg0, s:bg2, 'bold')
call s:hi('Pmenu',        s:fg0, s:bg1)
call s:hi('PmenuSel',     s:bg0, s:yellow)
call s:hi('PmenuSbar',    [],    s:bg2)
call s:hi('PmenuThumb',   [],    s:fg1)
call s:hi('Visual',       [],    s:bg2)
call s:hi('VisualNOS',    [],    s:bg2)
call s:hi('Search',       s:bg0, s:yellow)
call s:hi('IncSearch',    s:bg0, s:orange)
call s:hi('MatchParen',   s:bg0, s:blue, 'bold')
call s:hi('Folded',       s:fg1, s:bg1)
call s:hi('FoldColumn',   s:fg1, s:bg0)
call s:hi('WildMenu',     s:bg0, s:yellow)
call s:hi('Directory',    s:blue)
call s:hi('Title',        s:yellow, [], 'bold')
call s:hi('ModeMsg',      s:green)
call s:hi('MoreMsg',      s:green)
call s:hi('Question',     s:green)
call s:hi('WarningMsg',   s:red)
call s:hi('ErrorMsg',     s:red, [], 'bold')

" Diff ----------------------------------------------------------------------
call s:hi('DiffAdd',    s:green,  s:bg0)
call s:hi('DiffChange', s:yellow, s:bg0)
call s:hi('DiffDelete', s:red,    s:bg0)
call s:hi('DiffText',   s:orange, s:bg0, 'bold')

" Spelling --------------------------------------------------------------------
call s:hi('SpellBad',   s:red,    [], 'underline')
call s:hi('SpellCap',   s:blue,   [], 'underline')
call s:hi('SpellRare',  s:purple, [], 'underline')
call s:hi('SpellLocal', s:cyan,   [], 'underline')

" Diagnostics (LSP) --------------------------------------------------------
" Severity is its own scale, separate from the syntax palette: red alarms,
" orange warns, blue informs, teal hints. The squiggle carries the color
" (guisp) so the underlying token keeps its own syntax color.
call s:hi('DiagnosticError', s:red)
call s:hi('DiagnosticWarn',  s:orange)
call s:hi('DiagnosticInfo',  s:blue)
call s:hi('DiagnosticHint',  s:cyan)
call s:hi('DiagnosticOk',    s:green)

call s:hi('DiagnosticUnderlineError', [], [], 'undercurl', s:red)
call s:hi('DiagnosticUnderlineWarn',  [], [], 'undercurl', s:orange)
call s:hi('DiagnosticUnderlineInfo',  [], [], 'undercurl', s:blue)
call s:hi('DiagnosticUnderlineHint',  [], [], 'undercurl', s:cyan)
call s:hi('DiagnosticUnderlineOk',    [], [], 'undercurl', s:green)

call s:hi('DiagnosticDeprecated',  s:fg1, [], 'strikethrough', s:fg1)
call s:hi('DiagnosticUnnecessary', s:fg1)

" LSP ----------------------------------------------------------------------
call s:hi('LspReferenceText',  [], s:bg2)
call s:hi('LspReferenceRead',  [], s:bg2)
call s:hi('LspReferenceWrite', [], s:bg2)
call s:hi('LspInlayHint',      s:fg1, s:bg1, 'italic')
call s:hi('LspSignatureActiveParameter', s:param, [], 'bold')
call s:hi('LspCodeLens',       s:fg1, [], 'italic')

" Floating windows (hover, signature help, completion docs) ----------------
call s:hi('NormalFloat', s:fg0, s:bg1)
call s:hi('FloatBorder', s:bg2, s:bg1)
call s:hi('FloatTitle',  s:blue, s:bg1, 'bold')
call s:hi('WinSeparator', s:bg2, s:bg0)
call s:hi('CurSearch',   s:bg0, s:orange)
call s:hi('QuickFixLine', [], s:bg1)

" Plugins ------------------------------------------------------------------
" gitsigns -- reuse the diff semantics
call s:hi('GitSignsAdd',    s:green)
call s:hi('GitSignsChange', s:yellow)
call s:hi('GitSignsDelete', s:red)

" telescope
call s:hi('TelescopeBorder',       s:bg2, s:bg1)
call s:hi('TelescopeTitle',        s:blue, s:bg1, 'bold')
call s:hi('TelescopeNormal',       s:fg0, s:bg1)
call s:hi('TelescopeSelection',    s:fg0, s:bg2)
call s:hi('TelescopeMatching',     s:orange, [], 'bold')
call s:hi('TelescopePromptPrefix', s:purple)

" Tree-sitter ------------------------------------------------------------
" Base regex syntax leaves Identifier/Delimiter (and calls vs definitions)
" unpopulated. Tree-sitter resolves them, which is what lets the chroma tiers
" actually land: definitions run at full chroma, the references to them
" whisper. Without these, @function.call would inherit full-chroma purple on
" every call site -- exactly the noise the frequency-inverse rule forbids.
call s:hi('@variable',           s:var)
call s:hi('@variable.member',    s:var)
call s:hi('@variable.parameter', s:param)
call s:hi('@function',           s:purple)
call s:hi('@function.method',    s:purple)
call s:hi('@function.call',        s:call)
call s:hi('@function.method.call', s:call)
call s:hi('@function.builtin',     s:call)
call s:hi('@constructor',        s:purple)
call s:hi('@property',           s:var)
call s:hi('@operator',           s:op)
call s:hi('@keyword.operator',   s:op)
call s:hi('@punctuation.delimiter', s:fg1)
call s:hi('@punctuation.bracket',   s:fg1)
call s:hi('@punctuation.special',   s:op)
call s:hi('@constant',           s:yellow)
call s:hi('@constant.builtin',   s:yellow)
call s:hi('@boolean',            s:yellow)
call s:hi('@type',               s:cyan)
call s:hi('@type.builtin',       s:cyan)
call s:hi('@module',             s:cyan)

delfunction s:hi
