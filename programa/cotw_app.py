"""Janela do ResetMissionsCOTW - Reset de Missões por Mapa (theHunter: Call of the Wild).

Os textos ficam em idiomas.py (português, inglês e espanhol).
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cotw_core as core
import diagnostico
import idiomas
import registro
import temas
from idiomas import t

VERSAO = '0.9.6 (Beta)'
NOME_DO_PROGRAMA = 'ResetMissionsCOTW'
TITULO = 'ResetMissionsCOTW (Beta)'
AUTOR = 'Sheeerpha'
PLATAFORMAS = ('Steam', 'Epic', 'Outra')  # 'Outra' só aparece se houver save de pasta desconhecida

# Links de doação. Deixe '' para o botão aparecer como "em breve".
LINK_BUYMEACOFFEE = 'https://buymeacoffee.com/sheeerpha'
LINK_LIVEPIX = 'https://livepix.gg/sherpa'
# Link do repositório no GitHub (aparece no aviso da primeira vez). '' = "será adicionado em breve".
LINK_GITHUB = 'https://github.com/Sheeerpha/ResetMissionsCOTW'
URL_PROTECAO_RANSOMWARE = 'windowsdefender://RansomwareProtection'


def caminho_do_programa():
    if getattr(sys, 'frozen', False):  # rodando como .exe
        return sys.executable
    return os.path.abspath(sys.argv[0])


def abrir_link(link):
    """Abre o link no navegador padrão."""
    import webbrowser
    webbrowser.open(link)


def nome_plataforma(plat):
    return t('plat_outra') if plat == 'Outra' else plat


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry('920x720')
        self.minsize(800, 620)
        self.raiz = core.pasta_do_programa_padrao()
        self.saves = []
        self.save_atual = None
        self.saves_visiveis = []
        self.mapas = {}
        self.bloqueado = False
        self.verificacao = None          # último resultado da "Verificação antes de começar"
        self.avisos_discretos = []       # avisos que não atrapalham (limpeza de backups, sobras...)
        self.onedrive_fechado = None     # caminho do OneDrive, se a verificação o fechou (para reabrir)
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
        self._agendados.append(self.after(300, self.mostrar_boas_vindas))

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
        pad = {'padx': 10, 'pady': 4}

        # Faixa de aviso do Acesso Controlado a Pastas (só aparece se houver bloqueio)
        aviso = temas.cor('aviso_fundo')
        self.faixa = tk.Frame(self, bg=aviso, highlightbackground=temas.cor('aviso_borda'), highlightthickness=1)
        self.faixa_texto = tk.Label(self.faixa, bg=aviso, fg=temas.cor('aviso_texto'), justify='left', anchor='w',
                                    wraplength=860, font=('Segoe UI', 9, 'bold'))
        self.faixa_texto.pack(fill='x', padx=10, pady=(8, 4))
        bts = tk.Frame(self.faixa, bg=aviso)
        bts.pack(fill='x', padx=10, pady=(0, 8))
        self.botoes_cfa = [ttk.Button(bts, text=t('bt_como_liberar'), command=self.mostrar_passo_a_passo),
                           ttk.Button(bts, text=t('bt_abrir_seguranca'), command=self.abrir_seguranca),
                           ttk.Button(bts, text=t('bt_copiar_caminho'), command=self.copiar_caminho)]
        for bt in self.botoes_cfa:
            bt.pack(side='left', padx=(0, 6))
        self.bt_testar_de_novo = ttk.Button(bts, text=t('bt_testar_de_novo'), command=self.testar_de_novo)
        self.bt_testar_de_novo.pack(side='left')

        # Rodapé (empacotado primeiro, embaixo, para nunca sumir quando a janela encolhe)
        rodape = ttk.Frame(self)
        rodape.pack(side='bottom', fill='x', padx=10, pady=(0, 8))
        ttk.Separator(self, orient='horizontal').pack(side='bottom', fill='x', padx=10, pady=(0, 6))
        self.credito = ttk.Label(rodape, text=t('credito', autor=AUTOR, versao=VERSAO), style='Fraco.TLabel')
        self.credito.pack(side='left')
        if LINK_GITHUB:
            ttk.Label(rodape, text='   •   ', style='Fraco.TLabel').pack(side='left')
            self.link_github = ttk.Label(rodape, text='GitHub', style='Link.TLabel', cursor='hand2')
            self.link_github.pack(side='left')
            self.link_github.bind('<Button-1>', lambda e: abrir_link(LINK_GITHUB))
        ttk.Button(rodape, text=t('bt_apoiar'), command=lambda: JanelaApoio(self)).pack(side='right')
        self.bt_tema = ttk.Button(rodape, command=self.alternar_tema,
                                  text=t('bt_tema_claro') if temas.atual() == 'escuro' else t('bt_tema_escuro'))
        self.bt_tema.pack(side='right', padx=(0, 8))
        nomes = list(idiomas.IDIOMAS.values())
        self.combo_idioma = ttk.Combobox(rodape, state='readonly', values=nomes, width=18)
        self.combo_idioma.current(list(idiomas.IDIOMAS).index(idiomas.atual()))
        self.combo_idioma.bind('<<ComboboxSelected>>',
                               lambda e: self.trocar_idioma(list(idiomas.IDIOMAS)[self.combo_idioma.current()]))
        self.combo_idioma.pack(side='right', padx=(0, 12))
        ttk.Label(rodape, text='🌐').pack(side='right', padx=(0, 4))
        ttk.Button(rodape, text=t('bt_ajuda'), command=self.mostrar_intro).pack(side='right', padx=(0, 12))

        # Linha 1: plataforma
        self.topo = ttk.Frame(self)
        self.topo.pack(fill='x', padx=10, pady=(8, 2))
        ttk.Label(self.topo, text=t('rotulo_plataforma'), width=11).pack(side='left')
        self.var_plataforma = tk.StringVar()
        self.radios = {}
        for plat in PLATAFORMAS:
            self.radios[plat] = ttk.Radiobutton(self.topo, text=nome_plataforma(plat), value=plat,
                                                variable=self.var_plataforma, command=self.trocar_plataforma)
        ttk.Button(self.topo, text=t('bt_escolher_pasta'), command=self.escolher_pasta).pack(side='right')
        ttk.Button(self.topo, text=t('bt_procurar'), command=self.procurar_saves).pack(side='right', padx=6)

        # Linha 2: save daquela plataforma
        linha2 = ttk.Frame(self)
        linha2.pack(fill='x', padx=10, pady=2)
        ttk.Label(linha2, text=t('rotulo_save'), width=11).pack(side='left')
        self.combo = ttk.Combobox(linha2, state='readonly')
        self.combo.pack(side='left', fill='x', expand=True)
        self.combo.bind('<<ComboboxSelected>>', lambda e: self.escolher_save(self.combo.current()))
        self.aviso_saves = temas.label_tk(self, text='', fg=temas.cor('aviso_saves'), anchor='w', justify='left',
                                          wraplength=860, font=('Segoe UI', 9, 'bold'))

        self.info = ttk.Label(self, text='', style='Fraco.TLabel')
        self.info.pack(fill='x', **pad)

        # Linha discreta da "Verificação antes de começar"
        self.linha_verif = ttk.Frame(self)
        self.linha_verif.pack(fill='x', padx=10, pady=(0, 2))
        self.status_verif = temas.label_tk(self.linha_verif, text='', anchor='w', font=('Segoe UI', 9, 'bold'),
                                           cursor='hand2')
        self.status_verif.pack(side='left')
        self.status_verif.bind('<Button-1>', lambda e: self.abrir_verificacao())
        ttk.Button(self.linha_verif, text=t('bt_ver_verificacao'), command=self.abrir_verificacao).pack(
            side='left', padx=8)
        self.bt_logs = ttk.Button(self.linha_verif, text=t('bt_logs'), command=self.abrir_logs)
        self.bt_logs.pack(side='left')
        self.aviso_discreto = temas.label_tk(self, text='', fg=temas.cor('aviso_saves'), anchor='w', justify='left',
                                             wraplength=860)

        meio = ttk.Frame(self)
        meio.pack(fill='both', expand=True, **pad)
        colunas = ('mapa', 'concluidas', 'andamento', 'total')
        self.lista = ttk.Treeview(meio, columns=colunas, show='headings', selectmode='extended')
        for col, chave, larg, anc in [('mapa', 'col_mapa', 380, 'w'), ('concluidas', 'col_concluidas', 150, 'center'),
                                      ('andamento', 'col_andamento', 110, 'center'), ('total', 'col_total', 70, 'center')]:
            self.lista.heading(col, text=t(chave))
            self.lista.column(col, width=larg, anchor=anc, stretch=(col == 'mapa'))
        self.lista.tag_configure('resetado', background=temas.cor('resetado_fundo'),
                                 foreground=temas.cor('resetado_texto'))
        barra = ttk.Scrollbar(meio, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side='left', fill='both', expand=True)
        barra.pack(side='left', fill='y')

        ttk.Label(self, text=t('dica_selecao'), style='Fraco.TLabel').pack(fill='x', padx=10)

        # Botões em duas linhas: missões e save completo
        botoes = ttk.Frame(self)
        botoes.pack(fill='x', padx=10, pady=(8, 6))
        ttk.Label(botoes, text=t('rotulo_linha_missoes'), style='Negrito.TLabel').grid(
            row=0, column=0, sticky='w', padx=(0, 8), pady=2)
        self.bt_reset = ttk.Button(botoes, text=t('bt_resetar'), command=self.resetar)
        self.bt_reset.grid(row=0, column=1, sticky='ew', pady=2)
        self.bt_restaurar = ttk.Button(botoes, text=t('bt_restaurar'), command=self.janela_restaurar)
        self.bt_restaurar.grid(row=0, column=2, sticky='ew', padx=6, pady=2)
        ttk.Button(botoes, text=t('bt_abrir_pasta'), command=self.abrir_backups).grid(
            row=0, column=3, sticky='ew', pady=2)
        ttk.Label(botoes, text=t('rotulo_linha_save'), style='Negrito.TLabel').grid(
            row=1, column=0, sticky='w', padx=(0, 8), pady=2)
        self.bt_backup_save = ttk.Button(botoes, text=t('bt_backup_save'), command=self.fazer_backup_save)
        self.bt_backup_save.grid(row=1, column=1, sticky='ew', pady=2)
        self.bt_restaurar_save = ttk.Button(botoes, text=t('bt_restaurar_save'), command=self.janela_restaurar_save)
        self.bt_restaurar_save.grid(row=1, column=2, sticky='ew', padx=6, pady=2)
        ttk.Button(botoes, text=t('bt_abrir_pasta'), command=self.abrir_backups_save).grid(
            row=1, column=3, sticky='ew', pady=2)

        ttk.Label(self, text=t('como_funciona'), wraplength=860, justify='left').pack(
            fill='x', padx=10, pady=(0, 10))

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
        save, saves = self.save_atual, self.saves
        for w in self.winfo_children():
            w.destroy()
        self._montar()
        self.verificar_permissao()
        self.saves = saves
        if save is not None and save in saves:
            self.mostrar_save(save)
        else:
            self.procurar_saves()
        if self.verificacao is not None:
            self.mostrar_status_verificacao(self.verificacao)
        self.mostrar_avisos_discretos()

    # --------------------------------------------------- verificação e avisos
    def verificar_agora(self):
        self.verificacao = diagnostico.verificar(self.save_atual, self.raiz)
        self.mostrar_status_verificacao(self.verificacao)
        return self.verificacao

    def mostrar_status_verificacao(self, r):
        if r.impedimentos:
            texto, cor = t('status_impede', n=len(r.impedimentos)), temas.cor('erro_texto')
        elif r.avisos:
            texto, cor = t('status_avisos', n=len(r.avisos)), temas.cor('aviso_saves')
        else:
            texto, cor = t('status_ok'), temas.cor('ok_texto')
        self.status_verif.config(text=texto, fg=cor)

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
            self.aviso_discreto.pack(fill='x', padx=10, pady=(0, 2), after=self.linha_verif)
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
                texto = t('faixa_bloqueio')
            else:
                texto = t('faixa_erro_causa', causa=' '.join(causa.textos))
            # os botões de "como liberar" só fazem sentido se o Acesso Controlado está ligado
            cfa = causa.cfa_confirmado or core.acesso_controlado_ligado() is True
            for bt in self.botoes_cfa:
                if cfa:
                    bt.pack(side='left', padx=(0, 6), before=self.bt_testar_de_novo)
                else:
                    bt.pack_forget()
            self.faixa_texto.config(text=texto)
            self.faixa.pack(fill='x', padx=10, pady=(10, 0), before=self.topo)
        estado = ['disabled'] if self.bloqueado else ['!disabled']
        for bt in (self.bt_reset, self.bt_restaurar, self.bt_backup_save, self.bt_restaurar_save):
            bt.state(estado)
        return not self.bloqueado

    def mostrar_passo_a_passo(self):
        messagebox.showinfo(TITULO, core.mensagem_acesso_controlado(caminho_do_programa())
                            + '\n\n' + t('dica_copiar'))

    def abrir_seguranca(self):
        try:
            os.startfile(URL_PROTECAO_RANSOMWARE)
        except OSError:
            messagebox.showinfo(TITULO, t('nao_abriu_seguranca'))

    def copiar_caminho(self):
        self.clipboard_clear()
        self.clipboard_append(caminho_do_programa())
        messagebox.showinfo(TITULO, t('caminho_copiado', caminho=caminho_do_programa()))

    def testar_de_novo(self):
        if self.verificar_permissao():
            self.recarregar()
            messagebox.showinfo(TITULO, t('tudo_certo'))
        else:
            messagebox.showwarning(TITULO, t('ainda_bloqueado', caminho=caminho_do_programa()))

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
            self.info.config(text=t('nao_encontrei_save'))
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
            rb.pack(side='left', padx=(0, 14))

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
            self.aviso_saves.pack(fill='x', padx=10, pady=(2, 0), before=self.info)
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
        self.recarregar()

    def recarregar(self):
        s = self.save_atual
        if s is None:
            self.mostrar_mapas(None)
            return
        try:
            mapas = core.mapas_para_mostrar(s, self.raiz)
        except (OSError, core.ErroSave) as e:
            self.mostrar_mapas(None)
            self.info.config(text=t('nao_li_save', erro=e))
            return
        self.mostrar_mapas(mapas)
        partes = []
        if s.steam_cloud:
            partes.append(t('steam_cloud_ativo'))
        n = len(core.listar_backups(s, self.raiz))
        partes.append(t('n_backups', n=n) if n else t('nenhum_backup_ainda'))
        n_save = len(core.listar_backups_save(s, self.raiz))
        partes.append(t('n_backups_save', n=n_save) if n_save else t('nenhum_backup_save'))
        self.info.config(text='   |   '.join(partes))

    def mostrar_mapas(self, mapas):
        self.mapas = {m.chave: m for m in mapas or []}
        self.lista.delete(*self.lista.get_children())
        for m in mapas or []:
            nome = f'{m.nome}   —   {t("sufixo_resetado")}' if m.resetado else m.nome
            self.lista.insert('', 'end', iid=str(m.chave), tags=('resetado',) if m.resetado else (),
                              values=(nome, m.concluidas, m.em_andamento, m.total))

    # ---------------------------------------------------------------- ações
    def _pode_alterar(self, parent=None):
        if not self.verificar_permissao():
            messagebox.showwarning(TITULO, t('aviso_usar_faixa'), parent=parent)
            return False
        return self.checar_antes(parent)

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
        if not messagebox.askyesno(TITULO, t('confirmar_reset', save=self.save_atual.nome_curto(),
                                             detalhes=detalhes), icon='warning'):
            return
        registro.log(f'Reset pedido: {", ".join(core.nome_do_mapa(k) for k in sel)}')
        try:
            b = core.resetar_mapas(self.save_atual, sel, self.raiz)
        except (OSError, core.ErroSave) as e:
            self.mostrar_erro(e, 'Reset de missões', prefixo='nao_foi_possivel_resetar')
            self.recarregar()
            return
        registro.log('Reset concluído.')
        self.recarregar()
        self.avisar_resultado(b)
        self.lista.selection_set(())  # sem seleção, para o destaque verde aparecer
        for k in sel:
            if self.lista.exists(str(k)):
                self.lista.see(str(k))
        messagebox.showinfo(TITULO, t('reset_ok', nomes=nomes))

    def abrir_backups(self):
        if self.save_atual is not None:
            pasta = core.pasta_backups_do_save(self.save_atual, self.raiz)
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
    def fazer_backup_save(self, perguntar_ok=True, parent=None, ja_verificado=False):
        """Copia a pasta inteira do save. Devolve True se deu certo."""
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'), parent=parent)
            return False
        if not ja_verificado and not self._pode_alterar(parent=parent):
            return False
        self.config(cursor='watch')
        self.update_idletasks()
        try:
            b = core.fazer_backup_save_completo(self.save_atual, self.raiz)
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


class JanelaRestaurar(tk.Toplevel):
    """Lista os backups e mostra, para o escolhido, como cada mapa ficaria."""

    def __init__(self, app, backups):
        super().__init__(app)
        self.app = app
        self.backups = backups
        self.cache = {}
        self.title(t('rest_titulo'))
        self.geometry('920x600')
        self.minsize(760, 480)
        temas.preparar_janela(self)
        self.transient(app)
        _modal(self)

        ttk.Label(self, wraplength=880, justify='left', text=t('rest_intro')).pack(fill='x', padx=10, pady=(10, 6))

        ttk.Label(self, text=t('rest_passo1'), font=('Segoe UI', 9, 'bold')).pack(fill='x', padx=10)
        cima = ttk.Frame(self)
        cima.pack(fill='x', padx=10, pady=4)
        self.lista = ttk.Treeview(cima, columns=('data', 'hora', 'oque'), show='headings',
                                  selectmode='browse', height=6)
        for col, chave, larg, anc in [('data', 'col_data', 100, 'center'), ('hora', 'col_hora', 80, 'center'),
                                      ('oque', 'col_motivo', 600, 'w')]:
            self.lista.heading(col, text=t(chave))
            self.lista.column(col, width=larg, anchor=anc, stretch=(col == 'oque'))
        for i, b in enumerate(backups):
            motivo = f'{b.titulo}     {t("backup_protegido")}' if b.protegido else b.titulo
            self.lista.insert('', 'end', iid=str(i), values=(idiomas.data(b.quando), f'{b.quando:%H:%M:%S}',
                                                              motivo))
        barra = ttk.Scrollbar(cima, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side='left', fill='x', expand=True)
        barra.pack(side='left', fill='y')
        self.lista.bind('<<TreeviewSelect>>', lambda e: self.mostrar_detalhes())
        ttk.Label(self, text=t('limite_backups', n=core.LIMITE_MISSOES), style='Fraco.TLabel').pack(
            fill='x', padx=10)

        ttk.Label(self, text=t('rest_passo2'), font=('Segoe UI', 9, 'bold')).pack(fill='x', padx=10, pady=(8, 0))
        baixo = ttk.Frame(self)
        baixo.pack(fill='both', expand=True, padx=10, pady=4)
        self.det = ttk.Treeview(baixo, columns=('mapa', 'agora', 'backup'), show='headings', selectmode='none')
        for col, chave, larg, anc in [('mapa', 'col_mapa', 300, 'w'), ('agora', 'col_agora', 250, 'center'),
                                      ('backup', 'col_depois', 250, 'center')]:
            self.det.heading(col, text=t(chave))
            self.det.column(col, width=larg, anchor=anc, stretch=True)
        self.det.tag_configure('diferente', background=temas.cor('diferente_fundo'))
        barra2 = ttk.Scrollbar(baixo, orient='vertical', command=self.det.yview)
        self.det.configure(yscrollcommand=barra2.set)
        self.det.pack(side='left', fill='both', expand=True)
        barra2.pack(side='left', fill='y')
        self.resumo = ttk.Label(self, text='', style='Fraco.TLabel')
        self.resumo.pack(fill='x', padx=10)

        bts = ttk.Frame(self)
        bts.pack(fill='x', padx=10, pady=10)
        ttk.Button(bts, text=t('bt_restaurar_este'), command=self.restaurar).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_pasta_backup'), command=self.abrir_pasta).pack(side='left', padx=6)
        ttk.Button(bts, text=t('bt_fechar'), command=self.destroy).pack(side='right')

        self.lista.selection_set('0')

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


class JanelaRestaurarSave(tk.Toplevel):
    """Lista os backups do save completo e devolve o escolhido."""

    def __init__(self, app, backups):
        super().__init__(app)
        self.app = app
        self.backups = backups
        self.title(t('rest_save_titulo'))
        self.geometry('860x440')
        self.minsize(700, 380)
        temas.preparar_janela(self)
        self.transient(app)
        _modal(self)

        ttk.Label(self, wraplength=820, justify='left', text=t('rest_save_intro')).pack(fill='x', padx=10, pady=(10, 8))
        ttk.Label(self, text=t('rest_passo1'), style='Negrito.TLabel').pack(fill='x', padx=10)
        meio = ttk.Frame(self)
        meio.pack(fill='both', expand=True, padx=10, pady=4)
        self.lista = ttk.Treeview(meio, columns=('data', 'hora', 'oque', 'tamanho'), show='headings',
                                  selectmode='browse')
        for col, chave, larg, anc in [('data', 'col_data', 100, 'center'), ('hora', 'col_hora', 80, 'center'),
                                      ('oque', 'col_motivo', 480, 'w'), ('tamanho', 'col_tamanho', 90, 'center')]:
            self.lista.heading(col, text=t(chave))
            self.lista.column(col, width=larg, anchor=anc, stretch=(col == 'oque'))
        for i, b in enumerate(backups):
            motivo = f'{b.titulo}     {t("backup_protegido")}' if b.protegido else b.titulo
            self.lista.insert('', 'end', iid=str(i), values=(idiomas.data(b.quando), f'{b.quando:%H:%M:%S}',
                                                              motivo, idiomas.tamanho(b.tamanho)))
        barra = ttk.Scrollbar(meio, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side='left', fill='both', expand=True)
        barra.pack(side='left', fill='y')
        ttk.Label(self, text=t('limite_backups', n=core.LIMITE_SAVE), style='Fraco.TLabel').pack(fill='x', padx=10)

        bts = ttk.Frame(self)
        bts.pack(fill='x', padx=10, pady=10)
        ttk.Button(bts, text=t('bt_restaurar_save_este'), command=self.restaurar).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_pasta'), command=self.app.abrir_backups_save).pack(side='left', padx=6)
        ttk.Button(bts, text=t('bt_fechar'), command=self.destroy).pack(side='right')
        self.lista.selection_set('0')

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


class JanelaAviso(tk.Toplevel):
    """Aviso mostrado só na primeira vez que o programa é aberto."""

    def __init__(self, app, depois=None):
        super().__init__(app)
        self.app = app
        self.depois = depois
        self.title(t('aviso_titulo'))
        self.resizable(False, False)
        temas.preparar_janela(self)
        self.transient(app)
        _modal(self)
        self.protocol('WM_DELETE_WINDOW', self.fechar)

        corpo = ttk.Frame(self, padding=20)
        corpo.pack(fill='both', expand=True)
        ttk.Label(corpo, text=t('aviso_titulo'), style='Titulo.TLabel').pack(anchor='w')
        link = LINK_GITHUB or t('link_em_breve')
        ttk.Label(corpo, wraplength=520, justify='left',
                  text=t('aviso_texto', link=link, bt_backup=idiomas.sem_icone(t('bt_backup_save')))).pack(
            anchor='w', pady=(10, 16))
        if LINK_GITHUB:
            ttk.Button(corpo, text='GitHub', command=lambda: JanelaApoio.abrir(LINK_GITHUB)).pack(anchor='w')
        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(12, 0))
        ttk.Button(bts, text=t('bt_backup_save'), command=self.fazer_backup).pack(side='left')
        ttk.Button(bts, text=t('aviso_entendi'), command=self.fechar).pack(side='right')
        _centralizar(self, app)

    def fazer_backup(self):
        self.app.fazer_backup_save(parent=self)

    def fechar(self):
        self.destroy()
        if self.depois:
            try:
                self.app._agendados.append(self.app.after(150, self.depois))
            except tk.TclError:
                pass  # a janela principal já foi fechada


class JanelaIntro(tk.Toplevel):
    """Introdução em telas, com Pular / Voltar / Próximo. Na primeira vez abre sozinha;
    depois, pelo botão "Como usar" do rodapé."""

    TOTAL = 6

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.pagina = 1
        self.title(t('intro_titulo'))
        self.resizable(False, False)
        temas.preparar_janela(self)
        self.transient(app)
        _modal(self)
        self.protocol('WM_DELETE_WINDOW', self.fechar)

        corpo = ttk.Frame(self, padding=20)
        corpo.pack(fill='both', expand=True)
        self.titulo = ttk.Label(corpo, style='Titulo.TLabel')
        self.titulo.pack(anchor='w')
        self.texto = ttk.Label(corpo, wraplength=540, justify='left', anchor='nw')
        self.texto.pack(anchor='nw', fill='both', expand=True, pady=(10, 14))
        rodape = ttk.Frame(corpo)
        rodape.pack(fill='x', side='bottom')
        self.contador = ttk.Label(rodape, style='Fraco.TLabel')
        self.contador.pack(side='left')
        self.bt_proximo = ttk.Button(rodape, command=self.proximo)
        self.bt_proximo.pack(side='right')
        self.bt_voltar = ttk.Button(rodape, text=t('intro_voltar'), command=self.voltar)
        self.bt_voltar.pack(side='right', padx=6)
        self.bt_pular = ttk.Button(rodape, text=t('intro_pular'), command=self.fechar)
        self.bt_pular.pack(side='right', padx=(0, 12))
        corpo.configure(width=600, height=400)
        corpo.pack_propagate(False)
        self.mostrar()
        _centralizar(self, app)

    def campos(self):
        b = lambda chave: idiomas.sem_icone(t(chave))
        return {'procurar': b('bt_procurar'), 'escolher_pasta': b('bt_escolher_pasta'),
                'resetadas': t('sufixo_resetado'), 'resetar': b('bt_resetar'),
                'backup_save': b('bt_backup_save'), 'restaurar_save': b('bt_restaurar_save'),
                'restaurar': b('bt_restaurar'), 'abrir_pasta': b('bt_abrir_pasta'),
                'limite_missoes': core.LIMITE_MISSOES, 'limite_save': core.LIMITE_SAVE,
                'tema_escuro': b('bt_tema_escuro'), 'tema_claro': b('bt_tema_claro'),
                'apoiar': b('bt_apoiar'), 'ajuda': b('bt_ajuda')}

    def mostrar(self):
        n = self.pagina
        self.titulo.config(text=t(f'intro_titulo_{n}'))
        texto = idiomas.TEXTOS[idiomas.atual()][f'intro_texto_{n}']
        self.texto.config(text=texto.format(**self.campos()))
        self.contador.config(text=t('intro_pagina', n=n, total=self.TOTAL))
        self.bt_voltar.state(['disabled'] if n == 1 else ['!disabled'])
        ultima = n == self.TOTAL
        self.bt_proximo.config(text=t('intro_comecar') if ultima else t('intro_proximo'))
        if ultima:
            self.bt_pular.pack_forget()
        elif not self.bt_pular.winfo_manager():
            self.bt_pular.pack(side='right', padx=(0, 12), before=self.bt_voltar)

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


class JanelaVerificacao(tk.Toplevel):
    """Tela "Verificação antes de começar".

    modo 'info'  : só mostra (ao abrir o programa ou pelo botão "Ver verificação");
    modo 'antes' : aparece antes de alterar o save quando algo impede; termina com
                   self.continuar = True (seguir) ou False (cancelar).
    Regras: nada é fechado sem o clique do usuário, nada é fechado à força, e depois
    de cada botão a verificação é feita de novo."""

    BOTOES_FECHAR = {'steam': 'bt_fechar_steam', 'onedrive': 'bt_fechar_onedrive', 'epic': 'bt_fechar_epic',
                     'googledrive': 'bt_fechar_googledrive', 'dropbox': 'bt_fechar_dropbox'}

    def __init__(self, app, modo, resultado, depois=None):
        super().__init__(app)
        self.app, self.modo, self.resultado, self.depois = app, modo, resultado, depois
        self.continuar = False
        self._espera = None
        self.title(t('verif_titulo'))
        self.geometry('720x520')
        self.minsize(620, 420)
        temas.preparar_janela(self)
        self.transient(app)
        _modal(self)
        self.protocol('WM_DELETE_WINDOW', self.cancelar)

        corpo = ttk.Frame(self, padding=16)
        corpo.pack(fill='both', expand=True)
        ttk.Label(corpo, text=t('verif_titulo'), style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(corpo, text=t('verif_explicacao'), wraplength=680, justify='left', style='Fraco.TLabel').pack(
            anchor='w', fill='x', pady=(6, 10))
        self.area = ttk.Frame(corpo)
        self.area.pack(fill='both', expand=True)
        self.mensagem = temas.label_tk(corpo, text='', anchor='w', justify='left', wraplength=680,
                                       fg=temas.cor('aviso_saves'))
        self.mensagem.pack(fill='x', pady=(6, 0))
        self.barra = ttk.Frame(corpo)
        self.barra.pack(fill='x', pady=(10, 0))
        self.desenhar()
        _centralizar(self, app)

    # -------------------------------------------------------------- desenho
    def desenhar(self):
        for w in self.area.winfo_children() + self.barra.winfo_children():
            w.destroy()
        r = self.resultado
        if not r.itens:
            temas.label_tk(self.area, text=t('verif_tudo_pronto'), fg=temas.cor('ok_texto'),
                           font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=10)
        for titulo, itens, cor in ((t('verif_impede'), r.impedimentos, temas.cor('erro_texto')),
                                   (t('verif_atencao'), r.avisos, temas.cor('aviso_saves'))):
            if not itens:
                continue
            temas.label_tk(self.area, text=titulo, fg=cor, font=('Segoe UI', 9, 'bold')).pack(
                anchor='w', pady=(6, 2))
            for item in itens:
                self._linha(item)
        if self.app.onedrive_fechado and not diagnostico.esta_aberto('onedrive.exe'):
            linha = ttk.Frame(self.area)
            linha.pack(fill='x', pady=(8, 0))
            ttk.Button(linha, text=t('bt_reabrir_onedrive'), command=self.reabrir_onedrive).pack(side='right')
        ttk.Button(self.barra, text=t('bt_verificar_de_novo'), command=self.verificar_de_novo).pack(side='left')
        if self.modo == 'antes':
            ttk.Button(self.barra, text=t('bt_cancelar'), command=self.cancelar).pack(side='right')
            if r.impedimentos:
                bt = ttk.Button(self.barra, text=t('bt_continuar_mesmo_assim'), command=self.continuar_mesmo_assim)
                if r.jogo_aberto:
                    bt.state(['disabled'])   # com o jogo aberto, a alteração seria recusada de qualquer jeito
            else:
                bt = ttk.Button(self.barra, text=t('bt_continuar'), command=self.seguir)
            bt.pack(side='right', padx=6)
            self.bt_seguir = bt
        else:
            ttk.Button(self.barra, text=t('bt_fechar'), command=self.cancelar).pack(side='right')

    def _linha(self, item):
        linha = ttk.Frame(self.area)
        linha.pack(fill='x', pady=3)
        botoes = ttk.Frame(linha)
        botoes.pack(side='right', anchor='n')
        ttk.Label(linha, text='•  ' + item.texto, wraplength=500, justify='left').pack(side='left', fill='x')
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


class JanelaErro(tk.Toplevel):
    """Janela de erro: o que aconteceu, a causa encontrada (quando der) e "Copiar detalhes"."""

    def __init__(self, app, mensagem, causa, erro, contexto, parent=None):
        super().__init__(parent or app)
        self.app = app
        self.title(t('erro_titulo'))
        self.resizable(True, True)
        self.minsize(560, 300)
        temas.preparar_janela(self)
        self.transient(parent or app)
        _modal(self)

        corpo = ttk.Frame(self, padding=18)
        corpo.pack(fill='both', expand=True)
        temas.label_tk(corpo, text='⛔  ' + t('erro_titulo'), fg=temas.cor('erro_texto'),
                       font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        texto = mensagem
        if causa and causa.textos:
            titulo = t('erro_causa_encontrada') if causa.encontrada else t('erro_causas_possiveis')
            texto += '\n\n' + titulo + '\n' + '\n'.join('•  ' + c for c in causa.textos)
            if causa.cfa_confirmado:
                texto += '\n\n' + core.mensagem_acesso_controlado(caminho_do_programa())
        self.texto = texto
        caixa = tk.Text(corpo, wrap='word', height=14, width=78, relief='flat', borderwidth=0,
                        font=('Segoe UI', 9), bg=temas.cor('campo') if temas.atual() == 'escuro' else 'SystemButtonFace',
                        fg=temas.cor('texto') or 'SystemButtonText')
        caixa.insert('1.0', texto)
        caixa.config(state='disabled')
        caixa.pack(fill='both', expand=True, pady=(10, 10))
        self.aviso = ttk.Label(corpo, text='', style='Fraco.TLabel')
        self.aviso.pack(anchor='w')
        bts = ttk.Frame(corpo)
        bts.pack(fill='x', pady=(8, 0))
        ttk.Button(bts, text=t('bt_copiar_detalhes'), command=self.copiar).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_pasta_logs'), command=app.abrir_logs).pack(side='left', padx=6)
        ttk.Button(bts, text=t('bt_fechar'), command=self.destroy).pack(side='right')
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


class JanelaApoio(tk.Toplevel):
    """Pequena janela de doação."""

    def __init__(self, app):
        super().__init__(app)
        self.title(t('apoio_titulo'))
        self.resizable(False, False)
        temas.preparar_janela(self)
        self.transient(app)
        _modal(self)
        corpo = ttk.Frame(self, padding=18)
        corpo.pack(fill='both', expand=True)
        ttk.Label(corpo, text=t('apoio_pergunta'), font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        ttk.Label(corpo, wraplength=380, justify='left', text=t('apoio_texto', programa=NOME_DO_PROGRAMA)).pack(
            anchor='w', pady=(8, 14))
        for texto, link in (('☕  Buy Me a Coffee', LINK_BUYMEACOFFEE), ('💠  LivePix (Pix)', LINK_LIVEPIX)):
            bt = ttk.Button(corpo, text=texto if link else f'{texto}  {t("em_breve")}',
                            command=lambda l=link: self.abrir(l))
            bt.pack(fill='x', pady=3)
            if not link:
                bt.state(['disabled'])
        ttk.Label(corpo, text=t('credito', autor=AUTOR, versao=VERSAO), style='Fraco.TLabel').pack(
            anchor='w', pady=(14, 0))
        ttk.Button(corpo, text=t('bt_fechar'), command=self.destroy).pack(anchor='e', pady=(10, 0))

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
