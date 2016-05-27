set nocp

function! MySys()
    return "linux"
endfunction

" Setting up Vundle
filetype off
set rtp+=~/.vim/bundle/Vundle.vim/
call vundle#begin()

" Let Vundle manage Vundle
" Required by Vundle doc.
Plugin 'VundleVim/Vundle.vim'

Plugin 'Yggdroot/indentLine'
Plugin 'myusuf3/numbers.vim'
Plugin 'mhinz/vim-signify'
Plugin 'bling/vim-airline'
Plugin 'junegunn/goyo.vim'

Plugin 'kien/ctrlp.vim'
Plugin 'fisadev/vim-ctrlp-cmdpalette'
Plugin 'msanders/snipmate.vim'
Plugin 'l04m33/vim-skuld'
Plugin 'Lokaltog/vim-easymotion'
Plugin 'tpope/vim-fugitive'

Plugin 'davidhalter/jedi-vim'
Plugin 'nvie/vim-flake8'
Plugin 'zah/nimrod.vim'
Plugin 'kovisoft/slimv'
Plugin 'jimenezrick/vimerl'
Plugin 'rstacruz/sparkup', {'rtp': 'vim'}
Plugin 'jamessan/vim-gnupg'

Plugin 'chriskempson/vim-tomorrow-theme'
Plugin 'vim-scripts/Wombat'

""""""""" Plugin settings """""""""

" airline
let g:airline_powerline_fonts=1

" indentLine
let g:indentLine_color_gui='#404040'
let g:indentLine_color_term=237

" vim-jedi
let g:jedi#force_py_version=3

" vim-flake8
let g:flake8_cmd='python3-flake8'

" slimv
let g:slimv_leader='\'
let g:paredit_leader='\'

" skuld
let g:skuld_progress_symbol="✓"
let g:skuld_squash_symbol="✗"

" Goyo
function! s:goyo_enter()
    NumbersDisable
    set norelativenumber
endfunction

function! s:goyo_leave()
    set relativenumber
    NumbersEnable
endfunction

autocmd User GoyoEnter nested call <SID>goyo_enter()
autocmd User GoyoLeave nested call <SID>goyo_leave()

""""""""" End of plugin settings """""""""

call vundle#end()

" UI options
set visualbell
set mouse=a
set laststatus=2
"set statusline=%(%F%(\ [%Y%M]%)%)%<%=%(\ %l.%02c/%L\ (%p%%)\ %)
set wildmenu
set pastetoggle=<F3>

function! ChangeCursorLine()
    if has("gui_running")
        set cursorline
        hi CursorLine guibg=Grey30
        hi CursorColumn guibg=Grey30
    endif
endfunction

" It won't work if I set these directly, so I used an event callback instead
autocmd! ColorScheme * call ChangeCursorLine()

let s:paths = substitute(escape(&runtimepath, ' '), '\(,\|$\)', '/**\1', 'g')
let s:colorscheme_file = fnamemodify(findfile('Tomorrow-Night.vim', s:paths), ':p')
if filereadable(s:colorscheme_file)
    colorscheme Tomorrow-Night
endif

if has("gui_running")
    if MySys() == "linux"
        set gfn=Inconsolata\ for\ Powerline\ 13
    elseif MySys() == "windows"
        set gfn=Inconsolata:h13
    endif
    set guioptions=aegit
endif

" Editing options
set shiftwidth=4
set tabstop=4
set expandtab
set smarttab
set cindent
set autoindent
set scrolloff=7
set ignorecase
set incsearch
set hlsearch
set showmatch
set fileencoding=utf-8
set fileencodings=utf-8,gbk,big5,shift-jis,euc-kr,latin-1
set foldmethod=marker
set nowrap

" Smarter foldtext
function! SmarterFoldText()
    let text = foldtext()
    let idx = match(text, "^+-\\+[ \t]*[0-9]\\+.\\+:[ \t]*$")
    if idx >= 0
        let line = getline(v:foldstart + 1)
        return text . line . " "
    else
        return text
    endif
endfunction

set foldtext=SmarterFoldText()

" Smarter <C-]>
function! JumpToDef()
    if exists("*GotoDefinition_" . &filetype)
        call GotoDefinition_{&filetype}()
    else
        exe "normal! \<C-]>"
    endif
endf

nnoremap <C-]> :call JumpToDef()<cr>

" Misc options
filetype on
filetype plugin on
filetype indent on
syntax on
set nu
set backupdir=~/.vim_tmp,.
set directory=~/.vim_tmp,.
set undodir=~/.vim_tmp,.
let g:lisp_rainbow=1

" Key mappings
let mapleader=","
let g:mapleader=","

noremap <C-j> <C-W>j
noremap <C-k> <C-W>k
noremap <C-h> <C-W>h
noremap <C-l> <C-W>l

noremap H ^
noremap L $

noremap <leader>tn :tabnew %<cr>
noremap <leader>te :tabedit 
noremap <leader>tc :tabclose<cr>
noremap <leader>tm :tabmove 
noremap <leader>to :tabonly<cr>
noremap <M-1> 1gt
noremap <M-2> 2gt
noremap <M-3> 3gt
noremap <M-4> 4gt
noremap <M-5> 5gt
noremap <M-6> 6gt
noremap <M-7> 7gt
noremap <M-8> 8gt
noremap <M-9> 9gt
noremap <M-0> 10gt

noremap <leader>t2 :set shiftwidth=2<cr>
noremap <leader>t4 :set shiftwidth=4<cr>

noremap <leader>hl :set hlsearch<cr>
noremap <leader>nl :nohl<cr>

noremap <leader>cw :cw<cr>
noremap <leader>cn :cn<cr>
noremap <leader>cp :cp<cr>

noremap <leader>y "+y
noremap <leader>p "+p
noremap <leader>P "+P
noremap <leader>x "+x
noremap <leader>d "+d

noremap <leader>ve :vsplit $MYVIMRC<cr>
noremap <leader>vs :source $MYVIMRC<cr>

nnoremap <leader>gw :GrepWR<cr>
nnoremap <leader>gr :GrepR 

inoremap <C-c> <esc>

" vim-ctrlp-cmdpalette
noremap <leader>/ :CtrlPCmdPalette<cr>

" Custom commands
command! -nargs=1 GrepR  execute 'silent grep! -R <args> .' | copen
command! -nargs=0 GrepWR execute 'silent grep! -R '.expand('<cword>').' .' | copen

