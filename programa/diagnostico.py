"""Verificação antes de começar: o que pode atrapalhar a edição do save.

Tudo acontece só no computador (nada é enviado para a internet) e sem precisar de
administrador. Usa apenas recursos do próprio Windows:
- "Restart Manager" (rstrtmgr.dll) para saber QUAIS programas estão com os arquivos abertos;
- tasklist para ver os programas abertos;
- o registro e as variáveis do Windows para achar Steam, OneDrive, Google Drive e Dropbox.

Regras: nunca fechar nada sem o clique do usuário e nunca fechar à força.
"""
import csv
import ctypes
import io
import os
import subprocess
from ctypes import wintypes
from dataclasses import dataclass, field

import cotw_core as core
import registro
from idiomas import t

SEM_JANELA = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

# Programas conhecidos (nome do processo em minúsculas). O do jogo foi conferido na
# pasta de instalação: F:\SteamLibrary\steamapps\common\theHunterCotW\theHunterCotW_F.exe
JOGO = 'thehuntercotw_f.exe'
PROGRAMAS = {
    'steam': ('steam.exe', 'Steam'),
    'epic': ('epicgameslauncher.exe', 'Epic Games Launcher'),
    'onedrive': ('onedrive.exe', 'OneDrive'),
    'googledrive': ('googledrivefs.exe', 'Google Drive'),
    'dropbox': ('dropbox.exe', 'Dropbox'),
}


# ---------------------------------------------------------------------------
# Programas abertos
# ---------------------------------------------------------------------------

def processos_abertos():
    """{nome do processo em minúsculas: [pids]}"""
    try:
        # o tasklist escreve na página de código do console (com acentos): 'oem' lê certo
        saida = subprocess.run(['tasklist', '/fo', 'csv', '/nh'], capture_output=True, encoding='oem',
                               errors='replace', creationflags=SEM_JANELA, timeout=15).stdout
    except Exception:
        return {}
    abertos = {}
    for linha in csv.reader(io.StringIO(saida)):
        if len(linha) >= 2 and linha[1].isdigit():
            abertos.setdefault(linha[0].lower(), []).append(int(linha[1]))
    return abertos


def caminho_do_processo(pid):
    """Caminho completo do .exe de um processo (ou None)."""
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    h = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return None
    try:
        tamanho = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(tamanho)):
            return buf.value
        return None
    finally:
        k32.CloseHandle(h)


# ---------------------------------------------------------------------------
# Quem está usando os arquivos (Restart Manager do Windows)
# ---------------------------------------------------------------------------

class _RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [('dwProcessId', wintypes.DWORD), ('ProcessStartTime', wintypes.FILETIME)]


class _RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [('Process', _RM_UNIQUE_PROCESS),
                ('strAppName', wintypes.WCHAR * 256),
                ('strServiceShortName', wintypes.WCHAR * 64),
                ('ApplicationType', ctypes.c_int),
                ('AppStatus', wintypes.ULONG),
                ('TSSessionId', wintypes.DWORD),
                ('bRestartable', wintypes.BOOL)]


@dataclass
class ProgramaUsando:
    pid: int
    nome: str            # nome amigável (ex.: "Microsoft OneDrive")
    exe: str = ''        # nome do .exe em minúsculas (ex.: "onedrive.exe")

    @property
    def chave(self):
        """'steam', 'onedrive'... se for um programa conhecido."""
        for chave, (exe, _) in PROGRAMAS.items():
            if self.exe == exe:
                return chave
        return 'jogo' if self.exe == JOGO else None

    def texto(self):
        return f'{self.nome} ({self.exe})' if self.exe and self.exe not in self.nome.lower() else self.nome


def quem_usa(caminhos):
    """Lista de ProgramaUsando com algum destes arquivos aberto. None se não deu para saber."""
    caminhos = [c for c in caminhos if c]
    if not caminhos:
        return []
    try:
        rm = ctypes.WinDLL('rstrtmgr')
    except OSError:
        return None
    sessao = wintypes.DWORD()
    chave = ctypes.create_unicode_buffer(33)          # CCH_RM_SESSION_KEY + 1
    if rm.RmStartSession(ctypes.byref(sessao), 0, chave) != 0:
        return None
    try:
        lista = (wintypes.LPCWSTR * len(caminhos))(*caminhos)
        if rm.RmRegisterResources(sessao, len(caminhos), lista, 0, None, 0, None) != 0:
            return None
        precisa, quantos, motivo = wintypes.UINT(0), wintypes.UINT(0), wintypes.DWORD(0)
        r = rm.RmGetList(sessao, ctypes.byref(precisa), ctypes.byref(quantos), None, ctypes.byref(motivo))
        if r == 0:
            return []
        if r != 234:                                   # ERROR_MORE_DATA
            return None
        infos = (_RM_PROCESS_INFO * precisa.value)()
        quantos = wintypes.UINT(precisa.value)
        if rm.RmGetList(sessao, ctypes.byref(precisa), ctypes.byref(quantos), infos, ctypes.byref(motivo)) != 0:
            return None
        achados, vistos = [], set()
        for i in range(quantos.value):
            pid = infos[i].Process.dwProcessId
            if pid == os.getpid() or pid in vistos:
                continue
            vistos.add(pid)
            caminho = caminho_do_processo(pid) or ''
            achados.append(ProgramaUsando(pid, infos[i].strAppName or os.path.basename(caminho),
                                          os.path.basename(caminho).lower()))
        return achados
    finally:
        rm.RmEndSession(sessao)


def arquivos_em(pasta, limite=2000):
    """Arquivos de uma pasta (com subpastas), até 'limite'."""
    out = []
    if os.path.isfile(pasta):
        return [pasta]
    for atual, _, arquivos in os.walk(pasta):
        for a in arquivos:
            out.append(os.path.join(atual, a))
            if len(out) >= limite:
                return out
    return out


# ---------------------------------------------------------------------------
# Pastas de nuvem e "somente leitura"
# ---------------------------------------------------------------------------

def _pastas_dropbox():
    try:
        import json
        with open(os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Dropbox', 'info.json'), encoding='utf-8') as f:
            info = json.load(f)
        return [v.get('path') for v in info.values() if isinstance(v, dict) and v.get('path')]
    except Exception:
        return []


def pasta_de_nuvem(pasta):
    """'OneDrive', 'Google Drive', 'Dropbox' ou None."""
    p = os.path.normcase(os.path.abspath(pasta))
    partes = [x.lower() for x in p.split(os.sep)]
    for var in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        base = os.environ.get(var)
        if base and (p + os.sep).startswith(os.path.normcase(base) + os.sep):
            return 'OneDrive'
    if any(x == 'onedrive' or x.startswith('onedrive - ') for x in partes):
        return 'OneDrive'
    if any(x in ('my drive', 'meu drive', 'mi unidad', 'google drive', 'shared drives', 'drives compartilhados')
           for x in partes):
        return 'Google Drive'
    for base in _pastas_dropbox():
        if (p + os.sep).startswith(os.path.normcase(base) + os.sep):
            return 'Dropbox'
    if 'dropbox' in partes:
        return 'Dropbox'
    return None


def itens_somente_leitura(pastas):
    """Arquivos e pastas marcados como somente leitura dentro destas pastas."""
    achados = []
    for pasta in pastas:
        if not pasta or not os.path.exists(pasta):
            continue
        for atual, subpastas, arquivos in os.walk(pasta):
            for nome in [atual] + [os.path.join(atual, a) for a in subpastas + arquivos]:
                if core.eh_somente_leitura(nome) and nome not in achados:
                    achados.append(nome)
    return achados


def corrigir_somente_leitura(itens):
    n = sum(1 for c in itens if core.tirar_somente_leitura(c))
    registro.log(f'Somente leitura retirado de {n} item(ns).')
    return n


# ---------------------------------------------------------------------------
# A verificação
# ---------------------------------------------------------------------------

@dataclass
class Item:
    tipo: str                 # 'jogo', 'em_uso', 'somente_leitura', 'steam', 'epic', 'onedrive', 'googledrive',
                              # 'dropbox', 'nuvem'
    nivel: str                # 'impede' (precisa resolver ou "continuar mesmo assim") ou 'atencao'
    texto: str
    dados: dict = field(default_factory=dict)


@dataclass
class Resultado:
    itens: list = field(default_factory=list)

    @property
    def impedimentos(self):
        return [i for i in self.itens if i.nivel == 'impede']

    @property
    def avisos(self):
        return [i for i in self.itens if i.nivel == 'atencao']

    @property
    def jogo_aberto(self):
        return any(i.tipo == 'jogo' for i in self.itens)


def verificar(save, raiz):
    """Confere o que pode atrapalhar a edição deste save."""
    r = Resultado()
    abertos = processos_abertos()
    if core.jogo_aberto():
        r.itens.append(Item('jogo', 'impede', t('item_jogo')))
    if save is not None:
        usando = quem_usa(arquivos_em(save.pasta))
        if usando:
            for p in usando:
                if p.chave == 'jogo':
                    continue  # já aparece no item do jogo
                r.itens.append(Item('em_uso', 'impede', t('item_em_uso', programa=p.texto()),
                                    {'programa': p}))
        leitura = itens_somente_leitura([save.pasta, core.pasta_do_save_no_programa(save, raiz)])
        if leitura:
            r.itens.append(Item('somente_leitura', 'atencao', t('item_somente_leitura', n=len(leitura)),
                                {'itens': leitura}))
        nuvem = pasta_de_nuvem(save.pasta)
        if nuvem:
            r.itens.append(Item('nuvem', 'atencao', t('item_nuvem', servico=nuvem), {'servico': nuvem}))
    ja_em_uso = {i.dados['programa'].chave for i in r.itens if i.tipo == 'em_uso'}
    for chave, (exe, _nome) in PROGRAMAS.items():
        if exe in abertos and chave not in ja_em_uso:
            r.itens.append(Item(chave, 'atencao', t(f'item_{chave}'), {'pids': abertos[exe]}))
    registro.log('Verificação: ' + ('tudo pronto' if not r.itens else
                                    '; '.join(f'[{i.nivel}] {i.tipo}' for i in r.itens)))
    return r


# ---------------------------------------------------------------------------
# Botões (sempre pelo clique do usuário, nunca à força)
# ---------------------------------------------------------------------------

def caminho_do_steam():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            exe = winreg.QueryValueEx(k, 'SteamExe')[0]
        exe = os.path.normpath(exe)
        return exe if os.path.isfile(exe) else None
    except OSError:
        return None


def fechar_steam():
    """Comando oficial do Steam para fechar normalmente: steam.exe -shutdown."""
    exe = caminho_do_steam()
    if not exe:
        return False
    registro.log('Pedindo ao Steam para fechar (steam.exe -shutdown).')
    subprocess.Popen([exe, '-shutdown'], creationflags=SEM_JANELA)
    return True


def caminho_do_onedrive():
    for pid in processos_abertos().get('onedrive.exe', []):
        caminho = caminho_do_processo(pid)
        if caminho:
            return caminho
    for base in (os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'OneDrive'),
                 os.path.join(os.environ.get('ProgramFiles', ''), 'Microsoft OneDrive'),
                 os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Microsoft OneDrive')):
        exe = os.path.join(base, 'OneDrive.exe')
        if os.path.isfile(exe):
            return exe
    return None


def fechar_onedrive():
    """Comando oficial do OneDrive para fechar normalmente: OneDrive.exe /shutdown.
    Devolve o caminho do OneDrive (para poder reabrir depois) ou None."""
    exe = caminho_do_onedrive()
    if not exe:
        return None
    registro.log('Pedindo ao OneDrive para fechar (OneDrive.exe /shutdown).')
    subprocess.Popen([exe, '/shutdown'], creationflags=SEM_JANELA)
    return exe


def reabrir_onedrive(exe):
    registro.log('Reabrindo o OneDrive (OneDrive.exe /background).')
    subprocess.Popen([exe, '/background'], creationflags=SEM_JANELA)


def fechar_normalmente(exe):
    """Pede para o programa fechar como se o usuário clicasse no X (taskkill SEM /f).
    Programas que ficam só no ícone perto do relógio normalmente não fecham assim."""
    registro.log(f'Pedindo para {exe} fechar (taskkill sem /f).')
    try:
        r = subprocess.run(['taskkill', '/im', exe], capture_output=True, encoding='oem', errors='replace',
                           creationflags=SEM_JANELA, timeout=15)
        return r.returncode == 0
    except Exception:
        return False


def esta_aberto(exe):
    return exe.lower() in processos_abertos()


# ---------------------------------------------------------------------------
# Descobrir a causa de um erro
# ---------------------------------------------------------------------------

def cfa_bloqueou_recentemente(exe, minutos=15):
    """O Windows Defender registrou bloqueio deste programa (Acesso Controlado a Pastas)?
    True/False, ou None se não deu para consultar o histórico."""
    comando = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
               "Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Windows Defender/Operational';"
               f"Id=1123; StartTime=(Get-Date).AddMinutes(-{minutos})}} -ErrorAction SilentlyContinue |"
               " ForEach-Object { $_.Message }")
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', comando],
                           capture_output=True, encoding='utf-8', errors='replace',
                           creationflags=SEM_JANELA, timeout=20)
    except Exception:
        return None
    return os.path.normcase(exe) in os.path.normcase(r.stdout or '')


@dataclass
class Causa:
    textos: list = field(default_factory=list)   # causas encontradas (ou possíveis)
    encontrada: bool = False                      # True se há uma causa concreta
    cfa_confirmado: bool = False


def descobrir_causa(erro, caminho, exe):
    """Tenta descobrir por que uma operação de arquivo falhou."""
    c = Causa()
    original = getattr(erro, 'original', None) or erro
    alvo = getattr(original, 'filename', None) or caminho
    if not isinstance(original, OSError):
        return c
    # O Acesso Controlado a Pastas aparece como "acesso negado" OU como "não encontrado"
    # (WinError 2/3) ao criar pastas; as outras causas só valem para "acesso negado".
    bloqueio = core._eh_acesso_negado(original) or getattr(original, 'winerror', None) in (2, 3)
    if not bloqueio:
        c.textos.append(t('causa_desconhecida'))
        return c
    candidatos = [x for x in (alvo, caminho) if x]
    for x in candidatos:
        if os.path.exists(x) and core.eh_somente_leitura(x):
            c.textos.append(t('causa_somente_leitura', caminho=x))
            c.encontrada = True
            break
    arquivos = []
    for x in candidatos:
        if os.path.exists(x):
            arquivos += arquivos_em(x, limite=500)
    usando = quem_usa(arquivos) if arquivos else []
    if usando:
        c.textos.append(t('causa_em_uso', programas=', '.join(p.texto() for p in usando)))
        c.encontrada = True
    nuvem = next((n for n in (pasta_de_nuvem(x) for x in candidatos) if n), None)
    if nuvem:
        c.textos.append(t('causa_nuvem', servico=nuvem))
    if core.acesso_controlado_ligado() is True:
        if cfa_bloqueou_recentemente(exe):
            c.textos.insert(0, t('causa_cfa_confirmado'))
            c.encontrada = c.cfa_confirmado = True
        else:
            c.textos.append(t('causa_cfa_possivel'))
    if not c.textos:
        c.textos.append(t('causa_desconhecida'))
    registro.log('Causa do erro: ' + ' | '.join(c.textos), 'ERRO')
    return c
