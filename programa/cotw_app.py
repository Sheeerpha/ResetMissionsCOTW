"""Janela do ResetMissionsCOTW - Reset de Missões por Mapa (theHunter: Call of the Wild).

Os textos ficam em idiomas.py (português, inglês e espanhol).
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cotw_core as core
import idiomas
import temas
from idiomas import t

VERSAO = '0.9.5 (Beta)'
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
        self._agendados = []
        self._montar()
        self._agendados.append(self.after(100, self.iniciar))

    def destroy(self):
        for a in self._agendados:
            self.after_cancel(a)
        super().destroy()

    def iniciar(self):
        self.verificar_permissao()
        self.procurar_saves()
        self._agendados.append(self.after(300, self.mostrar_boas_vindas))

    # O aviso "Antes de começar" aparece toda vez que o programa abre (os testes desligam isto).
    mostrar_aviso_ao_abrir = True

    def mostrar_boas_vindas(self):
        """Ao abrir: o aviso "Antes de começar" (sempre) e, depois dele, a introdução
        (só na primeira vez)."""
        if any(isinstance(w, (JanelaAviso, JanelaIntro)) for w in self.winfo_children()):
            return  # já está aberta
        if self.mostrar_aviso_ao_abrir:
            JanelaAviso(self, depois=self._intro_se_primeira_vez)
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
        ttk.Button(bts, text=t('bt_como_liberar'), command=self.mostrar_passo_a_passo).pack(side='left')
        ttk.Button(bts, text=t('bt_abrir_seguranca'), command=self.abrir_seguranca).pack(side='left', padx=6)
        ttk.Button(bts, text=t('bt_copiar_caminho'), command=self.copiar_caminho).pack(side='left')
        ttk.Button(bts, text=t('bt_testar_de_novo'), command=self.testar_de_novo).pack(side='left', padx=6)

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

    # --------------------------------------------- Acesso Controlado a Pastas
    def verificar_permissao(self):
        erro = core.testar_gravacao(self.raiz)
        self.bloqueado = erro is not None
        if erro is None:
            self.faixa.pack_forget()
            core.migrar_pasta_antiga(self.raiz)
        else:
            if core.parece_bloqueio_do_windows(erro):
                texto = t('faixa_bloqueio')
            else:
                texto = t('faixa_erro', erro=erro)
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
        if core.jogo_aberto():
            messagebox.showwarning(TITULO, t('jogo_aberto'), parent=parent)
            return False
        return True

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
            if resposta and not self.fazer_backup_save(perguntar_ok=False):
                return
        if not messagebox.askyesno(TITULO, t('confirmar_reset', save=self.save_atual.nome_curto(),
                                             detalhes=detalhes), icon='warning'):
            return
        try:
            core.resetar_mapas(self.save_atual, sel, self.raiz)
        except (OSError, core.ErroSave) as e:
            texto = core.texto_do_erro(e, caminho_do_programa())
            if isinstance(e, core.ErroSave):
                texto = t('nao_foi_possivel_resetar', texto=texto)
            messagebox.showerror(TITULO, texto)
            self.recarregar()
            return
        self.recarregar()
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
    def fazer_backup_save(self, perguntar_ok=True, parent=None):
        """Copia a pasta inteira do save. Devolve True se deu certo."""
        if self.save_atual is None:
            messagebox.showinfo(TITULO, t('nenhum_save_escolhido'), parent=parent)
            return False
        if not self._pode_alterar(parent=parent):
            return False
        self.config(cursor='watch')
        self.update_idletasks()
        try:
            b = core.fazer_backup_save_completo(self.save_atual, self.raiz)
        except (OSError, core.ErroSave) as e:
            messagebox.showerror(TITULO, t('nao_foi_possivel_backup_save',
                                           texto=core.texto_do_erro(e, caminho_do_programa())), parent=parent)
            return False
        finally:
            self.config(cursor='')
        self.recarregar()
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
        try:
            core.restaurar_backup(self.app.save_atual, b, self.app.raiz)
        except (OSError, core.ErroSave) as e:
            messagebox.showerror(TITULO, t('nao_foi_possivel_restaurar',
                                           texto=core.texto_do_erro(e, caminho_do_programa())), parent=self)
            return
        self.destroy()
        self.app.recarregar()
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
            core.restaurar_save_completo(self.app.save_atual, b, self.app.raiz)
        except (OSError, core.ErroSave) as e:
            self.config(cursor='')
            messagebox.showerror(TITULO, t('nao_foi_possivel_restaurar',
                                           texto=core.texto_do_erro(e, caminho_do_programa())), parent=self)
            return
        self.destroy()
        self.app.recarregar()
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
    App().mainloop()


if __name__ == '__main__':
    main()
