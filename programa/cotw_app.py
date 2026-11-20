"""Janela do ResetMissionsCOTW - Reset de Missões por Mapa (theHunter: Call of the Wild).

Visual em 4 passos numerados (escolher o save, backup completo, marcar os mapas, resetar).
Os textos ficam em idiomas.py (português, inglês e espanhol); as cores, em temas.py;
as peças desenhadas (caixinhas, círculos, barrinhas), em componentes.py.
"""
import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import atualizacao
import componentes as comp
import cotw_core as core
import diagnostico
import idiomas
import registro
import temas
from idiomas import t
from temas import px

VERSAO = '0.9.8 (Beta)'
NOME_DO_PROGRAMA = 'ResetMissionsCOTW'
TITULO = 'ResetMissionsCOTW (Beta)'
AUTOR = 'Sheeerpha'
PLATAFORMAS = ('Steam', 'Epic', 'Outra')  # 'Outra' só aparece se houver save de pasta desconhecida

# Links de doação. Deixe '' para o botão aparecer como "em breve".
LINK_BUYMEACOFFEE = 'https://buymeacoffee.com/sheeerpha'
LINK_LIVEPIX = 'https://livepix.gg/sherpa'
# Link do repositório no GitHub. '' = "será adicionado em breve".
LINK_GITHUB = 'https://github.com/Sheeerpha/ResetMissionsCOTW'
URL_PROTECAO_RANSOMWARE = 'windowsdefender://RansomwareProtection'
# Easter egg do rodapé: amigos que ajudaram com testes, feedbacks e sugestões
AMIGOS = ('Sr.ª V.', 'F. M.', 'B. Z.')
CORACAO = '#e0475b'


def caminho_do_programa():
    if getattr(sys, 'frozen', False):  # rodando como .exe
        return sys.executable
    return os.path.abspath(sys.argv[0])


def caminho_recurso(nome):
    """Arquivo que vai junto com o programa (dentro do .exe, ou ao lado do .py)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nome)


def abrir_link(link):
    """Abre o link no navegador padrão."""
    import webbrowser
    webbrowser.open(link)


def nome_plataforma(plat):
    return t('plat_outra') if plat == 'Outra' else plat


def id_curto(texto):
    """76561198000000000 -> 7656…0000 (o suficiente para reconhecer a conta)."""
    return f'{texto[:4]}…{texto[-4:]}' if len(texto) > 12 else texto


def juntar_nomes(nomes):
    """['A', 'B', 'C'] -> 'A, B e C' (com o 'e' do idioma)."""
    nomes = list(nomes)
    if len(nomes) <= 1:
        return ''.join(nomes)
    return ', '.join(nomes[:-1]) + t('conjuncao_e') + nomes[-1]


def quando_relativo(dt):
    hora = f'{dt:%H:%M}'
    hoje = datetime.date.today()
    if dt.date() == hoje:
        return t('hoje_as', hora=hora)
    if dt.date() == hoje - datetime.timedelta(days=1):
        return t('ontem_as', hora=hora)
    return t('dia_as', data=idiomas.data(dt), hora=hora)


def rotulo(pai, texto='', estilo='texto', tamanho=10, negrito=False, fundo=None, **opcoes):
    """tk.Label com as cores do tema. estilo: 'texto', 'fraco', 'fraquinho', 'destaque', 'aviso', 'erro'."""
    cor = temas.cor(estilo) if estilo != 'texto' else temas.cor('texto')
    opcoes.setdefault('anchor', 'w')
    return tk.Label(pai, text=texto, bg=fundo or temas.cor('fundo'), fg=cor, bd=0, padx=0, pady=0,
                    font=temas.fonte(tamanho, 'bold') if negrito else temas.fonte(tamanho), **opcoes)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        temas.medir(self)
        try:
            self.iconbitmap(default=caminho_recurso('icone.ico'))   # ícone de todas as janelas
        except tk.TclError:
            pass
        larg = min(px(1000), self.winfo_screenwidth() - px(40))
        alt = min(px(740), self.winfo_screenheight() - px(90))
        self.geometry(f'{larg}x{alt}')
        self.minsize(min(px(820), larg), min(px(560), alt))
        self.raiz = core.pasta_do_programa_padrao()
        self.saves = []
        self.save_atual = None
        self.saves_visiveis = []
        self.mapas = {}
        self.bloqueado = False
        self.verificacao = None          # último resultado da "Verificação antes de começar"
        self.avisos_discretos = []       # avisos que não atrapalham (limpeza de backups, sobras...)
        self.onedrive_fechado = None     # caminho do OneDrive, se a verificação o fechou (para reabrir)
        self.trocar_aberto = False       # painel "Trocar" (plataforma e save) aberto
        self.atualizacao = None          # (tag, link) se houver versão nova no GitHub
        self._agendados = []
        self._montar()
        self._agendados.append(self.after(100, self.iniciar))

    def report_callback_exception(self, tipo, erro, tb):
        """Qualquer erro inesperado num botão vai para o log (e aparece na janela de erro)."""
        registro.log_erro('Erro inesperado na janela', erro)
        try:
            self.mostrar_erro(erro, 'Erro inesperado')
        except Exception:
            super().report_callback_exception(tipo, erro, tb)

    def destroy(self):
        for a in self._agendados:
            try:
                self.after_cancel(a)
            except tk.TclError:
                pass
        super().destroy()

    def iniciar(self):
        self.verificar_permissao()
        self.procurar_saves()
        self.arrumar_ao_abrir()
        self.verificar_agora()
        if self.verificar_atualizacao_ao_abrir:
            self._consulta = atualizacao.Consulta(VERSAO)
            self._esperar_consulta(40)
        self._agendados.append(self.after(300, self.mostrar_boas_vindas))

    # Consulta de versão nova no GitHub ao abrir (os testes desligam isto).
    verificar_atualizacao_ao_abrir = True

    def _esperar_consulta(self, vezes):
        if self._consulta.pronto:
            self.mostrar_atualizacao(self._consulta.resultado)
        elif vezes > 0:
            self._agendados.append(self.after(500, lambda: self._esperar_consulta(vezes - 1)))

    def mostrar_atualizacao(self, resultado):
        """Faixa verde "Nova versão disponível" (some se não houver versão nova)."""
        self.atualizacao = resultado
        if not resultado:
            self.faixa_update.pack_forget()
            return
        tag, link = resultado
        self.update_texto.config(text=t('update_disponivel', versao=tag))
        self.link_baixar.comando = lambda: abrir_link(link)
        antes = self.passos[0][0]
        self.faixa_update.pack(fill='x', padx=(self._recuo, 0), pady=(px(4), px(10)), before=antes)

    def ignorar_atualizacao(self):
        if self.atualizacao:
            atualizacao.ignorar(self.atualizacao[0])
        self.mostrar_atualizacao(None)

    def arrumar_ao_abrir(self):
        """Guarda sobras de restaurações anteriores e aplica os limites de backups.
        Nada disso bloqueia o programa: o que não der certo vira um aviso discreto."""
        self.avisos_discretos = []
        if self.save_atual is None or self.bloqueado:
            self.mostrar_avisos_discretos()
            return
        for r in core.recolher_sobras(self.save_atual, self.raiz):
            if r.situacao in ('guardada', 'copiada'):
                self.avisos_discretos.append(t('aviso_sobra_guardada', titulo=core.titulo_do_backup_save('sobra')))
            elif r.situacao == 'falhou':
                self.avisos_discretos.append(t('aviso_sobra_falhou'))
        falhas = core.limpar_excesso_de_backups(self.save_atual, self.raiz)
        if falhas:
            self.avisos_discretos.append(t('aviso_limpeza_falhou', n=len(falhas)))
        self.mostrar_avisos_discretos()
        self.recarregar()

    # O aviso "Antes de começar" aparece toda vez que o programa abre (os testes desligam isto).
    mostrar_aviso_ao_abrir = True

    def mostrar_boas_vindas(self):
        """Ao abrir: o aviso "Antes de começar" (sempre), depois a verificação (só se algo
        precisar ser resolvido) e por fim a introdução (só na primeira vez)."""
        if any(isinstance(w, (JanelaAviso, JanelaIntro, JanelaVerificacao)) for w in self.winfo_children()):
            return  # já está aberta
        if self.mostrar_aviso_ao_abrir:
            JanelaAviso(self, depois=self._depois_do_aviso)
        else:
            self._depois_do_aviso()

    def _depois_do_aviso(self):
        if self.verificacao is not None and self.verificacao.impedimentos:
            JanelaVerificacao(self, 'info', self.verificacao, depois=self._intro_se_primeira_vez)
        else:
            self._intro_se_primeira_vez()

    def _intro_se_primeira_vez(self):
        if not idiomas.ler_config().get('intro_vista'):
            self.mostrar_intro()

    def mostrar_intro(self):
        if not any(isinstance(w, JanelaIntro) for w in self.winfo_children()):
            JanelaIntro(self)

    # ----------------------------------------------------------------- tela
    def _montar(self):
        temas.aplicar(self)
        temas.preparar_janela(self)
        self.title(t('titulo_janela', versao=VERSAO))
        fundo = temas.cor('fundo')

        # Rodapé (empacotado primeiro, embaixo, para nunca sumir quando a janela encolhe)
        rodape = ttk.Frame(self)
        rodape.pack(side='bottom', fill='x', pady=(px(4), px(10)))
        centro = ttk.Frame(rodape)
        centro.pack()
        self.credito = rotulo(centro, t('credito', autor=AUTOR, versao=VERSAO), 'fraquinho', 9)
        self.credito.pack(side='left')
        if LINK_GITHUB:
            self.link_github = comp.Link(centro, 'GitHub', lambda: abrir_link(LINK_GITHUB), tamanho=9,
                                         cor=temas.cor('fraquinho'))
            self.link_github.pack(side='left', padx=px(18))
        self.pilula_apoio = comp.Pilula(centro, t('pilula_apoiar'), lambda: JanelaApoio(self))
        self.pilula_apoio.pack(side='left')
        # Easter egg: coraçãozinho de agradecimento aos amigos que ajudaram
        self.coracao = rotulo(centro, '♥', 'fraquinho', 10, cursor='heart')
        self.coracao.pack(side='left', padx=(px(14), 0))
        self.coracao.bind('<Enter>', lambda e: self.coracao.config(fg=CORACAO), add='+')
        self.coracao.bind('<Leave>', lambda e: self.coracao.config(fg=temas.cor('fraquinho')), add='+')
        comp.Dica(self.coracao, lambda: t('agradecimento') + '\n' + juntar_nomes(AMIGOS), atraso=150)

        # Topo: título e utilidades
        topo = ttk.Frame(self)
        topo.pack(fill='x', padx=px(28), pady=(px(14), px(6)))
        rotulo(topo, t('cabecalho').upper(), negrito=True, tamanho=12).pack(side='left')
        util = ttk.Frame(topo)
        util.pack(side='right')
        self.bt_ajuda = comp.Link(util, t('link_como_usar'), self.mostrar_intro, sublinhado=False)
        self.bt_logs = comp.Link(util, t('link_logs'), self.abrir_logs, sublinhado=False)
        self.combo_idioma = comp.SeletorIdioma(util, idiomas.IDIOMAS, idiomas.atual(), self.trocar_idioma)
        self.bt_tema = comp.Link(util, t('bt_tema_claro') if temas.atual() == 'escuro' else t('bt_tema_escuro'),
                                 self.alternar_tema, sublinhado=False)
        for w in (self.bt_ajuda, self.bt_logs, self.combo_idioma, self.bt_tema):
            w.pack(side='left', padx=(px(18), 0))

        # Coluna central com rolagem
        self.area = comp.AreaRolavel(self, largura=px(800))
        self.area.pack(fill='both', expand=True)
        col = self.area.dentro
        recuo = px(44)   # alinha com o texto dos passos (depois do círculo)

        # Faixa "Nova versão disponível" (só aparece se houver)
        c = temas.CORES[temas.atual()]
        self.faixa_update = tk.Frame(col, bg=c['destaque_suave'], highlightbackground=c['destaque'],
                                     highlightthickness=1)
        self.update_texto = rotulo(self.faixa_update, '', 'destaque', 10, negrito=True, fundo=c['destaque_suave'])
        self.update_texto.pack(side='left', padx=(px(14), px(14)), pady=px(8))
        self.link_baixar = comp.Link(self.faixa_update, t('link_baixar'), None, forte=True, fundo=c['destaque_suave'],
                                     negrito=True)
        self.link_baixar.pack(side='left')
        self.link_ignorar = comp.Link(self.faixa_update, t('link_agora_nao'), self.ignorar_atualizacao,
                                      fundo=c['destaque_suave'])
        self.link_ignorar.pack(side='left', padx=px(16))

        self.aviso_discreto = rotulo(col, '', 'aviso', 9, justify='left', anchor='w', wraplength=px(700))

        # Faixa do Windows Defender (só aparece se houver bloqueio)
        self._montar_faixa(col, recuo)

        # Os 5 passos
        self.passos = []
        self._passo_verificacao(self._passo(col, 1))
        self._passo1(self._passo(col, 2))
        self._passo2(self._passo(col, 3))
        self._passo3(self._passo(col, 4))
        self._passo4(self._passo(col, 5, ultimo=True))
        self.atualizar_passos()

    def _passo(self, col, n, ultimo=False):
        """Uma linha da sequência: círculo numerado à esquerda (com o traço que liga ao próximo)
        e o conteúdo à direita."""
        linha = ttk.Frame(col)
        linha.pack(fill='x')
        circulo = comp.Circulo(linha, n)
        circulo.grid(row=0, column=0, sticky='n')
        if not ultimo:
            tk.Frame(linha, width=max(1, px(1.5)), bg=temas.cor('borda')).grid(row=1, column=0, sticky='ns',
                                                                                pady=(px(2), 0))
        conteudo = ttk.Frame(linha)
        conteudo.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=(px(16), 0),
                      pady=(px(3), px(4) if ultimo else px(18)))
        linha.columnconfigure(1, weight=1)
        linha.rowconfigure(1, weight=1)
        self.passos.append((linha, circulo))
        return conteudo

    def _titulo_passo(self, pai, texto, extra=None):
        """Título do passo; devolve a linha do título (para pôr links à direita)."""
        f = ttk.Frame(pai)
        f.pack(fill='x')
        rotulo(f, texto.upper(), negrito=True, tamanho=11).pack(side='left')
        if extra:
            rotulo(f, extra, 'fraco', 10).pack(side='left', padx=(px(8), 0))
        return f

    def _montar_faixa(self, col, recuo):
        c = temas.CORES[temas.atual()]
        bg = c['aviso_suave']
        self.faixa = tk.Frame(col, bg=bg, highlightbackground=c['aviso_borda'], highlightthickness=1)
        icone = comp.Circulo(self.faixa, '!', fundo=bg, tam=px(30))
        icone.definir('aviso')
        icone.grid(row=0, column=0, rowspan=3, sticky='n', padx=(px(16), px(12)), pady=px(14))
        self.faixa_titulo = rotulo(self.faixa, '', negrito=True, tamanho=10, fundo=bg, anchor='w', justify='left')
        self.faixa_titulo.grid(row=0, column=1, sticky='w', pady=(px(14), 0), padx=(0, px(16)))
        self.faixa_texto = rotulo(self.faixa, '', 'fraco', 10, fundo=bg, anchor='w', justify='left',
                                  wraplength=px(620))
        self.faixa_texto.grid(row=1, column=1, sticky='w', pady=(px(3), 0), padx=(0, px(16)))
        bts = tk.Frame(self.faixa, bg=bg)
        bts.grid(row=2, column=1, sticky='w', pady=(px(10), px(14)))
        self.botoes_cfa = [ttk.Button(bts, text=t('bt_como_liberar'), style='Primario.TButton',
                                      command=self.mostrar_passo_a_passo)]
        for bt in self.botoes_cfa:
            bt.pack(side='left', padx=(0, px(10)))
        self.bt_testar_de_novo = ttk.Button(bts, text=t('bt_testar_de_novo'), command=self.testar_de_novo)
        self.bt_testar_de_novo.pack(side='left')
        self.faixa.columnconfigure(1, weight=1)
        self._recuo = recuo

    # ---- passo 1: verificação antes de começar
    def _passo_verificacao(self, p):
        self._titulo_passo(p, t('passo_verif_titulo'))
        self.linha_status = ttk.Frame(p)
        self.linha_status.pack(fill='x', pady=(px(4), 0))
        self.status_verif = rotulo(self.linha_status, '', 'destaque', 10, cursor='hand2', wraplength=px(520),
                                   justify='left')
        self.status_verif.pack(side='left')
        self.status_verif.bind('<Button-1>', lambda e: self.abrir_verificacao())
        self.link_detalhes = comp.Link(self.linha_status, t('link_detalhes'), self.abrir_verificacao)
        self.link_detalhes.pack(side='left', padx=(px(14), 0))
        self.link_verificar = comp.Link(self.linha_status, t('link_verificar_de_novo'), self.verificar_de_novo)
        self.link_verificar.pack(side='left', padx=(px(14), 0))

    # ---- passo 2: save
    def _passo1(self, p):
        self._titulo_passo(p, t('passo1_titulo'))
        linha = ttk.Frame(p)
        linha.pack(fill='x', pady=(px(4), 0))
        self.p1_resumo = rotulo(linha, '', 'fraco', 10, anchor='w', justify='left', wraplength=px(560))
        self.p1_resumo.pack(side='left')
        self.link_trocar = comp.Link(linha, t('link_trocar'), self.alternar_trocar)
        self.link_escolher_pasta = comp.Link(linha, t('link_escolher_pasta'), self.escolher_pasta)
        self.link_trocar.pack(side='left', padx=(px(14), 0))
        self.link_escolher_pasta.pack(side='left', padx=(px(14), 0))
        self.aviso_saves = rotulo(p, '', 'aviso', 9, anchor='w', justify='left', wraplength=px(680))
        self.p1_fim = ttk.Frame(p)          # marca o fim do passo (o painel "Trocar" entra antes dela)
        self.p1_fim.pack(fill='x')

        # Painel "Trocar": plataforma e save daquela plataforma
        sup = temas.cor('sup')
        self.painel_trocar = tk.Frame(p, bg=sup, highlightbackground=temas.cor('borda'), highlightthickness=1)
        rotulo(self.painel_trocar, t('rotulo_plataforma'), 'fraco', 10, fundo=sup).grid(
            row=0, column=0, sticky='w', padx=(px(14), px(10)), pady=(px(10), px(4)))
        radios = tk.Frame(self.painel_trocar, bg=sup)
        radios.grid(row=0, column=1, sticky='w', pady=(px(10), px(4)))
        self.var_plataforma = tk.StringVar()
        self.radios = {}
        for plat in PLATAFORMAS:
            self.radios[plat] = ttk.Radiobutton(radios, text=nome_plataforma(plat), value=plat, style='Sup.TRadiobutton',
                                                variable=self.var_plataforma, command=self.trocar_plataforma)
        rotulo(self.painel_trocar, t('rotulo_save'), 'fraco', 10, fundo=sup).grid(
            row=1, column=0, sticky='w', padx=(px(14), px(10)), pady=(px(4), px(12)))
        self.combo = ttk.Combobox(self.painel_trocar, state='readonly')
        self.combo.grid(row=1, column=1, sticky='ew', pady=(px(4), px(12)))
        self.combo.bind('<<ComboboxSelected>>', lambda e: self.escolher_save(self.combo.current()))
        self.link_procurar = comp.Link(self.painel_trocar, t('link_procurar'), self.procurar_saves, fundo=sup)
        self.link_procurar.grid(row=1, column=2, sticky='w', padx=(px(12), px(14)), pady=(px(4), px(12)))
        self.painel_trocar.columnconfigure(1, weight=1)

    # ---- passo 3: backup do save completo
    def _passo2(self, p):
        self._titulo_passo(p, t('passo2_titulo'), t('recomendado'))
        self.p2_sub = rotulo(p, t('passo2_sub'), 'fraco', 10, anchor='w', justify='left', wraplength=px(680))
        self.p2_sub.pack(fill='x', pady=(px(3), 0))
        self.p2_linha = ttk.Frame(p)
        self.p2_resumo = rotulo(self.p2_linha, '', 'fraco', 10, anchor='w', justify='left', wraplength=px(440))
        self.p2_resumo.pack(side='left')
        self.bt_novo_backup = ttk.Button(self.p2_linha, text=t('bt_novo_backup'), command=self.pedir_backup_save)
        self.bt_novo_backup.pack(side='left', padx=(px(16), 0))
        self.link_fazer_outro = self.bt_novo_backup     # nome antigo
        self.bt_backup_save = ttk.Button(p, text=t('bt_backup_save'), style='Primario.TButton',
                                         command=self.pedir_backup_save)
        self.p2_fim = ttk.Frame(p)
        self.p2_fim.pack(fill='x')

    # ---- passo 4: mapas
    def _passo3(self, p):
        cab = self._titulo_passo(p, t('passo3_titulo'))
        self.link_desmarcar = comp.Link(cab, t('link_desmarcar_todos'), lambda: self.lista.selection_set(()),
                                        tamanho=9)
        self.link_desmarcar.pack(side='right')
        self.link_marcar = comp.Link(cab, t('link_marcar_todos'), self.marcar_todos, tamanho=9)
        self.link_marcar.pack(side='right', padx=(0, px(14)))
        self.p3_sub = rotulo(p, t('passo3_sub'), 'fraco', 10, anchor='w', justify='left', wraplength=px(680))
        self.p3_sub.pack(fill='x', pady=(px(3), 0))
        self.lista = ListaMapas(p, self.ao_marcar)
        self.lista.pack(fill='x', pady=(px(10), 0))

    # ---- passo 5: resetar (e o quadro "Precisa desfazer?")
    def _passo4(self, p):
        self._titulo_passo(p, t('passo4_titulo'))
        acao = ttk.Frame(p)
        acao.pack(fill='x', pady=(px(10), 0))
        self.bt_reset = ttk.Button(acao, text=t('bt_resetar_nenhum'), style='Grande.TButton', command=self.resetar)
        self.bt_reset.pack(side='left')
        self.p4_resumo = rotulo(acao, '', 'fraco', 10, anchor='w', justify='left', wraplength=px(500))
        self.p4_resumo.pack(side='left', padx=(px(16), 0), fill='x')

        c = temas.CORES[temas.atual()]
        sup, fundo = c['sup'], c['fundo']
        quadro = tk.Frame(p, bg=sup, highlightbackground=c['borda'], highlightthickness=1)
        quadro.pack(fill='x', pady=(px(22), 0))
        cab = tk.Frame(quadro, bg=sup)
        cab.pack(fill='x', padx=px(16), pady=(px(14), px(2)))
        rotulo(cab, '↩  ' + t('desfazer').upper(), negrito=True, tamanho=10, fundo=sup).pack(side='left')
        self.link_como_desfazer = comp.Link(cab, t('link_como_desfazer'), self.mostrar_como_desfazer, forte=True,
                                            fundo=sup, tamanho=9)
        self.link_como_desfazer.pack(side='right')
        rotulo(quadro, t('desfazer_sub'), 'fraco', 9, fundo=sup, wraplength=px(680), justify='left').pack(
            fill='x', padx=px(16))
        opcoes = tk.Frame(quadro, bg=sup)
        opcoes.pack(fill='x', padx=px(16), pady=(px(10), px(4)))
        opcoes.columnconfigure(0, weight=1, uniform='op')
        opcoes.columnconfigure(1, weight=1, uniform='op')
        itens = (('bt_restaurar', t('bt_restaurar_missoes'), t('desc_restaurar_missoes'), self.janela_restaurar),
                 ('bt_restaurar_save', t('bt_restaurar_save_curto'), t('desc_restaurar_save'),
                  self.janela_restaurar_save))
        for coluna, (nome, texto, descricao, comando) in enumerate(itens):
            caixa = tk.Frame(opcoes, bg=fundo, highlightbackground=c['borda'], highlightthickness=1)
            caixa.grid(row=0, column=coluna, sticky='nsew', padx=(0, px(10)) if coluna == 0 else 0)
            bt = ttk.Button(caixa, text=texto, command=comando)
            bt.pack(anchor='w', padx=px(12), pady=(px(12), px(6)))
            rotulo(caixa, descricao, 'fraco', 9, fundo=fundo, wraplength=px(310), justify='left').pack(
                fill='x', padx=px(12), pady=(0, px(12)))
            setattr(self, nome, bt)
        rodape = tk.Frame(quadro, bg=sup)
        rodape.pack(fill='x', padx=px(16), pady=(px(6), px(12)))
        self.info = rotulo(rodape, '', 'fraquinho', 9, fundo=sup, wraplength=px(540), justify='left')
        self.info.pack(side='left')
        self.link_pasta_backups = comp.Link(rodape, t('link_pasta_backups'), self.abrir_pasta_backups, tamanho=9,
                                            fundo=sup)
        self.link_pasta_backups.pack(side='right')

    # --------------------------------------------------- estado dos passos
    def _estado_verificacao(self):
        r = self.verificacao
        if self.bloqueado or (r is not None and r.impedimentos):
            return 'aviso'
        return 'feito' if r is not None else 'atual'

    def atualizar_passos(self):
        """Marca cada passo como feito (✓), atual (verde) ou esperando, e ajusta os textos."""
        s = self.save_atual
        circ = [c for _, c in self.passos]
        circ[0].definir(self._estado_verificacao())
        # passo 2: save
        if s is None:
            circ[1].definir('atual')
            self.p1_resumo.config(text=t('nao_encontrei_save'), fg=temas.cor('aviso'))
        else:
            circ[1].definir('feito')
            plat = s.plataforma if s.plataforma in ('Steam', 'Epic') else t('plat_outra')
            self.p1_resumo.config(text=t('passo1_resumo', plat=plat, id=id_curto(s.id), quando=s.quando_jogado()),
                                  fg=temas.cor('fraco'))
        if self.saves:
            if not self.link_trocar.winfo_manager():
                self.link_trocar.pack(side='left', padx=(px(14), 0), before=self.link_escolher_pasta)
        else:
            self.link_trocar.pack_forget()
        # passo 3: backup completo
        ultimo = None
        if s is not None and not self.bloqueado:
            try:
                backups = core.listar_backups_save(s, self.raiz)
            except OSError:
                backups = []
            ultimo = backups[0] if backups else None
        if ultimo is not None:
            dias = (datetime.datetime.now() - ultimo.quando).days
            velho = dias >= core.DIAS_PROTECAO_SAVE
            circ[2].definir('atual' if velho else 'feito')
            self.p2_sub.pack_forget()
            self.bt_backup_save.pack_forget()
            if velho:
                self.p2_resumo.config(text=t('passo2_velho', dias=dias, tamanho=idiomas.tamanho(ultimo.tamanho)),
                                      fg=temas.cor('aviso'))
            else:
                self.p2_resumo.config(text=t('passo2_feito', quando=quando_relativo(ultimo.quando),
                                             tamanho=idiomas.tamanho(ultimo.tamanho)), fg=temas.cor('fraco'))
            self.bt_novo_backup.config(style='Primario.TButton' if velho else 'TButton')
            self.p2_linha.pack(fill='x', pady=(px(6), 0), before=self.p2_fim)
        else:
            circ[2].definir('espera' if s is None or self.bloqueado else 'atual')
            self.p2_linha.pack_forget()
            self.p2_sub.pack(fill='x', pady=(px(3), 0), before=self.p2_fim)
            self.bt_backup_save.pack(anchor='w', pady=(px(10), 0), before=self.p2_fim)
        # passos 4 e 5
        marcados = self.marcados()
        if s is None or self.bloqueado:
            circ[3].definir('espera')
            circ[4].definir('espera')
        else:
            circ[3].definir('feito' if marcados else 'atual')
            circ[4].definir('atual' if marcados else 'espera')
        n = len(marcados)
        if n == 0:
            self.bt_reset.config(text=t('bt_resetar_nenhum'), style='TButton')
            self.p4_resumo.config(text=t('passo4_nenhum'))
        else:
            self.bt_reset.config(text=t('bt_resetar_um') if n == 1 else t('bt_resetar_varios', n=n),
                                 style='Grande.TButton')
            self.p4_resumo.config(text=t('passo4_resumo', nomes=juntar_nomes(core.nome_do_mapa(k) for k in marcados)))

    def marcados(self):
        """Chaves marcadas na lista que ainda não foram resetadas."""
        out = []
        for i in self.lista.selection():
            k = int(i)
            if not (self.mapas.get(k) and self.mapas[k].resetado):
                out.append(k)
        return out

    def marcar_todos(self):
        self.lista.selection_set([i for i in self.lista.get_children()
                                  if not (self.mapas.get(int(i)) and self.mapas[int(i)].resetado)])

    def mostrar_como_desfazer(self):
        if not any(isinstance(w, JanelaComoDesfazer) for w in self.winfo_children()):
            JanelaComoDesfazer(self)

    def ao_marcar(self):
        self.atualizar_passos()

    def alternar_trocar(self, abrir=None):
        self.trocar_aberto = (not self.trocar_aberto) if abrir is None else abrir
        if self.trocar_aberto:
            self.painel_trocar.pack(fill='x', pady=(px(10), 0), before=self.p1_fim)
        else:
            self.painel_trocar.pack_forget()

    def trocar_idioma(self, cod):
        if cod == idiomas.atual():
            return
        idiomas.definir(cod)
        idiomas.salvar_preferencia(cod)
        self.reconstruir()

    def alternar_tema(self):
        temas.definir('claro' if temas.atual() == 'escuro' else 'escuro')
        self.reconstruir()

    def reconstruir(self):
        """Monta a janela de novo (novo idioma ou tema), mantendo o save escolhido."""
        save, saves, marcados = self.save_atual, self.saves, self.lista.selection()
        trocar = self.trocar_aberto
        for w in self.winfo_children():
            w.destroy()
        self._montar()
        self.verificar_permissao()
        self.saves = saves
        if save is not None and save in saves:
            self.mostrar_save(save)
        else:
            self.procurar_saves()
        self.lista.selection_set([i for i in marcados if self.lista.exists(i)])
        if trocar:
            self.alternar_trocar(True)
        if self.verificacao is not None:
            self.mostrar_status_verificacao(self.verificacao)
        self.mostrar_avisos_discretos()
        self.mostrar_atualizacao(self.atualizacao)

    # --------------------------------------------------- verificação e avisos
    def verificar_agora(self):
        self.verificacao = diagnostico.verificar(self.save_atual, self.raiz)
        self.mostrar_status_verificacao(self.verificacao)
        return self.verificacao

    def verificar_de_novo(self):
        """Link "Verificar de novo" do passo 1."""
        self.verificar_permissao()
        self.verificar_agora()

    def mostrar_status_verificacao(self, r):
        if self.bloqueado:
            texto, cor = t('status_bloqueado'), temas.cor('aviso')
        elif r.impedimentos:
            texto, cor = t('status_impede', n=len(r.impedimentos)), temas.cor('erro')
        elif r.avisos:
            texto, cor = t('status_avisos', n=len(r.avisos)), temas.cor('aviso')
        else:
            texto, cor = t('status_ok'), temas.cor('destaque')
        self.status_verif.config(text=texto, fg=cor)
        self.passos[0][1].definir(self._estado_verificacao())

    def abrir_verificacao(self):
        if not any(isinstance(w, JanelaVerificacao) for w in self.winfo_children()):
            JanelaVerificacao(self, 'info', self.verificar_agora())

    def checar_antes(self, parent=None):
        """Antes de alterar o save: se algo impede, mostra a verificação; senão segue sem incomodar."""
        r = self.verificar_agora()
        if not r.impedimentos:
            return True
        janela = JanelaVerificacao(self, 'antes', r)
        self.wait_window(janela)
        return janela.continuar

    def mostrar_avisos_discretos(self):
        if self.avisos_discretos:
            self.aviso_discreto.config(text='\n'.join(dict.fromkeys(self.avisos_discretos)))
            self.aviso_discreto.pack(fill='x', padx=(self._recuo, 0), pady=(0, px(10)), before=self.passos[0][0])
        else:
            self.aviso_discreto.pack_forget()

    def avisar_resultado(self, resultado):
        """Avisos discretos depois de uma operação que deu certo."""
        falhas = getattr(resultado, 'falhas_limpeza', None)
        if falhas:
            self.avisos_discretos.append(t('aviso_limpeza_falhou', n=len(falhas)))
        if getattr(resultado, 'sobra_nao_apagada', None):
            self.avisos_discretos.append(t('aviso_sobra_falhou'))
        self.mostrar_avisos_discretos()
        if self.onedrive_fechado and not diagnostico.esta_aberto('onedrive.exe'):
            if messagebox.askyesno(TITULO, t('perguntar_reabrir_onedrive')):
                diagnostico.reabrir_onedrive(self.onedrive_fechado)
            self.onedrive_fechado = None

    def abrir_logs(self):
        pasta = registro.pasta()
        if os.path.isdir(pasta):
            os.startfile(pasta)
        else:
            messagebox.showinfo(TITULO, t('sem_logs'))

    def mostrar_erro(self, erro, contexto, prefixo=None, parent=None):
        """Janela de erro com a causa encontrada (quando der) e o botão "Copiar detalhes"."""
        registro.log_erro(contexto, erro)
        if isinstance(erro, core.ErroSave):
            mensagem = str(erro)
        else:
            mensagem = t('erro_ao_gravar', erro=erro)
        if prefixo:
            mensagem = t(prefixo, texto=mensagem)
        causa = None
        if isinstance(erro, OSError) or isinstance(getattr(erro, 'original', None), OSError):
            causa = diagnostico.descobrir_causa(erro, getattr(erro, 'caminho', None), caminho_do_programa())
        return JanelaErro(self, mensagem, causa, erro, contexto, parent=parent)

    # --------------------------------------------- Acesso Controlado a Pastas
    def verificar_permissao(self):
        erro = core.testar_gravacao(self.raiz)
        self.bloqueado = erro is not None
        if erro is None:
            self.faixa.pack_forget()
            core.migrar_pasta_antiga(self.raiz)
        else:
            registro.log_erro('Não foi possível gravar na pasta do programa', erro)
            causa = diagnostico.descobrir_causa(erro, self.raiz, caminho_do_programa())
            if causa.cfa_confirmado:
                titulo, texto = t('faixa_titulo_cfa'), t('faixa_bloqueio')
            else:
                titulo, texto = t('faixa_titulo_erro'), t('faixa_erro_causa', causa=' '.join(causa.textos))
            # o botão "como liberar" só faz sentido se o Acesso Controlado está ligado
            cfa = causa.cfa_confirmado or core.acesso_controlado_ligado() is True
            for bt in self.botoes_cfa:
                if cfa:
                    bt.pack(side='left', padx=(0, px(10)), before=self.bt_testar_de_novo)
                else:
                    bt.pack_forget()
            self.faixa_titulo.config(text=titulo.upper())
            self.faixa_texto.config(text=texto)
            self.faixa.pack(fill='x', padx=(self._recuo, 0), pady=(px(4), px(16)), before=self.passos[0][0])
        estado = ['disabled'] if self.bloqueado else ['!disabled']
        for bt in (self.bt_reset, self.bt_restaurar, self.bt_backup_save, self.bt_restaurar_save,
                   self.bt_novo_backup):
            bt.state(estado)
        self.atualizar_passos()
        if self.verificacao is not None:
            self.mostrar_status_verificacao(self.verificacao)
        return not self.bloqueado

    def mostrar_passo_a_passo(self):
        if not any(isinstance(w, JanelaDefender) for w in self.winfo_children()):
            JanelaDefender(self)

    def abrir_seguranca(self):
        try:
            os.startfile(URL_PROTECAO_RANSOMWARE)
        except OSError:
            messagebox.showinfo(TITULO, t('nao_abriu_seguranca'))

    def copiar_caminho(self):
        self.clipboard_clear()
        self.clipboard_append(caminho_do_programa())

    def testar_de_novo(self, parent=None):
        if self.verificar_permissao():
            self.recarregar()
            messagebox.showinfo(TITULO, t('tudo_certo'), parent=parent)
            return True
        messagebox.showwarning(TITULO, t('ainda_bloqueado', caminho=caminho_do_programa()), parent=parent)
        return False

    # ---------------------------------------------------------------- saves
    @staticmethod
    def plataforma_de(s):
        return s.plataforma if s.plataforma in ('Steam', 'Epic') else 'Outra'

    def saves_da(self, plat):
        return [s for s in self.saves if self.plataforma_de(s) == plat]

    def procurar_saves(self):
        # já vem do save jogado mais recentemente para o mais antigo
        self.saves = core.encontrar_saves()
        if not self.saves:
            self.atualizar_plataformas()
            self.var_plataforma.set('')
            self.saves_visiveis = []
            self.combo['values'] = ()
            self.combo.set('')
            self.save_atual = None
            self.mostrar_mapas(None)
            self.atualizar_aviso_saves()
            self.info.config(text='')
            self.atualizar_passos()
            return
        self.mostrar_save(self.saves[0])

    def atualizar_plataformas(self):
        for plat in PLATAFORMAS:
            rb = self.radios[plat]
            n = len(self.saves_da(plat))
            if plat == 'Outra' and n == 0:
                rb.pack_forget()
                continue
            nome = nome_plataforma(plat)
            if n == 0:
                rb.config(text=t('radio_nenhum', plat=nome))
                rb.state(['disabled'])
            else:
                rb.config(text=t('radio_um', plat=nome) if n == 1 else t('radio_varios', plat=nome, n=n))
                rb.state(['!disabled'])
            rb.pack(side='left', padx=(0, px(16)))

    def mostrar_save(self, save):
        """Seleciona a plataforma do save, preenche a lista e escolhe esse save."""
        self.atualizar_plataformas()
        self.var_plataforma.set(self.plataforma_de(save))
        self.saves_visiveis = self.saves_da(self.plataforma_de(save))
        self.combo['values'] = [s.descricao() for s in self.saves_visiveis]
        i = self.saves_visiveis.index(save)
        self.combo.current(i)
        self.escolher_save(i)

    def trocar_plataforma(self):
        lista = self.saves_da(self.var_plataforma.get())
        if lista:
            self.mostrar_save(lista[0])  # o mais recente daquela plataforma

    def atualizar_aviso_saves(self):
        plat = self.var_plataforma.get()
        n = len(self.saves_visiveis)
        outras = [p for p in ('Steam', 'Epic') if p != plat and self.saves_da(p)]
        textos = []
        if n > 1:
            textos.append(t('aviso_varios_saves', n=n, plat=nome_plataforma(plat)))
        if outras:
            textos.append(t('aviso_outra_plataforma', plat=outras[0]))
        if textos:
            self.aviso_saves.config(text='\n'.join(textos))
            self.aviso_saves.pack(fill='x', pady=(px(6), 0), before=self.p1_fim)
            if n > 1 and not self.trocar_aberto:
                self.alternar_trocar(True)   # com mais de um save, já mostra onde trocar
        else:
            self.aviso_saves.pack_forget()

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title=t('titulo_escolher_pasta'))
        if not pasta:
            return
        pasta = os.path.normpath(pasta)
        if not os.path.isfile(os.path.join(pasta, core.NOME_ARQUIVO)):
            messagebox.showerror(TITULO, t('pasta_sem_arquivo', arquivo=core.NOME_ARQUIVO))
            return
        if os.path.basename(os.path.dirname(pasta)).lower() == 'slots':
            messagebox.showerror(TITULO, t('pasta_slots'))
            return
        iguais = [x for x in self.saves if os.path.normcase(x.pasta) == os.path.normcase(pasta)]
        if iguais:
            s = iguais[0]
        else:
            s = core.descrever_pasta(pasta)
            self.saves.append(s)
        self.mostrar_save(s)

    def escolher_save(self, i):
        vis = self.saves_visiveis
        self.save_atual = vis[i] if 0 <= i < len(vis) else None
        self.atualizar_aviso_saves()
        self.lista.selection_set(())
        self.recarregar()

    def recarregar(self):
        s = self.save_atual
        if s is None:
            self.mostrar_mapas(None)
            self.atualizar_passos()
            return
        try:
            mapas = core.mapas_para_mostrar(s, self.raiz)
        except (OSError, core.ErroSave) as e:
            self.mostrar_mapas(None)
            self.info.config(text=t('nao_li_save', erro=e), fg=temas.cor('erro'))
            self.atualizar_passos()
            return
        self.mostrar_mapas(mapas)
        partes = []
        if s.steam_cloud:
            partes.append(t('steam_cloud_ativo'))
        n = len(core.listar_backups(s, self.raiz))
        partes.append(t('n_backups', n=n) if n else t('nenhum_backup_ainda'))
        n_save = len(core.listar_backups_save(s, self.raiz))
        partes.append(t('n_backups_save', n=n_save) if n_save else t('nenhum_backup_save'))
        if n or n_save:
            partes.append(t('espaco_backups', tamanho=idiomas.tamanho(core.tamanho_dos_backups(s, self.raiz))))
        self.info.config(text='  ·  '.join(partes), fg=temas.cor('fraquinho'))
        self.atualizar_passos()

    def mostrar_mapas(self, mapas):
        self.mapas = {m.chave: m for m in mapas or []}
        if mapas is None:
            vazio = t('passo3_sem_save')
        else:
            vazio = t('passo3_vazio')
        self.lista.mostrar(mapas or [], vazio)

    # ---------------------------------------------------------------- ações
    def _pode_alterar(self, parent=None):
        if not self.verificar_permissao():
            messagebox.showwarning(TITULO, t('aviso_usar_faixa'), parent=parent)
            return False
        return self.checar_antes(parent)

    # Confirmação, "Pronto!" e apelido do backup em janelas próprias (os testes usam as caixinhas simples).
    janelas_visuais = True

    def resetar(self):
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'))
            return
        sel = [int(i) for i in self.lista.selection()]
        if not sel:
            messagebox.showinfo(TITULO, t('selecione_mapa'))
            return
        ja = [k for k in sel if self.mapas.get(k) and self.mapas[k].resetado]
        sel = [k for k in sel if k not in ja]
        if not sel:
            messagebox.showinfo(TITULO, t('ja_resetados'))
            return
        if not self._pode_alterar():
            return
        nomes = '\n'.join(f'  • {core.nome_do_mapa(k)}' for k in sel)
        detalhes = '\n'.join(t('linha_detalhe', nome=m.nome, c=m.concluidas, a=m.em_andamento, t=m.total)
                             for m in (self.mapas[k] for k in sel))
        if ja:
            detalhes += '\n\n' + t('ignorados', nomes=', '.join(core.nome_do_mapa(k) for k in ja))
        if not core.tem_backup_save(self.save_atual, self.raiz):
            resposta = messagebox.askyesnocancel(TITULO, t('sugerir_backup_save'), icon='warning')
            if resposta is None:
                return
            if resposta and not self.fazer_backup_save(perguntar_ok=False, ja_verificado=True):
                return
        if self.janelas_visuais:
            janela = JanelaConfirmarReset(self, [self.mapas[k] for k in sel], ja)
            self.wait_window(janela)
            confirmado = janela.confirmado
        else:
            confirmado = messagebox.askyesno(TITULO, t('confirmar_reset', save=self.save_atual.nome_curto(),
                                                       detalhes=detalhes), icon='warning')
        if not confirmado:
            return
        registro.log(f'Reset pedido: {", ".join(core.nome_do_mapa(k) for k in sel)}')
        try:
            b = core.resetar_mapas(self.save_atual, sel, self.raiz)
        except (OSError, core.ErroSave) as e:
            self.mostrar_erro(e, 'Reset de missões', prefixo='nao_foi_possivel_resetar')
            self.recarregar()
            return
        registro.log('Reset concluído.')
        self.lista.selection_set(())
        self.recarregar()
        self.avisar_resultado(b)
        for k in sel:
            if self.lista.exists(str(k)):
                self.lista.see(str(k))
        if self.janelas_visuais:
            JanelaPronto(self, sel)
        else:
            messagebox.showinfo(TITULO, t('reset_ok', nomes=nomes))

    def abrir_backups(self):
        if self.save_atual is not None:
            pasta = core.pasta_backups_do_save(self.save_atual, self.raiz)
            if os.path.isdir(pasta):
                os.startfile(pasta)
                return
        messagebox.showinfo(TITULO, t('sem_backups'))

    def abrir_pasta_backups(self):
        """Pasta deste save no programa (tem Backups_MISSIONS e Backups_SAVE)."""
        if self.save_atual is not None:
            pasta = os.path.dirname(core.pasta_backups_do_save(self.save_atual, self.raiz))
            if os.path.isdir(pasta):
                os.startfile(pasta)
                return
        messagebox.showinfo(TITULO, t('sem_backups'))

    def janela_restaurar(self):
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'))
            return
        backups = core.listar_backups(self.save_atual, self.raiz)
        if not backups:
            messagebox.showinfo(TITULO, t('sem_backups_explica'))
            return
        JanelaRestaurar(self, backups)

    # ------------------------------------------------------- save completo
    def pedir_backup_save(self, parent=None):
        """Botões de backup completo: pergunta um apelido opcional e faz o backup."""
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'), parent=parent)
            return False
        apelido = ''
        if self.janelas_visuais:
            janela = JanelaApelido(self, parent=parent)
            self.wait_window(janela)
            if janela.apelido is None:
                return False
            apelido = janela.apelido
        return self.fazer_backup_save(parent=parent, apelido=apelido)

    def fazer_backup_save(self, perguntar_ok=True, parent=None, ja_verificado=False, apelido=''):
        """Copia a pasta inteira do save. Devolve True se deu certo."""
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'), parent=parent)
            return False
        if not ja_verificado and not self._pode_alterar(parent=parent):
            return False
        self.config(cursor='watch')
        self.update_idletasks()
        try:
            b = core.fazer_backup_save_completo(self.save_atual, self.raiz, apelido=apelido)
        except (OSError, core.ErroSave) as e:
            self.config(cursor='')
            self.mostrar_erro(e, 'Backup do save completo', prefixo='nao_foi_possivel_backup_save', parent=parent)
            return False
        finally:
            self.config(cursor='')
        self.recarregar()
        self.avisar_resultado(b)
        if perguntar_ok:
            messagebox.showinfo(TITULO, t('backup_save_ok', arquivos=b.arquivos, tamanho=idiomas.tamanho(b.tamanho),
                                          pasta=b.pasta), parent=parent)
        return True

    def abrir_backups_save(self):
        if self.save_atual is not None:
            pasta = core.pasta_backups_save_completo(self.save_atual, self.raiz)
            if os.path.isdir(pasta):
                os.startfile(pasta)
                return
        messagebox.showinfo(TITULO, t('sem_backups_save', bt=idiomas.sem_icone(t('bt_backup_save'))))

    def janela_restaurar_save(self):
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'))
            return
        backups = core.listar_backups_save(self.save_atual, self.raiz)
        if not backups:
            messagebox.showinfo(TITULO, t('sem_backups_save', bt=idiomas.sem_icone(t('bt_backup_save'))))
            return
        JanelaRestaurarSave(self, backups)


class ListaMapas(tk.Frame):
    """Lista de mapas em duas colunas: caixinha, nome, barrinha de progresso e contagem.

    Funciona parecido com a lista antiga (Treeview): selection_set, selection, item,
    exists, see e get_children usam a chave do mapa como texto ('21')."""

    def __init__(self, pai, ao_mudar):
        c = temas.CORES[temas.atual()]
        super().__init__(pai, bg=c['sup'], highlightbackground=c['borda'], highlightthickness=1)
        self.ao_mudar = ao_mudar
        self.linhas = {}
        self.ordem = []
        self._sel = []
        self.vazio = None
        self.columnconfigure(0, weight=1, uniform='col')
        self.columnconfigure(1, weight=1, uniform='col')

    # --- como o Treeview
    def get_children(self, _=''):
        return tuple(self.ordem)

    def exists(self, iid):
        return str(iid) in self.linhas

    def selection(self):
        return tuple(self._sel)

    def selection_set(self, itens):
        if isinstance(itens, (str, int)):
            itens = (itens,)
        self._sel = [str(i) for i in itens if str(i) in self.linhas]
        for iid, linha in self.linhas.items():
            linha.desenhar(iid in self._sel)
        if self.ao_mudar:
            self.ao_mudar()

    def item(self, iid):
        linha = self.linhas[str(iid)]
        m = linha.mapa
        nome = f'{m.nome}   —   {t("sufixo_resetado")}' if m.resetado else m.nome
        return {'values': [nome, m.concluidas, m.em_andamento, m.total],
                'tags': ('resetado',) if m.resetado else ()}

    def see(self, iid):
        linha = self.linhas.get(str(iid))
        area = self._area()
        if linha is not None and area is not None:
            area.mostrar(linha)

    def _area(self):
        w = self.master
        while w is not None and not isinstance(w, comp.AreaRolavel):
            w = w.master
        return w

    # --- desenho
    def mostrar(self, mapas, texto_vazio=''):
        for w in self.winfo_children():
            w.destroy()
        self.linhas, self.ordem = {}, []
        antes = self._sel
        self._sel = []
        if not mapas:
            self.vazio = tk.Label(self, text=texto_vazio, bg=temas.cor('sup'), fg=temas.cor('fraco'),
                                  font=temas.fonte(10), pady=px(14))
            self.vazio.grid(row=0, column=0, columnspan=2)
            return
        metade = (len(mapas) + 1) // 2
        for i, m in enumerate(mapas):
            iid = str(m.chave)
            linha = LinhaMapa(self, iid, m, self.alternar)
            coluna, fila = (0, i) if i < metade else (1, i - metade)
            linha.grid(row=fila, column=coluna, sticky='ew',
                       pady=(px(6) if fila == 0 else 0, px(6) if fila == metade - 1 else 0))
            self.linhas[iid] = linha
            self.ordem.append(iid)
        self._sel = [i for i in antes if i in self.linhas]
        for iid, linha in self.linhas.items():
            linha.desenhar(iid in self._sel)

    def alternar(self, iid):
        if iid in self._sel:
            self._sel.remove(iid)
        else:
            self._sel.append(iid)
        self.linhas[iid].desenhar(iid in self._sel)
        if self.ao_mudar:
            self.ao_mudar()


class LinhaMapa(tk.Frame):
    def __init__(self, lista, iid, mapa, ao_clicar):
        self.sup = temas.cor('sup')
        super().__init__(lista, bg=self.sup, cursor='hand2')
        self.iid, self.mapa, self.ao_clicar = iid, mapa, ao_clicar
        self.marcada = None
        self._hover = False
        self.caixa = tk.Label(self, bd=0, bg=self.sup)
        self.nome = tk.Label(self, text=mapa.nome, anchor='w', bd=0, bg=self.sup, font=temas.fonte(10))
        self.barra = tk.Label(self, bd=0, bg=self.sup)
        self.n = tk.Label(self, anchor='e', bd=0, bg=self.sup, font=temas.fonte(9))
        self.caixa.grid(row=0, column=0, padx=(px(14), px(9)), pady=px(4))
        self.nome.grid(row=0, column=1, sticky='ew')
        if mapa.resetado:   # sem barrinha: o texto "↺ resetado" usa o espaço dela
            self.n.grid(row=0, column=2, columnspan=2, sticky='e', padx=(px(6), px(14)))
        else:
            self.barra.grid(row=0, column=2, padx=(px(6), px(4)))
            self.n.grid(row=0, column=3, sticky='e', padx=(0, px(14)))
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, minsize=px(56))
        for w in (self, self.caixa, self.nome, self.barra, self.n):
            if not mapa.resetado:
                w.bind('<Button-1>', lambda e: self.ao_clicar(self.iid))
            w.bind('<Enter>', lambda e: self._passar(True))
            w.bind('<Leave>', lambda e: self._passar(False))
        if mapa.resetado:
            self.configure(cursor='')
            for w in (self.caixa, self.nome, self.barra, self.n):
                w.configure(cursor='')
        comp.Dica(self.nome, self.dica)

    def dica(self):
        m = self.mapa
        if m.resetado:
            return t('dica_mapa_resetado', t=m.total)
        return t('dica_mapa', c=m.concluidas, a=m.em_andamento, t=m.total)

    def _passar(self, dentro):
        if self.mapa.resetado or dentro == self._hover:
            return
        self._hover = dentro
        self.desenhar(self.marcada, forcar=True)

    def desenhar(self, marcada, forcar=False):
        if marcada == self.marcada and not forcar:
            return
        self.marcada = marcada
        c = temas.CORES[temas.atual()]
        bg = c['hover'] if self._hover else c['sup']
        for w in (self, self.caixa, self.nome, self.barra, self.n):
            w.configure(bg=bg)
        m = self.mapa
        if m.resetado:
            self.caixa.configure(image=comp.img_vazia(self, bg, px(16), px(16)))
            self.nome.configure(fg=c['fraco'], font=temas.fonte(10))
            self.barra.configure(image=comp.img_barra(self, 0, c['fraquinho'], bg, largura=px(52)))
            self.n.configure(text=t('mapa_resetado_curto'), fg=c['destaque'])
            return
        fracao = m.concluidas / m.total if m.total else 0
        self.caixa.configure(image=comp.img_caixa(self, bool(marcada), bg))
        self.nome.configure(fg=c['texto'], font=temas.fonte(10, 'bold') if marcada else temas.fonte(10))
        self.barra.configure(image=comp.img_barra(self, fracao, c['destaque'] if marcada else c['fraquinho'], bg,
                                                  largura=px(52)))
        self.n.configure(text=f'{m.concluidas}/{m.total}', fg=c['fraco'])


class Janela(tk.Toplevel):
    """Base das janelas: cores do tema, presa na frente da principal, centralizada."""

    def __init__(self, app, titulo, parent=None, redimensionar=False):
        super().__init__(parent or app)
        self.app = app
        self.title(titulo)
        self.resizable(redimensionar, redimensionar)
        temas.preparar_janela(self)
        self.transient(parent or app)
        self._grab_anterior = self.grab_current()
        _modal(self)

    def destroy(self):
        anterior = getattr(self, '_grab_anterior', None)
        super().destroy()
        if anterior is not None and anterior is not self:
            try:
                if anterior.winfo_exists():
                    anterior.grab_set()   # devolve o foco preso para a janela de trás
            except tk.TclError:
                pass


class JanelaRestaurar(Janela):
    """Lista os backups e mostra, para o escolhido, como cada mapa ficaria."""

    def __init__(self, app, backups):
        super().__init__(app, t('rest_titulo'), redimensionar=True)
        self.backups = backups
        self.cache = {}
        self.geometry(f'{px(920)}x{px(620)}')
        self.minsize(px(760), px(480))

        corpo = ttk.Frame(self, padding=px(20))
        corpo.pack(fill='both', expand=True)
        rotulo(corpo, t('rest_titulo').upper(), negrito=True, tamanho=13).pack(anchor='w')
        rotulo(corpo, t('rest_intro'), 'fraco', 10, wraplength=px(860), justify='left').pack(
            fill='x', pady=(px(6), px(12)))

        rotulo(corpo, t('rest_passo1'), negrito=True).pack(fill='x')
        cima = ttk.Frame(corpo)
        cima.pack(fill='x', pady=px(6))
        self.lista = ttk.Treeview(cima, columns=('data', 'hora', 'oque'), show='headings',
                                  selectmode='browse', height=6)
        for col, chave, larg, anc in [('data', 'col_data', 100, 'center'), ('hora', 'col_hora', 80, 'center'),
                                      ('oque', 'col_motivo', 600, 'w')]:
            self.lista.heading(col, text=t(chave))
            self.lista.column(col, width=px(larg), anchor=anc, stretch=(col == 'oque'))
        self.lista.tag_configure('original', background=temas.cor('destaque_suave'),
                                 foreground=temas.cor('destaque'), font=temas.fonte(10, 'bold'))
        # O backup original (🔒, de antes do primeiro uso) fica sempre em cima, destacado.
        ordem = sorted(range(len(backups)), key=lambda i: (not backups[i].protegido, i))
        for i in ordem:
            b = backups[i]
            if b.protegido:
                motivo, tags = f'🔒 {t("backup_original")}   ·   {b.titulo}', ('original',)
            else:
                motivo, tags = b.titulo, ()
            self.lista.insert('', 'end', iid=str(i), tags=tags,
                              values=(idiomas.data(b.quando), f'{b.quando:%H:%M:%S}', motivo))
        barra = ttk.Scrollbar(cima, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side='left', fill='x', expand=True)
        barra.pack(side='left', fill='y')
        self.lista.bind('<<TreeviewSelect>>', lambda e: self.mostrar_detalhes())
        rotulo(corpo, t('rest_original_nota'), 'destaque', 9, wraplength=px(860), justify='left').pack(fill='x')
        rotulo(corpo, t('limite_backups', n=core.LIMITE_MISSOES), 'fraquinho', 9).pack(fill='x')

        rotulo(corpo, t('rest_passo2'), negrito=True).pack(fill='x', pady=(px(12), 0))
        baixo = ttk.Frame(corpo)
        baixo.pack(fill='both', expand=True, pady=px(6))
        self.det = ttk.Treeview(baixo, columns=('mapa', 'agora', 'backup'), show='headings', selectmode='none')
        for col, chave, larg, anc in [('mapa', 'col_mapa', 300, 'w'), ('agora', 'col_agora', 250, 'center'),
                                      ('backup', 'col_depois', 250, 'center')]:
            self.det.heading(col, text=t(chave))
            self.det.column(col, width=px(larg), anchor=anc, stretch=True)
        self.det.tag_configure('diferente', background=temas.cor('diferente_fundo'))
        barra2 = ttk.Scrollbar(baixo, orient='vertical', command=self.det.yview)
        self.det.configure(yscrollcommand=barra2.set)
        self.det.pack(side='left', fill='both', expand=True)
        barra2.pack(side='left', fill='y')
        self.resumo = ttk.Label(corpo, text='', style='Fraco.TLabel')
        self.resumo.pack(fill='x')

        bts = ttk.Frame(corpo)
        bts.pack(side='bottom', fill='x', pady=(px(12), 0), before=corpo.winfo_children()[0])
        ttk.Button(bts, text=t('bt_restaurar_este'), style='Primario.TButton', command=self.restaurar).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_pasta_backup'), command=self.abrir_pasta).pack(side='left', padx=px(8))
        ttk.Button(bts, text=t('bt_fechar'), command=self.destroy).pack(side='right')

        self.lista.selection_set('0')
        _centralizar(self, app)

    def backup_escolhido(self):
        sel = self.lista.selection()
        return self.backups[int(sel[0])] if sel else None

    @staticmethod
    def _texto(m):
        if m is None:
            return t('txt_sem_missoes')
        if m.resetado:
            return t('txt_resetado', t=m.total)
        return t('txt_progresso', c=m.concluidas, t=m.total, a=m.em_andamento)

    def mostrar_detalhes(self):
        b = self.backup_escolhido()
        self.det.delete(*self.det.get_children())
        if b is None:
            return
        if b.pasta not in self.cache:
            try:
                self.cache[b.pasta] = {m.chave: m for m in core.mapas_do_backup(b)}
            except (OSError, core.ErroSave) as e:
                self.cache[b.pasta] = None
                self.resumo.config(text=t('backup_ilegivel', erro=e))
        no_backup = self.cache[b.pasta]
        if no_backup is None:
            return
        agora = self.app.mapas
        mudam = 0
        for k in sorted(set(agora) | set(no_backup)):
            a, d = agora.get(k), no_backup.get(k)
            ta, td = self._texto(a), self._texto(d)
            diferente = ta != td
            mudam += diferente
            self.det.insert('', 'end', values=(core.nome_do_mapa(k), ta, td),
                            tags=('diferente',) if diferente else ())
        self.resumo.config(text=t('nenhum_muda') if not mudam else t('n_mudam', n=mudam))

    def abrir_pasta(self):
        b = self.backup_escolhido()
        if b and os.path.isdir(b.pasta):
            os.startfile(b.pasta)

    def restaurar(self):
        b = self.backup_escolhido()
        if b is None:
            return
        if not self.app._pode_alterar(parent=self):
            return
        if not messagebox.askyesno(TITULO, t('confirmar_restaurar', save=self.app.save_atual.nome_curto(),
                                             quando=idiomas.data_hora(b.quando, segundos=True), titulo=b.titulo),
                                   parent=self):
            return
        registro.log(f'Restaurar backup de missões: {b.pasta}')
        try:
            novo = core.restaurar_backup(self.app.save_atual, b, self.app.raiz)
        except (OSError, core.ErroSave) as e:
            self.app.mostrar_erro(e, 'Restaurar backup de missões', prefixo='nao_foi_possivel_restaurar', parent=self)
            return
        registro.log('Backup de missões restaurado.')
        self.destroy()
        self.app.recarregar()
        self.app.avisar_resultado(novo)
        messagebox.showinfo(TITULO, t('backup_restaurado'))


class JanelaRestaurarSave(Janela):
    """Lista os backups do save completo e devolve o escolhido."""

    def __init__(self, app, backups):
        super().__init__(app, t('rest_save_titulo'), redimensionar=True)
        self.backups = backups
        self.geometry(f'{px(860)}x{px(470)}')
        self.minsize(px(700), px(400))

        corpo = ttk.Frame(self, padding=px(20))
        corpo.pack(fill='both', expand=True)
        rotulo(corpo, t('rest_save_titulo').upper(), negrito=True, tamanho=13).pack(anchor='w')
        rotulo(corpo, t('rest_save_intro'), 'fraco', 10, wraplength=px(800), justify='left').pack(
            fill='x', pady=(px(6), px(12)))
        rotulo(corpo, t('rest_passo1'), negrito=True).pack(fill='x')
        meio = ttk.Frame(corpo)
        meio.pack(fill='both', expand=True, pady=px(6))
        self.lista = ttk.Treeview(meio, columns=('data', 'hora', 'oque', 'tamanho'), show='headings',
                                  selectmode='browse')
        for col, chave, larg, anc in [('data', 'col_data', 100, 'center'), ('hora', 'col_hora', 80, 'center'),
                                      ('oque', 'col_motivo', 480, 'w'), ('tamanho', 'col_tamanho', 90, 'center')]:
            self.lista.heading(col, text=t(chave))
            self.lista.column(col, width=px(larg), anchor=anc, stretch=(col == 'oque'))
        for i, b in enumerate(backups):
            motivo = f'{b.titulo}     {t("backup_protegido_save", dias=core.DIAS_PROTECAO_SAVE)}' if b.protegido else b.titulo
            self.lista.insert('', 'end', iid=str(i), values=(idiomas.data(b.quando), f'{b.quando:%H:%M:%S}',
                                                              motivo, idiomas.tamanho(b.tamanho)))
        barra = ttk.Scrollbar(meio, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side='left', fill='both', expand=True)
        barra.pack(side='left', fill='y')
        rotulo(corpo, t('limite_backups_save', n=core.LIMITE_SAVE, dias=core.DIAS_PROTECAO_SAVE), 'fraquinho', 9,
               wraplength=px(800), justify='left').pack(fill='x')

        bts = ttk.Frame(corpo)
        bts.pack(side='bottom', fill='x', pady=(px(12), 0), before=corpo.winfo_children()[0])
        ttk.Button(bts, text=t('bt_restaurar_save_este'), style='Primario.TButton',
                   command=self.restaurar).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_pasta'), command=self.app.abrir_backups_save).pack(side='left', padx=px(8))
        ttk.Button(bts, text=t('bt_fechar'), command=self.destroy).pack(side='right')
        self.lista.selection_set('0')
        _centralizar(self, app)

    def backup_escolhido(self):
        sel = self.lista.selection()
        return self.backups[int(sel[0])] if sel else None

    def restaurar(self):
        b = self.backup_escolhido()
        if b is None:
            return
        if not self.app._pode_alterar(parent=self):
            return
        if not messagebox.askyesno(TITULO, t('confirmar_restaurar_save', save=self.app.save_atual.nome_curto(),
                                             quando=idiomas.data_hora(b.quando, segundos=True), titulo=b.titulo),
                                   icon='warning', parent=self):
            return
        self.config(cursor='watch')
        self.update_idletasks()
        try:
            antes = core.restaurar_save_completo(self.app.save_atual, b, self.app.raiz)
        except (OSError, core.ErroSave) as e:
            self.config(cursor='')
            self.app.mostrar_erro(e, 'Restaurar save completo', prefixo='nao_foi_possivel_restaurar', parent=self)
            return
        self.destroy()
        self.app.recarregar()
        self.app.avisar_resultado(antes)
        messagebox.showinfo(TITULO, t('save_restaurado'))


def _linha_com_icone(pai, estado, texto, simbolo='!', largura=None, fundo=None):
    """Linha com um circulinho (✓ verde, ! amarelo ou número) e o texto ao lado."""
    linha = tk.Frame(pai, bg=fundo or temas.cor('fundo'))
    linha.pack(fill='x', pady=px(4))
    circ = comp.Circulo(linha, simbolo, fundo=fundo, tam=px(22))
    circ.definir(estado)
    circ.itemconfigure(circ._txt, font=temas.fonte(9, 'bold'))
    circ.pack(side='left', anchor='n', padx=(0, px(12)))
    rotulo(linha, texto, wraplength=largura or px(460), justify='left', fundo=fundo).pack(side='left', fill='x')
    return linha


class JanelaConfirmarReset(Janela):
    """Confirmação do reset: cada mapa com o progresso de hoje → "começa do zero"."""

    MAXIMO_LINHAS = 8

    def __init__(self, app, mapas, ignorados=()):
        n = len(mapas)
        super().__init__(app, t('conf_janela'))
        self.confirmado = False
        self.protocol('WM_DELETE_WINDOW', self.cancelar)
        c = temas.CORES[temas.atual()]
        sup = c['sup']

        corpo = ttk.Frame(self, padding=(px(26), px(22), px(26), px(18)))
        corpo.pack(fill='both', expand=True)
        cab = ttk.Frame(corpo)
        cab.pack(fill='x')
        icone = comp.Circulo(cab, '↺', tam=px(40))
        icone.definir('atual')
        icone.itemconfigure(icone._txt, font=temas.fonte(15, 'bold'))
        icone.pack(side='left', padx=(0, px(14)))
        textos = ttk.Frame(cab)
        textos.pack(side='left', fill='x')
        self.titulo = (t('conf_titulo_um') if n == 1 else t('conf_titulo_varios', n=n)).upper()
        rotulo(textos, self.titulo, negrito=True, tamanho=13).pack(anchor='w')
        rotulo(textos, t('conf_save', save=app.save_atual.nome_curto()), 'fraco', 9).pack(anchor='w')

        lista = tk.Frame(corpo, bg=sup, highlightbackground=c['borda'], highlightthickness=1)
        lista.pack(fill='x', pady=(px(16), px(4)))
        lista.columnconfigure(0, weight=1)
        for i, m in enumerate(mapas[:self.MAXIMO_LINHAS]):
            py_ = (px(10) if i == 0 else px(3), px(10) if i == min(n, self.MAXIMO_LINHAS) - 1 else px(3))
            rotulo(lista, m.nome, negrito=True, fundo=sup).grid(row=i, column=0, sticky='w', padx=(px(14), px(10)),
                                                                pady=py_)
            rotulo(lista, t('conf_hoje', c=m.concluidas, t=m.total), 'fraco', 9, fundo=sup).grid(
                row=i, column=1, sticky='e', pady=py_)
            rotulo(lista, '→', 'destaque', 11, negrito=True, fundo=sup).grid(row=i, column=2, padx=px(10), pady=py_)
            rotulo(lista, t('conf_zero'), 'destaque', 9, negrito=True, fundo=sup).grid(
                row=i, column=3, sticky='w', padx=(0, px(14)), pady=py_)
        if n > self.MAXIMO_LINHAS:
            rotulo(lista, t('conf_mais', n=n - self.MAXIMO_LINHAS), 'fraco', 9, fundo=sup).grid(
                row=self.MAXIMO_LINHAS, column=0, columnspan=4, sticky='w', padx=px(14), pady=(0, px(10)))
        if ignorados:
            rotulo(corpo, t('ignorados', nomes=', '.join(core.nome_do_mapa(k) for k in ignorados)), 'fraquinho',
                   9, wraplength=px(500), justify='left').pack(fill='x')

        outros = len([k for k in app.mapas if k not in {m.chave for m in mapas}])
        checks = ttk.Frame(corpo)
        checks.pack(fill='x', pady=(px(12), 0))
        _linha_com_icone(checks, 'feito', t('conf_outros', n=outros))
        _linha_com_icone(checks, 'feito', t('conf_backup'))
        _linha_com_icone(checks, 'aviso', t('conf_desfazer', restaurar=idiomas.sem_icone(t('bt_restaurar_missoes'))))

        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(18), 0))
        self.bt_sim = ttk.Button(bts, text=t('conf_sim_um') if n == 1 else t('conf_sim_varios', n=n),
                                 style='Primario.TButton', command=self.confirmar)
        self.bt_sim.pack(side='right')
        ttk.Button(bts, text=t('bt_cancelar'), command=self.cancelar).pack(side='right', padx=(0, px(10)))
        self.bind('<Escape>', lambda e: self.cancelar())
        _centralizar(self, app)
        self.bt_sim.focus_set()

    def confirmar(self):
        self.confirmado = True
        self.destroy()

    def cancelar(self):
        self.confirmado = False
        self.destroy()


class JanelaPronto(Janela):
    """Depois do reset: "Pronto!" e o que fazer agora."""

    def __init__(self, app, chaves):
        super().__init__(app, t('pronto_janela'))
        n = len(chaves)
        c = temas.CORES[temas.atual()]
        corpo = ttk.Frame(self, padding=(px(30), px(24), px(30), px(20)))
        corpo.pack(fill='both', expand=True)
        icone = comp.Circulo(corpo, '', tam=px(56))
        icone.definir('feito')
        icone.pack(anchor='w')
        self.titulo = (t('pronto_titulo_um') if n == 1 else t('pronto_titulo_varios', n=n)).upper()
        rotulo(corpo, self.titulo, negrito=True, tamanho=14, wraplength=px(500), justify='left').pack(
            anchor='w', pady=(px(14), px(4)))
        nomes = juntar_nomes(core.nome_do_mapa(k) for k in chaves)
        rotulo(corpo, f'{nomes}. ' + t('pronto_sub'), 'fraco', 10, wraplength=px(500), justify='left').pack(
            anchor='w')

        sup = c['sup']
        agora = tk.Frame(corpo, bg=sup, highlightbackground=c['borda'], highlightthickness=1)
        agora.pack(fill='x', pady=(px(18), 0))
        dentro = tk.Frame(agora, bg=sup)
        dentro.pack(fill='x', padx=px(16), pady=px(14))
        rotulo(dentro, t('pronto_agora').upper(), negrito=True, tamanho=9, fundo=sup).pack(anchor='w',
                                                                                          pady=(0, px(6)))
        for i, chave in enumerate(('il_abra_jogo', 'il_local', 'il_entre_mapa'), start=1):
            _linha_com_icone(dentro, 'atual' if i == 1 else 'espera', t(chave), simbolo=str(i), fundo=sup)

        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(20), 0))
        ttk.Button(bts, text=t('pronto_outros'), style='Primario.TButton', command=self.destroy).pack(side='right')
        ttk.Button(bts, text=t('pronto_desfazer'), command=self.desfazer).pack(side='left')
        _centralizar(self, app)

    def desfazer(self):
        self.destroy()
        self.app.janela_restaurar()


class JanelaApelido(Janela):
    """Antes do backup completo: um nome opcional para reconhecer o backup depois."""

    def __init__(self, app, parent=None):
        super().__init__(app, t('apelido_janela'), parent=parent)
        self.apelido = None
        self.protocol('WM_DELETE_WINDOW', self.cancelar)
        corpo = ttk.Frame(self, padding=(px(26), px(22), px(26), px(18)))
        corpo.pack(fill='both', expand=True)
        rotulo(corpo, t('apelido_titulo').upper(), negrito=True, tamanho=13).pack(anchor='w')
        rotulo(corpo, t('apelido_texto'), 'fraco', 10, wraplength=px(420), justify='left').pack(
            anchor='w', pady=(px(6), px(12)))
        self.var = tk.StringVar()
        self.var.trace_add('write', lambda *a: len(self.var.get()) > 40 and self.var.set(self.var.get()[:40]))
        self.campo = ttk.Entry(corpo, textvariable=self.var, width=46, font=temas.fonte(10))
        self.campo.pack(fill='x')
        rotulo(corpo, t('apelido_exemplo'), 'fraquinho', 9).pack(anchor='w', pady=(px(4), 0))
        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(18), 0))
        ttk.Button(bts, text=t('apelido_fazer'), style='Primario.TButton', command=self.ok).pack(side='right')
        ttk.Button(bts, text=t('bt_cancelar'), command=self.cancelar).pack(side='right', padx=(0, px(10)))
        self.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.cancelar())
        _centralizar(self, parent or app)
        self.campo.focus_set()

    def ok(self):
        self.apelido = self.var.get().strip()
        self.destroy()

    def cancelar(self):
        self.apelido = None
        self.destroy()


class JanelaAviso(Janela):
    """"Antes de começar": aparece toda vez que o programa abre."""

    def __init__(self, app, depois=None):
        super().__init__(app, idiomas.sem_icone(t('aviso_titulo')))
        self.depois = depois
        self.protocol('WM_DELETE_WINDOW', self.fechar)
        c = temas.CORES[temas.atual()]
        larg_texto = px(470)

        corpo = ttk.Frame(self, padding=(px(28), px(24), px(28), px(20)))
        corpo.pack(fill='both', expand=True)
        cab = ttk.Frame(corpo)
        cab.pack(fill='x')
        icone = comp.Circulo(cab, '!', tam=px(40))
        icone.definir('aviso')
        icone.itemconfigure(icone._txt, font=temas.fonte(15, 'bold'))
        icone.pack(side='left', padx=(0, px(14)))
        rotulo(cab, idiomas.sem_icone(t('aviso_titulo')).upper(), negrito=True, tamanho=14).pack(side='left')

        self.textos = []
        intro = rotulo(corpo, t('aviso_intro'), 'fraco', 10, wraplength=larg_texto + px(54), justify='left',
                       anchor='w')
        intro.pack(fill='x', pady=(px(14), px(12)))
        self.textos.append(intro.cget('text'))
        bt_backup = idiomas.sem_icone(t('bt_backup_save'))
        for estado, chave in (('feito', 'aviso_ponto_1'), ('feito', 'aviso_ponto_2'), ('aviso', 'aviso_ponto_3')):
            linha = ttk.Frame(corpo)
            linha.pack(fill='x', pady=px(5))
            circ = comp.Circulo(linha, '!', tam=px(22))
            circ.definir(estado)
            circ.itemconfigure(circ._txt, font=temas.fonte(9, 'bold'))
            circ.pack(side='left', anchor='n', padx=(0, px(12)))
            texto = t(chave, bt_backup=bt_backup) if chave == 'aviso_ponto_3' else t(chave)
            rotulo(linha, texto, wraplength=larg_texto, justify='left', anchor='w').pack(side='left', fill='x')
            self.textos.append(texto)

        # faixa quente: "é gratuito... Apoiar"
        quente = tk.Frame(corpo, bg=c['quente_suave'], highlightbackground=c['quente_borda'], highlightthickness=1)
        quente.pack(fill='x', pady=(px(16), 0))
        rotulo(quente, '☕', 'quente', 13, fundo=c['quente_suave']).pack(side='left', padx=(px(14), px(8)),
                                                                        pady=px(10))
        rotulo(quente, t('aviso_apoio'), fundo=c['quente_suave'], wraplength=px(330), justify='left',
               anchor='w').pack(side='left', fill='x', expand=True, pady=px(10))
        self.bt_apoiar = ttk.Button(quente, text=t('bt_apoiar_curto'), style='Quente.TButton',
                                    command=lambda: JanelaApoio(self.app, parent=self))
        self.bt_apoiar.pack(side='right', padx=px(12))
        self.textos.append(t('aviso_apoio'))

        if LINK_GITHUB:
            self.link_github = comp.Link(corpo, t('aviso_github'), lambda: abrir_link(LINK_GITHUB), tamanho=9)
            self.link_github.pack(anchor='w', pady=(px(14), 0))

        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(18), 0))
        ttk.Button(bts, text=t('aviso_entendi'), style='Primario.TButton', command=self.fechar).pack(side='right')
        ttk.Button(bts, text=t('bt_backup_agora'), command=self.fazer_backup).pack(side='right', padx=(0, px(10)))
        _centralizar(self, app)

    def fazer_backup(self):
        self.app.pedir_backup_save(parent=self)

    def fechar(self):
        self.destroy()
        if self.depois:
            try:
                self.app._agendados.append(self.app.after(150, self.depois))
            except tk.TclError:
                pass  # a janela principal já foi fechada


class JanelaIntro(Janela):
    """Tutorial em 7 telas, que acompanham os 5 passos da janela. Na primeira vez abre
    sozinho; depois, pelo "Como usar" do topo."""

    TOTAL = 7
    PREFIXO = 'intro'             # chaves dos textos: intro_passo_N, intro_titulo_N, intro_texto_N
    TITULO_JANELA = 'intro_titulo'

    def __init__(self, app):
        super().__init__(app, t(self.TITULO_JANELA))
        self.pagina = 1
        self.protocol('WM_DELETE_WINDOW', self.fechar)
        self.larg_il, self.alt_il = px(520), px(190)

        corpo = ttk.Frame(self, padding=(px(28), px(22), px(28), px(18)))
        corpo.pack(fill='both', expand=True)
        cima = ttk.Frame(corpo)
        cima.pack(fill='x')
        self.bt_pular = comp.Link(cima, t('intro_pular'), self.fechar, tamanho=9)
        self.bt_pular.pack(side='right')
        self.passo = rotulo(cima, '', 'destaque', 9, negrito=True)
        self.passo.pack(side='left')

        self.desenho = tk.Canvas(corpo, width=self.larg_il, height=self.alt_il, bg=temas.cor('sup'),
                                 highlightthickness=1, highlightbackground=temas.cor('borda'), bd=0)
        self.desenho.pack(pady=(px(10), px(16)))
        self.titulo = rotulo(corpo, '', negrito=True, tamanho=14, anchor='w')
        self.titulo.pack(fill='x')
        self.texto = rotulo(corpo, '', 'fraco', 10, wraplength=self.larg_il, justify='left', anchor='nw',
                            height=6)
        self.texto.pack(fill='x', pady=(px(8), px(10)))

        rodape = ttk.Frame(corpo)
        rodape.pack(fill='x', side='bottom')
        self.pontos = tk.Canvas(rodape, width=px(16) * self.TOTAL, height=px(10), bg=temas.cor('fundo'),
                                highlightthickness=0, bd=0)
        self.pontos.pack(side='left')
        self.contador = rotulo(rodape, '', 'fraquinho', 9)
        self.contador.pack(side='left', padx=(px(8), 0))
        self.bt_proximo = ttk.Button(rodape, style='Primario.TButton', command=self.proximo)
        self.bt_proximo.pack(side='right')
        self.bt_voltar = ttk.Button(rodape, text=t('intro_voltar'), command=self.voltar)
        self.bt_voltar.pack(side='right', padx=px(8))
        self.mostrar()
        _centralizar(self, app)

    def campos(self):
        return {'limite_missoes': core.LIMITE_MISSOES, 'limite_save': core.LIMITE_SAVE,
                'trocar': t('link_trocar'), 'escolher_pasta': t('link_escolher_pasta'),
                'resetado': t('mapa_resetado_curto'), 'resetar': t('passo4_titulo'),
                'restaurar': idiomas.sem_icone(t('bt_restaurar_missoes')),
                'restaurar_save': idiomas.sem_icone(t('bt_restaurar_save_curto')),
                'backup_save': idiomas.sem_icone(t('bt_backup_save')), 'ajuda': t('link_como_usar'),
                'detalhes': t('link_detalhes'), 'verificar': t('link_verificar_de_novo'),
                'como_desfazer': t('link_como_desfazer'), 'novo_backup': idiomas.sem_icone(t('bt_novo_backup')),
                'dias': core.DIAS_PROTECAO_SAVE, 'desfazer': t('desfazer')}

    def mostrar(self):
        n = self.pagina
        p = self.PREFIXO
        self.passo.config(text=t(f'{p}_passo_{n}'))
        self.titulo.config(text=t(f'{p}_titulo_{n}').upper())
        texto = idiomas.TEXTOS[idiomas.atual()][f'{p}_texto_{n}']
        self.texto.config(text=texto.format(**self.campos()))
        self.contador.config(text=t('intro_pagina', n=n, total=self.TOTAL))
        self.bt_voltar.state(['disabled'] if n == 1 else ['!disabled'])
        ultima = n == self.TOTAL
        self.bt_proximo.config(text=t(f'{p}_ultimo_botao') if ultima else t('intro_proximo'))
        if ultima:
            self.bt_pular.pack_forget()
        elif not self.bt_pular.winfo_manager():
            self.bt_pular.pack(side='right')
        # bolinhas de progresso
        self.pontos.delete('all')
        c = temas.CORES[temas.atual()]
        for i in range(self.TOTAL):
            x, y, r = px(5) + i * px(16), px(5), px(3.5) if i + 1 == n else px(3)
            cor = c['destaque'] if i + 1 == n else (c['fraco'] if i + 1 < n else c['fraquinho'])
            self.pontos.create_oval(x - r, y - r, x + r, y + r, fill=cor, outline=cor)
        Ilustracoes(self.desenho, self.larg_il, self.alt_il).pagina(p, n)

    def proximo(self):
        if self.pagina == self.TOTAL:
            self.fechar()
            return
        self.pagina += 1
        self.mostrar()

    def voltar(self):
        if self.pagina > 1:
            self.pagina -= 1
            self.mostrar()

    def fechar(self):
        idiomas.salvar_config(intro_vista=True)
        self.destroy()


class JanelaComoDesfazer(JanelaIntro):
    """Tutorial ilustrado: como restaurar as missões, o backup original 🔒 e o save completo.
    Abre pelo "Como funciona?" do quadro "Precisa desfazer?"."""

    TOTAL = 6
    PREFIXO = 'desfazer'
    TITULO_JANELA = 'desfazer_janela'

    def fechar(self):
        self.destroy()


class Ilustracoes:
    """Desenhos simples (no estilo da própria janela) do tutorial e do guia do Defender."""

    def __init__(self, canvas, largura, altura):
        self.cv, self.w, self.h = canvas, largura, altura
        self.c = temas.CORES[temas.atual()]
        self.cv.delete('all')
        self.cv.imagens = []      # guarda as imagens enquanto o desenho existir

    # --- peças
    def img(self, x, y, imagem, anchor='nw'):
        self.cv.imagens.append(imagem)
        self.cv.create_image(x, y, image=imagem, anchor=anchor)

    def texto(self, x, y, texto, cor='texto', tamanho=10, negrito=False, anchor='w', largura=None):
        opcoes = {'width': largura} if largura else {}
        return self.cv.create_text(x, y, text=texto, fill=self.c[cor], anchor=anchor,
                                   font=temas.fonte(tamanho, 'bold') if negrito else temas.fonte(tamanho), **opcoes)

    def caixa(self, x0, y0, x1, y1, fundo='sup', borda='borda', largura=1):
        return self.cv.create_rectangle(x0, y0, x1, y1, fill=self.c[fundo] if fundo else '',
                                        outline=self.c[borda] if borda else '', width=largura)

    def circulo(self, x, y, estado, numero, fundo='sup', tam=None):
        tam = tam or px(26)
        self.img(x, y, comp.img_circulo(self.cv, estado, self.c[fundo], tam))
        if estado != 'feito':
            cor = self.c['destaque_texto'] if estado == 'atual' else ('#ffffff' if estado in ('aviso', 'quente')
                                                                      else self.c['fraco'])
            self.cv.create_text(x + tam / 2, y + tam / 2, text=str(numero), fill=cor, font=temas.fonte(9, 'bold'))

    def botao(self, x, y, texto, principal=True, tamanho=10):
        f = temas.fonte(tamanho, 'bold') if principal else temas.fonte(tamanho)
        item = self.cv.create_text(0, 0, text=texto, font=f, anchor='nw')
        x0, y0, x1, y1 = self.cv.bbox(item)
        self.cv.delete(item)
        lw, lh = x1 - x0 + px(28), y1 - y0 + px(14)
        fundo = self.c['destaque'] if principal else self.c['sup']
        self.img(x, y, comp.img_ret(self.cv, lw, lh, px(6), fundo, self.c['sup'],
                                    None if principal else self.c['borda'], 1.0))
        self.cv.create_text(x + lw / 2, y + lh / 2, text=texto, font=f,
                            fill=self.c['destaque_texto'] if principal else self.c['texto'])
        return x + lw, y + lh

    def anel(self, x0, y0, x1, y1):
        """Destaque verde em volta do que deve ser clicado."""
        self.cv.create_rectangle(x0, y0, x1, y1, outline=self.c['destaque'], width=max(2, px(2)))

    def linha_mapa(self, x, y, larg, nome, c, total, marcada=False):
        self.img(x, y - px(8), comp.img_caixa(self.cv, marcada, self.c['sup']))
        self.texto(x + px(26), y, nome, negrito=marcada)
        cor = self.c['destaque'] if marcada else self.c['fraquinho']
        self.img(x + larg - px(130), y - px(2), comp.img_barra(self.cv, c / total, cor, self.c['sup']))
        self.texto(x + larg, y, f'{c}/{total}', 'fraco', 9, anchor='e')

    # --- telas do tutorial
    def pagina(self, prefixo, n):
        getattr(self, f'_{prefixo}_{n}')()

    def intro(self, n):
        self.pagina('intro', n)

    def _intro_1(self):
        w, h = self.w, self.h
        cartoes = (('Yukon Valley', False), ('Te Awaroa', True), ('Intisuyu', False))
        cw, ch, gap = px(140), px(96), px(22)
        x = (w - (3 * cw + 2 * gap)) / 2
        y = (h - ch) / 2 - px(6)
        for nome, recomeca in cartoes:
            if recomeca:
                self.img(x, y, comp.img_ret(self.cv, cw, ch, px(8), self.c['destaque_suave'], self.c['sup'],
                                            self.c['destaque'], 1.5))
            else:
                self.img(x, y, comp.img_ret(self.cv, cw, ch, px(8), self.c['fundo'], self.c['sup'],
                                            self.c['borda'], 1.0))
            self.texto(x + cw / 2, y + px(30), nome, negrito=True, anchor='center')
            if recomeca:
                self.texto(x + cw / 2, y + px(62), t('il_recomeca'), 'destaque', 10, True, anchor='center')
            else:
                self.texto(x + cw / 2, y + px(62), t('il_mantem'), 'fraco', 10, anchor='center')
            x += cw + gap

    def _intro_3(self):
        x, y = px(36), px(34)
        agora = t('jogado_em', quando=idiomas.data_hora(datetime.datetime.now()))
        self.circulo(x, y, 'feito', 1)
        self.texto(x + px(40), y + px(13), t('passo1_titulo').upper(), negrito=True, tamanho=11)
        fim = self.cv.bbox(self.texto(x + px(40), y + px(40), t('passo1_resumo', plat='Steam', id='7656…0000',
                                                                quando=agora), 'fraco', 9))[2]
        fim = self.cv.bbox(self.texto(fim + px(14), y + px(40), t('link_trocar'), 'destaque', 9, True))[2]
        self.texto(fim + px(14), y + px(40), t('link_escolher_pasta'), 'fraco', 9)
        caixa_y = y + px(66)
        self.img(x + px(40), caixa_y, comp.img_ret(self.cv, px(400), px(64), px(6), self.c['fundo'], self.c['sup'],
                                                    self.c['borda'], 1.0))
        self.texto(x + px(56), caixa_y + px(20), t('rotulo_plataforma'), 'fraco', 9)
        px0 = x + px(150)
        for i, plat in enumerate(('Steam', 'Epic')):
            cx = px0 + i * px(110)
            r = px(6)
            cor = self.c['destaque'] if i == 0 else self.c['fraquinho']
            self.cv.create_oval(cx - r, caixa_y + px(20) - r, cx + r, caixa_y + px(20) + r, outline=cor,
                                width=max(1, px(1.5)), fill=self.c['fundo'])
            if i == 0:
                self.cv.create_oval(cx - px(3), caixa_y + px(17), cx + px(3), caixa_y + px(23), fill=cor, outline=cor)
            self.texto(cx + px(12), caixa_y + px(20), plat, tamanho=9)
        self.texto(x + px(56), caixa_y + px(46), t('rotulo_save'), 'fraco', 9)
        self.caixa(px0 - px(8), caixa_y + px(36), x + px(420), caixa_y + px(56), 'sup', 'borda')
        self.texto(px0, caixa_y + px(46), t('save_descricao', id='7656…0000', quando=agora, pasta='…').split('(')[0].strip(), tamanho=8)

    def _intro_4(self):
        x, y = px(36), px(40)
        self.circulo(x, y, 'atual', 3)
        tit = self.texto(x + px(40), y + px(13), t('passo2_titulo').upper(), negrito=True, tamanho=11)
        self.texto(self.cv.bbox(tit)[2] + px(8), y + px(13), t('recomendado'), 'fraco', 10)
        self.texto(x + px(40), y + px(42), t('passo2_sub'), 'fraco', 9, largura=self.w - x - px(80))
        bx, by = self.botao(x + px(40), y + px(80), t('bt_backup_save'))
        self.anel(x + px(34), y + px(74), bx + px(6), by + px(6))

    def _intro_5(self):
        x, y, larg = px(40), px(36), self.w - px(80)
        self.img(x - px(14), y - px(18), comp.img_ret(self.cv, larg + px(28), px(108), px(8), self.c['sup'],
                                                       self.c['sup'], self.c['borda'], 1.0))
        r = px(14)
        self.img(x + px(8) - r, y + px(32) - r, comp.img_ret(self.cv, 2 * r, 2 * r, r, self.c['sup'], self.c['sup'],
                                                             self.c['destaque'], max(2, px(2))))
        self.linha_mapa(x, y, larg, 'Yukon Valley', 22, 52)
        self.linha_mapa(x, y + px(32), larg, 'Te Awaroa National Park', 16, 23, marcada=True)
        self.linha_mapa(x, y + px(64), larg, 'Intisuyu', 11, 94)
        self.texto(x - px(6), y + px(118), t('il_clique_caixinha'), 'destaque', 10, True)

    def _intro_6(self):
        x, y = px(36), px(22)
        self.circulo(x, y, 'atual', 5)
        self.texto(x + px(40), y + px(13), t('passo4_titulo').upper(), negrito=True, tamanho=11)
        bx, by = self.botao(x + px(40), y + px(36), t('bt_resetar_um'), tamanho=11)
        self.texto(bx + px(16), (y + px(36) + by) / 2, t('passo4_resumo', nomes='Te Awaroa National Park'),
                   'fraco', 9, largura=self.w - bx - px(40))
        self.quadro_desfazer(x + px(40), by + px(14), self.w - x - px(70))

    def quadro_desfazer(self, x, y, larg, destacar=None):
        """Miniatura do quadro "Precisa desfazer?" com os dois botões."""
        c = self.c
        alt = px(78)
        self.img(x, y, comp.img_ret(self.cv, larg, alt, px(6), c['sup'], c['sup'], c['borda'], 1.0))
        self.texto(x + px(12), y + px(16), '↩  ' + t('desfazer').upper(), negrito=True, tamanho=8)
        self.texto(x + larg - px(12), y + px(16), t('link_como_desfazer'), 'destaque', 8, anchor='e')
        meio = (larg - px(36)) / 2
        for i, chave in enumerate(('bt_restaurar_missoes', 'bt_restaurar_save_curto')):
            bx = x + px(12) + i * (meio + px(12))
            fim_x, fim_y = self.botao(bx, y + px(32), t(chave), principal=False, tamanho=8)
            if destacar == i:
                self.anel(bx - px(4), y + px(28), fim_x + px(4), fim_y + px(4))

    def _intro_2(self):
        x, y = px(36), px(30)
        self.circulo(x, y, 'feito', 1)
        self.texto(x + px(40), y + px(13), t('passo_verif_titulo').upper(), negrito=True, tamanho=11)
        fim = self.cv.bbox(self.texto(x + px(40), y + px(40), t('status_ok'), 'destaque', 9))[2]
        self.texto(fim + px(12), y + px(40), t('link_detalhes'), 'fraco', 9)
        cy = y + px(66)
        self.img(x + px(40), cy, comp.img_ret(self.cv, px(400), px(84), px(6), self.c['fundo'], self.c['sup'],
                                               self.c['borda'], 1.0))
        for i, (estado, chave) in enumerate((('feito', 'il_verif_1'), ('feito', 'il_verif_2'),
                                            ('aviso', 'il_verif_3'))):
            ly = cy + px(10) + i * px(24)
            self.img(x + px(54), ly, comp.img_circulo(self.cv, estado, self.c['fundo'], px(16)))
            if estado == 'aviso':
                self.cv.create_text(x + px(62), ly + px(8), text='!', fill='#ffffff', font=temas.fonte(7, 'bold'))
            self.texto(x + px(78), ly + px(8), t(chave), 'texto' if estado == 'feito' else 'aviso', 9)

    # --- tutorial "Como desfazer"
    def lista_backups(self, x, y, larg, linhas, selecionada=None, titulo=None):
        """Miniatura da lista de backups. linhas = [(data, texto, destaque?)]."""
        c = self.c
        if titulo:
            self.texto(x, y - px(12), titulo.upper(), negrito=True, tamanho=8)
        alt = px(26) * len(linhas) + px(8)
        self.img(x, y, comp.img_ret(self.cv, larg, alt, px(6), c['sup'], c['sup'], c['borda'], 1.0))
        for i, (data, texto, original) in enumerate(linhas):
            ly = y + px(4) + i * px(26)
            if original:
                self.caixa(x + px(2), ly, x + larg - px(2), ly + px(24), 'destaque_suave', None)
            elif i == selecionada:
                self.caixa(x + px(2), ly, x + larg - px(2), ly + px(24), 'selecao', None)
            self.texto(x + px(12), ly + px(12), data, 'fraco', 8)
            self.texto(x + px(92), ly + px(12), texto, 'destaque' if original else 'texto', 8, negrito=original)
            if i == selecionada:
                self.anel(x, ly - px(1), x + larg, ly + px(25))
        return y + alt

    def _desfazer_1(self):
        larg = self.w - px(80)
        self.quadro_desfazer(px(40), px(26), larg)
        meio = (larg - px(36)) / 2
        for i, chave in enumerate(('desc_restaurar_missoes', 'desc_restaurar_save')):
            self.texto(px(52) + i * (meio + px(12)), px(122), t(chave), 'fraco', 8, anchor='nw', largura=meio)

    def _desfazer_2(self):
        hoje = datetime.date.today()
        d = lambda dias: idiomas.data(datetime.datetime.combine(hoje - datetime.timedelta(days=dias),
                                                                 datetime.time()))
        fim = self.lista_backups(px(36), px(36), self.w - px(72), [
            (d(9), '🔒 ' + t('backup_original'), True),
            (d(0), t('titulo_reset', nomes='Te Awaroa National Park'), False),
            (d(2), t('titulo_reset', nomes='Yukon Valley'), False)], selecionada=1, titulo=t('rest_titulo'))
        self.botao(px(36), fim + px(14), t('bt_restaurar_este'), tamanho=8)

    def _desfazer_3(self):
        c = self.c
        x, y, larg = px(30), px(28), self.w - px(60)
        cols = (x + px(12), x + px(220), x + px(330))
        self.texto(x, y - px(12), t('rest_passo2').split('(')[0].strip().upper(), negrito=True, tamanho=8)
        self.img(x, y, comp.img_ret(self.cv, larg, px(112), px(6), c['sup'], c['sup'], c['borda'], 1.0))
        for col, chave in zip(cols, ('col_mapa', 'col_agora', 'col_depois')):
            self.texto(col, y + px(14), t(chave), 'fraco', 8, True)
        linhas = (('Te Awaroa National Park', t('mapa_resetado_curto'), '16/23', True),
                  ('Yukon Valley', '22/52', '22/52', False),
                  ('Intisuyu', '11/94', '11/94', False))
        for i, (nome, agora, depois, muda) in enumerate(linhas):
            ly = y + px(30) + i * px(26)
            if muda:
                self.caixa(x + px(2), ly, x + larg - px(2), ly + px(24), 'diferente_fundo', None)
            self.texto(cols[0], ly + px(12), nome, tamanho=8, negrito=muda)
            self.texto(cols[1], ly + px(12), agora, 'fraco', 8)
            self.texto(cols[2], ly + px(12), depois, 'texto', 8, negrito=muda)
        self.texto(x, y + px(130), t('il_amarelo'), 'aviso', 9, True)

    def _desfazer_4(self):
        hoje = datetime.date.today()
        d = lambda dias: idiomas.data(datetime.datetime.combine(hoje - datetime.timedelta(days=dias),
                                                                 datetime.time()))
        fim = self.lista_backups(px(36), px(36), self.w - px(72), [
            (d(9), '🔒 ' + t('backup_original'), True),
            (d(0), t('titulo_reset', nomes='Te Awaroa National Park'), False),
            (d(2), t('titulo_reset', nomes='Yukon Valley'), False)], selecionada=0, titulo=t('rest_titulo'))
        self.texto(px(36), fim + px(22), t('il_original_sempre'), 'destaque', 9, True)

    def _desfazer_5(self):
        hoje = datetime.date.today()
        d = lambda dias: idiomas.data(datetime.datetime.combine(hoje - datetime.timedelta(days=dias),
                                                                 datetime.time()))
        fim = self.lista_backups(px(36), px(36), self.w - px(72), [
            (d(0), t('titulo_save_manual') + '  —  "' + t('il_apelido_exemplo') + '"  ·  13,1 MB', False),
            (d(1), t('titulo_save_manual') + '  ·  13,0 MB', False)], selecionada=0, titulo=t('rest_save_titulo'))
        self.texto(px(36), fim + px(22), t('il_save_aviso'), 'aviso', 9, True, largura=self.w - px(72))

    def _desfazer_6(self):
        x, y = px(48), px(30)
        for i, chave in enumerate(('il_abra_jogo', 'il_local', 'il_restaurado')):
            yy = y + i * px(48)
            self.circulo(x, yy, 'atual' if i == 0 else 'espera', i + 1)
            self.texto(x + px(42), yy + px(13), t(chave), tamanho=11, negrito=(i == 1))

    def _intro_7(self):
        x, y = px(48), px(30)
        for i, chave in enumerate(('il_abra_jogo', 'il_local', 'il_entre_mapa')):
            yy = y + i * px(48)
            self.circulo(x, yy, 'atual' if i == 0 else 'espera', i + 1)
            self.texto(x + px(42), yy + px(13), t(chave), tamanho=11, negrito=(i == 1))

    # --- guia do Windows Defender
    def defender(self, n):
        w, h = self.w, self.h
        c = self.c
        if n == 1:
            # menu Iniciar com a busca
            self.img(px(40), px(20), comp.img_ret(self.cv, w - px(80), h - px(40), px(10), c['fundo'], c['sup'],
                                                  c['borda'], 1.0))
            self.img(px(64), px(40), comp.img_ret(self.cv, w - px(128), px(34), px(17), c['sup'], c['fundo'],
                                                  c['borda'], 1.0))
            self.texto(px(84), px(57), '🔍  ' + t('win_seguranca'), tamanho=10)
            self.texto(px(70), px(100), t('win_melhor'), 'fraco', 8, negrito=True)
            self.caixa(px(64), px(112), w - px(64), px(150), 'sup', None)
            self.texto(px(80), px(131), '🛡  ' + t('win_seguranca'), tamanho=10, negrito=True)
            self.anel(px(62), px(110), w - px(62), px(152))
            return
        # janela da Segurança do Windows: menu à esquerda e conteúdo à direita
        self.img(px(16), px(12), comp.img_ret(self.cv, w - px(32), h - px(24), px(8), c['fundo'], c['sup'],
                                              c['borda'], 1.0))
        self.texto(px(30), px(28), t('win_seguranca'), 'fraco', 8)
        menu = ('win_inicio', 'win_virus', 'win_conta', 'win_firewall', 'win_aplicativos')
        for i, chave in enumerate(menu):
            yy = px(52) + i * px(24)
            ativo = (n >= 3 and chave == 'win_virus')
            if ativo:
                self.caixa(px(26), yy - px(10), px(150), yy + px(10), 'sup', None)
            nome = t(chave) if len(t(chave)) <= 17 else t(chave)[:16] + '…'
            self.texto(px(34), yy, nome, 'texto' if ativo else 'fraco', 8)
        x0 = px(172)
        if n == 2:
            self.texto(x0, px(40), t('win_seguranca_rapida'), negrito=True, tamanho=10)
            for i, chave in enumerate(('win_virus', 'win_conta', 'win_firewall', 'win_aplicativos')):
                cx = x0 + (i % 2) * px(170)
                cy = px(62) + (i // 2) * px(58)
                self.caixa(cx, cy, cx + px(158), cy + px(48), 'sup', 'borda')
                self.texto(cx + px(10), cy + px(24), ('🛡  ' if i == 0 else '▫  ') + t(chave), tamanho=8,
                           largura=px(140), negrito=(i == 0))
                if i == 0:
                    self.anel(cx - px(3), cy - px(3), cx + px(161), cy + px(51))
        elif n == 3:
            self.texto(x0, px(40), t('win_virus'), negrito=True, tamanho=10)
            for i in range(3):
                self.caixa(x0, px(60) + i * px(12), x0 + px(240 - i * 50), px(64) + i * px(12), 'borda', None)
            self.texto(x0, px(114), t('win_ransomware_titulo'), negrito=True, tamanho=9)
            self.texto(x0, px(136), t('win_ransomware'), 'destaque', 9)
            bb = self.cv.bbox(self.cv.find_all()[-1])
            self.anel(bb[0] - px(5), bb[1] - px(4), bb[2] + px(5), bb[3] + px(4))
        elif n == 4:
            self.texto(x0, px(40), t('win_ransomware_titulo'), negrito=True, tamanho=10)
            self.texto(x0, px(66), t('win_cfa'), tamanho=9)
            # chave "Ativado"
            ky = px(88)
            self.img(x0, ky - px(8), comp.img_ret(self.cv, px(36), px(16), px(8), c['destaque'], c['fundo']))
            self.cv.create_oval(x0 + px(22), ky - px(5), x0 + px(32), ky + px(5), fill='#ffffff', outline='#ffffff')
            self.texto(x0 + px(46), ky, t('win_ligado'), 'fraco', 8)
            self.texto(x0, px(112), t('win_historico'), 'fraco', 8)
            self.texto(x0, px(148), t('win_permitir'), 'destaque', 9, largura=w - x0 - px(40))
            bb = self.cv.bbox(self.cv.find_all()[-1])
            self.anel(bb[0] - px(5), bb[1] - px(4), bb[2] + px(5), bb[3] + px(4))
        else:
            self.texto(x0, px(40), t('win_permitir'), negrito=True, tamanho=9, largura=w - x0 - px(40))
            self.caixa(x0, px(70), x0 + px(220), px(96), 'sup', 'borda')
            self.texto(x0 + px(10), px(83), '+  ' + t('win_adicionar'), tamanho=9)
            self.caixa(x0 + px(10), px(100), x0 + px(230), px(150), 'sup', 'borda')
            self.texto(x0 + px(20), px(114), t('win_recentes'), 'fraco', 8)
            self.texto(x0 + px(20), px(137), t('win_procurar'), tamanho=9, negrito=True)
            self.anel(x0 + px(12), px(126), x0 + px(228), px(148))


class JanelaDefender(Janela):
    """Passo a passo para liberar o programa no "Acesso Controlado a Pastas" do Windows Defender."""

    TOTAL = 5

    def __init__(self, app):
        super().__init__(app, t('guia_titulo'))
        self.pagina = 1
        c = temas.CORES[temas.atual()]
        self.larg_il, self.alt_il = px(470), px(190)

        corpo = ttk.Frame(self, padding=(px(26), px(22), px(26), px(18)))
        corpo.pack(fill='both', expand=True)
        rotulo(corpo, t('guia_titulo').upper(), negrito=True, tamanho=14).grid(row=0, column=0, columnspan=2, sticky='w')
        rotulo(corpo, t('guia_intro'), 'fraco', 10).grid(row=1, column=0, columnspan=2, sticky='w',
                                                          pady=(px(4), px(16)))
        # lista dos passos à esquerda
        lado = ttk.Frame(corpo)
        lado.grid(row=2, column=0, sticky='nw', padx=(0, px(26)))
        self.itens = []
        for i in range(1, self.TOTAL + 1):
            linha = ttk.Frame(lado)
            linha.pack(fill='x', pady=px(4))
            circ = comp.Circulo(linha, i, tam=px(24))
            circ.itemconfigure(circ._txt, font=temas.fonte(9, 'bold'))
            circ.pack(side='left')
            nome = rotulo(linha, t(f'guia_passo_{i}'), 'fraco', 10, cursor='hand2', wraplength=px(190),
                          justify='left', anchor='w')
            nome.pack(side='left', padx=(px(10), 0))
            for w in (circ, nome):
                w.bind('<Button-1>', lambda e, n=i: self.ir(n))
            self.itens.append((circ, nome))

        # instrução à direita
        direita = ttk.Frame(corpo)
        direita.grid(row=2, column=1, sticky='nsew')
        self.contador = rotulo(direita, '', 'destaque', 9, negrito=True, anchor='w')
        self.contador.pack(fill='x')
        self.instrucao = rotulo(direita, '', wraplength=self.larg_il, justify='left', anchor='nw', height=4)
        self.instrucao.pack(fill='x', pady=(px(4), px(10)))
        self.desenho = tk.Canvas(direita, width=self.larg_il, height=self.alt_il, bg=c['sup'],
                                 highlightthickness=1, highlightbackground=c['borda'], bd=0)
        self.desenho.pack()
        rotulo(direita, t('guia_caminho'), 'fraco', 9, anchor='w').pack(fill='x', pady=(px(14), px(4)))
        caixa = ttk.Frame(direita)
        caixa.pack(fill='x')
        self.caminho = ttk.Entry(caixa)
        self.caminho.insert(0, caminho_do_programa())
        self.caminho.state(['readonly'])
        self.caminho.pack(side='left', fill='x', expand=True)
        self.bt_copiar = ttk.Button(caixa, text=t('bt_copiar'), command=self.copiar)
        self.bt_copiar.pack(side='left', padx=(px(8), 0))
        self.copiado = rotulo(direita, '', 'destaque', 9, anchor='w')
        self.copiado.pack(fill='x', pady=(px(4), 0))

        bts = ttk.Frame(corpo)
        bts.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(px(14), 0))
        self.bt_seguranca = ttk.Button(bts, text=t('bt_abrir_seguranca'), command=app.abrir_seguranca)
        self.bt_seguranca.pack(side='left')
        self.bt_proximo = ttk.Button(bts, style='Primario.TButton', command=self.proximo)
        self.bt_proximo.pack(side='right')
        self.bt_voltar = ttk.Button(bts, text=t('intro_voltar'), command=self.voltar)
        self.bt_voltar.pack(side='right', padx=px(8))
        corpo.columnconfigure(1, weight=1)
        self.mostrar()
        _centralizar(self, app)

    def mostrar(self):
        n = self.pagina
        for i, (circ, nome) in enumerate(self.itens, start=1):
            circ.definir('feito' if i < n else ('atual' if i == n else 'espera'))
            nome.config(fg=temas.cor('texto') if i == n else temas.cor('fraco'),
                        font=temas.fonte(10, 'bold') if i == n else temas.fonte(10))
        self.contador.config(text=t('guia_contador', n=n, total=self.TOTAL))
        self.instrucao.config(text=t(f'guia_texto_{n}'))
        self.bt_voltar.state(['disabled'] if n == 1 else ['!disabled'])
        self.bt_proximo.config(text=t('bt_testar_de_novo') if n == self.TOTAL else t('intro_proximo'))
        Ilustracoes(self.desenho, self.larg_il, self.alt_il).defender(n)

    def ir(self, n):
        self.pagina = n
        self.mostrar()

    def proximo(self):
        if self.pagina == self.TOTAL:
            if self.app.testar_de_novo(parent=self):
                self.destroy()
            return
        self.ir(self.pagina + 1)

    def voltar(self):
        if self.pagina > 1:
            self.ir(self.pagina - 1)

    def copiar(self):
        self.app.copiar_caminho()
        self.copiado.config(text=t('copiado'))


class JanelaVerificacao(Janela):
    """Tela "Verificação antes de começar".

    modo 'info'  : só mostra (ao abrir o programa ou pelo link "detalhes");
    modo 'antes' : aparece antes de alterar o save quando algo impede; termina com
                   self.continuar = True (seguir) ou False (cancelar).
    Regras: nada é fechado sem o clique do usuário, nada é fechado à força, e depois
    de cada botão a verificação é feita de novo."""

    BOTOES_FECHAR = {'steam': 'bt_fechar_steam', 'onedrive': 'bt_fechar_onedrive', 'epic': 'bt_fechar_epic',
                     'googledrive': 'bt_fechar_googledrive', 'dropbox': 'bt_fechar_dropbox'}

    def __init__(self, app, modo, resultado, depois=None):
        super().__init__(app, t('verif_titulo'), redimensionar=True)
        self.modo, self.resultado, self.depois = modo, resultado, depois
        self.continuar = False
        self._espera = None
        self.geometry(f'{px(720)}x{px(540)}')
        self.minsize(px(620), px(420))
        self.protocol('WM_DELETE_WINDOW', self.cancelar)

        corpo = ttk.Frame(self, padding=px(22))
        corpo.pack(fill='both', expand=True)
        rotulo(corpo, t('verif_titulo').upper(), negrito=True, tamanho=14).pack(anchor='w')
        rotulo(corpo, t('verif_explicacao'), 'fraco', 10, wraplength=px(670), justify='left', anchor='w').pack(
            anchor='w', fill='x', pady=(px(6), px(14)))
        self.area = ttk.Frame(corpo)
        self.area.pack(fill='both', expand=True)
        self.mensagem = rotulo(corpo, '', 'aviso', 10, anchor='w', justify='left', wraplength=px(670))
        self.mensagem.pack(fill='x', pady=(px(6), 0))
        self.barra = ttk.Frame(corpo)
        self.barra.pack(fill='x', pady=(px(12), 0))
        self.desenhar()
        _centralizar(self, app)

    # -------------------------------------------------------------- desenho
    def desenhar(self):
        for w in self.area.winfo_children() + self.barra.winfo_children():
            w.destroy()
        r = self.resultado
        if not r.itens:
            rotulo(self.area, t('verif_tudo_pronto'), 'destaque', 11, negrito=True).pack(anchor='w', pady=px(10))
        for titulo, itens, cor in ((t('verif_impede'), r.impedimentos, 'erro'),
                                   (t('verif_atencao'), r.avisos, 'aviso')):
            if not itens:
                continue
            rotulo(self.area, titulo, cor, 10, negrito=True).pack(anchor='w', pady=(px(8), px(4)))
            for item in itens:
                self._linha(item)
        if self.app.onedrive_fechado and not diagnostico.esta_aberto('onedrive.exe'):
            linha = ttk.Frame(self.area)
            linha.pack(fill='x', pady=(px(8), 0))
            ttk.Button(linha, text=t('bt_reabrir_onedrive'), command=self.reabrir_onedrive).pack(side='right')
        ttk.Button(self.barra, text=t('bt_verificar_de_novo'), command=self.verificar_de_novo).pack(side='left')
        if self.modo == 'antes':
            ttk.Button(self.barra, text=t('bt_cancelar'), command=self.cancelar).pack(side='right')
            if r.impedimentos:
                bt = ttk.Button(self.barra, text=t('bt_continuar_mesmo_assim'), command=self.continuar_mesmo_assim)
                if r.jogo_aberto:
                    bt.state(['disabled'])   # com o jogo aberto, a alteração seria recusada de qualquer jeito
            else:
                bt = ttk.Button(self.barra, text=t('bt_continuar'), style='Primario.TButton', command=self.seguir)
            bt.pack(side='right', padx=px(8))
            self.bt_seguir = bt
        else:
            ttk.Button(self.barra, text=t('bt_fechar'), style='Primario.TButton', command=self.cancelar).pack(
                side='right')

    def _linha(self, item):
        linha = ttk.Frame(self.area)
        linha.pack(fill='x', pady=px(4))
        botoes = ttk.Frame(linha)
        botoes.pack(side='right', anchor='n')
        rotulo(linha, '•  ' + item.texto, wraplength=px(500), justify='left', anchor='w').pack(side='left', fill='x')
        chave = item.tipo
        if item.tipo == 'em_uso':
            chave = item.dados['programa'].chave
        if chave in self.BOTOES_FECHAR:
            ttk.Button(botoes, text=t(self.BOTOES_FECHAR[chave]),
                       command=lambda c=chave: self.fechar_programa(c)).pack()
        elif item.tipo == 'somente_leitura':
            ttk.Button(botoes, text=t('bt_corrigir'),
                       command=lambda i=item: self.corrigir(i)).pack()

    # --------------------------------------------------------------- botões
    def verificar_de_novo(self, mensagem=''):
        self.resultado = self.app.verificar_agora()
        self.mensagem.config(text=mensagem)
        self.desenhar()

    def corrigir(self, item):
        n = diagnostico.corrigir_somente_leitura(item.dados['itens'])
        self.verificar_de_novo(t('corrigidos', n=n))

    def fechar_programa(self, chave):
        exe, nome = diagnostico.PROGRAMAS[chave]
        if chave == 'steam':
            pediu = diagnostico.fechar_steam()
        elif chave == 'onedrive':
            caminho = diagnostico.fechar_onedrive()
            if caminho:
                self.app.onedrive_fechado = caminho
            pediu = bool(caminho)
        else:
            pediu = diagnostico.fechar_normalmente(exe)
            if not pediu:
                self.verificar_de_novo(t('nao_fechou', programa=nome))
                return
        if not pediu:
            self.verificar_de_novo(t('nao_achei_programa', programa=nome))
            return
        self.mensagem.config(text=t('fechando', programa=nome))
        self._aguardar_fechar(exe, nome, tentativas=20)

    def _aguardar_fechar(self, exe, nome, tentativas):
        if not self.winfo_exists():
            return
        if not diagnostico.esta_aberto(exe):
            self.verificar_de_novo()
        elif tentativas <= 0:
            self.verificar_de_novo(t('nao_fechou', programa=nome))
        else:
            self._espera = self.after(1000, lambda: self._aguardar_fechar(exe, nome, tentativas - 1))

    def reabrir_onedrive(self):
        diagnostico.reabrir_onedrive(self.app.onedrive_fechado)
        self.app.onedrive_fechado = None
        self.after(1500, self.verificar_de_novo)

    def continuar_mesmo_assim(self):
        if messagebox.askyesno(TITULO, t('confirmar_continuar_risco'), icon='warning', parent=self):
            registro.log('Verificação: o usuário escolheu "Continuar mesmo assim".', 'AVISO')
            self.seguir()

    def seguir(self):
        self.continuar = True
        self._fechar()

    def cancelar(self):
        self.continuar = False
        self._fechar()

    def _fechar(self):
        if self._espera:
            try:
                self.after_cancel(self._espera)
            except tk.TclError:
                pass
        self.destroy()
        if self.depois:
            try:
                self.app._agendados.append(self.app.after(150, self.depois))
            except tk.TclError:
                pass


class JanelaErro(Janela):
    """Janela de erro: o que aconteceu, a causa encontrada (quando der) e "Copiar detalhes"."""

    def __init__(self, app, mensagem, causa, erro, contexto, parent=None):
        super().__init__(app, t('erro_titulo'), parent=parent, redimensionar=True)
        self.minsize(px(560), px(320))
        c = temas.CORES[temas.atual()]

        corpo = ttk.Frame(self, padding=px(22))
        corpo.pack(fill='both', expand=True)
        cab = ttk.Frame(corpo)
        cab.pack(fill='x')
        icone = comp.Circulo(cab, '!', tam=px(32))
        icone.definir('aviso')
        icone.itemconfigure(icone._img, image=comp.guardar_imagem(
            icone, ('erro_ic', px(32)), lambda: _circulo_cheio(px(32), c['erro'], c['fundo'])))
        icone.itemconfigure(icone._txt, fill='#ffffff')
        icone.pack(side='left', padx=(0, px(12)))
        rotulo(cab, t('erro_titulo').upper(), 'erro', 14, negrito=True).pack(side='left')
        texto = mensagem
        if causa and causa.textos:
            titulo = t('erro_causa_encontrada') if causa.encontrada else t('erro_causas_possiveis')
            texto += '\n\n' + titulo + '\n' + '\n'.join('•  ' + c for c in causa.textos)
            if causa.cfa_confirmado:
                texto += '\n\n' + core.mensagem_acesso_controlado(caminho_do_programa())
        self.texto = texto
        caixa = tk.Text(corpo, wrap='word', height=14, width=78, relief='flat', borderwidth=0, padx=px(12),
                        pady=px(10), font=temas.fonte(10), bg=c['sup'], fg=c['texto'],
                        highlightthickness=1, highlightbackground=c['borda'])
        caixa.insert('1.0', texto)
        caixa.config(state='disabled')
        caixa.pack(fill='both', expand=True, pady=(px(14), px(10)))
        self.aviso = ttk.Label(corpo, text='', style='Fraco.TLabel')
        self.aviso.pack(anchor='w')
        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(8), 0))
        ttk.Button(bts, text=t('bt_copiar_detalhes'), command=self.copiar).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_pasta_logs'), command=app.abrir_logs).pack(side='left', padx=px(8))
        ttk.Button(bts, text=t('bt_fechar'), style='Primario.TButton', command=self.destroy).pack(side='right')
        self.detalhes = self._montar_detalhes(erro, contexto)
        _centralizar(self, app)

    def _montar_detalhes(self, erro, contexto):
        import traceback
        linhas = [f'ResetMissionsCOTW {VERSAO}', f'Operação: {contexto}', '', self.texto, '',
                  'Erro técnico: ' + repr(erro)]
        original = getattr(erro, 'original', None)
        if original is not None:
            linhas.append('Erro original: ' + repr(original))
        if isinstance(erro, BaseException) and erro.__traceback__:
            linhas.append(''.join(traceback.format_exception(type(erro), erro, erro.__traceback__)).rstrip())
        log = registro.conteudo_atual(limite=8000)
        if log:
            linhas += ['', '----- log -----', log]
        return registro.mascarar('\n'.join(linhas))

    def copiar(self):
        self.clipboard_clear()
        self.clipboard_append(self.detalhes)
        self.aviso.config(text=t('detalhes_copiados'))


def _circulo_cheio(tam, cor, fundo):
    p = comp.Pintura(tam, tam, fundo)
    p.circulo(tam / 2, tam / 2, tam / 2 - 0.5, cor)
    return p


def _modal(janela):
    """Prende o foco nesta janela (se outra janela já tiver o foco preso, segue sem prender)."""
    try:
        janela.grab_set()
    except tk.TclError:
        pass


def _centralizar(janela, pai):
    """Põe a janela no meio da janela principal."""
    try:
        janela.update_idletasks()
        x = pai.winfo_rootx() + (pai.winfo_width() - janela.winfo_width()) // 2
        y = pai.winfo_rooty() + (pai.winfo_height() - janela.winfo_height()) // 3
        janela.geometry(f'+{max(x, 0)}+{max(y, 0)}')
    except tk.TclError:
        pass


def desenhar_xicara(widget, fundo):
    """Xícara de café com coração e fumacinha (imagem da janela "Apoiar")."""
    c = temas.CORES[temas.atual()]
    w, h = px(150), px(118)

    def fazer():
        p = comp.Pintura(w, h, fundo)
        s = temas.ESCALA
        # fumaça
        for dx in (-14, 0, 14):
            x = w / 2 + dx * s - 6 * s
            p.linha([(x, 30 * s), (x - 4 * s, 22 * s), (x + 1 * s, 14 * s), (x - 3 * s, 6 * s)], 2.4 * s,
                    c['quente_borda'])
        # pires
        p.elipse(w / 2 - 6 * s, 104 * s, 58 * s, 9 * s, c['quente_borda'])
        p.elipse(w / 2 - 6 * s, 102 * s, 50 * s, 6 * s, c['quente_suave'])
        # alça
        p.circulo(w / 2 + 38 * s, 62 * s, 15 * s, c['quente'])
        p.circulo(w / 2 + 38 * s, 62 * s, 8 * s, fundo)
        # corpo da xícara
        p.ret(w / 2 - 46 * s, 38 * s, w / 2 + 34 * s, 98 * s, 18 * s, c['quente'])
        p.ret(w / 2 - 46 * s, 38 * s, w / 2 + 34 * s, 50 * s, 4 * s, c['quente'])
        # coração
        p.coracao(w / 2 - 6 * s, 64 * s, 26 * s, '#ffffff')
        return p
    return comp.guardar_imagem(widget, ('xicara', fundo, w, h), fazer)


class JanelaApoio(Janela):
    """Janela "Apoiar o projeto"."""

    def __init__(self, app, parent=None):
        super().__init__(app, t('apoio_titulo'), parent=parent)
        c = temas.CORES[temas.atual()]
        corpo = ttk.Frame(self, padding=(px(30), px(22), px(30), px(20)))
        corpo.pack(fill='both', expand=True)
        arte = tk.Label(corpo, image=desenhar_xicara(self, c['fundo']), bg=c['fundo'], bd=0)
        arte.pack()
        rotulo(corpo, t('apoio_pergunta', programa=NOME_DO_PROGRAMA).upper(), negrito=True, tamanho=14).pack(
            pady=(px(10), px(6)))
        rotulo(corpo, t('apoio_texto'), 'fraco', 10, wraplength=px(400), justify='center').pack()

        self.opcoes = []
        lista = ttk.Frame(corpo)
        lista.pack(fill='x', pady=(px(18), px(6)))
        for icone, nome, sub, link in (('☕', 'Buy Me a Coffee', t('apoio_bmc_sub'), LINK_BUYMEACOFFEE),
                                       ('💠', 'LivePix (Pix)', t('apoio_livepix_sub'), LINK_LIVEPIX)):
            self.opcoes.append((f'{icone}  {nome}', link))
            self._opcao(lista, icone, nome, sub, link)

        mais = ttk.Frame(corpo)
        mais.pack(pady=(px(12), 0))
        rotulo(corpo, t('apoio_sem_dinheiro'), 'fraco', 9).pack(before=mais, pady=(px(10), px(4)))
        links = []
        if LINK_GITHUB:
            links += [(t('apoio_estrela'), lambda: abrir_link(LINK_GITHUB)),
                      (t('apoio_compartilhar'), self.compartilhar),
                      (t('apoio_erros'), lambda: abrir_link(LINK_GITHUB + '/issues'))]
        for i, (texto, cmd) in enumerate(links):
            if i:
                rotulo(mais, '·', 'fraquinho', 9).pack(side='left', padx=px(6))
            comp.Link(mais, texto, cmd, tamanho=9).pack(side='left')
        self.copiado = rotulo(corpo, '', 'destaque', 9)
        self.copiado.pack(pady=(px(4), 0))
        rotulo(corpo, t('apoio_obrigado', autor=AUTOR), 'quente', 10, negrito=True).pack(pady=(px(8), 0))
        ttk.Button(corpo, text=t('bt_fechar'), command=self.destroy).pack(pady=(px(14), 0))
        _centralizar(self, parent or app)

    def _opcao(self, pai, icone, nome, sub, link):
        c = temas.CORES[temas.atual()]
        caixa = tk.Frame(pai, bg=c['sup'], highlightbackground=c['borda'], highlightthickness=1,
                         cursor='hand2' if link else '')
        caixa.pack(fill='x', pady=px(4))
        ic = tk.Label(caixa, text=icone, bg=c['quente_suave'], fg=c['quente'], font=temas.fonte(13), width=3,
                      height=1)
        ic.pack(side='left', padx=px(12), pady=px(10))
        textos = tk.Frame(caixa, bg=c['sup'])
        textos.pack(side='left', fill='x', expand=True)
        a = tk.Label(textos, text=nome if link else f'{nome}  {t("em_breve")}', bg=c['sup'], fg=c['texto'],
                     font=temas.fonte(10, 'bold'), anchor='w')
        a.pack(fill='x')
        b = tk.Label(textos, text=sub, bg=c['sup'], fg=c['fraco'], font=temas.fonte(9), anchor='w')
        b.pack(fill='x')
        seta = tk.Label(caixa, text='→', bg=c['sup'], fg=c['quente'], font=temas.fonte(12, 'bold'))
        seta.pack(side='right', padx=px(14))
        if link:
            def entrar(_=None, cor=c['quente']):
                caixa.configure(highlightbackground=cor)

            def sair(_=None, cor=c['borda']):
                caixa.configure(highlightbackground=cor)
            for w in (caixa, ic, textos, a, b, seta):
                w.bind('<Button-1>', lambda e, l=link: self.abrir(l))
                w.bind('<Enter>', entrar)
                w.bind('<Leave>', sair)

    def compartilhar(self):
        self.clipboard_clear()
        self.clipboard_append(LINK_GITHUB)
        self.copiado.config(text=t('apoio_link_copiado'))

    @staticmethod
    def abrir(link):
        import webbrowser
        webbrowser.open(link)


def main():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # letras nítidas em telas com zoom
    except Exception:
        pass
    idiomas.iniciar()  # idioma salvo pelo usuário, ou o idioma do Windows
    temas.iniciar()    # tema salvo pelo usuário, ou o tema do Windows
    registro.iniciar(VERSAO)   # um log por abertura (guarda os 5 mais recentes)
    registro.log(f'Idioma: {idiomas.atual()} | Tema: {temas.atual()} | Programa: {caminho_do_programa()}')
    try:
        App().mainloop()
    except Exception as e:
        registro.log_erro('Erro inesperado', e)
        raise


if __name__ == '__main__':
    main()
