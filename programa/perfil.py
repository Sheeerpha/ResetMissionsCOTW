"""Nível, XP e dinheiro do personagem (só leitura), do arquivo thp_player_profile_adf do save.

O arquivo tem o mesmo cabeçalho SAVE/COMP + zlib + 5 bytes do arquivo de missões, seguido de um
ADF (formato da Avalanche). Os valores são lidos pelos NOMES dos membros (Level, Xp, Cash) do tipo
PlayerProfileData_*, nunca por posição fixa, para continuar funcionando se o jogo mudar o tipo.
"""
import os
import struct
import zlib

ARQUIVO = 'thp_player_profile_adf'
PRIMITIVOS = {0x0ca2821d: 'B', 0x580d0a62: 'b', 0x86d152bd: 'H', 0xd13fcf93: 'h', 0x075e4e4f: 'I',
              0x192fe633: 'i', 0xa139e01f: 'Q', 0xaf41354f: 'q', 0x7515a207: 'f', 0xc609f663: 'd'}


def _adf(dados):
    if dados[:4] == b'SAVE':
        dados = zlib.decompress(dados[32:])[5:]
    if dados[:4] != b' FDA':
        raise ValueError('não é ADF')
    return dados


def ler_adf(dados):
    """Devolve (adf, tipos, instancias). tipos[hash] = {'nome', 'membros': [(nome, hash_tipo, offset)]}."""
    adf = _adf(dados)
    _mg, _ver, ic, io, tc, to, _sc, _so, nc, no, _total = struct.unpack_from('<4s10I', adf, 0)
    nomes, p = [], no + nc
    for n in adf[no:no + nc]:
        nomes.append(adf[p:p + n].decode('latin1'))
        p += n + 1
    tipos, p = {}, to
    for _ in range(tc):
        meta, _size, _al, th, ni, _fl, _esc, _eth, _el, mc = struct.unpack_from('<4IQHHIII', adf, p)
        p += 40
        membros = []
        if meta == 1:
            for _ in range(mc):
                mn, mth, _mal, moff, _dt, _dv = struct.unpack_from('<QIIIIQ', adf, p)
                p += 32
                membros.append((nomes[mn], mth, moff & 0xFFFFFF))
        elif meta == 8:
            p += 12 * mc
        tipos[th] = {'nome': nomes[ni], 'membros': membros}
    inst = []
    for i in range(ic):
        _nh, th, off, size, ni = struct.unpack_from('<IIIIQ', adf, io + 24 * i)
        inst.append((nomes[ni], th, off, size))
    return adf, tipos, inst


def ler(pasta_do_save):
    """{'nivel', 'xp', 'dinheiro'} ou None se não der para ler (arquivo ausente, formato diferente...)."""
    try:
        with open(os.path.join(pasta_do_save, ARQUIVO), 'rb') as f:
            adf, tipos, inst = ler_adf(f.read())
        for _nome, th, off, _size in inst:
            tipo = tipos.get(th)
            if not tipo or not tipo['nome'].startswith('PlayerProfileData'):
                continue
            valores = {}
            for nome, mth, moff in tipo['membros']:
                if nome in ('Level', 'Xp', 'Cash') and mth in PRIMITIVOS:
                    valores[nome] = struct.unpack_from('<' + PRIMITIVOS[mth], adf, off + moff)[0]
            if len(valores) == 3:
                return {'nivel': valores['Level'], 'xp': valores['Xp'], 'dinheiro': valores['Cash']}
    except (OSError, ValueError, struct.error, zlib.error, IndexError, KeyError):
        pass
    return None
