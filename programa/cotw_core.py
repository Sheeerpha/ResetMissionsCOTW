"""Núcleo do "Reset de Missões por Mapa" para theHunter: Call of the Wild.

Tudo o que mexe no arquivo fica aqui; a janela (cotw_app.py) só chama estas
funções. O método é o mesmo do protótipo validado no jogo em 18/11/2026:
remover a entrada do mapa da tabela hash "Campaigns".
"""
import ctypes
import datetime
import errno
import json
import os
import shutil
import struct
import subprocess
import zlib
from dataclasses import dataclass, field

import idiomas
from idiomas import t

NOME_ARQUIVO = 'missions_missiondata_adf'
PASTA_PROGRAMA = '.BKP_ResetMissions_Saves_COTW'  # oculta, dentro de Documentos (o ponto põe no topo)
PASTA_ANTIGA = 'COTW Reset Missoes - Backups'     # usada nas versões 1.0 e 1.1
PASTA_ANTIGA_2 = 'COTW Reset Missoes'             # usada nas versões 1.2 a 1.5
BACKUPS_MISSOES = 'Backups_MISSIONS'              # backups do arquivo de missões
BACKUPS_SAVE = 'Backups_SAVE'                     # backups da pasta do save inteira
PASTA_ARQUIVOS_SAVE = 'save'                      # dentro de cada backup completo: a cópia da pasta do save
LIMITE_MISSOES = 50   # backups de missões guardados por save (o mais antigo nunca é apagado)
LIMITE_SAVE = 5       # backups do save completo guardados por save (o mais antigo nunca é apagado)

B = 5             # o ADF começa no byte 5 do conteúdo descomprimido
INST = B + 0x68   # instância raiz (MissionManager_1)
ENTRY = 104       # tamanho de cada entrada da tabela Campaigns
NODE = 96         # tamanho de um MissionSaveData_1
CONCLUIDA = 4     # CompletionState de missão concluída
EM_ANDAMENTO = 2  # CompletionState de missão ativa / em andamento
VAZIO = 0xFFFF

MAPAS = {
    0: 'Hirschfelden Hunting Reserve',
    1: 'Layton Lake District',
    2: 'Medved-Taiga National Park',
    3: 'Vurhonga Savanna',
    4: 'Parque Fernando',
    6: 'Yukon Valley',
    8: 'Cuatro Colinas Game Reserve',
    9: 'Silver Ridge Peaks',
    10: 'Te Awaroa National Park',
    11: 'Rancho del Arroyo',
    12: 'Mississippi Acres Preserve',
    13: 'Revontuli Coast',
    14: 'New England Mountains',
    15: 'Layton Lakes Trophy Lodge',
    16: 'Emerald Coast',
    17: 'Sundarpatan Nepal',
    18: 'Salzwiesen Park',
    19: 'Askiy Ridge',
    20: 'Tòrr nan Sithean',
    21: 'Intisuyu',
}

PROCESSOS_DO_JOGO = ('thehuntercotw_f.exe',)


class ErroSave(Exception):
    """Erro com mensagem já pronta para mostrar ao usuário."""


def nome_do_mapa(chave):
    if chave in MAPAS:
        return MAPAS[chave]
    return t('mapa_desconhecido', chave=chave)


# ---------------------------------------------------------------------------
# Leitura e escrita do formato
# ---------------------------------------------------------------------------

@dataclass
class InfoMapa:
    chave: int
    nome: str
    total: int
    concluidas: int
    em_andamento: int
    resetado: bool = False  # missões apagadas; o jogo recria ao entrar no mapa


class Tabela:
    """Tabela hash 'Campaigns' (chave int32 = id do mapa -> MissionSaveData)."""

    def __init__(self, raw):
        self.raw = raw
        try:
            self.idx_off = INST + struct.unpack_from('<I', raw, INST + 8)[0]
            self.chain_off = INST + struct.unpack_from('<I', raw, INST + 16)[0]
            self.F = INST + 24
            (self.length, self.first_free, self.pool,
             self.free_cnt, self.size) = struct.unpack_from('<5H', raw, self.F)
        except struct.error:
            raise ErroSave(t('erro_incompleto'))
        if self.length == 0 or self.pool == 0:
            raise ErroSave(t('erro_tabela', codigo='T1'))
        if (self.idx_off + self.length * 2 > len(raw)
                or self.chain_off + self.pool * ENTRY > len(raw)):
            raise ErroSave(t('erro_tabela', codigo='T2'))

    def key(self, c): return struct.unpack_from('<i', self.raw, self.chain_off + c * ENTRY)[0]
    def nxt(self, c): return struct.unpack_from('<H', self.raw, self.chain_off + c * ENTRY + 4)[0]
    def set_nxt(self, c, v): struct.pack_into('<H', self.raw, self.chain_off + c * ENTRY + 4, v)
    def bucket(self, k): return struct.unpack_from('<H', self.raw, self.idx_off + (k % self.length) * 2)[0]
    def set_bucket(self, k, v): struct.pack_into('<H', self.raw, self.idx_off + (k % self.length) * 2, v)
    def valor(self, c): return self.chain_off + c * ENTRY + 8

    def entradas(self):
        """Lista (chave, índice) de todas as entradas, conferindo a estrutura."""
        out, vistos = [], set()
        for b in range(self.length):
            c = struct.unpack_from('<H', self.raw, self.idx_off + b * 2)[0]
            while c != VAZIO:
                if c >= self.pool or c in vistos:
                    raise ErroSave(t('erro_tabela', codigo='T3'))
                vistos.add(c)
                k = self.key(c)
                if k % self.length != b:
                    raise ErroSave(t('erro_tabela', codigo='T4'))
                out.append((k, c))
                c = self.nxt(c)
        if len(out) != self.size:
            raise ErroSave(t('erro_tabela', codigo='T5'))
        return sorted(out)

    def remover(self, k):
        c = self.bucket(k)
        prev = None
        while c != VAZIO and self.key(c) != k:
            prev, c = c, self.nxt(c)
        if c == VAZIO:
            raise ErroSave(t('erro_mapa_ausente', mapa=nome_do_mapa(k)))
        nx = self.nxt(c)
        if prev is None:
            self.set_bucket(k, nx)
        else:
            self.set_nxt(prev, nx)
        self.set_nxt(c, self.first_free)  # entrada vai para a lista de livres
        self.first_free = c
        self.free_cnt += 1
        self.size -= 1
        struct.pack_into('<5H', self.raw, self.F, self.length, self.first_free,
                         self.pool, self.free_cnt, self.size)

    def posicoes_permitidas(self):
        """Bytes que uma remoção pode alterar (para conferir o resultado)."""
        pos = set(range(self.F, self.F + 10))
        pos.update(range(self.idx_off, self.idx_off + self.length * 2))
        for c in range(self.pool):
            o = self.chain_off + c * ENTRY + 4
            pos.update((o, o + 1))
        return pos


class Save:
    """Um missions_missiondata_adf aberto na memória."""

    def __init__(self, dados):
        self.dados = bytes(dados)
        d = self.dados
        if len(d) < 34 or d[:4] != b'SAVE' or d[16:20] != b'COMP':
            raise ErroSave(t('erro_nao_e_save'))
        try:
            self.raw = bytearray(zlib.decompress(d[32:]))
        except zlib.error:
            raise ErroSave(t('erro_descompactar'))
        t1 = struct.unpack_from('<Q', d, 8)[0]
        t2 = struct.unpack_from('<Q', d, 24)[0]
        if t1 != len(self.raw) or t2 != len(self.raw):
            raise ErroSave(t('erro_tamanho'))
        if self.raw[:5] != b'\x01\x01\x00\x00\x00' or self.raw[5:9] != b' FDA':
            raise ErroSave(t('erro_formato'))
        self.cabecalho = d[:32]
        self.tabela = Tabela(self.raw)
        self.chaves = [k for k, _ in self.tabela.entradas()]

    @classmethod
    def abrir(cls, caminho):
        with open(caminho, 'rb') as f:
            return cls(f.read())

    def mapas(self):
        out = []
        t = self.tabela
        for k, c in t.entradas():
            v = t.valor(c)
            ch_off = struct.unpack_from('<I', self.raw, v + 80)[0]
            n = struct.unpack_from('<Q', self.raw, v + 88)[0]
            concl = andam = 0
            if INST + ch_off + n * NODE <= len(self.raw):
                for i in range(n):
                    estado = self.raw[INST + ch_off + i * NODE + 9]
                    concl += estado == CONCLUIDA
                    andam += estado == EM_ANDAMENTO
            out.append(InfoMapa(k, nome_do_mapa(k), n, concl, andam))
        return out

    def sem_mapas(self, chaves):
        """Devolve (bytes_do_novo_arquivo, raw_esperado) sem os mapas pedidos."""
        raw = bytearray(self.raw)
        t = Tabela(raw)
        for k in chaves:
            t.remover(k)
        return montar_arquivo(self.cabecalho, raw), bytes(raw)


def montar_arquivo(cabecalho, raw):
    cab = bytearray(cabecalho)
    struct.pack_into('<Q', cab, 8, len(raw))
    struct.pack_into('<Q', cab, 24, len(raw))
    return bytes(cab) + zlib.compress(bytes(raw), 1)


def conferir_resultado(original, novo_bytes, raw_esperado, chaves_removidas):
    """Reabre o arquivo gerado e confere tudo. Levanta ErroSave se algo falhar."""
    novo = Save(novo_bytes)
    if bytes(novo.raw) != raw_esperado:
        raise ErroSave(t('erro_conferencia', codigo='C1'))
    esperadas = [k for k in original.chaves if k not in chaves_removidas]
    if novo.chaves != esperadas:
        raise ErroSave(t('erro_conferencia', codigo='C2'))
    if len(novo.raw) != len(original.raw):
        raise ErroSave(t('erro_conferencia', codigo='C3'))
    permitidas = original.tabela.posicoes_permitidas()
    for i, (a, b) in enumerate(zip(original.raw, novo.raw)):
        if a != b and i not in permitidas:
            raise ErroSave(t('erro_conferencia', codigo='C4'))
    if novo.cabecalho[:8] != original.cabecalho[:8] or novo.cabecalho[16:24] != original.cabecalho[16:24]:
        raise ErroSave(t('erro_conferencia', codigo='C5'))
    return novo


# ---------------------------------------------------------------------------
# Pastas: encontrar saves e backups
# ---------------------------------------------------------------------------

@dataclass
class PastaSave:
    pasta: str
    plataforma: str      # 'Steam', 'Epic' ou 'Desconhecida'
    steam_cloud: bool
    ultimo_jogo: datetime.datetime = None  # quando o jogo gravou algo nesse save pela última vez

    @property
    def arquivo(self):
        return os.path.join(self.pasta, NOME_ARQUIVO)

    @property
    def id(self):
        return os.path.basename(os.path.normpath(self.pasta))

    def quando_jogado(self):
        if self.ultimo_jogo is None:
            return t('data_desconhecida')
        return t('jogado_em', quando=idiomas.data_hora(self.ultimo_jogo))

    def descricao(self):
        return t('save_descricao', id=self.id, quando=self.quando_jogado(), pasta=self.pasta)

    def nome_curto(self):
        plat = self.plataforma if self.plataforma in ('Steam', 'Epic') else t('plat_outra')
        return t('save_nome_curto', plat=plat, id=self.id, quando=self.quando_jogado())


def _ultimo_jogo(pasta):
    """Data mais recente entre os arquivos do save (sem olhar dentro de 'slots').

    O arquivo de missões fica de fora, porque o próprio reset muda a data dele."""
    try:
        arquivos = [e for e in os.scandir(pasta) if e.is_file()]
        outros = [e for e in arquivos if not e.name.startswith(NOME_ARQUIVO)]
        datas = [e.stat().st_mtime for e in (outros or arquivos)]
        return datetime.datetime.fromtimestamp(max(datas)) if datas else None
    except OSError:
        return None


def _documentos_do_windows():
    """Pasta Documentos de verdade (respeita redirecionamento para o OneDrive)."""
    try:
        class GUID(ctypes.Structure):
            _fields_ = [('a', ctypes.c_uint32), ('b', ctypes.c_uint16),
                        ('c', ctypes.c_uint16), ('d', ctypes.c_ubyte * 8)]
        # FOLDERID_Documents {FDD39AD0-238F-46AF-ADB4-6C85480369C7}
        g = GUID(0xFDD39AD0, 0x238F, 0x46AF,
                 (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7))
        p = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(p)) == 0:
            valor = p.value
            ctypes.windll.ole32.CoTaskMemFree(p)
            return valor
    except Exception:
        pass
    return None


def pastas_documentos():
    candidatos = [_documentos_do_windows()]
    perfil = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    candidatos += [os.path.join(perfil, 'Documents'), os.path.join(perfil, 'Documentos')]
    for var in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        base = os.environ.get(var)
        if base:
            candidatos += [os.path.join(base, 'Documents'), os.path.join(base, 'Documentos')]
    vistos, out = set(), []
    for c in candidatos:
        if c and os.path.isdir(c):
            chave = os.path.normcase(os.path.realpath(c))
            if chave not in vistos:
                vistos.add(chave)
                out.append(c)
    return out


def descrever_pasta(pasta):
    pid = os.path.basename(os.path.normpath(pasta))
    caminho = pasta.lower()
    steam_cloud = os.path.exists(os.path.join(pasta, 'steam_autocloud.vdf'))
    if steam_cloud or (pid.isdigit() and pid.startswith('7656') and len(pid) == 17):
        plat = 'Steam'
    elif 'epic' in caminho or (len(pid) == 32 and all(ch in '0123456789abcdef' for ch in pid.lower())):
        plat = 'Epic'
    else:
        plat = 'Desconhecida'
    return PastaSave(pasta, plat, steam_cloud, _ultimo_jogo(pasta))


def encontrar_saves(documentos=None):
    """Procura missions_missiondata_adf dentro de Documentos\\Avalanche Studios.

    Ignora as pastas 'slots' (cópias de segurança feitas pelo próprio jogo).
    Devolve do save jogado mais recentemente para o mais antigo."""
    achados, vistos = [], set()
    for doc in (documentos if documentos is not None else pastas_documentos()):
        raiz = os.path.join(doc, 'Avalanche Studios')
        if not os.path.isdir(raiz):
            continue
        for pasta, subpastas, arquivos in os.walk(raiz):
            subpastas[:] = [s for s in subpastas if s.lower() != 'slots'
                            and not s.endswith(('.restaurando_tmp', '.anterior_tmp'))]
            if NOME_ARQUIVO in arquivos:
                chave = os.path.normcase(os.path.realpath(pasta))
                if chave not in vistos:
                    vistos.add(chave)
                    achados.append(descrever_pasta(pasta))
    antigo = datetime.datetime.min
    return sorted(achados, key=lambda s: s.ultimo_jogo or antigo, reverse=True)


# ---------------------------------------------------------------------------
# Pasta do programa (oculta) e backups
#
#   Documentos\.BKP_ResetMissions_Saves_COTW\   (oculta)
#     LEIA-ME.txt  (ou README.txt / LEEME.txt, no idioma de quem criou a pasta)
#     Steam - 76561190000000000\              (número da conta, só de exemplo)
#       Backups_MISSIONS\                      (até 50; o mais antigo é protegido)
#         2026-11-18 21-34-36 - Antes de resetar Intisuyu\
#           missions_missiondata_adf
#           info.json
#       Backups_SAVE\                          (até 5; o mais antigo é protegido)
#         COMO RESTAURAR MANUALMENTE.txt
#         2026-11-19 10-00-00 - Backup feito por você\
#           save\                              (cópia da pasta inteira do save)
#           info.json
#       mapas_resetados.json
# ---------------------------------------------------------------------------

NOMES_LEIA_ME = ('LEIA-ME.txt', 'README.txt', 'LEEME.txt')


def pasta_do_programa_padrao():
    docs = pastas_documentos()
    base = docs[0] if docs else os.path.expanduser('~')
    return os.path.join(base, PASTA_PROGRAMA)


def _ocultar(pasta):
    try:
        FILE_ATTRIBUTE_HIDDEN = 0x2
        atual = ctypes.windll.kernel32.GetFileAttributesW(pasta)
        if atual != -1 and atual != 0xFFFFFFFF and not atual & FILE_ATTRIBUTE_HIDDEN:
            ctypes.windll.kernel32.SetFileAttributesW(pasta, atual | FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass


def preparar_pasta_do_programa(raiz):
    """Cria a pasta (oculta) com o LEIA-ME. Levanta OSError se o Windows bloquear."""
    os.makedirs(raiz, exist_ok=True)
    _ocultar(raiz)
    if not any(os.path.exists(os.path.join(raiz, n)) for n in NOMES_LEIA_ME):
        with open(os.path.join(raiz, t('nome_leia_me')), 'w', encoding='utf-8') as f:
            f.write(t('leia_me_pasta'))


def testar_gravacao(raiz):
    """Testa se o programa consegue gravar na pasta Documentos.

    Devolve None se der certo, ou o erro (OSError) se o Windows bloquear."""
    teste = os.path.join(raiz, '.teste_de_gravacao')
    try:
        preparar_pasta_do_programa(raiz)
        with open(teste, 'wb') as f:
            f.write(b'ok')
        os.remove(teste)
        return None
    except OSError as e:
        return e


def pasta_do_save_no_programa(save, raiz):
    """Pasta deste save dentro da pasta do programa (ex.: 'Steam - 7656...')."""
    if os.path.isdir(raiz):
        for nome in os.listdir(raiz):
            if (nome == save.id or nome.endswith(' - ' + save.id)) and os.path.isdir(os.path.join(raiz, nome)):
                return os.path.join(raiz, nome)
    return os.path.join(raiz, f'{save.plataforma} - {save.id}')


def pasta_backups_do_save(save, raiz):
    """Backups do arquivo de missões."""
    return os.path.join(pasta_do_save_no_programa(save, raiz), BACKUPS_MISSOES)


_pasta_backups_do_save = pasta_backups_do_save


def pasta_backups_save_completo(save, raiz):
    """Backups da pasta inteira do save."""
    return os.path.join(pasta_do_save_no_programa(save, raiz), BACKUPS_SAVE)


def _limpar_backups(lista, limite, manter=()):
    """Apaga os backups mais antigos além do limite. O mais antigo de todos nunca é
    apagado (é o único com o estado de antes de tudo). 'manter': pastas que não podem sair."""
    if len(lista) <= limite:
        return []
    do_mais_antigo = sorted(lista, key=lambda b: b.quando)
    candidatos = [b for b in do_mais_antigo[1:] if b.pasta not in manter]
    apagados = []
    sobra = len(lista)
    while sobra > limite and candidatos:
        b = candidatos.pop(0)
        try:
            shutil.rmtree(b.pasta)
            apagados.append(b)
            sobra -= 1
        except OSError:
            pass  # se não der para apagar agora, tenta na próxima vez
    return apagados


def _nome_de_pasta_seguro(texto, limite=70):
    # O Windows não aceita pontos/espaços no fim do nome; por isso '…' e não '...'.
    texto = ''.join('-' if ch in '<>:"/\\|?*' else ch for ch in texto).strip(' .')
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip(' .,') + '…'


def titulo_do_backup(tipo, chaves=(), origem=None):
    """Motivo do backup, no idioma atual."""
    if tipo == 'reset':
        return t('titulo_reset', nomes=', '.join(nome_do_mapa(k) for k in chaves))
    if tipo == 'restauracao' and origem is not None:
        return t('titulo_restauracao', quando=idiomas.data_hora(origem))
    return t('titulo_backup')


@dataclass
class Backup:
    pasta: str
    quando: datetime.datetime
    titulo_salvo: str         # texto gravado no info.json (usado para backups antigos)
    mapas: list               # resumo dos mapas no momento do backup (pode estar vazio)
    tipo: str = None          # 'reset' ou 'restauracao' (backups da v1.4 em diante)
    chaves: tuple = field(default_factory=tuple)
    origem: datetime.datetime = None  # para 'restauracao': de quando era o backup restaurado
    protegido: bool = False           # o mais antigo: nunca é apagado pela limpeza automática

    @property
    def titulo(self):
        """Motivo no idioma atual (backups antigos mostram o texto que foi gravado)."""
        if self.tipo in ('reset', 'restauracao'):
            return titulo_do_backup(self.tipo, self.chaves, self.origem)
        return self.titulo_salvo

    @property
    def arquivo(self):
        return os.path.join(self.pasta, NOME_ARQUIVO)

    def descricao(self):
        return f'{idiomas.data_hora(self.quando, segundos=True)} - {self.titulo}'


def fazer_backup(save, raiz, tipo, chaves=(), origem=None, manter=()):
    preparar_pasta_do_programa(raiz)
    destino_base = _pasta_backups_do_save(save, raiz)
    agora = datetime.datetime.now()
    titulo = titulo_do_backup(tipo, chaves, origem)
    nome = _nome_de_pasta_seguro(f'{agora:%Y-%m-%d %H-%M-%S} - {titulo}')
    destino = os.path.join(destino_base, nome)
    n = 2
    while os.path.exists(destino):
        destino = os.path.join(destino_base, f'{nome} ({n})')
        n += 1
    os.makedirs(destino)
    with open(save.arquivo, 'rb') as f:
        original = f.read()
    shutil.copy2(save.arquivo, os.path.join(destino, NOME_ARQUIVO))
    with open(os.path.join(destino, NOME_ARQUIVO), 'rb') as f:
        if f.read() != original:
            raise ErroSave(t('erro_backup_diferente'))
    try:
        mapas = [vars(m) for m in Save(original).mapas()]
    except ErroSave:
        mapas = []
    info = {'criado_em': agora.isoformat(timespec='seconds'), 'titulo': titulo, 'tipo': tipo,
            'chaves': list(chaves), 'origem': origem.isoformat(timespec='seconds') if origem else None,
            'pasta_do_save': save.pasta, 'mapas': mapas}
    with open(os.path.join(destino, 'info.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    _limpar_backups(listar_backups(save, raiz), LIMITE_MISSOES, manter=manter)
    return Backup(destino, agora, titulo, mapas, tipo, tuple(chaves), origem)


def listar_backups(save, raiz):
    base = _pasta_backups_do_save(save, raiz)
    out = []
    if not os.path.isdir(base):
        return out
    for nome in os.listdir(base):
        pasta = os.path.join(base, nome)
        if not os.path.isfile(os.path.join(pasta, NOME_ARQUIVO)):
            continue
        quando, titulo, mapas, tipo, chaves, origem = None, t('titulo_backup'), [], None, (), None
        try:
            with open(os.path.join(pasta, 'info.json'), encoding='utf-8') as f:
                info = json.load(f)
            quando = datetime.datetime.fromisoformat(info['criado_em'])
            titulo = info.get('titulo') or info.get('motivo', titulo)
            titulo = titulo[:1].upper() + titulo[1:]
            mapas = info.get('mapas') or []
            tipo = info.get('tipo')
            chaves = tuple(int(k) for k in info.get('chaves') or ())
            if info.get('origem'):
                origem = datetime.datetime.fromisoformat(info['origem'])
            if tipo is None:
                tipo, chaves, origem = _entender_titulo_antigo(titulo)
        except Exception:
            pass
        if quando is None:
            quando = datetime.datetime.fromtimestamp(os.path.getmtime(pasta))
        out.append(Backup(pasta, quando, titulo, mapas, tipo, chaves, origem))
    out.sort(key=lambda b: b.quando, reverse=True)
    if out:
        out[-1].protegido = True
    return out


def _entender_titulo_antigo(titulo):
    """Backups das versões até a 1.3 só gravaram o texto em português. Tenta descobrir
    o tipo a partir dele, para que o motivo também apareça traduzido."""
    if titulo.startswith('Antes de resetar '):
        por_nome = {v: k for k, v in MAPAS.items()}
        nomes = titulo[len('Antes de resetar '):].split(', ')
        if all(n in por_nome for n in nomes):
            return 'reset', tuple(por_nome[n] for n in nomes), None
    if titulo.startswith('Antes de restaurar o backup de '):
        resto = titulo[len('Antes de restaurar o backup de '):]
        for formato in ('%d-%m-%Y %H-%M', '%d/%m/%Y %H:%M:%S'):
            try:
                return 'restauracao', (), datetime.datetime.strptime(resto, formato)
            except ValueError:
                pass
    return None, (), None


def mapas_do_backup(backup):
    """Lê o próprio arquivo do backup e devolve os mapas (InfoMapa)."""
    return Save.abrir(backup.arquivo).mapas()


def _modernizar_backup_antigo(pasta, nome):
    """Arruma o info.json de um backup da v1.0/1.1 e devolve o nome novo da pasta."""
    import re
    arq = os.path.join(pasta, 'info.json')
    try:
        with open(arq, encoding='utf-8') as f:
            info = json.load(f)
        if 'titulo' in info:
            return nome
        titulo = re.sub(r' \(provável, chave \d+\)', '', info.get('motivo', 'Backup'))
        titulo = titulo.replace('antes de resetar: ', 'antes de resetar ')
        titulo = titulo[:1].upper() + titulo[1:]
        quando = datetime.datetime.fromisoformat(info['criado_em'])
        info['titulo'] = titulo
        with open(arq, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        return _nome_de_pasta_seguro(f'{quando:%Y-%m-%d %H-%M-%S} - {titulo}')
    except Exception:
        return nome


def _mover_conteudo(origem, destino):
    """Move o que está em 'origem' para 'destino' (sem sobrescrever nada) e apaga 'origem' se esvaziar."""
    os.makedirs(destino, exist_ok=True)
    for item in os.listdir(origem):
        d = os.path.join(destino, item)
        if not os.path.exists(d):
            shutil.move(os.path.join(origem, item), d)
    if not os.listdir(origem):
        os.rmdir(origem)


def migrar_pasta_antiga(raiz, documentos=None):
    """Traz os backups das versões antigas para a pasta atual. Erros são ignorados
    (os backups antigos continuam onde estão e a migração tenta de novo na próxima vez).

    v1.0/1.1: Documentos\\COTW Reset Missoes - Backups\\<id>\\<backup>
    v1.2-1.5: Documentos\\COTW Reset Missoes\\<Plataforma - id>\\Backups\\<backup>
    atual:    Documentos\\.BKP_ResetMissions_Saves_COTW\\<Plataforma - id>\\Backups_MISSIONS\\<backup>"""
    for doc in (documentos if documentos is not None else pastas_documentos()):
        antiga = os.path.join(doc, PASTA_ANTIGA)
        if os.path.isdir(antiga):
            try:
                preparar_pasta_do_programa(raiz)
                for sid in os.listdir(antiga):
                    origem = os.path.join(antiga, sid)
                    if not os.path.isdir(origem):
                        continue
                    falso = descrever_pasta(os.path.join(doc, sid))  # só para nome/plataforma
                    destino_save = pasta_do_save_no_programa(falso, raiz)
                    destino_bk = os.path.join(destino_save, BACKUPS_MISSOES)
                    os.makedirs(destino_bk, exist_ok=True)
                    for item in os.listdir(origem):
                        o = os.path.join(origem, item)
                        if item == 'mapas_resetados.json':
                            d = os.path.join(destino_save, item)
                        else:
                            d = os.path.join(destino_bk, _modernizar_backup_antigo(o, item))
                        if not os.path.exists(d):
                            shutil.move(o, d)
                    if not os.listdir(origem):
                        os.rmdir(origem)
                if not os.listdir(antiga):
                    os.rmdir(antiga)
            except OSError:
                pass

        antiga2 = os.path.join(doc, PASTA_ANTIGA_2)
        if os.path.isdir(antiga2) and os.path.normcase(antiga2) != os.path.normcase(raiz):
            try:
                preparar_pasta_do_programa(raiz)
                for nome in os.listdir(antiga2):
                    o = os.path.join(antiga2, nome)
                    if nome in NOMES_LEIA_ME:
                        os.remove(o)  # a pasta nova já tem o seu
                        continue
                    if not os.path.isdir(o):
                        continue
                    destino_save = os.path.join(raiz, nome)
                    velhos = os.path.join(o, 'Backups')
                    if os.path.isdir(velhos):
                        _mover_conteudo(velhos, os.path.join(destino_save, BACKUPS_MISSOES))
                    _mover_conteudo(o, destino_save)
                if not os.listdir(antiga2):
                    os.rmdir(antiga2)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Backup do save completo (a pasta inteira do save, com os 'slots')
# ---------------------------------------------------------------------------

NOMES_INSTRUCOES = ('COMO RESTAURAR MANUALMENTE.txt', 'HOW TO RESTORE MANUALLY.txt',
                    'CÓMO RESTAURAR MANUALMENTE.txt')


def titulo_do_backup_save(tipo, origem=None):
    if tipo == 'antes_restaurar' and origem is not None:
        return t('titulo_save_antes_restaurar', quando=idiomas.data_hora(origem))
    return t('titulo_save_manual')


@dataclass
class BackupSave:
    pasta: str
    quando: datetime.datetime
    tipo: str = 'manual'              # 'manual' (botão) ou 'antes_restaurar'
    origem: datetime.datetime = None  # para 'antes_restaurar': de quando era o backup restaurado
    tamanho: int = 0                  # bytes
    arquivos: int = 0
    protegido: bool = False

    @property
    def titulo(self):
        return titulo_do_backup_save(self.tipo, self.origem)

    @property
    def pasta_arquivos(self):
        return os.path.join(self.pasta, PASTA_ARQUIVOS_SAVE)


def _arquivos_da_pasta(pasta):
    """{caminho relativo: caminho completo} de todos os arquivos (inclui subpastas como 'slots')."""
    out = {}
    for atual, _, arquivos in os.walk(pasta):
        for a in arquivos:
            if a.endswith('.tmp_reset_missoes'):
                continue
            completo = os.path.join(atual, a)
            out[os.path.relpath(completo, pasta)] = completo
    return out


def _conferir_copia(origem, destino):
    """Confere, arquivo por arquivo e byte a byte, que 'destino' é igual a 'origem'."""
    a, b = _arquivos_da_pasta(origem), _arquivos_da_pasta(destino)
    if set(a) != set(b):
        raise ErroSave(t('erro_copia_save'))
    for rel, caminho in a.items():
        with open(caminho, 'rb') as f1, open(b[rel], 'rb') as f2:
            if f1.read() != f2.read():
                raise ErroSave(t('erro_copia_save'))


def _copiar_pasta(origem, destino):
    shutil.copytree(origem, destino, ignore=shutil.ignore_patterns('*.tmp_reset_missoes'))
    _conferir_copia(origem, destino)


def _escrever_instrucoes(base, save):
    if not any(os.path.exists(os.path.join(base, n)) for n in NOMES_INSTRUCOES):
        with open(os.path.join(base, t('nome_instrucoes_save')), 'w', encoding='utf-8') as f:
            f.write(t('instrucoes_save', pasta_jogo=save.pasta, subpasta=PASTA_ARQUIVOS_SAVE))


def fazer_backup_save_completo(save, raiz, tipo='manual', origem=None, manter=()):
    """Copia a pasta inteira do save (com os 'slots') para Backups_SAVE e confere a cópia."""
    if jogo_aberto():
        raise ErroSave(t('erro_jogo_aberto'))
    preparar_pasta_do_programa(raiz)
    base = pasta_backups_save_completo(save, raiz)
    os.makedirs(base, exist_ok=True)
    _escrever_instrucoes(base, save)
    agora = datetime.datetime.now()
    nome = _nome_de_pasta_seguro(f'{agora:%Y-%m-%d %H-%M-%S} - {titulo_do_backup_save(tipo, origem)}')
    destino = os.path.join(base, nome)
    n = 2
    while os.path.exists(destino):
        destino = os.path.join(base, f'{nome} ({n})')
        n += 1
    os.makedirs(destino)
    try:
        _copiar_pasta(save.pasta, os.path.join(destino, PASTA_ARQUIVOS_SAVE))
    except Exception:
        shutil.rmtree(destino, ignore_errors=True)  # não deixa backup pela metade
        raise
    arquivos = _arquivos_da_pasta(os.path.join(destino, PASTA_ARQUIVOS_SAVE))
    tamanho = sum(os.path.getsize(c) for c in arquivos.values())
    info = {'criado_em': agora.isoformat(timespec='seconds'), 'tipo': tipo,
            'origem': origem.isoformat(timespec='seconds') if origem else None,
            'pasta_do_save': save.pasta, 'tamanho': tamanho, 'arquivos': len(arquivos)}
    with open(os.path.join(destino, 'info.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    _limpar_backups(listar_backups_save(save, raiz), LIMITE_SAVE, manter=manter)
    return BackupSave(destino, agora, tipo, origem, tamanho, len(arquivos))


def listar_backups_save(save, raiz):
    base = pasta_backups_save_completo(save, raiz)
    out = []
    if not os.path.isdir(base):
        return out
    for nome in os.listdir(base):
        pasta = os.path.join(base, nome)
        if not os.path.isdir(os.path.join(pasta, PASTA_ARQUIVOS_SAVE)):
            continue
        b = BackupSave(pasta, None)
        try:
            with open(os.path.join(pasta, 'info.json'), encoding='utf-8') as f:
                info = json.load(f)
            b.quando = datetime.datetime.fromisoformat(info['criado_em'])
            b.tipo = info.get('tipo') or 'manual'
            if info.get('origem'):
                b.origem = datetime.datetime.fromisoformat(info['origem'])
            b.tamanho = int(info.get('tamanho') or 0)
            b.arquivos = int(info.get('arquivos') or 0)
        except Exception:
            pass
        if b.quando is None:
            b.quando = datetime.datetime.fromtimestamp(os.path.getmtime(pasta))
        out.append(b)
    out.sort(key=lambda x: x.quando, reverse=True)
    if out:
        out[-1].protegido = True
    return out


def tem_backup_save(save, raiz):
    return bool(listar_backups_save(save, raiz))


def restaurar_save_completo(save, backup, raiz):
    """Devolve a pasta inteira do save a partir de um backup completo.

    Antes, guarda o save atual num backup completo novo. A troca é feita assim:
    1) copia o backup para uma pasta temporária ao lado do save e confere;
    2) renomeia o save atual para '.anterior_tmp' e a cópia para o nome do save;
    3) confere de novo e só então apaga o '.anterior_tmp'. Se algo falhar, volta como estava."""
    if jogo_aberto():
        raise ErroSave(t('erro_jogo_aberto'))
    if not os.path.isdir(backup.pasta_arquivos):
        raise ErroSave(t('erro_backup_save_invalido'))
    arquivo_missoes = os.path.join(backup.pasta_arquivos, NOME_ARQUIVO)
    if os.path.isfile(arquivo_missoes):
        Save.abrir(arquivo_missoes)  # garante que o arquivo de missões do backup é válido
    antes = fazer_backup_save_completo(save, raiz, 'antes_restaurar', origem=backup.quando,
                                       manter=(backup.pasta,))
    alvo = os.path.normpath(save.pasta)
    novo = alvo + '.restaurando_tmp'
    anterior = alvo + '.anterior_tmp'
    for sobra in (novo, anterior):
        if os.path.exists(sobra):
            shutil.rmtree(sobra)
    _copiar_pasta(backup.pasta_arquivos, novo)
    try:
        os.rename(alvo, anterior)
    except OSError as e:
        shutil.rmtree(novo, ignore_errors=True)
        raise ErroSave(t('erro_pasta_em_uso', erro=e))
    try:
        os.rename(novo, alvo)
        _conferir_copia(backup.pasta_arquivos, alvo)
    except Exception as e:
        # desfaz: volta a pasta original para o lugar
        if os.path.exists(alvo):
            shutil.rmtree(alvo, ignore_errors=True)
        os.rename(anterior, alvo)
        shutil.rmtree(novo, ignore_errors=True)
        if isinstance(e, ErroSave):
            raise
        raise ErroSave(t('erro_pasta_em_uso', erro=e))
    shutil.rmtree(anterior, ignore_errors=True)
    return antes


def _gravar_com_seguranca(destino, conteudo, conferir):
    """Grava num temporário, confere, e só então troca pelo arquivo real."""
    tmp = destino + '.tmp_reset_missoes'
    try:
        with open(tmp, 'wb') as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
        with open(tmp, 'rb') as f:
            if f.read() != conteudo:
                raise ErroSave(t('erro_conferencia', codigo='G1'))
        conferir(conteudo)
        os.replace(tmp, destino)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    with open(destino, 'rb') as f:
        if f.read() != conteudo:
            raise ErroSave(t('erro_pos_gravacao'))


def resetar_mapas(save, chaves, raiz_backups):
    """Faz backup, gera o novo arquivo, confere e substitui. Devolve o Backup."""
    if jogo_aberto():
        raise ErroSave(t('erro_jogo_aberto'))
    original = Save.abrir(save.arquivo)
    for k in chaves:
        if k not in original.chaves:
            raise ErroSave(t('erro_mapa_ausente', mapa=nome_do_mapa(k)))
    novo_bytes, raw_esperado = original.sem_mapas(chaves)
    conferir_resultado(original, novo_bytes, raw_esperado, chaves)
    backup = fazer_backup(save, raiz_backups, 'reset', chaves=chaves)
    _gravar_com_seguranca(save.arquivo, novo_bytes,
                          lambda c: conferir_resultado(original, c, raw_esperado, chaves))
    totais = {m.chave: m.total for m in original.mapas()}
    try:
        reg = _ler_registro(save, raiz_backups)
        for k in chaves:
            reg[str(k)] = {'total': totais[k], 'quando': datetime.datetime.now().isoformat(timespec='seconds')}
        _gravar_registro(save, raiz_backups, reg)
    except (OSError, ValueError):
        pass  # a anotação é só para a lista; o reset já deu certo
    return backup


# ---------------------------------------------------------------------------
# Anotação dos mapas resetados
#
# Depois do reset, o mapa some de dentro do save até o jogador entrar nele de
# novo. Para continuar mostrando o mapa na lista ("Missões resetadas"), o
# programa anota os mapas resetados num arquivo junto dos backups.
# ---------------------------------------------------------------------------

def _arquivo_registro(save, raiz_backups):
    return os.path.join(pasta_do_save_no_programa(save, raiz_backups), 'mapas_resetados.json')


def _ler_registro(save, raiz_backups):
    try:
        with open(_arquivo_registro(save, raiz_backups), encoding='utf-8') as f:
            reg = json.load(f)
        return reg if isinstance(reg, dict) else {}
    except (OSError, ValueError):
        return {}


def _gravar_registro(save, raiz_backups, reg):
    caminho = _arquivo_registro(save, raiz_backups)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)


def mapas_para_mostrar(save, raiz_backups):
    """Mapas do save + mapas resetados (que sumiram do save até o jogador voltar)."""
    dados = Save.abrir(save.arquivo)
    mapas = dados.mapas()
    reg = _ler_registro(save, raiz_backups)
    presentes = set(dados.chaves)
    limpo = {}
    for chave_txt, info in reg.items():
        try:
            k = int(chave_txt)
            total = int(info.get('total', 0))
        except (ValueError, AttributeError, TypeError):
            continue
        if k in presentes:
            continue  # o jogador já entrou no mapa (ou restaurou um backup)
        limpo[chave_txt] = info
        mapas.append(InfoMapa(k, nome_do_mapa(k), total, 0, 0, resetado=True))
    if limpo != reg:
        try:
            _gravar_registro(save, raiz_backups, limpo)
        except OSError:
            pass
    return sorted(mapas, key=lambda m: m.chave)


def restaurar_backup(save, backup, raiz_backups):
    """Devolve o arquivo do backup. Antes, guarda o arquivo atual num backup novo."""
    if jogo_aberto():
        raise ErroSave(t('erro_jogo_aberto'))
    with open(backup.arquivo, 'rb') as f:
        conteudo = f.read()
    Save(conteudo)  # garante que o backup é um save válido
    novo_backup = None
    if os.path.exists(save.arquivo):
        novo_backup = fazer_backup(save, raiz_backups, 'restauracao', origem=backup.quando,
                                   manter=(backup.pasta,))

    def conferir(c):
        if c != conteudo:
            raise ErroSave(t('erro_conferencia', codigo='R1'))
        Save(c)
    _gravar_com_seguranca(save.arquivo, conteudo, conferir)
    return novo_backup


def mensagem_acesso_controlado(exe):
    """Passo a passo para liberar o programa, no idioma atual."""
    return t('msg_acesso_controlado', exe=exe)


def acesso_controlado_ligado():
    """Lê no registro se o Acesso Controlado a Pastas está ligado.

    Devolve True, False, ou None se não der para saber."""
    try:
        import winreg
        chave = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r'SOFTWARE\Microsoft\Windows Defender\Windows Defender Exploit Guard\Controlled Folder Access')
        with chave:
            valor, _ = winreg.QueryValueEx(chave, 'EnableControlledFolderAccess')
        return valor in (1, 3, 4)  # 1 = bloquear; 3/4 = bloquear modificação de disco; 0/2 = desligado/só auditar
    except OSError:
        return None


def parece_bloqueio_do_windows(erro):
    """O Acesso Controlado a Pastas aparece como 'arquivo/caminho não encontrado'
    ou 'acesso negado' ao gravar dentro de uma pasta protegida. Dependendo da
    função que falhou, o código vem em 'winerror' (pastas) ou só em 'errno'
    (arquivos abertos com open())."""
    if not isinstance(erro, OSError):
        return False
    if getattr(erro, 'winerror', None) in (2, 3, 5):
        return True
    if getattr(erro, 'winerror', None) is None and erro.errno in (errno.ENOENT, errno.EACCES):
        return True
    return acesso_controlado_ligado() is True


def texto_do_erro(erro, exe):
    if isinstance(erro, ErroSave):
        return str(erro)
    if parece_bloqueio_do_windows(erro):
        return (mensagem_acesso_controlado(exe) + '\n\n' + t('nada_alterado')
                + '\n\n(' + t('detalhe_tecnico', erro=erro) + ')')
    return t('erro_ao_gravar', erro=erro)


# ---------------------------------------------------------------------------
# Jogo aberto?
# ---------------------------------------------------------------------------

def jogo_aberto():
    try:
        saida = subprocess.run(
            ['tasklist', '/fo', 'csv', '/nh'], capture_output=True, text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=15,
        ).stdout
    except Exception:
        return False
    for linha in saida.splitlines():
        nome = linha.split(',')[0].strip('"').lower()
        if nome in PROCESSOS_DO_JOGO or nome.startswith('thehuntercotw'):
            return True
    return False
