"""Janela do ResetMissionsCOTW - Reset de Missões por Mapa (theHunter: Call of the Wild).

Visual da 0.9.9: duas colunas. À esquerda, os passos em sequência (1 verificação, 2 save,
3 backup completo, 4 mapa); cada passo só libera o próximo. À direita, o painel do mapa
(passo 5): faixa com a ilustração do mapa e as duas opções, "Resetar tudo" e "Voltar
missões da história". Embaixo, o quadro "Precisa desfazer?" (sempre liberado).
Os textos ficam em idiomas.py; as cores, em temas.py; as peças desenhadas, em componentes.py.
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
import faixa_mapa
import idiomas
import jogo
import perfil
import registro
import temas
import voltar
from idiomas import t
from temas import px

VERSAO = '0.9.9 (Beta)'
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
JANELA_TIMELINE = 9      # quantas missões da história a linha do tempo mostra de uma vez


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


def numero(n):
    """293384 -> 293.384 (pt/es) ou 293,384 (en)."""
    texto = f'{n:,}'
    return texto if idiomas.atual() == 'en' else texto.replace(',', '.')


def rotulo(pai, texto='', estilo='texto', tamanho=10, negrito=False, fundo=None, **opcoes):
    """tk.Label com as cores do tema. estilo: 'texto', 'fraco', 'fraquinho', 'destaque', 'aviso', 'erro'."""
    cor = temas.cor(estilo) if estilo != 'texto' else temas.cor('texto')
    opcoes.setdefault('anchor', 'w')
    opcoes.setdefault('padx', 0)
    opcoes.setdefault('pady', 0)
    return tk.Label(pai, text=texto, bg=fundo or temas.cor('fundo'), fg=cor, bd=0,
                    font=temas.fonte(tamanho, 'bold') if negrito else temas.fonte(tamanho), **opcoes)


class Cartao(tk.Frame):
    """Cartão de um passo: círculo numerado, título (e 🔒 quando travado) e o conteúdo."""

    def __init__(self, pai, n, titulo):
        c = temas.CORES[temas.atual()]
        super().__init__(pai, bg=c['sup'], highlightbackground=c['borda'], highlightthickness=1)
        self.sup = c['sup']
        cab = tk.Frame(self, bg=self.sup)
        cab.pack(fill='x', padx=px(12), pady=(px(10), 0))
        self.circulo = comp.Circulo(cab, n, fundo=self.sup, tam=px(24))
        self.circulo.pack(side='left')
        self.titulo = rotulo(cab, titulo.upper(), negrito=True, tamanho=10, fundo=self.sup)
        self.titulo.pack(side='left', padx=(px(10), 0))
        self.cadeado = rotulo(cab, '🔒', 'fraquinho', 9, fundo=self.sup)
        self.direita = tk.Frame(cab, bg=self.sup)
        self.direita.pack(side='right')
        self.corpo = tk.Frame(self, bg=self.sup)
        self.corpo.pack(fill='both', expand=True, padx=(px(46), px(12)), pady=(px(2), px(10)))
        self.estado = None

    def definir(self, estado):
        """'feito', 'atual', 'aviso' ou 'travado'."""
        self.estado = estado
        self.circulo.definir('espera' if estado == 'travado' else estado)
        self.titulo.config(fg=temas.cor('fraquinho') if estado == 'travado' else temas.cor('texto'))
        if estado == 'travado':
            if not self.cadeado.winfo_manager():
                self.cadeado.pack(side='left', padx=(px(6), 0), after=self.titulo)
        else:
            self.cadeado.pack_forget()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        temas.medir(self)
        try:
            self.iconbitmap(default=caminho_recurso('icone.ico'))   # ícone de todas as janelas
        except tk.TclError:
            pass
        larg = min(px(1180), self.winfo_screenwidth() - px(40))
        alt = min(px(900), self.winfo_screenheight() - px(90))
        self.geometry(f'{larg}x{alt}')
        self.minsize(min(px(980), larg), min(px(620), alt))
        self.raiz = core.pasta_do_programa_padrao()
        self.saves = []
        self.save_atual = None
        self.saves_visiveis = []
        self.mapas = {}
        self.dados_save = None           # core.Save aberto (para os planos de "voltar missões")
        self.perfil = None               # nível, XP e dinheiro do save
        self.nomes = None                # nomes das missões lidos do jogo ({idioma: {hash: nome}})
        self.bloqueado = False
        self.verificacao = None          # último resultado da "Verificação antes de começar"
        self.avisos_aceitos = False      # "Li o aviso e quero continuar" no passo 1
        self.save_confirmado = False     # "Sim, é este save" no passo 2
        self.backup_velho_aceito = False  # "Continuar com o backup de X dias" no passo 3
        self.modo = 'resetar'            # passo 5: 'resetar' (tudo) ou 'voltar' (missões da história)
        self.foco = None                 # mapa mostrado no painel (chave)
        self.n_voltar = 1
        self._modos_mostrado = False     # tutorial "Resetar tudo × Voltar missões" já abriu nesta abertura
        self._modos_agendado = False
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
        if self.ler_nomes_do_jogo:
            self.carregar_nomes()
        self._agendados.append(self.after(300, self.mostrar_boas_vindas))

    # Consulta de versão nova no GitHub ao abrir (os testes desligam isto).
    verificar_atualizacao_ao_abrir = True
    # Nomes das missões lidos do jogo instalado (os testes desligam isto).
    ler_nomes_do_jogo = True

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
        self.faixa_update.pack(fill='x', pady=(0, px(8)), before=self.fim_avisos)

    def ignorar_atualizacao(self):
        if self.atualizacao:
            atualizacao.ignorar(self.atualizacao[0])
        self.mostrar_atualizacao(None)

    # ---- nomes das missões (do jogo instalado)
    def carregar_nomes(self, pasta_jogo=None):
        hashes = sorted({m[4] for d in voltar.dados().values() for m in d['missoes'] if m[4]})
        self._consulta_nomes = jogo.Consulta(hashes, pasta_jogo)
        self._esperar_nomes(120)

    def _esperar_nomes(self, vezes):
        if self._consulta_nomes.pronto:
            self.nomes = self._consulta_nomes.resultado
            self.atualizar_painel()
            self.lista.atualizar_dicas()
        elif vezes > 0:
            self._agendados.append(self.after(250, lambda: self._esperar_nomes(vezes - 1)))

    def escolher_pasta_jogo(self):
        pasta = filedialog.askdirectory(title=t('titulo_escolher_jogo'))
        if not pasta:
            return
        valida = jogo.pasta_valida(os.path.normpath(pasta))
        if not valida:
            messagebox.showerror(TITULO, t('pasta_jogo_invalida'))
            return
        idiomas.salvar_config(pasta_jogo=valida)
        self.carregar_nomes(valida)

    def nome_missao(self, plano, m):
        """Nome da missão no idioma do programa, ou 'Missão N da história'."""
        if self.nomes:
            nome = self.nomes.get(idiomas.atual(), {}).get(m.nome_hash) or self.nomes.get('en', {}).get(m.nome_hash)
            if nome:
                return nome
        if m.tipo == 'M' and m in plano.historia:
            return t('missao_historia_n', n=plano.posicao(m))
        return t('missao_sem_nome')

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

    # Os tutoriais abrem sozinhos nos momentos certos (os testes desligam isto).
    tutoriais_automaticos = True

    def _intro_se_primeira_vez(self):
        """Tutorial "Como usar": abre sozinho toda vez, até marcar "Não mostrar mais"."""
        if self.tutoriais_automaticos and JanelaIntro.mostrar_sozinho():
            self.mostrar_intro()

    def _modos_se_preciso(self):
        """Tutorial "Resetar tudo × Voltar missões": uma vez por abertura, quando o passo 4 é liberado."""
        if self._modos_mostrado or not self.tutoriais_automaticos or not JanelaModos.mostrar_sozinho():
            self._modos_agendado = False
            return
        if any(isinstance(w, Janela) for w in self.winfo_children()):
            self._agendados.append(self.after(800, self._modos_se_preciso))   # espera a outra janela fechar
            return
        self._modos_agendado = False
        if self.liberado(4):
            self._modos_mostrado = True
            self.mostrar_modos()

    def _desfazer_depois_da_mudanca(self, janela_pronto=None):
        """Tutorial "Como desfazer": depois de cada mudança (após a tela "Pronto!")."""
        if not self.tutoriais_automaticos or not JanelaComoDesfazer.mostrar_sozinho():
            return
        if janela_pronto is not None and janela_pronto.winfo_exists():
            self.wait_window(janela_pronto)
        if not any(isinstance(w, (JanelaRestaurar, JanelaComoDesfazer)) for w in self.winfo_children()):
            self.mostrar_como_desfazer()

    def mostrar_intro(self):
        if not any(isinstance(w, JanelaIntro) for w in self.winfo_children()):
            JanelaIntro(self)

    def mostrar_modos(self):
        if not any(isinstance(w, JanelaModos) for w in self.winfo_children()):
            JanelaModos(self)

    # ----------------------------------------------------------------- tela
    def _montar(self):
        temas.aplicar(self)
        temas.preparar_janela(self)
        self.title(t('titulo_janela', versao=VERSAO))
        c = temas.CORES[temas.atual()]

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

        # Quadro "Precisa desfazer?" (sempre liberado), logo acima do rodapé
        self._montar_desfazer()

        # Topo: título e utilidades
        topo = ttk.Frame(self)
        topo.pack(fill='x', padx=px(26), pady=(px(14), px(8)))
        rotulo(topo, '📋 ' + t('cabecalho').upper(), negrito=True, tamanho=12).pack(side='left')
        util = ttk.Frame(topo)
        util.pack(side='right')
        self.bt_ajuda = comp.Link(util, '❔ ' + t('link_como_usar'), self.mostrar_intro, sublinhado=False)
        self.bt_logs = comp.Link(util, '📄 ' + t('link_logs'), self.abrir_logs, sublinhado=False)
        self.combo_idioma = comp.SeletorIdioma(util, idiomas.IDIOMAS, idiomas.atual(), self.trocar_idioma)
        self.bt_tema = comp.Link(util, t('bt_tema_claro') if temas.atual() == 'escuro' else t('bt_tema_escuro'),
                                 self.alternar_tema, sublinhado=False)
        for w in (self.bt_ajuda, self.bt_logs, self.combo_idioma, self.bt_tema):
            w.pack(side='left', padx=(px(18), 0))

        # Avisos de largura total: versão nova, avisos discretos e a faixa do Windows Defender
        self.avisos = ttk.Frame(self)
        self.avisos.pack(fill='x', padx=px(26))
        self.faixa_update = tk.Frame(self.avisos, bg=c['destaque_suave'], highlightbackground=c['destaque'],
                                     highlightthickness=1)
        self.update_texto = rotulo(self.faixa_update, '', 'destaque', 10, negrito=True, fundo=c['destaque_suave'])
        self.update_texto.pack(side='left', padx=(px(14), px(14)), pady=px(7))
        self.link_ignorar = comp.Link(self.faixa_update, t('link_agora_nao'), self.ignorar_atualizacao,
                                      fundo=c['destaque_suave'])
        self.link_ignorar.pack(side='right', padx=(px(10), px(14)))
        self.link_baixar = comp.Link(self.faixa_update, t('link_baixar'), None, forte=True, fundo=c['destaque_suave'],
                                     negrito=True)
        self.link_baixar.pack(side='right', padx=px(6))
        self.aviso_discreto = rotulo(self.avisos, '', 'aviso', 9, justify='left', anchor='w', wraplength=px(1000))
        self._montar_faixa(self.avisos)
        self.fim_avisos = ttk.Frame(self.avisos)
        self.fim_avisos.pack(fill='x')

        # Corpo: passos à esquerda, painel do mapa à direita
        corpo = ttk.Frame(self)
        corpo.pack(fill='both', expand=True, padx=px(26))
        corpo.columnconfigure(0, minsize=px(370))
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)
        esquerda = ttk.Frame(corpo)
        esquerda.grid(row=0, column=0, sticky='nsew', padx=(0, px(18)))
        self.cartoes = []
        self._passo_verificacao(self._cartao(esquerda, 1, t('p1_titulo')))
        self._passo_save(self._cartao(esquerda, 2, t('p2_titulo')))
        self._passo_backup(self._cartao(esquerda, 3, t('p3_titulo')))
        self._passo_mapas(self._cartao(esquerda, 4, t('p4_titulo'), expandir=True))
        self.painel = tk.Frame(corpo, bg=c['sup'], highlightbackground=c['borda'], highlightthickness=1)
        self.painel.grid(row=0, column=1, sticky='nsew')
        self._montar_painel(self.painel)
        self.atualizar_passos()

    def _cartao(self, pai, n, titulo, expandir=False):
        cartao = Cartao(pai, n, titulo)
        cartao.pack(fill='both' if expandir else 'x', expand=expandir, pady=(0, px(10)))
        self.cartoes.append(cartao)
        return cartao

    @property
    def passos(self):
        """(linha, círculo) de cada passo (nome antigo, usado pelos testes)."""
        return [(c, c.circulo) for c in self.cartoes] + [(self.painel, self.circulo5)]

    def _montar_faixa(self, pai):
        c = temas.CORES[temas.atual()]
        bg = c['aviso_suave']
        self.faixa = tk.Frame(pai, bg=bg, highlightbackground=c['aviso_borda'], highlightthickness=1)
        icone = comp.Circulo(self.faixa, '!', fundo=bg, tam=px(30))
        icone.definir('aviso')
        icone.grid(row=0, column=0, rowspan=3, sticky='n', padx=(px(16), px(12)), pady=px(14))
        self.faixa_titulo = rotulo(self.faixa, '', negrito=True, tamanho=10, fundo=bg, anchor='w', justify='left')
        self.faixa_titulo.grid(row=0, column=1, sticky='w', pady=(px(14), 0), padx=(0, px(16)))
        self.faixa_texto = rotulo(self.faixa, '', 'fraco', 10, fundo=bg, anchor='w', justify='left',
                                  wraplength=px(900))
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

    # ---- passo 1: verificação
    def _passo_verificacao(self, cartao):
        p, sup = cartao.corpo, cartao.sup
        self.linha_status = tk.Frame(p, bg=sup)
        self.linha_status.pack(fill='x')
        self.status_verif = rotulo(self.linha_status, '', 'destaque', 9, fundo=sup, cursor='hand2',
                                   wraplength=px(290), justify='left')
        self.status_verif.pack(side='left')
        self.status_verif.bind('<Button-1>', lambda e: self.abrir_verificacao())
        links = tk.Frame(p, bg=sup)
        links.pack(fill='x', pady=(px(2), 0))
        self.link_detalhes = comp.Link(links, t('link_detalhes'), self.abrir_verificacao, fundo=sup, tamanho=9,
                                       forte=True)
        self.link_detalhes.pack(side='left')
        self.link_verificar = comp.Link(links, t('link_verificar_de_novo'), self.verificar_de_novo, fundo=sup,
                                        tamanho=9)
        self.link_verificar.pack(side='left', padx=(px(12), 0))
        self.p1_acao = tk.Frame(p, bg=sup)
        self.bt_ver_o_que_fazer = ttk.Button(self.p1_acao, text=t('bt_ver_o_que_fazer'), style='Aviso.TButton',
                                             command=self.abrir_verificacao)
        self.bt_li_aviso = ttk.Button(self.p1_acao, text=t('bt_li_aviso'), style='Aviso.TButton',
                                      command=self.aceitar_avisos)

    def aceitar_avisos(self):
        self.avisos_aceitos = True
        if self.verificacao is not None:
            self.mostrar_status_verificacao(self.verificacao)
        self.atualizar_passos()

    # ---- passo 2: save
    def _passo_save(self, cartao):
        p, sup = cartao.corpo, cartao.sup
        self.selo = rotulo(cartao.direita, '', 'destaque', 8, negrito=True, fundo=temas.cor('destaque_suave'),
                           padx=px(8), pady=px(1))
        self.selo.pack(side='right')
        linha = tk.Frame(p, bg=sup)
        linha.pack(fill='x')
        self.p1_resumo = rotulo(linha, '', 'fraco', 9, fundo=sup, anchor='w', justify='left', wraplength=px(300))
        self.p1_resumo.pack(side='left', fill='x')
        links = tk.Frame(p, bg=sup)
        links.pack(fill='x', pady=(px(2), 0))
        self.link_trocar = comp.Link(links, t('link_trocar'), self.alternar_trocar, fundo=sup, tamanho=9, forte=True)
        self.link_escolher_pasta = comp.Link(links, t('link_escolher_pasta'), self.escolher_pasta, fundo=sup,
                                             tamanho=9)
        self.link_trocar.pack(side='left', padx=(0, px(12)))
        self.link_escolher_pasta.pack(side='left')
        self.aviso_saves = rotulo(p, '', 'aviso', 9, fundo=sup, anchor='w', justify='left', wraplength=px(300))
        self.stats = tk.Frame(p, bg=sup)
        self.stats.pack(fill='x', pady=(px(6), 0))
        self.p2_acao = tk.Frame(p, bg=sup)
        self.p2_acao.pack(fill='x')
        self.bt_e_este = ttk.Button(self.p2_acao, text=t('bt_e_este_save'), style='Primario.TButton',
                                    command=self.confirmar_save)
        self.p2_ok = rotulo(self.p2_acao, '✓ ' + t('save_confirmado'), 'destaque', 9, negrito=True, fundo=sup)
        self.p1_fim = tk.Frame(p, bg=sup)     # o painel "Trocar" entra antes dela
        self.p1_fim.pack(fill='x')

        # Painel "Trocar": plataforma e save daquela plataforma
        fundo = temas.cor('fundo')
        self.painel_trocar = tk.Frame(p, bg=fundo, highlightbackground=temas.cor('borda'), highlightthickness=1)
        rotulo(self.painel_trocar, t('rotulo_plataforma'), 'fraco', 9, fundo=fundo).grid(
            row=0, column=0, sticky='w', padx=(px(10), px(8)), pady=(px(8), px(3)))
        radios = tk.Frame(self.painel_trocar, bg=fundo)
        radios.grid(row=0, column=1, columnspan=2, sticky='w', pady=(px(8), px(3)))
        self.var_plataforma = tk.StringVar()
        self.radios = {}
        for plat in PLATAFORMAS:
            self.radios[plat] = ttk.Radiobutton(radios, text=nome_plataforma(plat), value=plat,
                                                variable=self.var_plataforma, command=self.trocar_plataforma)
        rotulo(self.painel_trocar, t('rotulo_save'), 'fraco', 9, fundo=fundo).grid(
            row=1, column=0, sticky='w', padx=(px(10), px(8)), pady=(px(3), px(8)))
        self.combo = ttk.Combobox(self.painel_trocar, state='readonly', width=20)
        self.combo.grid(row=1, column=1, sticky='ew', pady=(px(3), px(8)))
        self.combo.bind('<<ComboboxSelected>>', lambda e: self.escolher_save(self.combo.current()))
        self.link_procurar = comp.Link(self.painel_trocar, t('link_procurar'), self.procurar_saves, fundo=fundo,
                                       tamanho=9)
        self.link_procurar.grid(row=1, column=2, sticky='w', padx=(px(8), px(10)), pady=(px(3), px(8)))
        self.painel_trocar.columnconfigure(1, weight=1)

    def confirmar_save(self):
        if self.save_atual is not None:
            self.save_confirmado = True
            self.atualizar_passos()

    def _mostrar_stats(self):
        for w in self.stats.winfo_children():
            w.destroy()
        if self.save_atual is None:
            return
        sup, fundo = temas.cor('sup'), temas.cor('fundo')
        itens = []
        if self.perfil:
            itens += [(t('st_nivel'), numero(self.perfil['nivel'])), (t('st_xp'), numero(self.perfil['xp'])),
                      (t('st_dinheiro'), '$ ' + numero(self.perfil['dinheiro']))]
        if self.mapas:
            itens.append((t('st_missoes'), numero(sum(m.concluidas for m in self.mapas.values()))))
        for nome, valor in itens:
            caixa = tk.Frame(self.stats, bg=fundo, highlightbackground=temas.cor('borda'), highlightthickness=1)
            caixa.pack(side='left', padx=(0, px(6)))
            rotulo(caixa, nome, 'fraco', 8, fundo=fundo).pack(anchor='w', padx=px(7), pady=(px(3), 0))
            rotulo(caixa, valor, negrito=True, tamanho=10, fundo=fundo).pack(anchor='w', padx=px(7), pady=(0, px(3)))
        _ = sup

    # ---- passo 3: backup do save completo
    def _passo_backup(self, cartao):
        p, sup = cartao.corpo, cartao.sup
        self.p2_resumo = rotulo(p, '', 'fraco', 9, fundo=sup, anchor='w', justify='left', wraplength=px(300))
        self.p2_resumo.pack(fill='x')
        self.p3_acao = tk.Frame(p, bg=sup)
        self.p3_acao.pack(fill='x')
        self.bt_backup_save = ttk.Button(self.p3_acao, text=t('bt_backup_save'), style='Primario.TButton',
                                         command=self.pedir_backup_save)
        self.bt_novo_backup = ttk.Button(self.p3_acao, text=t('bt_novo_backup'), command=self.pedir_backup_save)
        self.link_fazer_outro = self.bt_novo_backup     # nome antigo
        self.link_continuar_velho = comp.Link(self.p3_acao, '', self.aceitar_backup_velho, fundo=sup, tamanho=9)
        self.link_fazer_novo = comp.Link(self.p3_acao, t('link_fazer_novo'), self.pedir_backup_save, fundo=sup,
                                         tamanho=9, forte=True)

    def aceitar_backup_velho(self):
        self.backup_velho_aceito = True
        self.atualizar_passos()

    # ---- passo 4: mapas
    def _passo_mapas(self, cartao):
        p = cartao.corpo
        self.link_desmarcar = comp.Link(cartao.direita, t('link_desmarcar_todos'), lambda: self.lista.selection_set(()),
                                        tamanho=9, fundo=cartao.sup)
        self.link_marcar = comp.Link(cartao.direita, t('link_marcar_todos'), self.marcar_todos, tamanho=9,
                                     fundo=cartao.sup)
        self.cartao_mapas = cartao
        cartao.corpo.pack_configure(padx=(px(4), px(4)))
        self.lista = ListaMapas(p, self.ao_marcar, self.ao_focar)
        self.lista.pack(fill='both', expand=True)

    # ---- passo 5: painel do mapa
    def _montar_painel(self, painel):
        c = temas.CORES[temas.atual()]
        sup = c['sup']
        self.banner = tk.Canvas(painel, height=px(140), bg=sup, highlightthickness=0, bd=0)
        self.banner.pack(fill='x')
        self.banner.bind('<Configure>', lambda e: self._agendar_banner())
        self.circulo5 = comp.Circulo(painel, 5, fundo=sup, tam=px(1))   # só guarda o estado do passo 5
        self._banner_info = None
        self._banner_job = None

        # ação (embaixo, empacotada antes do conteúdo para nunca sumir)
        self.acao = tk.Frame(painel, bg=sup)
        self.acao.pack(side='bottom', fill='x')
        tk.Frame(self.acao, bg=c['borda'], height=1).pack(fill='x')
        dentro = tk.Frame(self.acao, bg=sup)
        dentro.pack(fill='x', padx=px(20), pady=px(12))
        self.bt_reset = ttk.Button(dentro, text=t('bt_resetar_nenhum'), style='Grande.TButton', command=self.resetar)
        self.bt_voltar = ttk.Button(dentro, text='', style='Voltar.TButton', command=self.voltar_missoes)
        self.p4_resumo = rotulo(dentro, '', 'fraco', 9, fundo=sup, anchor='w', justify='left', wraplength=px(300))
        self.bt_reset.pack(side='left')
        self.p4_resumo.pack(side='left', padx=(px(14), 0), fill='x')

        def ajustar_texto(_=None):
            bt = self.bt_voltar if self.bt_voltar.winfo_manager() else self.bt_reset
            livre = dentro.winfo_width() - bt.winfo_reqwidth() - px(20)
            self.p4_resumo.config(wraplength=max(px(140), livre))
        dentro.bind('<Configure>', ajustar_texto)
        self.bt_voltar.bind('<Configure>', ajustar_texto)
        self.bt_reset.bind('<Configure>', ajustar_texto)

        # cartões das duas opções
        self.conteudo = tk.Frame(painel, bg=sup)
        self.conteudo.pack(fill='both', expand=True, padx=px(20), pady=(px(14), px(8)))
        self.cartoes_modo = tk.Frame(self.conteudo, bg=sup)
        self.cartoes_modo.pack(fill='x')
        self.cartoes_modo.columnconfigure(0, weight=1, uniform='m')
        self.cartoes_modo.columnconfigure(1, weight=1, uniform='m')
        self.modo_resetar = CartaoModo(self.cartoes_modo, '🔄', t('modo_resetar'), '', lambda: self.trocar_modo('resetar'))
        self.modo_resetar.grid(row=0, column=0, sticky='nsew', padx=(0, px(6)))
        self.modo_voltar = CartaoModo(self.cartoes_modo, '⏪', t('modo_voltar'), t('modo_voltar_sub'),
                                      lambda: self.trocar_modo('voltar'))
        self.modo_voltar.grid(row=0, column=1, sticky='nsew', padx=(px(6), 0))
        linha_qual = tk.Frame(self.conteudo, bg=sup)
        linha_qual.pack(fill='x', pady=(px(4), 0))
        self.link_qual = comp.Link(linha_qual, t('link_qual_escolher'), self.mostrar_modos, fundo=sup, tamanho=9,
                                   forte=True)
        self.link_qual.pack(side='right')
        self.area_modo = comp.AreaRolavel(self.conteudo, largura=None, fundo=sup, margem=0)
        self.area_modo.pack(fill='both', expand=True, pady=(px(4), 0))
        self.corpo_modo = self.area_modo.dentro

    def _montar_desfazer(self):
        c = temas.CORES[temas.atual()]
        sup = c['sup']
        quadro = tk.Frame(self, bg=sup, highlightbackground=c['borda'], highlightthickness=1)
        quadro.pack(side='bottom', fill='x', padx=px(26), pady=(px(10), 0))
        linha = tk.Frame(quadro, bg=sup)
        linha.pack(fill='x', padx=px(14), pady=(px(8), 0))
        rotulo(linha, '↩  ' + t('desfazer').upper(), negrito=True, tamanho=10, fundo=sup).pack(side='left')
        self.bt_restaurar = ttk.Button(linha, text=t('bt_restaurar_missoes'), style='Fundo.TButton',
                                       command=self.janela_restaurar)
        self.bt_restaurar.pack(side='left', padx=(px(14), px(8)))
        self.bt_restaurar_save = ttk.Button(linha, text=t('bt_restaurar_save_curto'), style='Fundo.TButton',
                                            command=self.janela_restaurar_save)
        self.bt_restaurar_save.pack(side='left')
        rotulo(linha, t('desfazer_sempre'), 'fraco', 9, fundo=sup).pack(side='left', padx=(px(14), 0))
        self.link_como_desfazer = comp.Link(linha, t('link_como_desfazer'), self.mostrar_como_desfazer, forte=True,
                                            fundo=sup, tamanho=9)
        self.link_como_desfazer.pack(side='right')
        linha2 = tk.Frame(quadro, bg=sup)
        linha2.pack(fill='x', padx=px(14), pady=(px(4), px(8)))
        self.info = rotulo(linha2, '', 'fraquinho', 9, fundo=sup, wraplength=px(800), justify='left')
        self.info.pack(side='left')
        self.link_pasta_backups = comp.Link(linha2, t('link_pasta_backups'), self.abrir_pasta_backups, tamanho=9,
                                            fundo=sup)
        self.link_pasta_backups.pack(side='right')

    # --------------------------------------------------- estado dos passos
    def _verif_ok(self):
        r = self.verificacao
        if self.bloqueado or r is None or r.impedimentos:
            return False
        return not r.avisos or self.avisos_aceitos

    def _ultimo_backup_save(self):
        if self.save_atual is None or self.bloqueado:
            return None
        try:
            backups = core.listar_backups_save(self.save_atual, self.raiz)
        except OSError:
            backups = []
        return backups[0] if backups else None

    def _backup_ok(self):
        b = self._ultimo_backup_save()
        if b is None:
            return False
        dias = (datetime.datetime.now() - b.quando).days
        return dias < core.DIAS_BACKUP_VELHO or self.backup_velho_aceito

    def liberado(self, passo):
        """O passo pode ser usado? (cada passo só libera o próximo)"""
        if passo <= 1:
            return True
        if passo == 2:
            return self._verif_ok()
        if passo == 3:
            return self.liberado(2) and self.save_atual is not None and self.save_confirmado
        if passo == 4:
            return self.liberado(3) and self._backup_ok()
        return self.liberado(4) and self.foco is not None

    def atualizar_passos(self):
        """Marca cada passo como feito (✓), atual (verde), aviso ou travado (🔒), e ajusta os textos."""
        c1, c2, c3, c4 = self.cartoes
        s = self.save_atual
        # passo 1
        r = self.verificacao
        for w in (self.bt_ver_o_que_fazer, self.bt_li_aviso):
            w.pack_forget()
        self.p1_acao.pack_forget()
        if self.bloqueado or (r is not None and r.impedimentos):
            c1.definir('aviso')
            if r is not None and r.impedimentos:
                self.p1_acao.pack(fill='x', pady=(px(8), 0))
                self.bt_ver_o_que_fazer.pack(side='left')
        elif r is not None and r.avisos and not self.avisos_aceitos:
            c1.definir('aviso')
            self.p1_acao.pack(fill='x', pady=(px(8), 0))
            self.bt_li_aviso.pack(side='left')
        else:
            c1.definir('feito' if r is not None else 'atual')
        # passo 2
        lib2 = self.liberado(2)
        self.bt_e_este.pack_forget()
        self.p2_ok.pack_forget()
        if s is None:
            c2.definir('atual' if lib2 else 'travado')
            self.p1_resumo.config(text=t('nao_encontrei_save'), fg=temas.cor('aviso'))
            self.selo.config(text='')
        else:
            plat = s.plataforma if s.plataforma in ('Steam', 'Epic') else t('plat_outra')
            self.p1_resumo.config(text=t('passo1_resumo', plat=plat, id=id_curto(s.id), quando=s.quando_jogado()),
                                  fg=temas.cor('fraco'))
            mais_recente = bool(self.saves) and s is self.saves[0]
            self.selo.config(text=t('selo_mais_recente') if mais_recente else t('selo_nao_recente'),
                             fg=temas.cor('destaque') if mais_recente else temas.cor('aviso'),
                             bg=temas.cor('destaque_suave') if mais_recente else temas.cor('aviso_suave'))
            if not lib2:
                c2.definir('travado')
            elif self.save_confirmado:
                c2.definir('feito')
                self.p2_ok.pack(side='left', pady=(px(8), 0))
            else:
                c2.definir('atual')
                self.bt_e_este.pack(side='left', pady=(px(8), 0))
        self.bt_e_este.state(['!disabled'] if lib2 and s is not None else ['disabled'])
        if self.saves:
            if not self.link_trocar.winfo_manager():
                self.link_trocar.pack(side='left', padx=(0, px(12)), before=self.link_escolher_pasta)
        else:
            self.link_trocar.pack_forget()
        # passo 3
        lib3 = self.liberado(3)
        ultimo = self._ultimo_backup_save()
        for w in self.p3_acao.winfo_children():
            w.pack_forget()
        if ultimo is None:
            c3.definir('atual' if lib3 else 'travado')
            self.p2_resumo.config(text=t('p3_obrigatorio'), fg=temas.cor('fraco'))
            self.bt_backup_save.pack(side='left', pady=(px(8), 0))
        else:
            dias = (datetime.datetime.now() - ultimo.quando).days
            tamanho = idiomas.tamanho(ultimo.tamanho)
            if dias >= core.DIAS_BACKUP_VELHO and not self.backup_velho_aceito:
                c3.definir('aviso' if lib3 else 'travado')
                self.p2_resumo.config(text=t('passo2_velho', dias=dias, tamanho=tamanho), fg=temas.cor('aviso'))
                self.bt_novo_backup.config(style='Primario.TButton')
                self.bt_novo_backup.pack(side='left', pady=(px(8), 0))
                self.link_continuar_velho.config(text=t('link_continuar_backup_velho', dias=dias))
                self.link_continuar_velho.pack(side='left', padx=(px(12), 0), pady=(px(8), 0))
            else:
                c3.definir('feito' if lib3 else 'travado')
                texto = (t('p3_velho_aceito', dias=dias, tamanho=tamanho) if dias >= core.DIAS_BACKUP_VELHO
                         else t('passo2_feito', quando=quando_relativo(ultimo.quando), tamanho=tamanho))
                self.p2_resumo.config(text=texto, fg=temas.cor('fraco'))
                self.bt_novo_backup.config(style='TButton')
                self.link_fazer_novo.pack(side='left', pady=(px(4), 0))
        estado3 = ['!disabled'] if lib3 and not self.bloqueado else ['disabled']
        for bt in (self.bt_backup_save, self.bt_novo_backup, self.link_continuar_velho, self.link_fazer_novo):
            bt.state(estado3)
        # passo 4
        lib4 = self.liberado(4)
        if lib4 and not self._modos_mostrado and self.tutoriais_automaticos and not self._modos_agendado:
            self._modos_agendado = True
            self._agendados.append(self.after(500, self._modos_se_preciso))
        self.lista.ativar(lib4, self.modo == 'resetar')
        marcados = self.marcados()
        if not lib4:
            c4.definir('travado')
        else:
            c4.definir('feito' if (marcados if self.modo == 'resetar' else self.foco is not None) else 'atual')
        for w in (self.link_marcar, self.link_desmarcar):
            w.pack_forget()
        if lib4 and self.modo == 'resetar':
            self.link_desmarcar.pack(side='right')
            self.link_marcar.pack(side='right', padx=(0, px(12)))
        self.atualizar_painel()

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
        marcados = self.marcados()
        if self.foco is None or (self.modo == 'resetar' and marcados and self.foco not in marcados):
            self.foco = marcados[0] if marcados else self.foco
        if self.modo == 'resetar' and not marcados and self.foco is not None and str(self.foco) not in \
                self.lista.selection():
            self.foco = None
        self.atualizar_passos()

    def ao_focar(self, chave):
        """Clique num mapa da lista."""
        if not self.liberado(4):
            return
        self.foco = chave
        self.n_voltar = 1
        m = self.mapas.get(chave)
        if self.modo == 'resetar' and m is not None and m.resetado:
            self.atualizar_passos()      # mapa já resetado: só mostra no painel
        elif self.modo == 'voltar':
            self.lista.selection_set((str(chave),))
        else:
            self.lista.alternar(str(chave))

    def trocar_modo(self, modo):
        if modo == self.modo:
            return
        self.modo = modo
        self.n_voltar = 1
        if modo == 'voltar':
            if self.foco is None and self.marcados():
                self.foco = self.marcados()[0]
            self.lista.selection_set((str(self.foco),) if self.foco is not None else ())
        else:
            self.lista.selection_set((str(self.foco),) if self.foco is not None and not (
                self.mapas.get(self.foco) and self.mapas[self.foco].resetado) else ())

    def alternar_trocar(self, abrir=None):
        self.trocar_aberto = (not self.trocar_aberto) if abrir is None else abrir
        if self.trocar_aberto:
            self.painel_trocar.pack(fill='x', pady=(px(8), 0), before=self.p1_fim)
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
        """Monta a janela de novo (novo idioma ou tema), mantendo o save e as escolhas."""
        save, saves, marcados = self.save_atual, self.saves, self.lista.selection()
        trocar, foco, modo, n = self.trocar_aberto, self.foco, self.modo, self.n_voltar
        confirmado, aceitos, velho = self.save_confirmado, self.avisos_aceitos, self.backup_velho_aceito
        for w in self.winfo_children():
            w.destroy()
        self._montar()
        self.verificar_permissao()
        self.saves = saves
        if save is not None and save in saves:
            self.mostrar_save(save)
        else:
            self.procurar_saves()
        self.save_confirmado, self.avisos_aceitos, self.backup_velho_aceito = confirmado, aceitos, velho
        self.modo, self.foco, self.n_voltar = modo, foco, n
        self.lista.selection_set([i for i in marcados if self.lista.exists(i)])
        self.foco, self.n_voltar = foco, n
        if trocar:
            self.alternar_trocar(True)
        if self.verificacao is not None:
            self.mostrar_status_verificacao(self.verificacao)
        self.mostrar_avisos_discretos()
        self.mostrar_atualizacao(self.atualizacao)
        self.atualizar_passos()

    # --------------------------------------------------- painel do mapa (passo 5)
    def _agendar_banner(self):
        if self._banner_job:
            try:
                self.after_cancel(self._banner_job)
            except tk.TclError:
                pass
        self._banner_job = self.after(60, self._desenhar_banner)

    def _desenhar_banner(self, info=None):
        """info = (chave ou None, linha pequena, título, subtítulo)."""
        self._banner_job = None
        if info is not None:
            self._banner_info = info
        if self._banner_info is None:
            return
        chave, pequeno, titulo, sub = self._banner_info
        w, h = self.banner.winfo_width(), int(self.banner.cget('height'))
        if w < 10:
            return
        cv = self.banner
        cv.delete('all')
        try:
            cv.imagem = faixa_mapa.imagem(chave, w, h, mestre=self)
            cv.create_image(0, 0, image=cv.imagem, anchor='nw')
        except Exception as e:   # sem imagem: fica só a cor do painel
            registro.log(f'Faixa do mapa sem imagem: {e!r}', 'AVISO')
        x, y = px(22), h - px(16)
        for dx, cor in ((1, '#000000'), (0, '#ffffff')):
            cv.create_text(x + dx, y + dx, text=sub, anchor='sw', fill=cor, font=temas.fonte(10),
                           width=w - px(44))
        cv.create_text(x + 1, y - px(22) + 1, text=titulo, anchor='sw', fill='#000000', font=temas.fonte(18, 'bold'))
        cv.create_text(x, y - px(22), text=titulo, anchor='sw', fill='#ffffff', font=temas.fonte(18, 'bold'))
        cv.create_text(x, y - px(58), text=pequeno, anchor='sw', fill='#e8e8e8', font=temas.fonte(8, 'bold'))

    def plano_do_foco(self):
        if self.foco is None or self.dados_save is None:
            return None
        try:
            return voltar.planejar(self.dados_save, self.foco)
        except core.ErroSave:
            return None

    def atualizar_painel(self):
        if not hasattr(self, 'banner'):
            return
        lib = self.liberado(4)
        sup = temas.cor('sup')
        self.circulo5.definir('atual' if lib and self.foco is not None else ('espera' if lib else 'travado'))
        for w in self.corpo_modo.winfo_children():
            w.destroy()
        self._pv = None
        self.bt_reset.pack_forget()
        self.bt_voltar.pack_forget()
        varios = self.modo == 'resetar' and len(self.marcados()) > 1
        self.modo_resetar.definir(self.modo == 'resetar', t('modo_resetar_sub_varios') if varios
                                  else t('modo_resetar_sub'), ativo=lib)
        self.modo_voltar.definir(self.modo == 'voltar', t('modo_voltar_sub'), ativo=lib)
        pequeno = '5 · ' + (t('p5_titulo_varios') if varios else t('p5_titulo_um')).upper()
        if not lib:
            self._desenhar_banner((None, '5 · ' + t('p5_titulo_um').upper(), '🔒 ' + t('p5_travado'),
                                   t('p5_travado_sub')))
            rotulo(self.corpo_modo, t('p5_travado_texto'), 'fraco', 10, fundo=sup, wraplength=px(560),
                   justify='left').pack(anchor='w', pady=(px(14), 0))
            self.bt_reset.pack(side='left', before=self.p4_resumo)
            self.bt_reset.config(text=t('bt_resetar_nenhum'), style='TButton')
            self.bt_reset.state(['disabled'])
            self.p4_resumo.config(text='')
            return
        if self.modo == 'resetar':
            self._painel_resetar(pequeno)
        else:
            self._painel_voltar(pequeno)

    def _banner_do_mapa(self, pequeno, chave, sub):
        self._desenhar_banner((chave, pequeno, core.nome_do_mapa(chave), sub))

    def _sub_historia(self, chave):
        """'Você está em: X · missão 5 de 8 da história' (ou o resumo do mapa)."""
        m = self.mapas.get(chave)
        if m is not None and m.resetado:
            return t('mapa_zerado_banner')
        plano = None
        if chave == self.foco:
            plano = self.plano_do_foco()
        elif self.dados_save is not None:
            try:
                plano = voltar.planejar(self.dados_save, chave)
            except core.ErroSave:
                plano = None
        if plano is None:
            return t('missoes_c_de_t', c=m.concluidas, t=m.total) if m else ''
        if plano.concluida:
            return t('historia_concluida', t=len(plano.historia))
        return t('voce_esta_em', nome=self.nome_missao(plano, plano.atual), n=plano.indice_atual + 1,
                 t=len(plano.historia))

    def _painel_resetar(self, pequeno):
        sup = temas.cor('sup')
        marcados = self.marcados()
        corpo = self.corpo_modo
        if len(marcados) > 1:
            titulo = ' + '.join(core.nome_do_mapa(k) for k in marcados[:2]) + (' …' if len(marcados) > 2 else '')
            total = sum(self.mapas[k].concluidas for k in marcados)
            self._desenhar_banner((marcados[0], pequeno, titulo, t('mapas_marcados_resumo', n=len(marcados), c=total)))
        elif marcados:
            self._banner_do_mapa(pequeno, marcados[0], self._sub_historia(marcados[0]))
        elif self.foco is not None:
            self._banner_do_mapa(pequeno, self.foco, self._sub_historia(self.foco))
        else:
            self._desenhar_banner((None, pequeno, t('p5_escolha'), t('p5_escolha_sub_resetar')))
        rotulo(corpo, t('mapas_marcados').upper(), negrito=True, tamanho=9, fundo=sup).pack(anchor='w', pady=(px(8), px(4)))
        chips = tk.Frame(corpo, bg=sup)
        chips.pack(fill='x')
        if marcados:
            linha = tk.Frame(chips, bg=sup)
            linha.pack(fill='x')
            largura = 0
            for k in marcados:
                m = self.mapas[k]
                texto = t('chip_mapa', nome=m.nome, c=m.concluidas, t=m.total)
                if largura > px(420):
                    linha = tk.Frame(chips, bg=sup)
                    linha.pack(fill='x', pady=(px(4), 0))
                    largura = 0
                rotulo(linha, texto, 'destaque', 9, negrito=True, fundo=temas.cor('destaque_suave'), padx=px(9),
                       pady=px(2)).pack(side='left', padx=(0, px(6)))
                largura += len(texto) * px(7)
        else:
            rotulo(chips, t('nenhum_mapa_marcado'), 'fraco', 9, fundo=sup).pack(anchor='w')
        caixas = tk.Frame(corpo, bg=sup)
        caixas.pack(fill='x', pady=(px(10), 0))
        caixas.columnconfigure(0, weight=1, uniform='c')
        caixas.columnconfigure(1, weight=1, uniform='c')
        for col, (tit, txt) in enumerate(((t('oque_acontece'), t('oque_acontece_txt')),
                                         (t('oque_nao_muda'), t('oque_nao_muda_txt')))):
            caixa = tk.Frame(caixas, bg=sup, highlightbackground=temas.cor('borda'), highlightthickness=1)
            caixa.grid(row=0, column=col, sticky='nsew', padx=(0, px(6)) if col == 0 else (px(6), 0))
            rotulo(caixa, tit, negrito=True, tamanho=9, fundo=sup).pack(anchor='w', padx=px(10), pady=(px(8), 0))
            rotulo(caixa, txt, 'fraco', 9, fundo=sup, wraplength=px(250), justify='left').pack(
                anchor='w', padx=px(10), pady=(px(2), px(8)))
        dica = tk.Frame(corpo, bg=sup, highlightbackground=temas.cor('borda'), highlightthickness=1)
        dica.pack(fill='x', pady=(px(10), 0))
        rotulo(dica, '💡 ' + t('dica_voltar'), 'fraco', 9, fundo=sup, wraplength=px(540), justify='left').pack(
            anchor='w', padx=px(10), pady=px(8))
        # ação
        n = len(marcados)
        self.bt_reset.pack(side='left', before=self.p4_resumo)
        if n == 0:
            self.bt_reset.config(text=t('bt_resetar_nenhum'), style='TButton')
            self.bt_reset.state(['disabled'])
            self.p4_resumo.config(text=t('passo4_nenhum'))
        else:
            self.bt_reset.config(text=t('bt_resetar_um') if n == 1 else t('bt_resetar_varios', n=n),
                                 style='Grande.TButton')
            self.bt_reset.state(['!disabled'] if not self.bloqueado else ['disabled'])
            self.p4_resumo.config(text=t('acao_resetar_aviso'))

    def _painel_voltar(self, pequeno):
        sup = temas.cor('sup')
        corpo = self.corpo_modo
        self.bt_voltar.pack(side='left', before=self.p4_resumo)
        self.bt_voltar.state(['disabled'])
        self.bt_voltar.config(text=t('bt_voltar_nenhum'))
        self.p4_resumo.config(text='')
        chave = self.foco
        if chave is None:
            self._desenhar_banner((None, pequeno, t('p5_escolha'), t('p5_escolha_sub_voltar')))
            rotulo(corpo, t('voltar_escolha_mapa'), 'fraco', 10, fundo=sup, wraplength=px(560), justify='left').pack(
                anchor='w', pady=(px(14), 0))
            return
        self._banner_do_mapa(pequeno, chave, self._sub_historia(chave))
        m = self.mapas.get(chave)
        plano = self.plano_do_foco()

        def aviso(texto):
            rotulo(corpo, texto, 'fraco', 10, fundo=sup, wraplength=px(560), justify='left').pack(
                anchor='w', pady=(px(14), 0))
        if m is not None and m.resetado:
            return aviso(t('voltar_zerado'))
        if plano is None:
            return aviso(t('voltar_sem_dados'))
        minimo = voltar.minimo_seguro(self.dados_save, plano)
        seguro = voltar.maximo_seguro(self.dados_save, plano)
        if plano.maximo == 0 and minimo > 0:
            return aviso(t('voltar_comeco'))
        if seguro < minimo:
            return aviso(t('voltar_mudou'))
        self.n_voltar = max(minimo, min(self.n_voltar, seguro))
        aviso_suave = temas.cor('aviso_suave')
        grade = tk.Frame(corpo, bg=sup)
        grade.pack(fill='both', expand=True, pady=(px(8), 0))
        grade.columnconfigure(0, minsize=px(270))
        grade.columnconfigure(1, weight=1)
        esq = tk.Frame(grade, bg=sup)
        esq.grid(row=0, column=0, sticky='nw')
        rotulo(esq, t('quantas_voltar').upper(), negrito=True, tamanho=9, fundo=sup).pack(anchor='w')
        cont = tk.Frame(esq, bg=sup)
        cont.pack(anchor='w', pady=(px(6), 0))
        self.bt_menos = ttk.Button(cont, text='−', width=3, style='Fundo.TButton', command=lambda: self.mudar_n(self.n_voltar - 1))
        self.bt_menos.pack(side='left')
        self.valor_n = rotulo(cont, '', negrito=True, tamanho=20, fundo=sup, width=3, anchor='center')
        self.valor_n.pack(side='left')
        self.bt_mais = ttk.Button(cont, text='+', width=3, style='Fundo.TButton', command=lambda: self.mudar_n(self.n_voltar + 1))
        self.bt_mais.pack(side='left')
        rotulo(cont, t('de_no_maximo', n=seguro), 'fraco', 9, fundo=sup).pack(side='left', padx=(px(10), 0))
        self.slider = None
        if seguro > minimo:
            self.slider = ttk.Scale(esq, from_=minimo, to=seguro, orient='horizontal', length=px(250),
                                    style='Voltar.Horizontal.TScale', command=self._slider_mudou)
            self.slider.set(self.n_voltar)
            self.slider.pack(anchor='w', pady=(px(8), 0))
            marcas = tk.Frame(esq, bg=sup, width=px(250), height=px(14))
            marcas.pack(anchor='w')
            marcas.pack_propagate(False)
            for v in sorted({minimo, seguro} | ({(minimo + seguro) // 2} if seguro - minimo > 4
                                                else set(range(minimo, seguro + 1)))):
                rotulo(marcas, str(v), 'fraquinho', 7, fundo=sup).place(
                    relx=(v - minimo) / (seguro - minimo),
                    x=0 if v == minimo else (-px(8) if v == seguro else -px(3)), y=0)
        if minimo == 0:
            rotulo(esq, t('zero_explica'), 'fraquinho', 8, fundo=sup, wraplength=px(260), justify='left').pack(
                anchor='w', pady=(px(2), 0))
        if seguro < plano.maximo:
            rotulo(esq, t('voltar_limite', n=seguro), 'aviso', 8, fundo=sup, wraplength=px(260), justify='left').pack(
                anchor='w', pady=(px(4), 0))
        destino = tk.Frame(esq, bg=aviso_suave)
        destino.pack(fill='x', pady=(px(12), 0))
        rotulo(destino, t('recomecar_em').upper(), 'aviso', 8, negrito=True, fundo=aviso_suave).pack(
            anchor='w', padx=px(10), pady=(px(8), 0))
        self.destino_nome = rotulo(destino, '', negrito=True, tamanho=11, fundo=aviso_suave, wraplength=px(250),
                                   justify='left')
        self.destino_nome.pack(anchor='w', padx=px(10))
        self.destino_pos = rotulo(destino, '', 'fraco', 9, fundo=aviso_suave)
        self.destino_pos.pack(anchor='w', padx=px(10), pady=(0, px(8)))
        self.tambem = rotulo(esq, '', 'fraco', 9, fundo=sup, wraplength=px(260), justify='left')
        self.tambem.pack(anchor='w', pady=(px(10), 0))
        if not self.nomes:
            linha = tk.Frame(esq, bg=sup)
            linha.pack(anchor='w', pady=(px(8), 0))
            rotulo(linha, t('nomes_sem_jogo'), 'fraquinho', 8, fundo=sup, wraplength=px(260), justify='left').pack(
                anchor='w')
            comp.Link(linha, t('link_escolher_jogo'), self.escolher_pasta_jogo, fundo=sup, tamanho=8).pack(anchor='w')
        # linha do tempo da história
        dir_ = tk.Frame(grade, bg=sup)
        dir_.grid(row=0, column=1, sticky='nsew', padx=(px(16), 0))
        cab = tk.Frame(dir_, bg=sup)
        cab.pack(fill='x')
        rotulo(cab, t('historia_de', mapa=core.nome_do_mapa(chave)).upper(), negrito=True, tamanho=9, fundo=sup).pack(
            side='left')
        feitas = sum(1 for x in plano.historia if x.estado == core.CONCLUIDA)
        rotulo(cab, t('n_de_t_concluidas', c=feitas, t=len(plano.historia)), 'fraco', 8, fundo=sup).pack(side='right')
        self.linha_do_tempo = tk.Frame(dir_, bg=sup)
        self.linha_do_tempo.pack(fill='x', pady=(px(4), 0))
        self._pv = (chave, plano, seguro, minimo)
        self._preencher_voltar()

    def _preencher_voltar(self):
        """Atualiza a parte do painel "Voltar missões" que muda com a quantidade (sem refazer o controle)."""
        chave, plano, seguro, minimo = self._pv
        n = self.n_voltar
        self.valor_n.config(text=str(n))
        self.bt_menos.state(['disabled'] if n <= minimo else ['!disabled'])
        self.bt_mais.state(['disabled'] if n >= seguro else ['!disabled'])
        if self.slider is not None and int(round(float(self.slider.get()))) != n:
            self._mexendo_slider = True
            self.slider.set(n)
            self._mexendo_slider = False
        alvo = plano.alvo(n)
        self.destino_nome.config(text=self.nome_missao(plano, alvo))
        self.destino_pos.config(text=t('missao_n_de', n=plano.posicao(alvo), t=len(plano.historia)) +
                                (t('do_comeco') if n == 0 else ''))
        secs = plano.secundarias_que_voltam(n)
        if secs:
            texto = t('tambem_volta_uma') if len(secs) == 1 else t('tambem_voltam', n=len(secs))
            if self.nomes:
                texto += '\n' + juntar_nomes(self.nome_missao(plano, s) for s in secs) + '.'
        else:
            texto = t('nenhuma_secundaria')
        self.tambem.config(text=texto + '\n' + t('outras_nao_mudam'))
        for w in self.linha_do_tempo.winfo_children():
            w.destroy()
        self._timeline(self.linha_do_tempo, plano, n)
        self.bt_voltar.config(text=self._texto_bt_voltar(chave, n))
        self.bt_voltar.state(['!disabled'] if not self.bloqueado else ['disabled'])
        self.p4_resumo.config(text=t('acao_voltar_aviso'))

    @staticmethod
    def _texto_bt_voltar(chave, n):
        mapa = core.nome_do_mapa(chave)
        if n == 0:
            return t('bt_recomecar_atual', mapa=mapa)
        return t('bt_voltar_1', mapa=mapa) if n == 1 else t('bt_voltar_n', n=n, mapa=mapa)

    def _timeline(self, pai, plano, n):
        c = temas.CORES[temas.atual()]
        sup = c['sup']
        volta = {m.id for m in plano.historia_que_volta(n)} | set(plano.conjunto(n)) & {m.id for m in plano.historia}
        alvo = plano.alvo(n)
        hist = plano.historia
        ia = hist.index(alvo)
        fim = min(len(hist), max(plano.indice_atual + 2, ia + JANELA_TIMELINE))
        ini = max(0, min(ia - 2, fim - JANELA_TIMELINE))
        if ini > 0:
            rotulo(pai, '   …', 'fraquinho', 9, fundo=sup).pack(anchor='w')
        for i in range(ini, fim):
            m = hist[i]
            voltando = m.id in volta and m.estado in (core.CONCLUIDA, core.EM_ANDAMENTO)
            atual = i == plano.indice_atual
            fundo = c['aviso_suave'] if voltando else sup
            linha = tk.Frame(pai, bg=fundo, highlightbackground=c['aviso'] if m is alvo else fundo,
                             highlightthickness=1)
            linha.pack(fill='x', pady=px(1))
            rotulo(linha, str(i + 1), 'fraco', 8, fundo=fundo, width=3, anchor='e').pack(side='left', padx=(px(2), px(6)))
            if voltando:
                simbolo, cor = '↺', c['aviso']
            elif m.estado == core.CONCLUIDA:
                simbolo, cor = '✓', c['destaque']
            elif m.estado == core.EM_ANDAMENTO:
                simbolo, cor = '▶', c['destaque']
            else:
                simbolo, cor = '○', c['fraquinho']
            tk.Label(linha, text=simbolo, bg=fundo, fg=cor, font=temas.fonte(10, 'bold'), width=2).pack(side='left')
            nome = self.nome_missao(plano, m)
            rotulo(linha, nome, 'fraquinho' if (m.estado not in (core.CONCLUIDA, core.EM_ANDAMENTO) and not voltando)
                   else 'texto', 9, fundo=fundo).pack(side='left', padx=(px(4), 0), pady=px(3))
            tag = ''
            if m is alvo:
                tag = t('tag_recomeca')
            elif voltando:
                tag = t('tag_voce_esta') if atual else t('tag_volta')
            elif atual:
                tag = t('tag_voce_esta')
            if tag:
                rotulo(linha, tag, 'aviso' if voltando or m is alvo else 'destaque', 8, negrito=True,
                       fundo=fundo).pack(side='right', padx=px(8))
        if fim < len(hist):
            rotulo(pai, '   …', 'fraquinho', 9, fundo=sup).pack(anchor='w')

    def mudar_n(self, n):
        """Botões − / + e o controle deslizante do "Voltar missões"."""
        if getattr(self, '_pv', None) is None or self._pv[0] != self.foco:
            return
        n = max(self._pv[3], min(int(n), self._pv[2]))
        if n != self.n_voltar:
            self.n_voltar = n
            self._preencher_voltar()

    def _slider_mudou(self, valor):
        if getattr(self, '_mexendo_slider', False):
            return
        n = int(round(float(valor)))
        if n != self.n_voltar:
            self.mudar_n(n)

    # --------------------------------------------------- verificação e avisos
    def verificar_agora(self):
        self.verificacao = diagnostico.verificar(self.save_atual, self.raiz)
        if not self.verificacao.avisos:
            self.avisos_aceitos = False
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
            texto, cor = (t('status_avisos_aceitos') if self.avisos_aceitos else t('status_avisos', n=len(r.avisos)),
                          temas.cor('aviso'))
        else:
            texto, cor = t('status_ok'), temas.cor('destaque')
        self.status_verif.config(text=texto, fg=cor)
        self.atualizar_passos()

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
            self.aviso_discreto.pack(fill='x', pady=(0, px(8)), before=self.fim_avisos)
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
            self.faixa.pack(fill='x', pady=(0, px(10)), before=self.fim_avisos)
        estado = ['disabled'] if self.bloqueado else ['!disabled']
        for bt in (self.bt_reset, self.bt_restaurar, self.bt_backup_save, self.bt_restaurar_save,
                   self.bt_novo_backup, self.bt_voltar):
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
            self.dados_save = None
            self.perfil = None
            self.mostrar_mapas(None)
            self.atualizar_aviso_saves()
            self.info.config(text='')
            self._mostrar_stats()
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
            rb.pack(side='left', padx=(0, px(12)))

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
            self.aviso_saves.pack(fill='x', pady=(px(4), 0), before=self.stats)
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
        novo = vis[i] if 0 <= i < len(vis) else None
        if novo is not self.save_atual:
            self.save_confirmado = False
            self.backup_velho_aceito = False
            self.foco = None
        self.save_atual = novo
        self.atualizar_aviso_saves()
        self.lista.selection_set(())
        self.recarregar()

    def recarregar(self):
        s = self.save_atual
        if s is None:
            self.dados_save = None
            self.mostrar_mapas(None)
            self._mostrar_stats()
            self.atualizar_passos()
            return
        try:
            mapas = core.mapas_para_mostrar(s, self.raiz)
            self.dados_save = core.Save.abrir(s.arquivo)
        except (OSError, core.ErroSave) as e:
            self.dados_save = None
            self.mostrar_mapas(None)
            self.info.config(text=t('nao_li_save', erro=e), fg=temas.cor('erro'))
            self.atualizar_passos()
            return
        self.perfil = perfil.ler(s.pasta)
        self.mostrar_mapas(mapas)
        self._mostrar_stats()
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
        if self.foco is not None and self.foco not in self.mapas:
            self.foco = None
        self.atualizar_passos()

    def resumo_historia(self, chave):
        """(concluídas, total) da história do mapa, ou None se não houver dados."""
        if self.dados_save is None:
            return None
        try:
            plano = voltar.planejar(self.dados_save, chave)
        except core.ErroSave:
            return None
        if plano is None:
            return None
        return sum(1 for m in plano.historia if m.estado == core.CONCLUIDA), len(plano.historia)

    def mostrar_mapas(self, mapas):
        self.mapas = {m.chave: m for m in mapas or []}
        if mapas is None:
            vazio = t('passo3_sem_save')
        else:
            vazio = t('passo3_vazio')
        historias = {m.chave: self.resumo_historia(m.chave) for m in mapas or [] if not m.resetado}
        self.lista.mostrar(mapas or [], vazio, historias)

    # ---------------------------------------------------------------- ações
    def _pode_alterar(self, parent=None):
        if not self.verificar_permissao():
            messagebox.showwarning(TITULO, t('aviso_usar_faixa'), parent=parent)
            return False
        return self.checar_antes(parent)

    # Confirmação, "Pronto!" e apelido do backup em janelas próprias (os testes usam as caixinhas simples).
    janelas_visuais = True

    def _exigir_backup_completo(self):
        """Backup completo é obrigatório antes de mexer nas missões (passo 3)."""
        if core.tem_backup_save(self.save_atual, self.raiz):
            return True
        if not messagebox.askyesno(TITULO, t('backup_obrigatorio'), icon='warning'):
            return False
        return self.fazer_backup_save(perguntar_ok=False, ja_verificado=True)

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
        if not self._exigir_backup_completo():
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
            self._desfazer_depois_da_mudanca(JanelaPronto(self, sel))
        else:
            messagebox.showinfo(TITULO, t('reset_ok', nomes=nomes))

    def voltar_missoes(self):
        """Botão "Voltar N missões em <mapa>"."""
        if self.save_atual is None or self.foco is None:
            messagebox.showinfo(TITULO, t('selecione_mapa'))
            return
        chave, n = self.foco, self.n_voltar
        if not self._pode_alterar():
            return
        try:
            self.dados_save = core.Save.abrir(self.save_atual.arquivo)   # o save pode ter mudado
        except (OSError, core.ErroSave) as e:
            self.mostrar_erro(e, 'Voltar missões', prefixo='nao_foi_possivel_voltar')
            return
        plano = self.plano_do_foco()
        if plano is None or plano.alvo(n) is None or not (
                voltar.minimo_seguro(self.dados_save, plano) <= n <= voltar.maximo_seguro(self.dados_save, plano)):
            messagebox.showwarning(TITULO, t('erro_voltar_invalido'))
            self.recarregar()
            return
        if not self._exigir_backup_completo():
            return
        alvo = plano.alvo(n)
        nome_alvo = self.nome_missao(plano, alvo)
        secs = [self.nome_missao(plano, s) for s in plano.secundarias_que_voltam(n)]
        de = self.nome_missao(plano, plano.atual) if not plano.concluida else t('historia_concluida_curto')
        if self.janelas_visuais:
            janela = JanelaConfirmarVoltar(self, chave, n, de, nome_alvo, secs)
            self.wait_window(janela)
            confirmado = janela.confirmado
        else:
            confirmado = messagebox.askyesno(TITULO, t('confirmar_voltar', mapa=core.nome_do_mapa(chave), n=n,
                                                       nome=nome_alvo), icon='warning')
        if not confirmado:
            return
        registro.log(f'Voltar missões pedido: {core.nome_do_mapa(chave)}, {n} (recomeçar em {alvo.id:#x})')
        try:
            b = voltar.voltar_missoes(self.save_atual, chave, n, self.raiz)
        except (OSError, core.ErroSave) as e:
            self.mostrar_erro(e, 'Voltar missões', prefixo='nao_foi_possivel_voltar')
            self.recarregar()
            return
        self.n_voltar = 1
        self.recarregar()
        self.avisar_resultado(b)
        if self.janelas_visuais:
            self._desfazer_depois_da_mudanca(JanelaProntoVoltar(self, chave, nome_alvo))
        else:
            messagebox.showinfo(TITULO, t('voltar_ok', mapa=core.nome_do_mapa(chave), nome=nome_alvo))

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
        self.backup_velho_aceito = False
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


class CartaoModo(tk.Frame):
    """Cartão clicável de uma opção do passo 5 ("Resetar tudo" / "Voltar missões da história")."""

    def __init__(self, pai, icone, titulo, sub, comando):
        c = temas.CORES[temas.atual()]
        super().__init__(pai, bg=c['sup'], highlightthickness=max(1, px(1.5)), highlightbackground=c['borda'],
                         cursor='hand2')
        self.comando, self.ativo, self.marcado = comando, True, False
        self.radio = tk.Label(self, bd=0)
        self.radio.grid(row=0, column=0, rowspan=2, sticky='n', padx=(px(12), px(8)), pady=(px(12), 0))
        self.icone = tk.Label(self, text=icone, bd=0, font=temas.fonte(14))
        self.icone.grid(row=0, column=1, rowspan=2, sticky='n', padx=(0, px(8)), pady=(px(9), 0))
        self.titulo = tk.Label(self, text=titulo, bd=0, anchor='w', font=temas.fonte(10, 'bold'))
        self.titulo.grid(row=0, column=2, sticky='w', pady=(px(10), 0), padx=(0, px(10)))
        self.sub = tk.Label(self, text=sub, bd=0, anchor='w', justify='left', font=temas.fonte(9),
                            wraplength=px(230))
        self.sub.grid(row=1, column=2, sticky='w', pady=(px(1), px(10)), padx=(0, px(10)))
        self.columnconfigure(2, weight=1)
        for w in (self, self.radio, self.icone, self.titulo, self.sub):
            w.bind('<Button-1>', lambda e: self.ativo and self.comando())

    def definir(self, marcado, sub=None, ativo=True):
        c = temas.CORES[temas.atual()]
        self.marcado, self.ativo = marcado, ativo
        bg = c['destaque_suave'] if marcado and ativo else c['sup']
        self.configure(bg=bg, highlightbackground=c['destaque'] if marcado and ativo else c['borda'],
                       cursor='hand2' if ativo else '')
        if sub is not None:
            self.sub.config(text=sub)
        for w in (self.radio, self.icone, self.titulo, self.sub):
            w.configure(bg=bg)
        self.titulo.config(fg=c['texto'] if ativo else c['fraquinho'])
        self.sub.config(fg=c['fraco'] if ativo else c['fraquinho'])
        self.icone.config(fg=c['texto'] if ativo else c['fraquinho'])
        tam = px(16)

        def fazer():
            p = comp.Pintura(tam, tam, bg)
            m = tam / 2
            if marcado and ativo:
                p.circulo(m, m, m - 0.5, c['destaque'])
                p.circulo(m, m, m * 0.38, bg)
            else:
                p.circulo(m, m, m - 0.5, c['sup'], borda=c['fraquinho'], espessura=1.5)
            return p
        self.radio.configure(image=comp.guardar_imagem(self, ('radio', marcado and ativo, bg, tam), fazer))

    def invoke(self):
        if self.ativo:
            return self.comando()


class ListaMapas(comp.AreaRolavel):
    """Lista de mapas: quadradinho da cor do mapa, nome, barrinha e "História c/t".

    Funciona parecido com a lista antiga (Treeview): selection_set, selection, item,
    exists, see e get_children usam a chave do mapa como texto ('21').
    No modo "Resetar tudo" cada linha tem caixinha (vários mapas); no modo "Voltar missões",
    clicar escolhe um mapa só."""

    def __init__(self, pai, ao_mudar, ao_focar):
        super().__init__(pai, largura=None, fundo=temas.cor('sup'), margem=0)
        self.ao_mudar, self.ao_focar = ao_mudar, ao_focar
        self.linhas = {}
        self.ordem = []
        self._sel = []
        self.vazio = None
        self.ativa = True
        self.caixinhas = True

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
        self._redesenhar()
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
        if linha is not None:
            self.mostrar_linha(linha)

    def mostrar_linha(self, widget):
        comp.AreaRolavel.mostrar(self, widget)

    # --- desenho
    def ativar(self, ativa, caixinhas):
        if ativa != self.ativa or caixinhas != self.caixinhas:
            self.ativa, self.caixinhas = ativa, caixinhas
            self._redesenhar(forcar=True)

    def _redesenhar(self, forcar=False):
        app = self.winfo_toplevel()
        foco = str(getattr(app, 'foco', None))
        for iid, linha in self.linhas.items():
            linha.desenhar(iid in self._sel, foco=(iid == foco), forcar=forcar)

    def atualizar_dicas(self):
        pass

    def mostrar(self, mapas, texto_vazio='', historias=None):
        for w in self.dentro.winfo_children():
            w.destroy()
        self.linhas, self.ordem = {}, []
        antes = self._sel
        self._sel = []
        if not mapas:
            self.vazio = tk.Label(self.dentro, text=texto_vazio, bg=temas.cor('sup'), fg=temas.cor('fraco'),
                                  font=temas.fonte(9), pady=px(14), wraplength=px(300), justify='left')
            self.vazio.pack(fill='x')
            return
        for m in mapas:
            iid = str(m.chave)
            linha = LinhaMapa(self.dentro, iid, m, self._clique, (historias or {}).get(m.chave))
            linha.pack(fill='x')
            self.linhas[iid] = linha
            self.ordem.append(iid)
        self._sel = [i for i in antes if i in self.linhas]
        self._redesenhar(forcar=True)

    def _clique(self, iid):
        if not self.ativa:
            return
        if self.ao_focar:
            self.ao_focar(int(iid))

    def alternar(self, iid):
        if iid in self._sel:
            self._sel.remove(iid)
        else:
            self._sel.append(iid)
        self._redesenhar()
        if self.ao_mudar:
            self.ao_mudar()


class LinhaMapa(tk.Frame):
    def __init__(self, pai, iid, mapa, ao_clicar, historia=None):
        self.sup = temas.cor('sup')
        super().__init__(pai, bg=self.sup, cursor='hand2')
        self.iid, self.mapa, self.ao_clicar, self.historia = iid, mapa, ao_clicar, historia
        self.marcada = self.focada = None
        self._hover = False
        self._caixinhas = None
        self.caixa = tk.Label(self, bd=0, bg=self.sup)
        self.cor = tk.Label(self, bd=0, bg=self.sup)
        self.nome = tk.Label(self, text=mapa.nome, anchor='w', bd=0, bg=self.sup, font=temas.fonte(9))
        self.barra = tk.Label(self, bd=0, bg=self.sup)
        self.n = tk.Label(self, anchor='e', bd=0, bg=self.sup, font=temas.fonte(8))
        self.caixa.grid(row=0, column=0, padx=(px(8), 0), pady=px(4))
        self.cor.grid(row=0, column=1, padx=(px(6), px(8)))
        self.nome.grid(row=0, column=2, sticky='ew')
        self.barra.grid(row=0, column=3, padx=(px(6), px(4)))
        self.n.grid(row=0, column=4, sticky='e', padx=(0, px(8)))
        self.columnconfigure(2, weight=1)
        self.columnconfigure(4, minsize=px(78))
        for w in (self, self.caixa, self.cor, self.nome, self.barra, self.n):
            w.bind('<Button-1>', lambda e: self.ao_clicar(self.iid))
            w.bind('<Enter>', lambda e: self._passar(True))
            w.bind('<Leave>', lambda e: self._passar(False))
        comp.Dica(self.nome, self.dica)

    def dica(self):
        m = self.mapa
        if m.resetado:
            return t('dica_mapa_resetado', t=m.total)
        return t('dica_mapa', c=m.concluidas, a=m.em_andamento, t=m.total)

    def _passar(self, dentro):
        if dentro == self._hover:
            return
        self._hover = dentro
        self.desenhar(self.marcada, self.focada, forcar=True)

    def desenhar(self, marcada, foco=False, forcar=False):
        lista = self.master.master.master   # dentro -> canvas -> ListaMapas
        ativa = getattr(lista, 'ativa', True)
        caixinhas = getattr(lista, 'caixinhas', True)
        if marcada == self.marcada and foco == self.focada and caixinhas == self._caixinhas and not forcar:
            return
        self.marcada, self.focada, self._caixinhas = marcada, foco, caixinhas
        c = temas.CORES[temas.atual()]
        destacada = (marcada if caixinhas else foco) and ativa
        bg = c['destaque_suave'] if destacada else (c['hover'] if self._hover and ativa else c['sup'])
        for w in (self, self.caixa, self.cor, self.nome, self.barra, self.n):
            w.configure(bg=bg, cursor='hand2' if ativa else '')
        m = self.mapa
        self.cor.configure(image=comp.img_ret(self, px(20), px(14), px(3), faixa_mapa.cor(m.chave), bg))
        if caixinhas:
            if m.resetado:
                self.caixa.configure(image=comp.img_vazia(self, bg, px(16), px(16)))
            else:
                self.caixa.configure(image=comp.img_caixa(self, bool(marcada) and ativa, bg))
            self.caixa.grid()
        else:
            self.caixa.configure(image=comp.img_vazia(self, bg, px(1), px(16)))
        texto_cor = c['texto'] if ativa else c['fraquinho']
        self.nome.configure(fg=c['fraco'] if m.resetado else texto_cor,
                            font=temas.fonte(9, 'bold') if destacada else temas.fonte(9))
        if m.resetado:
            self.barra.configure(image=comp.img_barra(self, 0, c['fraquinho'], bg, largura=px(42)))
            self.n.configure(text=t('mapa_resetado_curto'), fg=c['destaque'] if ativa else c['fraquinho'])
            return
        if self.historia:
            feitas, total = self.historia
            fracao = feitas / total if total else 0
            texto = t('hist_n', c=feitas, t=total)
        else:
            fracao = m.concluidas / m.total if m.total else 0
            texto = f'{m.concluidas}/{m.total}'
        self.barra.configure(image=comp.img_barra(self, fracao, c['destaque'] if destacada else c['fraquinho'], bg,
                                                  largura=px(42)))
        self.n.configure(text=texto, fg=c['fraco'] if ativa else c['fraquinho'])


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


class JanelaConfirmarVoltar(Janela):
    """Confirmação do "Voltar missões": de onde para onde, o que volta junto e os avisos."""

    def __init__(self, app, chave, n, de, para, secundarias):
        super().__init__(app, t('conf_janela'))
        self.confirmado = False
        self.protocol('WM_DELETE_WINDOW', self.cancelar)
        c = temas.CORES[temas.atual()]
        sup = c['sup']
        corpo = ttk.Frame(self, padding=(px(26), px(22), px(26), px(18)))
        corpo.pack(fill='both', expand=True)
        cab = ttk.Frame(corpo)
        cab.pack(fill='x')
        icone = comp.Circulo(cab, '⏪', tam=px(40))
        icone.definir('aviso')
        icone.itemconfigure(icone._txt, font=temas.fonte(13, 'bold'))
        icone.pack(side='left', padx=(0, px(14)))
        textos = ttk.Frame(cab)
        textos.pack(side='left', fill='x')
        self.titulo = (t('confv_titulo_0') if n == 0 else t('confv_titulo_1') if n == 1
                       else t('confv_titulo', n=n)).upper()
        rotulo(textos, self.titulo, negrito=True, tamanho=13).pack(anchor='w')
        rotulo(textos, f'{core.nome_do_mapa(chave)}  ·  ' + t('conf_save', save=app.save_atual.nome_curto()),
               'fraco', 9).pack(anchor='w')

        quadro = tk.Frame(corpo, bg=sup, highlightbackground=c['borda'], highlightthickness=1)
        quadro.pack(fill='x', pady=(px(16), px(4)))
        quadro.columnconfigure(1, weight=1)
        rotulo(quadro, t('confv_de'), 'fraco', 9, fundo=sup).grid(row=0, column=0, sticky='w', padx=(px(14), px(10)),
                                                                pady=(px(10), px(3)))
        rotulo(quadro, de, negrito=True, fundo=sup).grid(row=0, column=1, sticky='w', pady=(px(10), px(3)))
        rotulo(quadro, t('confv_para'), 'aviso', 9, negrito=True, fundo=sup).grid(
            row=1, column=0, sticky='w', padx=(px(14), px(10)), pady=(px(3), px(10)))
        rotulo(quadro, para, 'aviso', 11, negrito=True, fundo=sup).grid(row=1, column=1, sticky='w',
                                                                       pady=(px(3), px(10)), padx=(0, px(14)))
        checks = ttk.Frame(corpo)
        checks.pack(fill='x', pady=(px(12), 0))
        if secundarias:
            _linha_com_icone(checks, 'aviso', t('confv_sec', nomes=juntar_nomes(secundarias)))
        _linha_com_icone(checks, 'feito', t('confv_outros'))
        _linha_com_icone(checks, 'feito', t('conf_backup'))
        _linha_com_icone(checks, 'aviso', t('confv_xp'))
        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(18), 0))
        self.bt_sim = ttk.Button(bts, text=t('confv_sim'), style='Voltar.TButton', command=self.confirmar)
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


class JanelaProntoVoltar(Janela):
    """Depois do "Voltar missões": "Pronto!" e o que fazer agora."""

    def __init__(self, app, chave, nome):
        super().__init__(app, t('pronto_janela'))
        c = temas.CORES[temas.atual()]
        corpo = ttk.Frame(self, padding=(px(30), px(24), px(30), px(20)))
        corpo.pack(fill='both', expand=True)
        icone = comp.Circulo(corpo, '', tam=px(56))
        icone.definir('feito')
        icone.pack(anchor='w')
        self.titulo = t('prontov_titulo').upper()
        rotulo(corpo, self.titulo, negrito=True, tamanho=14, wraplength=px(500), justify='left').pack(
            anchor='w', pady=(px(14), px(4)))
        rotulo(corpo, t('prontov_sub', mapa=core.nome_do_mapa(chave), nome=nome), 'fraco', 10, wraplength=px(500),
               justify='left').pack(anchor='w')
        sup = c['sup']
        agora = tk.Frame(corpo, bg=sup, highlightbackground=c['borda'], highlightthickness=1)
        agora.pack(fill='x', pady=(px(18), 0))
        dentro = tk.Frame(agora, bg=sup)
        dentro.pack(fill='x', padx=px(16), pady=px(14))
        rotulo(dentro, t('pronto_agora').upper(), negrito=True, tamanho=9, fundo=sup).pack(anchor='w', pady=(0, px(6)))
        for i, chave_txt in enumerate(('il_abra_jogo', 'il_local', 'prontov_entre'), start=1):
            _linha_com_icone(dentro, 'atual' if i == 1 else 'espera', t(chave_txt), simbolo=str(i), fundo=sup)
        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(px(20), 0))
        ttk.Button(bts, text=t('bt_fechar'), style='Primario.TButton', command=self.destroy).pack(side='right')
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
    """Tutorial em 7 telas, que acompanham os 5 passos da janela. Abre sozinho toda vez que o
    programa abre, até o usuário marcar "Não mostrar mais"; sempre abre pelo "Como usar" do topo."""

    TOTAL = 7
    PREFIXO = 'intro'             # chaves dos textos: intro_passo_N, intro_titulo_N, intro_texto_N
    TITULO_JANELA = 'intro_titulo'
    CONFIG_NAO_MOSTRAR = 'nao_mostrar_intro'   # caixinha "Não mostrar mais" (abrir sozinho)

    @classmethod
    def mostrar_sozinho(cls):
        """Abre sozinho? (o usuário não marcou "Não mostrar mais")"""
        return not idiomas.ler_config().get(cls.CONFIG_NAO_MOSTRAR)

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

        self.var_nao_mostrar = tk.BooleanVar(value=not self.mostrar_sozinho())
        self.caixa_nao_mostrar = ttk.Checkbutton(corpo, text=t('nao_mostrar_mais'), variable=self.var_nao_mostrar,
                                                 command=self.guardar_nao_mostrar)
        rodape = ttk.Frame(corpo)
        rodape.pack(fill='x', side='bottom')
        self.caixa_nao_mostrar.pack(side='bottom', anchor='w', pady=(0, px(10)))
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
                'dias': core.DIAS_PROTECAO_SAVE, 'desfazer': t('desfazer'),
                'e_este': t('bt_e_este_save'), 'dias_velho': core.DIAS_BACKUP_VELHO,
                'qual_escolher': t('link_qual_escolher')}

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

    def guardar_nao_mostrar(self):
        idiomas.salvar_config(**{self.CONFIG_NAO_MOSTRAR: bool(self.var_nao_mostrar.get())})

    def fechar(self):
        idiomas.salvar_config(intro_vista=True)
        self.destroy()


class JanelaModos(JanelaIntro):
    """Tutorial "Resetar tudo × Voltar missões da história". Abre sozinho quando o passo 4 (escolher
    o mapa) é liberado, até marcar "Não mostrar mais"; sempre abre pelo "Qual escolher?"."""

    TOTAL = 4
    PREFIXO = 'modos'
    TITULO_JANELA = 'modos_janela'
    CONFIG_NAO_MOSTRAR = 'nao_mostrar_modos'

    def fechar(self):
        self.destroy()


class JanelaComoDesfazer(JanelaIntro):
    """Tutorial ilustrado: como restaurar as missões, o backup original 🔒 e o save completo.
    Abre sozinho depois de cada mudança (reset ou voltar missões), até marcar "Não mostrar mais";
    sempre abre pelo "Como funciona?" do quadro "Precisa desfazer?"."""

    TOTAL = 6
    PREFIXO = 'desfazer'
    TITULO_JANELA = 'desfazer_janela'
    CONFIG_NAO_MOSTRAR = 'nao_mostrar_desfazer'

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
        x, y = px(36), px(26)
        agora = t('jogado_em', quando=idiomas.data_hora(datetime.datetime.now()))
        self.circulo(x, y, 'atual', 2)
        tit = self.texto(x + px(40), y + px(13), t('p2_titulo').upper(), negrito=True, tamanho=11)
        fim = self.cv.bbox(tit)[2] + px(10)
        selo = self.texto(fim + px(8), y + px(13), t('selo_mais_recente'), 'destaque', 8, True)
        b = self.cv.bbox(selo)
        self.cv.tag_lower(self.cv.create_rectangle(b[0] - px(6), b[1] - px(2), b[2] + px(6), b[3] + px(2),
                                                   fill=self.c['destaque_suave'], outline=''))
        self.texto(x + px(40), y + px(38), t('passo1_resumo', plat='Steam', id='7656…0000', quando=agora), 'fraco', 9)
        bx = x + px(40)
        for nome, valor in ((t('st_nivel'), '60'), (t('st_xp'), '293.384'), (t('st_dinheiro'), '$ 2.343.449'),
                            (t('st_missoes'), '412')):
            larg = px(22) + max(len(nome), len(valor)) * px(7)
            self.img(bx, y + px(54), comp.img_ret(self.cv, larg, px(38), px(5), self.c['fundo'], self.c['sup'],
                                                  self.c['borda'], 1.0))
            self.texto(bx + px(8), y + px(65), nome, 'fraco', 7)
            self.texto(bx + px(8), y + px(81), valor, negrito=True, tamanho=9)
            bx += larg + px(6)
        fx, fy = self.botao(x + px(40), y + px(106), t('bt_e_este_save'), tamanho=9)
        self.anel(x + px(34), y + px(100), fx + px(6), fy + px(6))

    def _intro_4(self):
        x, y = px(36), px(36)
        self.circulo(x, y, 'atual', 3)
        self.texto(x + px(40), y + px(13), t('p3_titulo').upper(), negrito=True, tamanho=11)
        self.texto(x + px(40), y + px(42), t('p3_obrigatorio'), 'fraco', 9, largura=self.w - x - px(80))
        bx, by = self.botao(x + px(40), y + px(78), t('bt_backup_save'))
        self.anel(x + px(34), y + px(72), bx + px(6), by + px(6))
        self.texto(x + px(40), by + px(22), t('il_backup_dias', dias=core.DIAS_BACKUP_VELHO), 'aviso', 9,
                   largura=self.w - x - px(80))

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

    def cartao_modo(self, x, y, larg, icone, titulo, sub, marcado, cor='destaque'):
        """Miniatura de um dos dois cartões do passo 5."""
        c = self.c
        alt = px(62)
        fundo = c['destaque_suave'] if marcado else c['sup']
        self.img(x, y, comp.img_ret(self.cv, larg, alt, px(7), fundo, c['sup'], c[cor] if marcado else c['borda'],
                                    1.5 if marcado else 1.0))
        self.texto(x + px(12), y + px(20), icone, tamanho=12)
        self.texto(x + px(38), y + px(18), titulo, negrito=True, tamanho=9)
        self.texto(x + px(38), y + px(40), sub, 'fraco', 8, anchor='w', largura=larg - px(46))
        return y + alt

    def _intro_6(self):
        x, y = px(30), px(18)
        self.circulo(x, y, 'atual', 5)
        self.texto(x + px(36), y + px(13), t('p5_titulo_um').upper(), negrito=True, tamanho=11)
        larg = (self.w - 2 * x - px(12)) / 2
        fim = self.cartao_modo(x, y + px(36), larg, '🔄', t('modo_resetar'), t('modo_resetar_sub'), True)
        self.cartao_modo(x + larg + px(12), y + px(36), larg, '⏪', t('modo_voltar'), t('modo_voltar_sub'), False)
        self.texto(x, fim + px(22), t('il_dois_caminhos'), 'destaque', 9, True, largura=self.w - 2 * x)

    # --- tutorial "Resetar tudo × Voltar missões"
    def mini_historia(self, x, y, estados, titulo=None, cor_volta='aviso', alvo=None, atual=None, larg=None):
        """Linha do tempo pequena: estados = 'f' feita, 'v' volta, 'a' em andamento, 'z' zerada."""
        c = self.c
        larg = larg or px(200)
        if titulo:
            self.texto(x, y - px(12), titulo, negrito=True, tamanho=8)
        for i, e in enumerate(estados):
            ly = y + i * px(22)
            if e == 'v':
                self.caixa(x, ly, x + larg, ly + px(20), 'aviso_suave', 'aviso' if i == alvo else None)
            simbolo, cor = {'f': ('✓', 'destaque'), 'v': ('↺', cor_volta), 'a': ('▶', 'destaque'),
                            'z': ('○', 'fraquinho')}[e]
            self.texto(x + px(8), ly + px(10), str(i + 1), 'fraco', 7)
            self.texto(x + px(24), ly + px(10), simbolo, cor, 9, True)
            self.texto(x + px(42), ly + px(10), t('missao_historia_n', n=i + 1), 'fraquinho' if e == 'z' else 'texto', 8)
            tag = t('tag_recomeca') if i == alvo else (t('tag_voce_esta') if i == atual else '')
            if tag:
                self.texto(x + larg - px(6), ly + px(10), tag, 'aviso' if e == 'v' else 'destaque', 7, True, anchor='e')

    def _modos_1(self):
        larg = (self.w - px(84)) / 2
        x1, x2, y = px(30), px(30) + larg + px(24), px(30)
        self.texto(x1, y, '🔄 ' + t('modo_resetar'), negrito=True, tamanho=10)
        self.mini_historia(x1, y + px(24), 'zzzzzz', larg=larg)
        self.texto(x2, y, '⏪ ' + t('modo_voltar'), negrito=True, tamanho=10)
        self.mini_historia(x2, y + px(24), 'ffvvvz', alvo=2, atual=4, larg=larg)

    def _modos_2(self):
        x, y = px(30), px(26)
        self.texto(x, y, t('quantas_voltar').upper(), negrito=True, tamanho=8)
        bx = x
        for txt in ('−', '2', '+'):
            if txt == '2':
                self.texto(bx + px(14), y + px(30), txt, negrito=True, tamanho=16, anchor='center')
                bx += px(30)
            else:
                self.img(bx, y + px(16), comp.img_ret(self.cv, px(28), px(28), px(5), self.c['fundo'], self.c['sup'],
                                                      self.c['borda'], 1.0))
                self.texto(bx + px(14), y + px(30), txt, tamanho=11, anchor='center')
                bx += px(32)
        self.texto(x, y + px(66), t('recomecar_em').upper(), 'aviso', 7, True)
        self.texto(x, y + px(84), t('missao_historia_n', n=3), negrito=True, tamanho=10)
        self.texto(x, y + px(110), t('il_exemplo_voltar'), 'fraco', 8, largura=px(190))
        self.mini_historia(px(250), y + px(4), 'ffvvvz', alvo=2, atual=4, larg=self.w - px(280))

    def _modos_3(self):
        c = self.c
        x, y = px(40), px(40)
        self.img(x, y, comp.img_ret(self.cv, px(170), px(30), px(5), c['aviso_suave'], c['sup'], c['aviso'], 1.0))
        self.texto(x + px(10), y + px(15), '↺  ' + t('missao_historia_n', n=3), 'texto', 9, True)
        for i, (volta, texto) in enumerate(((True, t('il_sec_ligada')), (False, t('il_sec_solta')))):
            yy = y + px(10) + i * px(62)
            xx = x + px(240)
            if volta:
                self.cv.create_line(x + px(170), y + px(15), xx, yy + px(15), fill=c['aviso'], width=max(1, px(1.5)),
                                    arrow='last')
            fundo, borda = (c['aviso_suave'], c['aviso']) if volta else (c['sup'], c['borda'])
            self.img(xx, yy, comp.img_ret(self.cv, px(210), px(30), px(5), fundo, c['sup'], borda, 1.0))
            self.texto(xx + px(10), yy + px(15), ('↺  ' if volta else '✓  ') + texto, 'texto', 8, volta)

    def _modos_4(self):
        x, y = px(48), px(30)
        for i, (estado, chave) in enumerate((('feito', 'il_seguro_backup'), ('feito', 'il_seguro_desfazer'),
                                            ('aviso', 'il_seguro_xp'))):
            yy = y + i * px(44)
            self.circulo(x, yy, estado, '!')
            self.texto(x + px(42), yy + px(13), t(chave), tamanho=10, largura=self.w - x - px(80))

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
