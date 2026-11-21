"""Faixa do topo do painel do mapa: a ilustração do mapa (desenho próprio, já desfocado),
escurecida da esquerda para a direita para o texto branco ficar legível.

As ilustrações ficam em mapas\\mapa_<chave>.jpg (geradas a partir de modelos_layout\\v099\\artes_mapas.js).
São desenhos originais, inspirados no tipo de paisagem de cada região: nenhuma imagem do jogo.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageTk

# Cor de cada mapa (quadradinho da lista e fundo quando não há imagem)
CORES = {0: '#6e9a55', 1: '#3f7a6a', 2: '#566a6e', 3: '#c98f48', 4: '#9a7b4c', 6: '#7d9bb3', 8: '#b59a5a',
         9: '#8a8f6a', 10: '#3e7f5c', 11: '#c08a52', 12: '#6f8f4e', 13: '#2c5468', 14: '#a0623f', 16: '#4b9a7e',
         17: '#8e8ca8', 18: '#7a9a6a', 19: '#9aa4ae', 20: '#6e7f62', 21: '#7f9a52'}
COR_PADRAO = '#5f7f70'

_originais = {}


def _pasta():
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'mapas')


def cor(chave):
    return CORES.get(chave, COR_PADRAO)


def _original(chave):
    if chave not in _originais:
        caminho = os.path.join(_pasta(), f'mapa_{chave}.jpg')
        try:
            _originais[chave] = Image.open(caminho).convert('RGB')
        except OSError:
            _originais[chave] = None
    return _originais[chave]


def _cobrir(img, largura, altura):
    """Redimensiona cobrindo a área toda (corta o que sobrar, centralizado)."""
    w, h = img.size
    escala = max(largura / w, altura / h)
    nova = img.resize((max(1, round(w * escala)), max(1, round(h * escala))), Image.LANCZOS)
    x = (nova.width - largura) // 2
    y = (nova.height - altura) // 2
    return nova.crop((x, y, x + largura, y + altura))


def _rgb(cor_hex):
    cor_hex = cor_hex.lstrip('#')
    return tuple(int(cor_hex[i:i + 2], 16) for i in (0, 2, 4))


def imagem(chave, largura, altura, escurecer=True, mestre=None):
    """PhotoImage da faixa. chave=None: degradê neutro (nenhum mapa escolhido)."""
    largura, altura = max(1, int(largura)), max(1, int(altura))
    base = _original(chave) if chave is not None else None
    if base is not None:
        img = _cobrir(base, largura, altura)
    else:
        a, b = _rgb(cor(chave) if chave is not None else COR_PADRAO), (30, 40, 38)
        img = Image.new('RGB', (largura, altura))
        d = ImageDraw.Draw(img)
        for x in range(largura):
            f = x / max(1, largura - 1)
            d.line([(x, 0), (x, altura)], fill=tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3)))
    if escurecer:
        sombra = Image.new('L', (largura, 1))
        for x in range(largura):
            f = x / max(1, largura - 1)
            # .62 na esquerda -> .2 aos 70% -> .05 na direita (como no modelo aprovado)
            alfa = 0.62 - (0.42 * f / 0.7) if f < 0.7 else 0.2 - 0.15 * (f - 0.7) / 0.3
            sombra.putpixel((x, 0), round(255 * alfa))
        sombra = sombra.resize((largura, altura))
        img = Image.composite(Image.new('RGB', (largura, altura), (0, 0, 0)), img, sombra)
    return ImageTk.PhotoImage(img, master=mestre)
