"""Tema claro e tema escuro da janela (visual minimalista).

Tons neutros + UMA cor de destaque (verde) para "o que fazer agora" e um tom
quente (laranja) só para "Apoiar o projeto".

O tema inicial é o mesmo do Windows (Configurações > Personalização > Cores),
ou o que o usuário escolheu no topo da janela (fica salvo junto com o idioma).
"""
import ctypes
import tkinter as tk
from tkinter import ttk

import idiomas

TEMAS = ('claro', 'escuro')
FONTE = 'Segoe UI'

CORES = {
    'claro': {
        'fundo': '#f6f6f4', 'sup': '#ffffff', 'borda': '#e6e6e2',
        'texto': '#1f2328', 'fraco': '#6b7280', 'fraquinho': '#a3a8b0',
        'destaque': '#2f7d5b', 'destaque_suave': '#e9f3ee', 'destaque_texto': '#ffffff',
        'destaque_hover': '#286b4e',
        'aviso': '#a15c07', 'aviso_suave': '#fdf3e2', 'aviso_borda': '#ecd2a8',
        'erro': '#b42318', 'erro_suave': '#fdecea',
        'trilho': '#ececea',
        'quente': '#c2620a', 'quente_suave': '#fdf1e3', 'quente_borda': '#f3d3ad', 'quente_hover': '#a9550a',
        'hover': '#f0f0ec', 'selecao': '#dcebe3',
        'diferente_fundo': '#fdf3e2',
    },
    'escuro': {
        'fundo': '#121314', 'sup': '#1a1c1e', 'borda': '#2b2e32',
        'texto': '#e8eaed', 'fraco': '#9aa0a6', 'fraquinho': '#5f646b',
        'destaque': '#5cbf8c', 'destaque_suave': '#1b2a23', 'destaque_texto': '#0f1a14',
        'destaque_hover': '#6fcc9b',
        'aviso': '#e0a84a', 'aviso_suave': '#2a2215', 'aviso_borda': '#4d3b1c',
        'erro': '#ff8a80', 'erro_suave': '#2d1a19',
        'trilho': '#26292d',
        'quente': '#f0a050', 'quente_suave': '#2b2016', 'quente_borda': '#5a3d1f', 'quente_hover': '#f5b26f',
        'hover': '#222528', 'selecao': '#21352b',
        'diferente_fundo': '#3a2f17',
    },
}
# nomes antigos, usados em algumas janelas
for _c in CORES.values():
    _c.update({'texto_fraco': _c['fraco'], 'link': _c['fraco'], 'erro_texto': _c['erro'],
               'ok_texto': _c['destaque'], 'aviso_saves': _c['aviso'], 'aviso_texto': _c['aviso'],
               'aviso_fundo': _c['aviso_suave'], 'campo': _c['sup'], 'campo_texto': _c['texto']})

_atual = 'claro'


def atual():
    return _atual


def cor(nome):
    return CORES[_atual].get(nome)


def tema_do_windows():
    """'escuro' se o Windows estiver no modo escuro para aplicativos, senão 'claro'."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as chave:
            valor, _ = winreg.QueryValueEx(chave, 'AppsUseLightTheme')
        return 'claro' if valor else 'escuro'
    except OSError:
        return 'claro'


def iniciar():
    global _atual
    escolhido = idiomas.ler_config().get('tema')
    _atual = escolhido if escolhido in TEMAS else tema_do_windows()


def definir(nome, salvar=True):
    global _atual
    _atual = nome if nome in TEMAS else 'claro'
    if salvar:
        idiomas.salvar_config(tema=_atual)


ESCALA = 1.0   # 1.0 = 100% no Windows; 1.25 = 125% etc. (medida em medir())


def medir(raiz):
    """Mede o zoom do Windows, para as imagens e tamanhos acompanharem as letras."""
    global ESCALA
    try:
        ESCALA = max(1.0, raiz.winfo_fpixels('1i') / 96)
    except tk.TclError:
        ESCALA = 1.0


def px(n):
    """Tamanho em pixels já com o zoom do Windows."""
    return int(round(n * ESCALA))


def fonte(tamanho=10, *estilos):
    return (FONTE, tamanho, *estilos)


def aplicar(raiz):
    """Aplica as cores do tema atual nos estilos ttk e nas opções padrão do Tk.

    Chame antes de criar os widgets (a janela é reconstruída ao trocar de tema)."""
    medir(raiz)
    estilo = ttk.Style(raiz)
    c = CORES[_atual]
    estilo.theme_use('clam')
    fundo, texto, sup, borda = c['fundo'], c['texto'], c['sup'], c['borda']
    estilo.configure('.', background=fundo, foreground=texto, fieldbackground=sup, font=fonte(10),
                     bordercolor=borda, darkcolor=fundo, lightcolor=fundo, troughcolor=fundo,
                     selectbackground=c['selecao'], selectforeground=texto, insertcolor=texto,
                     focuscolor=fundo)
    estilo.configure('TFrame', background=fundo)
    estilo.configure('Sup.TFrame', background=sup)
    estilo.configure('TLabel', background=fundo, foreground=texto)

    # Botões: neutro (contorno), principal (verde) e quente (Apoiar)
    def botao(nome, bg, fg, hover, borda_bt, negrito=False, pad=(14, 7)):
        estilo.configure(nome, background=bg, foreground=fg, bordercolor=borda_bt, lightcolor=bg, darkcolor=bg,
                         padding=pad, relief='flat', focusthickness=0,
                         font=fonte(10, 'bold') if negrito else fonte(10))
        estilo.map(nome,
                   background=[('disabled', fundo), ('pressed', hover), ('active', hover)],
                   foreground=[('disabled', c['fraquinho'])],
                   bordercolor=[('disabled', borda), ('active', borda_bt if bg != sup else c['fraquinho'])],
                   lightcolor=[('active', hover), ('pressed', hover)],
                   darkcolor=[('active', hover), ('pressed', hover)])
    botao('TButton', sup, texto, c['hover'], borda)
    botao('Primario.TButton', c['destaque'], c['destaque_texto'], c['destaque_hover'], c['destaque'], True)
    botao('Grande.TButton', c['destaque'], c['destaque_texto'], c['destaque_hover'], c['destaque'], True,
          pad=(22, 10))
    botao('Quente.TButton', c['quente'], '#ffffff' if _atual == 'claro' else '#1a1208', c['quente_hover'],
          c['quente'], True, pad=(12, 5))
    botao('Aviso.TButton', c['aviso'], '#ffffff' if _atual == 'claro' else '#1a1208', c['aviso'], c['aviso'], True)

    estilo.configure('TCombobox', fieldbackground=sup, background=sup, foreground=texto, arrowcolor=c['fraco'],
                     bordercolor=borda, lightcolor=sup, darkcolor=sup, padding=4)
    estilo.map('TCombobox',
               fieldbackground=[('readonly', sup)], foreground=[('readonly', texto)],
               selectbackground=[('readonly', sup)], selectforeground=[('readonly', texto)],
               background=[('active', c['hover'])], bordercolor=[('focus', c['fraquinho'])])
    estilo.configure('TRadiobutton', background=fundo, foreground=texto, indicatorbackground=sup,
                     indicatorforeground=sup, upperbordercolor=c['fraquinho'], lowerbordercolor=c['fraquinho'],
                     indicatormargin=(0, 0, 6, 0))
    estilo.map('TRadiobutton',
               foreground=[('disabled', c['fraquinho'])],
               indicatorforeground=[('selected', c['destaque'])],
               indicatorbackground=[('disabled', fundo)],
               background=[('active', fundo)])
    estilo.configure('Sup.TRadiobutton', background=sup)
    estilo.map('Sup.TRadiobutton', background=[('active', sup)])
    estilo.configure('Treeview', background=sup, fieldbackground=sup, foreground=texto, rowheight=24,
                     bordercolor=borda, lightcolor=sup, darkcolor=sup)
    estilo.map('Treeview', background=[('selected', c['selecao'])], foreground=[('selected', texto)])
    estilo.configure('Treeview.Heading', background=fundo, foreground=c['fraco'], relief='flat',
                     bordercolor=borda, lightcolor=fundo, darkcolor=fundo, font=fonte(9, 'bold'), padding=(6, 4))
    estilo.map('Treeview.Heading', background=[('active', c['hover'])])
    estilo.configure('TScrollbar', background=c['trilho'], troughcolor=fundo, arrowcolor=c['fraco'],
                     bordercolor=fundo, lightcolor=c['trilho'], darkcolor=c['trilho'], gripcount=0, arrowsize=12)
    estilo.map('TScrollbar', background=[('active', c['fraquinho'])])
    estilo.configure('TSeparator', background=borda)
    estilo.configure('TEntry', fieldbackground=sup, foreground=texto, bordercolor=borda, lightcolor=sup,
                     darkcolor=sup, padding=5)

    estilo.configure('Fraco.TLabel', foreground=c['fraco'])
    estilo.configure('Fraquinho.TLabel', foreground=c['fraquinho'], font=fonte(9))
    estilo.configure('Link.TLabel', foreground=c['fraco'], font=fonte(10, 'underline'))
    estilo.configure('Negrito.TLabel', font=fonte(10, 'bold'))
    estilo.configure('Titulo.TLabel', font=fonte(14, 'bold'))
    estilo.configure('Sup.TLabel', background=sup)
    estilo.configure('SupFraco.TLabel', background=sup, foreground=c['fraco'])
    # Lista que abre ao clicar numa caixa de opções (Combobox)
    raiz.option_add('*TCombobox*Listbox.background', sup)
    raiz.option_add('*TCombobox*Listbox.foreground', texto)
    raiz.option_add('*TCombobox*Listbox.selectBackground', c['selecao'])
    raiz.option_add('*TCombobox*Listbox.selectForeground', texto)
    raiz.option_add('*TCombobox*Listbox.font', fonte(10))
    raiz.option_add('*Menu.background', sup)
    raiz.option_add('*Menu.foreground', texto)
    raiz.option_add('*Menu.activeBackground', c['selecao'])
    raiz.option_add('*Menu.activeForeground', texto)
    raiz.option_add('*Menu.font', fonte(10))
    raiz.configure(bg=fundo)


def preparar_janela(janela):
    """Cor de fundo e barra de título (escura no tema escuro) de uma janela."""
    janela.configure(bg=cor('fundo'))
    barra_de_titulo(janela)


def barra_de_titulo(janela):
    """Pede ao Windows 10/11 a barra de título escura ou clara."""
    try:
        janela.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(janela.winfo_id())
        valor = ctypes.c_int(1 if _atual == 'escuro' else 0)
        for atributo in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 11 / Windows 10 antigo)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, atributo, ctypes.byref(valor),
                                                          ctypes.sizeof(valor)) == 0:
                break
    except Exception:
        pass


def label_tk(pai, **opcoes):
    """tk.Label com as cores do tema (para os rótulos coloridos que não são ttk)."""
    opcoes.setdefault('bg', cor('fundo'))
    opcoes.setdefault('fg', cor('texto'))
    opcoes.setdefault('font', fonte(10))
    return tk.Label(pai, **opcoes)
