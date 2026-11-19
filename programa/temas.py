"""Tema claro e tema escuro da janela.

O tema inicial é o mesmo do Windows (Configurações > Personalização > Cores),
ou o que o usuário escolheu no botão do rodapé (fica salvo junto com o idioma).
"""
import ctypes
import tkinter as tk
from tkinter import ttk

import idiomas

TEMAS = ('claro', 'escuro')

CORES = {
    'claro': {
        'fundo': None,              # None = cor padrão do Windows
        'texto': None,
        'texto_fraco': '#555555',
        'link': '#0b5cd5',
        'erro_texto': '#b42318',
        'ok_texto': '#1a7f37',
        'campo': 'SystemWindow',
        'campo_texto': 'SystemWindowText',
        'resetado_fundo': '#d6f5d6', 'resetado_texto': '#14532d',
        'diferente_fundo': '#fff4ce',
        'aviso_fundo': '#fff4ce', 'aviso_texto': '#5c4400', 'aviso_borda': '#e0c060',
        'aviso_saves': '#9a5b00',
    },
    'escuro': {
        'fundo': '#202124',
        'texto': '#e8eaed',
        'texto_fraco': '#a0a4aa',
        'link': '#8ab4f8',
        'erro_texto': '#ff8a80',
        'ok_texto': '#7ee2a8',
        'campo': '#2b2d31',
        'campo_texto': '#e8eaed',
        'botao': '#3a3d42', 'botao_hover': '#4a4e55', 'botao_pressionado': '#55595f',
        'borda': '#4a4d52',
        'selecao': '#2f5d8a',
        'cabecalho': '#33363b',
        'resetado_fundo': '#1e4229', 'resetado_texto': '#a6e8b6',
        'diferente_fundo': '#4d4214',
        'aviso_fundo': '#3d3410', 'aviso_texto': '#ffe08a', 'aviso_borda': '#7a6420',
        'aviso_saves': '#ffb454',
    },
}

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


def aplicar(raiz):
    """Aplica as cores do tema atual nos estilos ttk e nas opções padrão do Tk.

    Chame antes de criar os widgets (a janela é reconstruída ao trocar de tema)."""
    estilo = ttk.Style(raiz)
    c = CORES[_atual]
    if _atual == 'claro':
        estilo.theme_use('vista' if 'vista' in estilo.theme_names() else 'clam')
        raiz.configure(bg='SystemButtonFace')
    else:
        estilo.theme_use('clam')
        fundo, texto = c['fundo'], c['texto']
        estilo.configure('.', background=fundo, foreground=texto, fieldbackground=c['campo'],
                         bordercolor=c['borda'], darkcolor=fundo, lightcolor=fundo, troughcolor=fundo,
                         selectbackground=c['selecao'], selectforeground=texto, insertcolor=texto,
                         focuscolor=c['botao'])
        estilo.configure('TButton', background=c['botao'], foreground=texto, bordercolor=c['borda'],
                         lightcolor=c['botao'], darkcolor=c['botao'], padding=(10, 4))
        estilo.map('TButton',
                   background=[('disabled', fundo), ('pressed', c['botao_pressionado']),
                               ('active', c['botao_hover'])],
                   foreground=[('disabled', c['texto_fraco'])],
                   lightcolor=[('active', c['botao_hover'])], darkcolor=[('active', c['botao_hover'])])
        estilo.configure('TCombobox', fieldbackground=c['campo'], background=c['botao'], foreground=texto,
                         arrowcolor=texto, bordercolor=c['borda'], lightcolor=c['campo'], darkcolor=c['campo'])
        estilo.map('TCombobox',
                   fieldbackground=[('readonly', c['campo'])], foreground=[('readonly', texto)],
                   selectbackground=[('readonly', c['campo'])], selectforeground=[('readonly', texto)],
                   background=[('active', c['botao_hover'])])
        # No tema 'clam', o círculo é 'indicatorbackground' e a bolinha marcada é 'indicatorforeground'.
        estilo.configure('TRadiobutton', background=fundo, foreground=texto, indicatorbackground=c['campo'],
                         indicatorforeground=c['campo'], upperbordercolor=c['borda'], lowerbordercolor=c['borda'])
        estilo.map('TRadiobutton',
                   foreground=[('disabled', c['texto_fraco'])],
                   indicatorforeground=[('selected', '#8ab4f8')],
                   indicatorbackground=[('disabled', fundo)],
                   background=[('active', fundo)])
        estilo.configure('Treeview', background=c['campo'], fieldbackground=c['campo'], foreground=texto,
                         bordercolor=c['borda'], lightcolor=c['campo'], darkcolor=c['campo'])
        estilo.map('Treeview', background=[('selected', c['selecao'])], foreground=[('selected', texto)])
        estilo.configure('Treeview.Heading', background=c['cabecalho'], foreground=texto,
                         bordercolor=c['borda'], lightcolor=c['cabecalho'], darkcolor=c['cabecalho'])
        estilo.map('Treeview.Heading', background=[('active', c['botao_hover'])])
        estilo.configure('TScrollbar', background=c['botao'], troughcolor=fundo, arrowcolor=texto,
                         bordercolor=c['borda'], lightcolor=c['botao'], darkcolor=c['botao'])
        estilo.map('TScrollbar', background=[('active', c['botao_hover'])])
        estilo.configure('TSeparator', background=c['borda'])
        raiz.configure(bg=fundo)
    estilo.configure('Fraco.TLabel', foreground=c['texto_fraco'])
    estilo.configure('Link.TLabel', foreground=c['link'], font=('Segoe UI', 9, 'underline'))
    estilo.configure('Negrito.TLabel', font=('Segoe UI', 9, 'bold'))
    estilo.configure('Titulo.TLabel', font=('Segoe UI', 12, 'bold'))
    # Lista que abre ao clicar numa caixa de opções (Combobox)
    raiz.option_add('*TCombobox*Listbox.background', c['campo'])
    raiz.option_add('*TCombobox*Listbox.foreground', c['campo_texto'])
    raiz.option_add('*TCombobox*Listbox.selectBackground', c.get('selecao', 'SystemHighlight'))
    raiz.option_add('*TCombobox*Listbox.selectForeground', c.get('texto') or 'SystemHighlightText')


def preparar_janela(janela):
    """Cor de fundo e barra de título (escura no tema escuro) de uma janela."""
    if _atual == 'escuro':
        janela.configure(bg=cor('fundo'))
    else:
        janela.configure(bg='SystemButtonFace')
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
    rotulo = tk.Label(pai, **opcoes)
    if _atual == 'escuro' and 'bg' not in opcoes:
        rotulo.configure(bg=cor('fundo'))
    return rotulo
