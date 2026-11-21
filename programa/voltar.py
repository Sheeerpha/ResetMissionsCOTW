"""'Voltar missões da história' de um mapa (validado no jogo em 20/11/2026, Rancho del Arroyo e Revontuli).

A missão escolhida e todas as que dependem dela (inclusive secundárias e gatilhos invisíveis)
voltam ao estado do modelo zerado: os estados de cada registro são copiados do modelo e as
tabelas de anotações (ValueOccurrences) são esvaziadas no lugar. O tamanho do arquivo não muda
e nenhuma outra missão ou mapa é tocado. O próprio jogo inicia a missão de onde se recomeça.

Segurança: só volta missões cujo modelo tem exatamente os mesmos registros (Ids, na mesma
ordem) que o save; se uma atualização do jogo mudou a missão, ela é recusada.
"""
import datetime
import struct
from dataclasses import dataclass, field

import cotw_core as core
import dados_missoes
import registro
from idiomas import t

VO = 16            # tabela ValueOccurrences dentro do MissionSaveData_1
CHAIN_VO = 200     # tamanho de cada entrada da tabela de anotações

_dados = None


def dados():
    global _dados
    if _dados is None:
        _dados = dados_missoes.carregar()
    return _dados


def mapa_suportado(chave):
    return str(chave) in dados()


# ---------------------------------------------------------------- leitura
def _u(fmt, raw, p):
    return struct.unpack_from('<' + fmt, raw, p)


def _filhos(raw, p):
    fo, n = _u('I', raw, p + 80)[0], _u('Q', raw, p + 88)[0]
    if core.INST + fo + n * core.NODE > len(raw):
        raise core.ErroSave(t('erro_tabela', codigo='V1'))
    return [core.INST + fo + core.NODE * k for k in range(n)]


def raiz_do_mapa(save_obj, chave):
    tab = save_obj.tabela
    for k, c in tab.entradas():
        if k == chave:
            return tab.valor(c)
    return None


def missoes_no_save(save_obj, chave):
    """{id: posição do registro da missão} na ordem do save."""
    p = raiz_do_mapa(save_obj, chave)
    if p is None:
        return {}
    return {_u('i', save_obj.raw, f)[0]: f for f in _filhos(save_obj.raw, p)}


def arvore(raw, p):
    """Registros da missão em pré-ordem: [(posição, id, n_filhos), ...]."""
    out = []

    def andar(q):
        fs = _filhos(raw, q)
        out.append((q, _u('i', raw, q)[0], len(fs)))
        for f in fs:
            andar(f)
    andar(p)
    return out


# ---------------------------------------------------------------- plano
@dataclass
class Missao:
    id: int
    tipo: str            # 'M' história, 'S' secundária
    visivel: bool
    deps: list
    nome_hash: int
    estado: int = 0      # CompletionState no save (0, 2, 4...)


@dataclass
class Plano:
    chave: int
    historia: list                    # missões da história (visíveis), na ordem do jogo
    indice_atual: int                 # posição da missão atual na história (== len se concluída)
    candidatas: list = field(default_factory=list)  # posições que podem ser alvo (da mais recente para trás)
    missoes: dict = field(default_factory=dict)     # id -> Missao (todas do mapa presentes no save)
    dependentes: dict = field(default_factory=dict)

    @property
    def concluida(self):
        return self.indice_atual >= len(self.historia)

    @property
    def maximo(self):
        return len(self.candidatas)

    @property
    def minimo(self):
        """0 quando dá para recomeçar só a missão atual (em andamento) do começo; senão 1."""
        return 0 if self.atual is not None and self.atual.estado == core.EM_ANDAMENTO else 1

    @property
    def atual(self):
        return None if self.concluida else self.historia[self.indice_atual]

    def alvo(self, n):
        """Missão da história de onde se recomeça ao voltar n (0 = a própria missão atual, do começo)."""
        if n == 0:
            return self.atual if self.minimo == 0 else None
        return self.historia[self.candidatas[n - 1]] if 1 <= n <= self.maximo else None

    def conjunto(self, n):
        """Ids que voltam ao modelo ao voltar n (o alvo e tudo que depende dele)."""
        alvo = self.alvo(n)
        if alvo is None:
            return []
        out, pilha = set(), [alvo.id]
        while pilha:
            i = pilha.pop()
            if i in out:
                continue
            out.add(i)
            pilha.extend(self.dependentes.get(i, ()))
        return [i for i in self.missoes if i in out]

    def historia_que_volta(self, n):
        ids = set(self.conjunto(n))
        return [m for m in self.historia if m.id in ids and m.estado in (core.EM_ANDAMENTO, core.CONCLUIDA)]

    def secundarias_que_voltam(self, n):
        """Secundárias com progresso que voltam junto (visíveis)."""
        return [self.missoes[i] for i in self.conjunto(n)
                if self.missoes[i].tipo == 'S' and self.missoes[i].visivel
                and self.missoes[i].estado in (core.EM_ANDAMENTO, core.CONCLUIDA)]

    def posicao(self, missao):
        return self.historia.index(missao) + 1


def planejar(save_obj, chave):
    """Plano de 'voltar missões' para um mapa, ou None se o mapa não tem dados (ou não está no save)."""
    d = dados().get(str(chave))
    presentes = missoes_no_save(save_obj, chave)
    if d is None or not presentes:
        return None
    raw = save_obj.raw
    missoes = {}
    for mid, tipo, vis, deps, h in d['missoes']:
        if mid in presentes:
            missoes[mid] = Missao(mid, tipo, bool(vis), deps, h, raw[presentes[mid] + 9])
    # mantém a ordem do jogo
    dependentes = {}
    for m in missoes.values():
        for dp in m.deps:
            dependentes.setdefault(dp, set()).add(m.id)
    historia = [m for m in missoes.values() if m.tipo == 'M' and m.visivel]
    if not historia:
        return None
    andamento = [i for i, m in enumerate(historia) if m.estado == core.EM_ANDAMENTO]
    if andamento:
        atual = andamento[-1]
    else:
        nao_feitas = [i for i, m in enumerate(historia) if m.estado != core.CONCLUIDA]
        atual = nao_feitas[0] if nao_feitas else len(historia)
    feitas = [i for i in range(atual - 1, -1, -1) if historia[i].estado in (core.CONCLUIDA, core.EM_ANDAMENTO)]
    candidatas = feitas
    if atual < len(historia):
        # mapas com várias histórias paralelas: volta pelas missões das quais a atual depende
        anteriores, pilha = set(), list(historia[atual].deps)
        while pilha:
            i = pilha.pop()
            if i in anteriores or i not in missoes:
                continue
            anteriores.add(i)
            pilha.extend(missoes[i].deps)
        ligadas = [i for i in feitas if historia[i].id in anteriores]
        if ligadas:
            candidatas = ligadas
    return Plano(chave, historia, atual, candidatas, missoes, dependentes)


def problemas(save_obj, plano, n):
    """Lista de (id, motivo) que impedem voltar n. motivo: 'sem_modelo' ou 'mudou'."""
    d = dados()[str(plano.chave)]
    presentes = missoes_no_save(save_obj, plano.chave)
    out = []
    for mid in plano.conjunto(n):
        modelo = d['modelos'].get(str(mid))
        if modelo is None:
            out.append((mid, 'sem_modelo'))
            continue
        arv = arvore(save_obj.raw, presentes[mid])
        ids_save = [(i, nf) for _, i, nf in arv]
        ids_modelo = [(modelo[k], modelo[k + 4]) for k in range(0, len(modelo), 5)]
        if ids_save != ids_modelo:
            out.append((mid, 'mudou'))
    return out


def maximo_seguro(save_obj, plano):
    """Maior n (a partir de 1, sem pular) que pode ser voltado com segurança."""
    n = 0
    while n < plano.maximo and not problemas(save_obj, plano, n + 1):
        n += 1
    return n


def minimo_seguro(save_obj, plano):
    """0 se dá para recomeçar só a missão atual com segurança; senão 1."""
    return 0 if plano.minimo == 0 and not problemas(save_obj, plano, 0) else 1


# ---------------------------------------------------------------- escrita
def _esvaziar_vo(raw, no):
    """Tabela de anotações do registro: sem entradas, toda a memória vira lista de livres."""
    tab = no + VO
    hl, ffc, pool, livres, tam = _u('5H', raw, tab + 16)
    if tam == 0:
        return 0
    buckets, chains = core.INST + _u('I', raw, tab)[0], core.INST + _u('I', raw, tab + 8)[0]
    if buckets + 2 * hl > len(raw) or chains + CHAIN_VO * pool > len(raw):
        raise core.ErroSave(t('erro_tabela', codigo='V2'))
    for b in range(hl):
        struct.pack_into('<H', raw, buckets + 2 * b, core.VAZIO)
    for i in range(pool):
        struct.pack_into('<H', raw, chains + CHAIN_VO * i + 4, i + 1 if i + 1 < pool else core.VAZIO)
    struct.pack_into('<HHH', raw, tab + 18, 0, pool, pool)   # FirstFreeChain, ChainPoolSize, ChainPoolFreeCount
    struct.pack_into('<H', raw, tab + 24, 0)                  # Size
    return tam


def montar(save_obj, plano, n):
    """Devolve (bytes do novo arquivo, raw esperado, ids voltados)."""
    erros = problemas(save_obj, plano, n)
    if erros:
        raise core.ErroSave(t('erro_voltar_mudou'))
    d = dados()[str(plano.chave)]
    raw = bytearray(save_obj.raw)
    presentes = missoes_no_save(save_obj, plano.chave)
    ids = plano.conjunto(n)
    for mid in ids:
        modelo = d['modelos'][str(mid)]
        for k, (q, _i, _nf) in enumerate(arvore(raw, presentes[mid])):
            done, track, comp = modelo[5 * k + 1:5 * k + 4]
            struct.pack_into('<iBB', raw, q + 4, done, track, comp)
            _esvaziar_vo(raw, q)
    return core.montar_arquivo(save_obj.cabecalho, raw), bytes(raw), ids


def conferir(original, novo_bytes, raw_esperado):
    novo = core.Save(novo_bytes)
    if bytes(novo.raw) != raw_esperado:
        raise core.ErroSave(t('erro_conferencia', codigo='V3'))
    if len(novo.raw) != len(original.raw) or novo.chaves != original.chaves:
        raise core.ErroSave(t('erro_conferencia', codigo='V4'))
    return novo


def voltar_missoes(save, chave, n, raiz_backups):
    """Faz backup das missões, volta n missões da história do mapa, confere e grava. Devolve o Backup."""
    if core.jogo_aberto():
        raise core.ErroSave(t('erro_jogo_aberto'))
    original = core.Save.abrir(save.arquivo)
    plano = planejar(original, chave)
    if plano is None or plano.alvo(n) is None:
        raise core.ErroSave(t('erro_voltar_invalido'))
    novo_bytes, raw_esperado, ids = montar(original, plano, n)
    conferir(original, novo_bytes, raw_esperado)
    backup = core.fazer_backup(save, raiz_backups, 'voltar', chaves=(chave,), n=n)
    core._gravar_com_seguranca(save.arquivo, novo_bytes, lambda c: conferir(original, c, raw_esperado))
    registro.log(f'Voltar missões: {core.nome_do_mapa(chave)}, {n} da história, {len(ids)} missões ao modelo '
                 f'({datetime.datetime.now():%H:%M:%S}).')
    return backup
