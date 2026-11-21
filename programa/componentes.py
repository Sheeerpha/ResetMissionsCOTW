"""Peças visuais da janela: caixinhas, círculos dos passos, barrinhas de progresso,
links, a "pílula" de Apoiar, dicas ao passar o mouse e a área com rolagem.

O Tk desenha círculos e cantos arredondados serrilhados. Por isso as formas são
pintadas aqui, pixel por pixel, com bordas suaves (antialiasing), e viram imagens.
"""
import math
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

import temas


# ------------------------------------------------------------------ pintura
def _rgb(cor):
    cor = cor.lstrip('#')
    return int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)


class Pintura:
    """Imagem pequena pintada com bordas suaves."""

    def __init__(self, largura, altura, fundo):
        self.w, self.h = int(largura), int(altura)
        self.px = [[_rgb(fundo)] * self.w for _ in range(self.h)]

    def _por(self, x, y, cor, a):
        if a <= 0:
            return
        linha = self.px[y]
        if a >= 1:
            linha[x] = cor
            return
        r, g, b = linha[x]
        linha[x] = (round(r + (cor[0] - r) * a), round(g + (cor[1] - g) * a), round(b + (cor[2] - b) * a))

    def _forma(self, x0, y0, x1, y1, distancia, cor):
        cor = _rgb(cor)
        for y in range(max(0, int(y0) - 1), min(self.h, math.ceil(y1) + 1)):
            for x in range(max(0, int(x0) - 1), min(self.w, math.ceil(x1) + 1)):
                self._por(x, y, cor, min(1.0, max(0.0, 0.5 - distancia(x + 0.5, y + 0.5))))

    def ret(self, x0, y0, x1, y1, raio, cor, borda=None, espessura=1.0):
        """Retângulo de cantos arredondados (com borda opcional)."""
        if borda:
            self.ret(x0, y0, x1, y1, raio, borda)
            e = espessura
            self.ret(x0 + e, y0 + e, x1 - e, y1 - e, max(0, raio - e), cor)
            return
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        raio = min(raio, (x1 - x0) / 2, (y1 - y0) / 2)
        mx, my = (x1 - x0) / 2 - raio, (y1 - y0) / 2 - raio

        def d(px, py):
            qx, qy = abs(px - cx) - mx, abs(py - cy) - my
            return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - raio
        self._forma(x0, y0, x1, y1, d, cor)

    def circulo(self, cx, cy, raio, cor, borda=None, espessura=1.5):
        self.ret(cx - raio, cy - raio, cx + raio, cy + raio, raio, cor, borda, espessura)

    def elipse(self, cx, cy, rx, ry, cor):
        def d(px, py):
            k = math.hypot((px - cx) / rx, (py - cy) / ry)
            return (k - 1) * min(rx, ry)
        self._forma(cx - rx, cy - ry, cx + rx, cy + ry, d, cor)

    def linha(self, pontos, espessura, cor):
        """Linha grossa de pontas redondas passando pelos pontos."""
        r = espessura / 2
        for (ax, ay), (bx, by) in zip(pontos, pontos[1:]):
            def d(px, py, ax=ax, ay=ay, bx=bx, by=by):
                vx, vy, wx, wy = bx - ax, by - ay, px - ax, py - ay
                h = max(0.0, min(1.0, (wx * vx + wy * vy) / ((vx * vx + vy * vy) or 1)))
                return math.hypot(wx - vx * h, wy - vy * h) - r
            self._forma(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r, d, cor)

    def coracao(self, cx, cy, tam, cor):
        """Coraçãozinho (dois círculos e um triângulo arredondado)."""
        r = tam * 0.3
        self.circulo(cx - r * 0.95, cy - r * 0.35, r, cor)
        self.circulo(cx + r * 0.95, cy - r * 0.35, r, cor)
        self.linha([(cx - r * 1.55, cy + r * 0.05), (cx, cy + tam * 0.62), (cx + r * 1.55, cy + r * 0.05)],
                   r * 0.9, cor)
        self.ret(cx - r * 1.2, cy - r * 0.4, cx + r * 1.2, cy + r * 0.3, 1, cor)
        self.linha([(cx - r * 0.9, cy + r * 0.2), (cx, cy + tam * 0.5), (cx + r * 0.9, cy + r * 0.2)], r * 1.4, cor)

    def imagem(self, mestre):
        img = tk.PhotoImage(master=mestre, width=self.w, height=self.h)
        img.put(' '.join('{' + ' '.join('#%02x%02x%02x' % p for p in linha) + '}' for linha in self.px))
        return img


def guardar_imagem(widget, chave, fazer):
    """Cria a imagem uma vez por janela principal (as imagens do Tk somem se ninguém as guardar)."""
    raiz = widget._root()
    cache = raiz.__dict__.setdefault('_cache_imagens', {})
    chave = (temas.atual(),) + tuple(chave)
    if chave not in cache:
        cache[chave] = fazer().imagem(raiz)
    return cache[chave]


def _visto(p, x0, y0, tam, cor, espessura=None):
    """Sinal de "visto" (✓) dentro de um quadrado de lado 'tam'."""
    e = espessura or max(1.6, tam * 0.13)
    p.linha([(x0 + tam * 0.27, y0 + tam * 0.53), (x0 + tam * 0.44, y0 + tam * 0.70),
             (x0 + tam * 0.74, y0 + tam * 0.34)], e, cor)


def img_circulo(widget, estado, fundo, tam=None):
    tam = tam or temas.px(28)
    """Círculo de um passo: 'feito' (✓), 'atual' (verde cheio) ou 'espera' (só contorno)."""
    c = temas.CORES[temas.atual()]

    def fazer():
        p = Pintura(tam, tam, fundo)
        m = tam / 2
        if estado == 'feito':
            p.circulo(m, m, m - 0.5, c['destaque_suave'], borda=c['destaque'], espessura=1.6)
            _visto(p, 0, 0, tam, c['destaque'], tam * 0.09)
        elif estado == 'atual':
            p.circulo(m, m, m - 0.5, c['destaque'])
        elif estado == 'aviso':
            p.circulo(m, m, m - 0.5, c['aviso'])
        elif estado == 'quente':
            p.circulo(m, m, m - 0.5, c['quente'])
        else:
            p.circulo(m, m, m - 0.5, c['sup'], borda=c['fraquinho'], espessura=1.5)
        return p
    return guardar_imagem(widget, ('circulo', estado, fundo, tam), fazer)


def img_caixa(widget, marcada, fundo, tam=None):
    tam = tam or temas.px(16)
    c = temas.CORES[temas.atual()]

    def fazer():
        p = Pintura(tam, tam, fundo)
        if marcada:
            p.ret(0.5, 0.5, tam - 0.5, tam - 0.5, 4, c['destaque'])
            _visto(p, 0, 0, tam, c['destaque_texto'], 2.0)
        else:
            p.ret(0.5, 0.5, tam - 0.5, tam - 0.5, 4, c['sup'], borda=c['fraquinho'], espessura=1.5)
        return p
    return guardar_imagem(widget, ('caixa', marcada, fundo, tam), fazer)


def img_vazia(widget, fundo, largura, altura):
    return guardar_imagem(widget, ('vazia', fundo, largura, altura), lambda: Pintura(largura, altura, fundo))


def img_barra(widget, fracao, cor_cheia, fundo, largura=None, altura=None):
    """Barrinha de progresso de pontas redondas."""
    largura, altura = largura or temas.px(64), altura or temas.px(4)
    c = temas.CORES[temas.atual()]
    cheio = round(max(0.0, min(1.0, fracao)) * largura)

    def fazer():
        p = Pintura(largura, altura, fundo)
        p.ret(0, 0, largura, altura, altura / 2, c['trilho'])
        if cheio > 0:
            p.ret(0, 0, max(cheio, altura), altura, altura / 2, cor_cheia)
        return p
    return guardar_imagem(widget, ('barra', cheio, cor_cheia, fundo, largura, altura), fazer)


def img_ret(widget, largura, altura, raio, cor, fundo, borda=None, espessura=1.0):
    def fazer():
        p = Pintura(largura, altura, fundo)
        p.ret(0, 0, largura, altura, raio, cor, borda, espessura)
        return p
    return guardar_imagem(widget, ('ret', largura, altura, raio, cor, fundo, borda, espessura), fazer)


def _existe(widget):
    try:
        return bool(widget.winfo_exists())
    except tk.TclError:
        return False


# -------------------------------------------------------------------- peças
class Circulo(tk.Canvas):
    """Círculo numerado de um passo."""

    def __init__(self, pai, numero, fundo=None, tam=None):
        tam = tam or temas.px(28)
        self.fundo = fundo or temas.cor('fundo')
        super().__init__(pai, width=tam, height=tam, bg=self.fundo, highlightthickness=0, bd=0)
        self.tam, self.numero, self.estado = tam, str(numero), None
        self._img = self.create_image(0, 0, anchor='nw')
        self._txt = self.create_text(tam / 2, tam / 2, font=temas.fonte(10, 'bold'))
        self.definir('espera')

    def definir(self, estado):
        if estado == self.estado:
            return
        self.estado = estado
        c = temas.CORES[temas.atual()]
        self.itemconfigure(self._img, image=img_circulo(self, estado, self.fundo, self.tam))
        texto = '' if estado == 'feito' else self.numero
        cor = {'atual': c['destaque_texto'], 'aviso': '#ffffff', 'quente': '#ffffff'}.get(estado, c['fraco'])
        self.itemconfigure(self._txt, text=texto, fill=cor)


class Link(tk.Label):
    """Texto clicável sublinhado. Tem invoke(), state() e instate() como um botão."""

    def __init__(self, pai, texto='', comando=None, forte=False, fundo=None, tamanho=10, sublinhado=True,
                 cor=None, negrito=False):
        self.fundo = fundo or temas.cor('fundo')
        self.cor_normal = cor or (temas.cor('destaque') if forte else temas.cor('fraco'))
        self.cor_hover = temas.cor('destaque_hover') if forte else temas.cor('texto')
        estilo = ['underline'] if sublinhado else []
        if negrito:
            estilo.append('bold')
        super().__init__(pai, text=texto, bg=self.fundo, fg=self.cor_normal, cursor='hand2', bd=0, padx=0, pady=0,
                         font=temas.fonte(tamanho, *estilo))
        self.comando = comando
        self._desativado = False
        self.bind('<Button-1>', lambda e: self.invoke())
        self.bind('<Enter>', lambda e: self._desativado or super(Link, self).configure(fg=self.cor_hover))
        self.bind('<Leave>', lambda e: self._desativado or super(Link, self).configure(fg=self.cor_normal))

    def invoke(self):
        if not self._desativado and self.comando:
            return self.comando()

    def state(self, especificacao=None):
        for s in especificacao or ():
            if s == 'disabled':
                self._desativado = True
            elif s == '!disabled':
                self._desativado = False
        super().configure(fg=temas.cor('fraquinho') if self._desativado else self.cor_normal,
                          cursor='' if self._desativado else 'hand2')
        return ('disabled',) if self._desativado else ()

    def instate(self, especificacao):
        return all((s == 'disabled') == self._desativado if not s.startswith('!') else
                   (s[1:] == 'disabled') != self._desativado for s in especificacao)


class SeletorIdioma(Link):
    """"Português ▾": abre um menu com os idiomas."""

    def __init__(self, pai, idiomas_nomes, atual, ao_escolher, fundo=None):
        self.nomes = idiomas_nomes          # {código: nome}
        self.atual = atual
        super().__init__(pai, texto=f'{idiomas_nomes[atual]} ▾', comando=self.abrir_menu, fundo=fundo,
                         sublinhado=False)
        self.ao_escolher = ao_escolher

    def get(self):
        return self.nomes[self.atual]

    def abrir_menu(self):
        menu = tk.Menu(self, tearoff=False)
        for cod, nome in self.nomes.items():
            menu.add_command(label=('✓  ' if cod == self.atual else '     ') + nome,
                             command=lambda c=cod: self.ao_escolher(c))
        try:
            menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height() + 2)
        finally:
            menu.grab_release()


class Pilula(tk.Canvas):
    """Botão arredondado de tom quente: "☕ Gostou? Apoie o projeto"."""

    def __init__(self, pai, texto, comando, fundo=None, icone='☕'):
        c = temas.CORES[temas.atual()]
        self.fundo = fundo or c['fundo']
        f = tkfont.Font(family=temas.FONTE, size=9, weight='bold')
        px = temas.px
        alt, ic = px(30), px(22)
        larg = px(6) + ic + px(8) + f.measure(texto) + px(14)
        super().__init__(pai, width=larg, height=alt, bg=self.fundo, highlightthickness=0, bd=0, cursor='hand2')
        self.normal = img_ret(self, larg, alt, alt / 2, c['quente_suave'], self.fundo, c['quente_borda'], 1.0)
        self.hover = img_ret(self, larg, alt, alt / 2, c['quente_suave'], self.fundo, c['quente'], 1.5)
        self._fundo_img = self.create_image(0, 0, anchor='nw', image=self.normal)
        self.create_image(px(5), (alt - ic) // 2, anchor='nw', image=img_circulo(self, 'quente', c['quente_suave'], ic))
        self._icone = self.create_text(px(5) + ic / 2, alt / 2, text=icone, fill='#ffffff', font=temas.fonte(8))
        self.create_text(px(5) + ic + px(8), alt / 2, text=texto, anchor='w', fill=c['quente'], font=f)
        self.texto, self.comando = texto, comando
        self.bind('<Button-1>', lambda e: self.invoke())
        self.bind('<Enter>', lambda e: self.itemconfigure(self._fundo_img, image=self.hover))
        self.bind('<Leave>', lambda e: self.itemconfigure(self._fundo_img, image=self.normal))

    def invoke(self):
        if self.comando:
            return self.comando()


class Dica:
    """Texto que aparece ao parar o mouse em cima de um widget."""

    def __init__(self, widget, texto, atraso=450):
        self.widget, self.texto, self.janela, self._espera = widget, texto, None, None
        self.atraso = atraso
        widget.bind('<Enter>', self._agendar, add='+')
        widget.bind('<Leave>', self._esconder, add='+')
        widget.bind('<Button-1>', self._esconder, add='+')

    def _agendar(self, _=None):
        self._cancelar()
        self._espera = self.widget.after(self.atraso, self._mostrar)

    def _cancelar(self):
        if self._espera:
            try:
                self.widget.after_cancel(self._espera)
            except tk.TclError:
                pass
            self._espera = None

    def _mostrar(self):
        texto = self.texto() if callable(self.texto) else self.texto
        if not texto or not self.widget.winfo_exists():
            return
        c = temas.CORES[temas.atual()]
        self.janela = tk.Toplevel(self.widget)
        self.janela.wm_overrideredirect(True)
        self.janela.configure(bg=c['borda'])
        tk.Label(self.janela, text=texto, bg=c['sup'], fg=c['texto'], font=temas.fonte(9), justify='left',
                 padx=8, pady=5, wraplength=360).pack(padx=1, pady=1)
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.janela.wm_geometry(f'+{x}+{y}')

    def _esconder(self, _=None):
        self._cancelar()
        if self.janela is not None:
            try:
                self.janela.destroy()
            except tk.TclError:
                pass
            self.janela = None


class AreaRolavel(ttk.Frame):
    """Área com rolagem vertical (só aparece a barra quando o conteúdo não cabe).
    O conteúdo fica numa coluna centralizada de largura máxima 'largura' (None = largura toda).
    A rodinha do mouse rola a área que está embaixo do ponteiro (pode haver várias na janela)."""

    _areas = []

    def __init__(self, pai, largura=800, fundo=None, margem=32):
        super().__init__(pai)
        self.largura, self.margem = largura, margem
        fundo = fundo or temas.cor('fundo')
        self.canvas = tk.Canvas(self, bg=fundo, highlightthickness=0, bd=0)
        self.barra = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._rolou)
        self.dentro = tk.Frame(self.canvas, bg=fundo)
        self._janela = self.canvas.create_window(0, 0, anchor='nw', window=self.dentro)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.dentro.bind('<Configure>', lambda e: self._ajustar())
        self.canvas.bind('<Configure>', lambda e: self._ajustar())
        AreaRolavel._areas = [a for a in AreaRolavel._areas if _existe(a)] + [self]
        self.bind_all('<MouseWheel>', AreaRolavel._roda_global)

    def _ajustar(self):
        w = self.canvas.winfo_width()
        larg = w if self.largura is None else min(self.largura, max(w - self.margem, 300))
        self.canvas.itemconfigure(self._janela, width=larg)
        self.canvas.coords(self._janela, max((w - larg) // 2, 0), 0)
        self.canvas.configure(scrollregion=(0, 0, w, self.dentro.winfo_reqheight()))

    @staticmethod
    def _roda_global(evento):
        try:
            w = evento.widget.winfo_containing(evento.x_root, evento.y_root)
        except (tk.TclError, AttributeError, KeyError):
            return
        while w is not None:
            if isinstance(w, AreaRolavel) and _existe(w):
                if w.barra.winfo_manager():
                    w.canvas.yview_scroll(int(-evento.delta / 120), 'units')
                    return
            w = getattr(w, 'master', None)

    def _rolou(self, primeiro, ultimo):
        self.barra.set(primeiro, ultimo)
        cabe = float(primeiro) <= 0 and float(ultimo) >= 1
        if cabe and self.barra.winfo_manager():
            self.barra.pack_forget()
        elif not cabe and not self.barra.winfo_manager():
            self.barra.pack(side='right', fill='y', before=self.canvas)

    def mostrar(self, widget):
        """Rola até o widget ficar visível."""
        try:
            self.update_idletasks()
            y = widget.winfo_rooty() - self.dentro.winfo_rooty()
            total = max(self.dentro.winfo_reqheight(), 1)
            topo, fim = self.canvas.yview()
            visivel = self.canvas.winfo_height()
            if y < topo * total or y + widget.winfo_height() > topo * total + visivel:
                self.canvas.yview_moveto(max(0, y - 20) / total)
        except tk.TclError:
            pass
