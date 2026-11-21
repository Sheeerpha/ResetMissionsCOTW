"""Nomes das missões, lidos da instalação do jogo no PC do usuário (só leitura).

Nenhum texto do jogo vai dentro do programa: as tabelas (dados_missoes.py) só têm o hash do nome de
cada missão, e o texto vem do arquivo de traduções do jogo instalado (Steam ou Epic), no idioma do
programa. O resultado fica guardado em %LOCALAPPDATA%\\ResetMissionsCOTW\\nomes_missoes.json para
abrir rápido nas próximas vezes (é refeito sozinho quando o jogo é atualizado).

Formato (descoberto em 20/11/2026): archives_win64\\gameN.tab = 'TAB\\0', u16 2, u16 1, u32 alinhamento,
e entradas de 12 bytes (hash do nome do arquivo, offset, tamanho) no gameN.arc, sem compressão.
O arquivo de traduções é um ADF 'StringLookup': Languages (array) + Text (bytes). Cada idioma tem
SortedPairs (hash u32, offset i32 no Text). Ordem dos idiomas: 0 en, 1 fr, 2 de, 3 es, 4 ru, 5 pl,
6 ja, 7 pt, 8 cs, 9 zh.
"""
import glob
import json
import os
import re
import struct
import threading

import idiomas
import registro

HASH_TRADUCOES = 0xb8d20a3c                 # arquivo de traduções principal (todas as missões)
IDIOMA_DO_JOGO = {'pt': 7, 'en': 0, 'es': 3}
PASTA_JOGO = 'theHunterCotW'
CACHE = 'nomes_missoes.json'


# ------------------------------------------------------------ onde está o jogo
def _caminho_steam():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            return winreg.QueryValueEx(k, 'SteamPath')[0]
    except OSError:
        return None


def _bibliotecas_steam():
    steam = _caminho_steam()
    out = []
    if steam:
        out.append(os.path.normpath(steam))
        try:
            with open(os.path.join(steam, 'steamapps', 'libraryfolders.vdf'), encoding='utf-8', errors='ignore') as f:
                for m in re.finditer(r'"path"\s+"([^"]+)"', f.read()):
                    out.append(os.path.normpath(m.group(1).replace('\\\\', '\\')))
        except OSError:
            pass
    return list(dict.fromkeys(out))


def _instalacoes_epic():
    base = os.path.join(os.environ.get('PROGRAMDATA', r'C:\ProgramData'), 'Epic', 'EpicGamesLauncher', 'Data',
                        'Manifests')
    out = []
    for item in glob.glob(os.path.join(base, '*.item')):
        try:
            with open(item, encoding='utf-8') as f:
                info = json.load(f)
            if 'thehunter' in (info.get('DisplayName', '') + info.get('InstallLocation', '')).lower():
                out.append(info.get('InstallLocation', ''))
        except (OSError, ValueError):
            pass
    return out


def pasta_valida(pasta):
    """Pasta do jogo (a que tem archives_win64)? Aceita também a própria archives_win64."""
    if not pasta:
        return None
    for p in (os.path.join(pasta, 'archives_win64'), pasta):
        if os.path.isdir(p) and glob.glob(os.path.join(p, 'game*.tab')):
            return os.path.dirname(p) if os.path.basename(p).lower() == 'archives_win64' else None
    return None


def encontrar_jogo():
    """Pasta de instalação do jogo, ou None. Primeiro a escolhida pelo usuário, depois Steam e Epic."""
    candidatas = [idiomas.ler_config().get('pasta_jogo')]
    candidatas += [os.path.join(b, 'steamapps', 'common', PASTA_JOGO) for b in _bibliotecas_steam()]
    candidatas += _instalacoes_epic()
    for c in candidatas:
        if pasta_valida(c):
            return pasta_valida(c)
    return None


# ------------------------------------------------------------ leitura das traduções
def _achar_traducoes(arquivos):
    for tab in sorted(glob.glob(os.path.join(arquivos, 'game*.tab'))):
        try:
            with open(tab, 'rb') as f:
                b = f.read()
        except OSError:
            continue
        if b[:4] != b'TAB\0':
            continue
        for p in range(12, len(b) - 11, 12):
            h, off, tam = struct.unpack_from('<III', b, p)
            if h == HASH_TRADUCOES:
                return tab[:-4] + '.arc', off, tam
    return None


def _ler_traducoes(arc, off, tam, hashes):
    """{codigo_idioma: {hash: texto}} só para os hashes pedidos."""
    with open(arc, 'rb') as f:
        f.seek(off)
        b = f.read(tam)
    if b[:4] != b' FDA':
        raise ValueError('traduções em formato desconhecido')
    _mg, _v, ic, io, *_ = struct.unpack_from('<4s10I', b, 0)
    _nh, _th, base, _size, _ni = struct.unpack_from('<IIIIQ', b, io)
    lp, ln = struct.unpack_from('<IxxxxQ', b, base)
    tp, tn = struct.unpack_from('<IxxxxQ', b, base + 16)
    texto = b[base + tp: base + tp + tn]
    out = {}
    for cod, i in IDIOMA_DO_JOGO.items():
        if i >= ln:
            continue
        sp, sn = struct.unpack_from('<IxxxxQ', b, base + lp + 32 * i)
        nomes = {}
        for k in range(sn):
            h, o = struct.unpack_from('<Ii', b, base + sp + 8 * k)
            if h in hashes and 0 <= o < len(texto):
                fim = texto.find(b'\0', o)
                nomes[h] = texto[o:fim].decode('utf-8', 'replace').strip()
        out[cod] = nomes
    return out


def _arquivo_cache():
    return os.path.join(idiomas.pasta_config(), CACHE)


def carregar_nomes(hashes, pasta_jogo=None):
    """{codigo_idioma: {hash: nome}} ou None se o jogo não foi encontrado / não deu para ler."""
    pasta = pasta_jogo or encontrar_jogo()
    if not pasta:
        return None
    arquivos = os.path.join(pasta, 'archives_win64')
    try:
        achado = _achar_traducoes(arquivos)
        if achado is None:
            registro.log('Nomes das missões: arquivo de traduções não encontrado no jogo.', 'AVISO')
            return None
        arc, off, tam = achado
        marca = f'{os.path.normcase(arc)}|{off}|{tam}|{int(os.path.getmtime(arc))}'
        try:
            with open(_arquivo_cache(), encoding='utf-8') as f:
                cache = json.load(f)
            if cache.get('marca') == marca and set(map(str, hashes)) <= set(cache.get('pt', {})):
                return {cod: {int(h): n for h, n in cache[cod].items()} for cod in IDIOMA_DO_JOGO if cod in cache}
        except (OSError, ValueError, KeyError, AttributeError):
            pass
        nomes = _ler_traducoes(arc, off, tam, set(hashes))
        try:
            os.makedirs(os.path.dirname(_arquivo_cache()), exist_ok=True)
            guardar = {'marca': marca}
            guardar.update({cod: {str(h): n for h, n in d.items()} for cod, d in nomes.items()})
            # todos os hashes pedidos entram na marca, mesmo os sem texto, para não reler à toa
            for h in hashes:
                guardar.setdefault('pt', {}).setdefault(str(h), nomes.get('pt', {}).get(h, ''))
            with open(_arquivo_cache(), 'w', encoding='utf-8') as f:
                json.dump(guardar, f, ensure_ascii=False)
        except OSError:
            pass
        return nomes
    except (OSError, ValueError, struct.error) as e:
        registro.log(f'Nomes das missões: não foi possível ler as traduções do jogo: {e!r}', 'AVISO')
        return None


class Consulta(threading.Thread):
    """Carrega os nomes sem travar a janela."""

    def __init__(self, hashes, pasta_jogo=None):
        super().__init__(daemon=True)
        self.hashes, self.pasta_jogo = hashes, pasta_jogo
        self.pronto = False
        self.resultado = None
        self.start()

    def run(self):
        try:
            self.resultado = carregar_nomes(self.hashes, self.pasta_jogo)
        finally:
            self.pronto = True
