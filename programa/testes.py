"""Testes do núcleo. Usam SÓ cópias das amostras, em pastas temporárias.

Rodar: python testes.py
"""
import hashlib
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import cotw_core as core
import idiomas

# Os testes rodam em português e não mexem na preferência de idioma real.
idiomas.definir('pt')
idiomas.ARQUIVO_PREF = os.path.join(tempfile.mkdtemp(), 'config.json')
# Nos testes da janela, o aviso e a introdução não aparecem sozinhos (há um teste próprio para eles)
idiomas.salvar_config(aviso_visto=True, intro_vista=True)
import cotw_app as _app
_app.App.mostrar_aviso_ao_abrir = False
# A sugestão de backup completo antes do reset responde "Não" (continuar), salvo nos testes dela
import tkinter.messagebox as _mb
_mb.askyesnocancel = lambda *a, **k: False

AMOSTRAS = os.path.join(AQUI, '..', 'amostras')
COMPLETO = os.path.join(AMOSTRAS, 'missions_missiondata_adf__save_completo')
ZERADO = os.path.join(AMOSTRAS, 'missions_missiondata_adf__save_zerado')
FUNCIONOU = os.path.join(AMOSTRAS, 'missions_missiondata_adf__teste_sem_chave10_FUNCIONOU')

# Progresso por mapa (concluídas, em andamento, total), igual ao do save de exemplo.
MAPAS_EXEMPLO = {
    0: (21, 12, 124), 1: (6, 15, 123), 2: (17, 6, 92), 3: (53, 5, 76), 4: (56, 2, 62), 6: (22, 10, 52),
    8: (12, 6, 76), 9: (12, 1, 16), 10: (16, 2, 23), 11: (12, 1, 14), 12: (8, 3, 16), 13: (16, 2, 18),
    14: (21, 0, 39), 16: (34, 6, 40), 17: (18, 11, 34), 18: (6, 3, 9), 19: (13, 7, 20), 20: (14, 12, 33),
    21: (11, 12, 94),
}


def gerar_save_sintetico(mapas):
    """Monta um missions_missiondata_adf falso, no mesmo formato do jogo, com o progresso pedido.

    Serve para os testes rodarem onde os saves de exemplo não existem (como no GitHub):
    os saves de exemplo são saves reais e nunca são publicados."""
    import struct
    import zlib
    inst, entry, node = core.INST, core.ENTRY, core.NODE
    chaves = list(mapas)
    n = tamanho_tabela = len(chaves)
    off_buckets = 64
    off_entradas = off_buckets + ((tamanho_tabela * 2 + 7) // 8) * 8
    off_filhos = off_entradas + n * entry
    raw = bytearray(inst + off_filhos + sum(m[2] for m in mapas.values()) * node)
    raw[0:5] = b'\x01\x01\x00\x00\x00'
    raw[5:9] = b' FDA'
    struct.pack_into('<I', raw, inst + 8, off_buckets)
    struct.pack_into('<I', raw, inst + 16, off_entradas)
    buckets, ultimo, pos = [0xFFFF] * tamanho_tabela, {}, off_filhos
    for i, k in enumerate(chaves):
        e = inst + off_entradas + i * entry
        struct.pack_into('<iH', raw, e, k, 0xFFFF)
        v = e + 8
        struct.pack_into('<ii', raw, v, -1, 0)
        raw[v + 9] = 2
        concl, andam, total = mapas[k]
        struct.pack_into('<I', raw, v + 80, pos)
        struct.pack_into('<Q', raw, v + 88, total)
        for j in range(total):
            no = inst + pos + j * node
            struct.pack_into('<i', raw, no, 1000 + j)
            raw[no + 9] = core.CONCLUIDA if j < concl else (core.EM_ANDAMENTO if j < concl + andam else 0)
        pos += total * node
        b = k % tamanho_tabela                     # mesma regra de "bucket" do jogo
        if buckets[b] == 0xFFFF:
            buckets[b] = i
        else:                                      # colisão: entra no fim da cadeia
            struct.pack_into('<H', raw, inst + off_entradas + ultimo[b] * entry + 4, i)
        ultimo[b] = i
    for b, valor in enumerate(buckets):
        struct.pack_into('<H', raw, inst + off_buckets + b * 2, valor)
    struct.pack_into('<5H', raw, inst + 24, tamanho_tabela, 0xFFFF, n, 0, n)
    cab = (b'SAVE' + struct.pack('<I', 0x00335D13) + struct.pack('<Q', len(raw))
           + b'COMP' + b'\x01\x01\x00\x00' + struct.pack('<Q', len(raw)))
    return cab + zlib.compress(bytes(raw), 1)


# Sem os saves de exemplo (ou com COTW_TESTES_SINTETICOS=1), usa saves sintéticos.
SINTETICO = os.environ.get('COTW_TESTES_SINTETICOS') == '1' or not os.path.isfile(COMPLETO)
if SINTETICO:
    _pasta_sint = tempfile.mkdtemp()
    COMPLETO = os.path.join(_pasta_sint, 'sintetico_completo')
    ZERADO = os.path.join(_pasta_sint, 'sintetico_zerado')
    open(COMPLETO, 'wb').write(gerar_save_sintetico(MAPAS_EXEMPLO))
    open(ZERADO, 'wb').write(gerar_save_sintetico({10: (1, 1, 23)}))
    FUNCIONOU = None   # o arquivo validado no jogo só existe nos saves de exemplo
    print('(usando saves sintéticos: os saves de exemplo não estão disponíveis)\n')

core.jogo_aberto = lambda: False  # nos testes, fingimos que o jogo está fechado

falhas = 0
pulados = 0


def teste(f):
    global falhas, pulados
    if getattr(f, 'so_com_amostras', False) and FUNCIONOU is None:
        pulados += 1
        print('PULADO', f.__name__, '(precisa dos saves de exemplo)')
        return f
    try:
        f()
        print('OK   ', f.__name__)
    except Exception as e:
        falhas += 1
        print('FALHA', f.__name__, '->', type(e).__name__, e)
    return f


def so_com_amostras(f):
    f.so_com_amostras = True
    return f


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def save_falso(tmp, origem=COMPLETO, sub=('Avalanche Studios', 'COTW', 'Saves', '76561190000000000')):
    pasta = os.path.join(tmp, 'Documentos', *sub)
    os.makedirs(os.path.join(pasta, 'slots', '0'))
    shutil.copy(origem, os.path.join(pasta, core.NOME_ARQUIVO))
    shutil.copy(origem, os.path.join(pasta, 'slots', '0', core.NOME_ARQUIVO))
    open(os.path.join(pasta, 'outro_arquivo_adf'), 'wb').write(b'nao mexer')
    return pasta


@teste
def le_save_completo():
    s = core.Save.abrir(COMPLETO)
    assert s.chaves == [0, 1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21], s.chaves
    m = {x.chave: x for x in s.mapas()}
    assert (m[10].concluidas, m[10].total) == (16, 23)
    assert m[10].nome == 'Te Awaroa National Park'
    assert (m[19].nome, m[20].nome, m[21].nome) == ('Askiy Ridge', 'Tòrr nan Sithean', 'Intisuyu')
    assert core.nome_do_mapa(5) == 'Mapa desconhecido (chave 5)'


@teste
def le_save_zerado():
    s = core.Save.abrir(ZERADO)
    assert s.chaves == [10]
    (m,) = s.mapas()
    assert (m.concluidas, m.total) == (1, 23)


@teste
@so_com_amostras
def remover_chave10_igual_ao_arquivo_testado_no_jogo():
    s = core.Save.abrir(COMPLETO)
    novo, raw = s.sem_mapas([10])
    core.conferir_resultado(s, novo, raw, [10])
    assert raw == bytes(core.Save.abrir(FUNCIONOU).raw), 'conteúdo diferente do que funcionou no jogo'


@teste
def remover_cada_mapa_e_todos_em_sequencia():
    s = core.Save.abrir(COMPLETO)
    for k in s.chaves:  # cada um sozinho
        novo, raw = s.sem_mapas([k])
        r = core.conferir_resultado(s, novo, raw, [k])
        assert k not in r.chaves and len(r.chaves) == len(s.chaves) - 1
    atual = s  # agora tirando um por um, em ordem que passa pelas cadeias com colisão
    for k in [19, 0, 21, 1, 2, 20] + [k for k in s.chaves if k not in (19, 0, 21, 1, 2, 20)]:
        novo, raw = atual.sem_mapas([k])
        prox = core.conferir_resultado(atual, novo, raw, [k])
        atual = prox
    assert atual.chaves == []


@teste
def mapa_inexistente_da_erro():
    s = core.Save.abrir(ZERADO)
    try:
        s.sem_mapas([3])
    except core.ErroSave:
        return
    raise AssertionError('deveria ter dado erro')


@teste
def arquivo_estranho_da_erro():
    for dados in [b'', b'oi', open(COMPLETO, 'rb').read()[:1000]]:
        try:
            core.Save(dados)
        except core.ErroSave:
            continue
        raise AssertionError('deveria ter dado erro')


@teste
def encontra_save_e_ignora_slots():
    with tempfile.TemporaryDirectory() as tmp:
        pasta = save_falso(tmp)
        achados = core.encontrar_saves([os.path.join(tmp, 'Documentos')])
        assert [a.pasta for a in achados] == [pasta], achados
        assert achados[0].plataforma == 'Steam'


@teste
def fluxo_completo_reset_e_restaurar():
    with tempfile.TemporaryDirectory() as tmp:
        pasta = save_falso(tmp)
        backups = os.path.join(tmp, 'backups')
        save = core.descrever_pasta(pasta)
        antes = {n: md5(os.path.join(pasta, n)) for n in os.listdir(pasta) if n != 'slots'}
        slot_antes = md5(os.path.join(pasta, 'slots', '0', core.NOME_ARQUIVO))

        b = core.resetar_mapas(save, [10], backups)
        assert md5(b.arquivo) == md5(COMPLETO)
        assert core.Save.abrir(save.arquivo).chaves == [k for k in core.Save.abrir(COMPLETO).chaves if k != 10]
        if FUNCIONOU:
            assert core.Save.abrir(save.arquivo).raw == core.Save.abrir(FUNCIONOU).raw
        depois = {n: md5(os.path.join(pasta, n)) for n in os.listdir(pasta) if n != 'slots'}
        assert set(depois) == set(antes), 'apareceu/sumiu arquivo na pasta do save'
        assert [n for n in antes if antes[n] != depois[n]] == [core.NOME_ARQUIVO]
        assert md5(os.path.join(pasta, 'slots', '0', core.NOME_ARQUIVO)) == slot_antes

        lista = core.listar_backups(save, backups)
        assert len(lista) == 1 and lista[0].titulo == 'Antes de resetar Te Awaroa National Park', lista[0].titulo
        assert os.path.basename(lista[0].pasta).endswith(' - Antes de resetar Te Awaroa National Park')
        assert os.path.dirname(lista[0].pasta) == os.path.join(backups, 'Steam - 76561190000000000',
                                                               'Backups_MISSIONS')
        assert {m['chave']: m['concluidas'] for m in lista[0].mapas}[10] == 16
        assert os.path.isfile(os.path.join(backups, 'LEIA-ME.txt'))
        core.restaurar_backup(save, lista[0], backups)
        assert md5(save.arquivo) == md5(COMPLETO)
        assert len(core.listar_backups(save, backups)) == 2  # backup automático antes de restaurar


@teste
def jogo_aberto_bloqueia():
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        original = core.jogo_aberto
        core.jogo_aberto = lambda: True
        try:
            core.resetar_mapas(save, [10], os.path.join(tmp, 'b'))
        except core.ErroSave:
            assert md5(save.arquivo) == md5(COMPLETO)
            return
        finally:
            core.jogo_aberto = original
        raise AssertionError('deveria ter bloqueado')


@teste
def bloqueio_do_windows_vira_mensagem_explicada_e_nao_altera_o_save():
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        original = core.os.makedirs

        def bloqueado(*a, **k):
            e = FileNotFoundError(2, 'O sistema não pode encontrar o arquivo especificado')
            e.winerror = 2
            raise e
        core.os.makedirs = bloqueado
        try:
            core.resetar_mapas(save, [10], os.path.join(tmp, 'b'))
        except OSError as e:
            texto = core.texto_do_erro(e, r'C:\x\COTW-Reset-Missoes.exe')
            assert 'Acesso Controlado a Pastas' in texto and r'C:\x\COTW-Reset-Missoes.exe' in texto
            assert md5(save.arquivo) == md5(COMPLETO)
            return
        finally:
            core.os.makedirs = original
        raise AssertionError('deveria ter dado erro')


@teste
def mapa_resetado_continua_na_lista_ate_voltar_ao_save():
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        bk = os.path.join(tmp, 'b')
        antes = {m.chave: m for m in core.mapas_para_mostrar(save, bk)}
        core.resetar_mapas(save, [21, 10], bk)
        (b,) = core.listar_backups(save, bk)
        assert b.titulo == 'Antes de resetar Intisuyu, Te Awaroa National Park'
        m = {x.chave: x for x in core.mapas_para_mostrar(save, bk)}
        assert len(m) == len(antes)
        for k in (21, 10):
            assert m[k].resetado and (m[k].concluidas, m[k].em_andamento, m[k].total) == (0, 0, antes[k].total)
        assert not m[0].resetado and m[0].concluidas == antes[0].concluidas
        # restaurar o backup traz o mapa de volta ao save -> deixa de aparecer como resetado
        core.restaurar_backup(save, core.listar_backups(save, bk)[0], bk)
        m = {x.chave: x for x in core.mapas_para_mostrar(save, bk)}
        assert not m[21].resetado and m[21].concluidas == antes[21].concluidas
        assert core._ler_registro(save, bk) == {}


@teste
def reset_de_varios_mapas_com_nome_comprido():
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        bk = os.path.join(tmp, 'b')
        core.resetar_mapas(save, [0, 1, 2, 3, 4, 6, 8], bk)
        (b,) = core.listar_backups(save, bk)
        assert os.path.basename(b.pasta).endswith('…') and md5(b.arquivo) == md5(COMPLETO)
        core.restaurar_backup(save, b, bk)
        assert md5(save.arquivo) == md5(COMPLETO)


@teste
def janela_mostra_mapa_resetado_destacado():
    import cotw_app
    from unittest import mock
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
             mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
             mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
             mock.patch.object(cotw_app.messagebox, 'askyesno', lambda *a, **k: True) as _, \
             mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
            app = cotw_app.App()
            app.withdraw()
            app.iniciar()
            app.lista.selection_set('21')
            app.resetar()
            item = app.lista.item('21')
            app.destroy()
        assert item['values'][0] == 'Intisuyu   —   Missões resetadas', item
        assert item['values'][1:] == [0, 0, 94] and 'resetado' in item['tags'], item


@teste
def pasta_do_programa_fica_oculta():
    import ctypes
    with tempfile.TemporaryDirectory() as tmp:
        raiz = os.path.join(tmp, 'COTW Reset Missoes')
        assert core.testar_gravacao(raiz) is None
        attrs = ctypes.windll.kernel32.GetFileAttributesW(raiz)
        assert attrs & 0x2, 'pasta não ficou oculta'
        assert os.listdir(raiz) == ['LEIA-ME.txt'], os.listdir(raiz)  # o arquivo de teste foi apagado


@teste
def backups_antigos_sao_movidos_para_a_pasta_nova():
    import json
    with tempfile.TemporaryDirectory() as tmp:
        docs = os.path.join(tmp, 'Documentos')
        velho = os.path.join(docs, core.PASTA_ANTIGA, '76561190000000000', '2026-11-18_21-34-36')
        os.makedirs(velho)
        shutil.copy(COMPLETO, os.path.join(velho, core.NOME_ARQUIVO))
        json.dump({'criado_em': '2026-11-18T21:34:36',
                   'motivo': 'antes de resetar: Intisuyu (provável, chave 21)'},
                  open(os.path.join(velho, 'info.json'), 'w', encoding='utf-8'))
        json.dump({'21': {'total': 94}}, open(os.path.join(os.path.dirname(velho), 'mapas_resetados.json'), 'w'))
        raiz = os.path.join(docs, core.PASTA_PROGRAMA)
        core.migrar_pasta_antiga(raiz, [docs])
        assert not os.path.exists(os.path.join(docs, core.PASTA_ANTIGA))
        save = core.descrever_pasta(os.path.join(docs, '76561190000000000'))
        (b,) = core.listar_backups(save, raiz)
        assert b.titulo == 'Antes de resetar Intisuyu', b.titulo
        assert os.path.basename(b.pasta) == '2026-11-18 21-34-36 - Antes de resetar Intisuyu', b.pasta
        assert md5(b.arquivo) == md5(COMPLETO)
        assert core._ler_registro(save, raiz) == {'21': {'total': 94}}


@teste
def faixa_de_aviso_aparece_quando_o_windows_bloqueia():
    import cotw_app
    from unittest import mock
    erro = FileNotFoundError(2, 'bloqueado')
    erro.winerror = 2
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        bloqueio = {'ativo': True}
        with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
             mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
             mock.patch.object(core, 'testar_gravacao', lambda raiz: erro if bloqueio['ativo'] else None), \
             mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
             mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None), \
             mock.patch.object(cotw_app.messagebox, 'showwarning', lambda *a, **k: None):
            app = cotw_app.App()
            app.withdraw()
            app.iniciar()
            app.update()
            visivel = app.faixa.winfo_manager() == 'pack'
            texto = app.faixa_texto.cget('text')
            desativado = app.bt_reset.instate(['disabled'])
            bloqueio['ativo'] = False
            app.testar_de_novo()
            some = app.faixa.winfo_manager() == ''
            ativado = app.bt_reset.instate(['!disabled'])
            app.destroy()
        assert visivel and 'Acesso Controlado a Pastas' in texto and desativado
        assert some and ativado


@teste
def janela_de_restaurar_mostra_o_que_vai_mudar():
    import cotw_app
    from unittest import mock
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
             mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
             mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
             mock.patch.object(cotw_app.messagebox, 'askyesno', lambda *a, **k: True), \
             mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
            app = cotw_app.App()
            app.withdraw()
            app.iniciar()
            app.lista.selection_set('21')
            app.resetar()
            jan = cotw_app.JanelaRestaurar(app, core.listar_backups(save, app.raiz))
            jan.update()
            linhas = {jan.det.item(i)['values'][0]: jan.det.item(i) for i in jan.det.get_children()}
            resumo = jan.resumo.cget('text')
            jan.restaurar()
            depois = app.lista.item('21')
            app.destroy()
        intisuyu = linhas['Intisuyu']
        assert intisuyu['values'][1:] == ['resetado (0 de 94)', '11 de 94 concluídas, 12 em and.'], intisuyu
        assert 'diferente' in intisuyu['tags']
        assert 'diferente' not in linhas['Te Awaroa National Park']['tags']
        assert resumo.startswith('1 mapa(s)'), resumo
        assert depois['values'][0] == 'Intisuyu' and 'resetado' not in depois['tags'], depois


@teste
def bloqueio_reconhecido_em_todos_os_formatos():
    from unittest import mock
    pasta = FileNotFoundError(2, 'x'); pasta.winerror = 2            # os.makedirs bloqueado
    negado = PermissionError(13, 'Permission denied')               # open() bloqueado (sem winerror)
    sumiu = FileNotFoundError(2, 'No such file or directory')       # open() bloqueado (sem winerror)
    for e in (pasta, negado, sumiu):
        assert core.parece_bloqueio_do_windows(e), e
    disco_cheio = OSError(28, 'No space left on device')
    with mock.patch.object(core, 'acesso_controlado_ligado', lambda: False):
        assert not core.parece_bloqueio_do_windows(disco_cheio)
    with mock.patch.object(core, 'acesso_controlado_ligado', lambda: True):
        assert core.parece_bloqueio_do_windows(disco_cheio)
    assert core.acesso_controlado_ligado() in (True, False, None)


def tres_saves(tmp):
    """Steam antigo, Steam novo e Epic (o mais recente de todos)."""
    epic_id = '3f9a2c' + '0' * 20 + 'abcdef'
    pastas = {
        'steam_antigo': save_falso(tmp, sub=('Avalanche Studios', 'COTW', 'Saves', '76561190000000001')),
        'steam_novo': save_falso(tmp, sub=('Avalanche Studios', 'COTW', 'Saves', '76561190000000002')),
        'epic': save_falso(tmp, sub=('Avalanche Studios', 'Epic Games Store', 'COTW', 'Saves', epic_id)),
    }
    for nome, quando in (('steam_antigo', 1_700_000_000), ('steam_novo', 1_750_000_000), ('epic', 1_760_000_000)):
        for arq in os.listdir(pastas[nome]):
            p = os.path.join(pastas[nome], arq)
            if os.path.isfile(p):
                os.utime(p, (quando, quando))
    return pastas


@teste
def saves_vem_do_mais_recente_e_com_plataforma_certa():
    with tempfile.TemporaryDirectory() as tmp:
        p = tres_saves(tmp)
        achados = core.encontrar_saves([os.path.join(tmp, 'Documentos')])
        assert [a.pasta for a in achados] == [p['epic'], p['steam_novo'], p['steam_antigo']]
        assert [a.plataforma for a in achados] == ['Epic', 'Steam', 'Steam']
        assert 'jogado em' in achados[0].descricao()
        # o reset não muda a data de "jogado em"
        antes = achados[1].ultimo_jogo
        core.resetar_mapas(achados[1], [10], os.path.join(tmp, 'b'))
        assert core.descrever_pasta(p['steam_novo']).ultimo_jogo == antes


@teste
def janela_com_steam_e_epic():
    import cotw_app
    from unittest import mock
    perguntas = []
    with tempfile.TemporaryDirectory() as tmp:
        p = tres_saves(tmp)
        achados = core.encontrar_saves([os.path.join(tmp, 'Documentos')])
        with mock.patch.object(core, 'encontrar_saves', lambda: achados), \
             mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
             mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
             mock.patch.object(cotw_app.messagebox, 'askyesno', lambda t, m, **k: perguntas.append(m) or True), \
             mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
            app = cotw_app.App()
            app.withdraw()
            app.iniciar()
            app.update()
            # abre no save mais recente: Epic
            r1 = (app.var_plataforma.get(), app.save_atual.pasta, app.radios['Epic'].cget('text'),
                  app.radios['Outra'].winfo_manager(), app.aviso_saves.cget('text'))
            # troca para Steam -> pega o Steam mais recente
            app.var_plataforma.set('Steam')
            app.trocar_plataforma()
            app.update()
            r2 = (app.save_atual.pasta, len(app.combo['values']), app.aviso_saves.cget('text'))
            app.lista.selection_set('21')
            app.resetar()
            credito = app.credito.cget('text')
            apoio = cotw_app.JanelaApoio(app)
            botoes = [w for w in apoio.winfo_children()[0].winfo_children() if isinstance(w, cotw_app.ttk.Button)]
            estados = [(b.cget('text'), b.instate(['disabled'])) for b in botoes]
            apoio.destroy()
            app.destroy()
        assert r1[0] == 'Epic' and r1[1] == p['epic'] and r1[2] == 'Epic (1 save)' and r1[3] == '', r1
        assert 'também tem save da Steam' in r1[4], r1
        assert r2[0] == p['steam_novo'] and r2[1] == 2, r2
        assert 'Há 2 saves da Steam' in r2[2] and 'também tem save da Epic' in r2[2], r2
        assert perguntas and perguntas[0].startswith('Save: Steam - conta 76561190000000002 (jogado em'), perguntas
        assert credito == f'Criado por Sheeerpha   •   versão {cotw_app.VERSAO}', credito
        assert ('☕  Buy Me a Coffee', False) in estados and ('💠  LivePix (Pix)', False) in estados, estados
        assert cotw_app.LINK_BUYMEACOFFEE == 'https://buymeacoffee.com/sheeerpha'
        assert cotw_app.LINK_LIVEPIX == 'https://livepix.gg/sherpa'


@teste
def textos_completos_nos_tres_idiomas():
    import string
    def campos(s):
        return sorted({c for _, c, _, _ in string.Formatter().parse(s) if c})
    base = idiomas.TEXTOS['pt']
    for cod in idiomas.IDIOMAS:
        txt = idiomas.TEXTOS[cod]
        assert set(txt) == set(base), (cod, set(base) ^ set(txt))
        for k in base:
            assert campos(txt[k]) == campos(base[k]), (cod, k, campos(txt[k]), campos(base[k]))


@teste
def detecta_idioma_do_windows():
    assert idiomas.idioma_do_langid(0x0416) == 'pt'   # português (Brasil)
    assert idiomas.idioma_do_langid(0x0816) == 'pt'   # português (Portugal)
    assert idiomas.idioma_do_langid(0x0C0A) == 'es'   # espanhol (Espanha)
    assert idiomas.idioma_do_langid(0x080A) == 'es'   # espanhol (México)
    assert idiomas.idioma_do_langid(0x0409) == 'en'   # inglês (EUA)
    assert idiomas.idioma_do_langid(0x0407) == 'en'   # alemão -> inglês
    assert idiomas.detectar_idioma_do_windows() in idiomas.IDIOMAS


@teste
def preferencia_de_idioma_e_salva_e_lida():
    idiomas.salvar_preferencia('es')
    assert idiomas.carregar_preferencia() == 'es'
    idiomas.iniciar()
    assert idiomas.atual() == 'es'
    idiomas.definir('pt')


@teste
def erros_e_motivos_de_backup_traduzidos():
    try:
        idiomas.definir('en')
        try:
            core.Save(b'')
            raise AssertionError('deveria ter dado erro')
        except core.ErroSave as e:
            assert str(e) == 'This file does not look like a COTW missions save.', e
        assert core.nome_do_mapa(5) == 'Unknown map (key 5)'
        # backup antigo, gravado só em português, aparece traduzido
        import datetime
        tipo, chaves, origem = core._entender_titulo_antigo('Antes de resetar Intisuyu, Te Awaroa National Park')
        b = core.Backup('x', datetime.datetime(2026, 11, 18, 21, 34), 'Antes de resetar …', [], tipo, chaves, origem)
        assert b.titulo == 'Before resetting Intisuyu, Te Awaroa National Park', b.titulo
        tipo, chaves, origem = core._entender_titulo_antigo('Antes de restaurar o backup de 18-11-2026 21-34')
        b = core.Backup('x', datetime.datetime(2026, 11, 18, 21, 36), '...', [], tipo, chaves, origem)
        assert b.titulo == 'Before restoring the backup from 11/18/2026 21:34', b.titulo
        idiomas.definir('es')
        assert b.titulo == 'Antes de restaurar la copia del 18/11/2026 21:34', b.titulo
    finally:
        idiomas.definir('pt')


@teste
def janela_troca_de_idioma_sem_perder_o_save():
    import cotw_app
    from unittest import mock
    try:
        with tempfile.TemporaryDirectory() as tmp:
            save = core.descrever_pasta(save_falso(tmp))
            with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
                 mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
                 mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
                 mock.patch.object(cotw_app.messagebox, 'askyesno', lambda *a, **k: True), \
                 mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
                app = cotw_app.App()
                app.withdraw()
                app.iniciar()
                app.lista.selection_set('21')
                app.resetar()
                app.trocar_idioma('en')
                app.update()
                en = (app.credito.cget('text'), app.lista.item('21')['values'][0], app.save_atual.pasta,
                      app.radios['Steam'].cget('text'), app.lista.heading('concluidas')['text'],
                      app.title(), core.listar_backups(save, app.raiz)[0].titulo, app.combo_idioma.get())
                app.trocar_idioma('es')
                app.update()
                es = (app.credito.cget('text'), app.lista.item('21')['values'][0],
                      app.radios['Steam'].cget('text'), app.combo['values'][0])
                app.destroy()
        assert en[0] == f'Created by Sheeerpha   •   version {cotw_app.VERSAO}', en
        assert en[1] == 'Intisuyu   —   Missions reset' and en[2] == save.pasta, en
        assert en[3] == 'Steam (1 save)' and en[4] == 'Completed missions', en
        assert en[5].startswith('ResetMissionsCOTW - Per-Map Mission Reset'), en
        assert en[6] == 'Before resetting Intisuyu' and en[7] == 'English', en
        assert es[0].startswith('Creado por Sheeerpha') and es[1] == 'Intisuyu   —   Misiones reiniciadas', es
        assert es[2] == 'Steam (1 partida)' and es[3].startswith('Cuenta 76561190000000000  —  jugada el'), es
        assert idiomas.carregar_preferencia() == 'es'
    finally:
        idiomas.definir('pt')


@teste
def idioma_e_tema_ficam_salvos_juntos():
    import temas
    idiomas.salvar_preferencia('en')
    temas.definir('escuro')
    cfg = idiomas.ler_config()
    assert cfg['idioma'] == 'en' and cfg['tema'] == 'escuro' and cfg['aviso_visto'] is True, cfg
    idiomas.salvar_preferencia('pt')
    assert idiomas.ler_config()['tema'] == 'escuro'  # trocar o idioma não apaga o tema
    temas.iniciar()
    assert temas.atual() == 'escuro'
    temas.definir('claro')
    idiomas.definir('pt')
    assert temas.tema_do_windows() in temas.TEMAS


@teste
def janela_alterna_tema_sem_perder_o_save():
    import cotw_app, temas
    from unittest import mock
    try:
        with tempfile.TemporaryDirectory() as tmp:
            save = core.descrever_pasta(save_falso(tmp))
            with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
                 mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
                 mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
                 mock.patch.object(cotw_app.messagebox, 'askyesno', lambda *a, **k: True), \
                 mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
                app = cotw_app.App()
                app.withdraw()
                app.iniciar()
                claro = (app.bt_tema.cget('text'), cotw_app.ttk.Style().theme_use())
                app.lista.selection_set('21')
                app.resetar()
                app.alternar_tema()
                app.update()
                estilo = cotw_app.ttk.Style()
                escuro = (app.bt_tema.cget('text'), estilo.theme_use(), estilo.lookup('Treeview', 'background'),
                          str(app.cget('bg')), str(app.lista.tag_configure('resetado', 'background')),
                          app.lista.item('21')['values'][0], app.save_atual.pasta,
                          idiomas.ler_config().get('tema'))
                jan = cotw_app.JanelaRestaurar(app, core.listar_backups(save, app.raiz))
                jan.update()
                fundo_restaurar = str(jan.cget('bg'))
                jan.destroy()
                app.alternar_tema()
                app.update()
                de_volta = (app.bt_tema.cget('text'), cotw_app.ttk.Style().theme_use())
                app.destroy()
        assert claro == ('🌙  Tema escuro', 'vista'), claro
        assert escuro[:4] == ('☀  Tema claro', 'clam', '#2b2d31', '#202124'), escuro
        assert escuro[4] == '#1e4229' and escuro[5] == 'Intisuyu   —   Missões resetadas', escuro
        assert escuro[6] == save.pasta and escuro[7] == 'escuro', escuro
        assert fundo_restaurar == '#202124', fundo_restaurar
        assert de_volta == ('🌙  Tema escuro', 'vista'), de_volta
    finally:
        temas.definir('claro', salvar=False)


def _backup_falso(pasta_base, nome, quando, conteudo_de, completo=False):
    """Cria um backup "à mão", com data escolhida (para testar a limpeza automática)."""
    import json
    p = os.path.join(pasta_base, nome)
    if completo:
        shutil.copytree(conteudo_de, os.path.join(p, core.PASTA_ARQUIVOS_SAVE))
        info = {'criado_em': quando.isoformat(timespec='seconds'), 'tipo': 'manual'}
    else:
        os.makedirs(p)
        shutil.copy(conteudo_de, os.path.join(p, core.NOME_ARQUIVO))
        info = {'criado_em': quando.isoformat(timespec='seconds'), 'tipo': 'reset', 'chaves': [10]}
    json.dump(info, open(os.path.join(p, 'info.json'), 'w', encoding='utf-8'))
    return p


@teste
def limite_de_50_backups_de_missoes_protege_o_primeiro():
    import datetime
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        raiz = os.path.join(tmp, 'b')
        base = core.pasta_backups_do_save(save, raiz)
        inicio = datetime.datetime(2026, 1, 1, 10, 0)
        pastas = [_backup_falso(base, f'b{i:02d}', inicio + datetime.timedelta(minutes=i), COMPLETO)
                  for i in range(55)]
        core.resetar_mapas(save, [10], raiz)   # cria o 56º e dispara a limpeza
        lista = core.listar_backups(save, raiz)
        assert len(lista) == core.LIMITE_MISSOES == 50, len(lista)
        assert os.path.isdir(pastas[0]), 'o primeiro (mais antigo) não pode ser apagado'
        assert lista[-1].pasta == pastas[0] and lista[-1].protegido
        assert not any(os.path.isdir(p) for p in pastas[1:7]), 'os seguintes mais antigos deveriam sair'
        assert all(os.path.isdir(p) for p in pastas[7:])
        assert sum(b.protegido for b in lista) == 1


@teste
def backup_e_restauracao_do_save_completo():
    with tempfile.TemporaryDirectory() as tmp:
        pasta = save_falso(tmp)
        save = core.descrever_pasta(pasta)
        raiz = os.path.join(tmp, 'b')
        antes = {rel: md5(c) for rel, c in core._arquivos_da_pasta(pasta).items()}
        b = core.fazer_backup_save_completo(save, raiz)
        assert b.arquivos == len(antes) == 3 and b.tamanho > 0, (b.arquivos, antes)
        assert os.path.dirname(b.pasta) == os.path.join(raiz, 'Steam - 76561190000000000', 'Backups_SAVE')
        assert os.path.isfile(os.path.join(os.path.dirname(b.pasta), 'COMO RESTAURAR MANUALMENTE.txt'))
        assert {rel: md5(c) for rel, c in core._arquivos_da_pasta(b.pasta_arquivos).items()} == antes
        assert core.tem_backup_save(save, raiz)
        # estraga o save: reseta um mapa, apaga um arquivo e cria outro
        core.resetar_mapas(save, [10], raiz)
        os.remove(os.path.join(pasta, 'outro_arquivo_adf'))
        open(os.path.join(pasta, 'novo_arquivo'), 'wb').write(b'x')
        (lst,) = core.listar_backups_save(save, raiz)
        antes_restaurar = core.restaurar_save_completo(save, lst, raiz)
        depois = {rel: md5(c) for rel, c in core._arquivos_da_pasta(pasta).items()}
        assert depois == antes, 'o save restaurado tem que ser idêntico ao do backup'
        assert antes_restaurar.tipo == 'antes_restaurar'
        assert 'novo_arquivo' in core._arquivos_da_pasta(antes_restaurar.pasta_arquivos)
        assert len(core.listar_backups_save(save, raiz)) == 2
        assert not any(n.endswith('_tmp') for n in os.listdir(os.path.dirname(pasta))), os.listdir(os.path.dirname(pasta))


@teste
def restauracao_completa_que_falha_volta_como_estava():
    from unittest import mock
    with tempfile.TemporaryDirectory() as tmp:
        pasta = save_falso(tmp)
        save = core.descrever_pasta(pasta)
        raiz = os.path.join(tmp, 'b')
        core.fazer_backup_save_completo(save, raiz)
        open(os.path.join(pasta, 'progresso_novo'), 'wb').write(b'importante')
        antes = {rel: md5(c) for rel, c in core._arquivos_da_pasta(pasta).items()}
        (b,) = core.listar_backups_save(save, raiz)
        original_rename = os.rename
        chamadas = []

        def rename_que_falha(a, d):
            chamadas.append((a, d))
            if len(chamadas) == 2:   # 1ª: save -> .anterior_tmp (ok); 2ª: cópia -> save (falha)
                raise PermissionError(13, 'em uso')
            return original_rename(a, d)
        with mock.patch.object(core.os, 'rename', rename_que_falha):
            try:
                core.restaurar_save_completo(save, b, raiz)
                raise AssertionError('deveria ter dado erro')
            except core.ErroSave as e:
                assert 'save continua como estava' in str(e), e
        assert {rel: md5(c) for rel, c in core._arquivos_da_pasta(pasta).items()} == antes
        assert not any(n.endswith('_tmp') for n in os.listdir(os.path.dirname(pasta)))


@teste
def limite_de_5_backups_do_save_e_pastas_temporarias_ignoradas():
    import datetime
    with tempfile.TemporaryDirectory() as tmp:
        pasta = save_falso(tmp)
        save = core.descrever_pasta(pasta)
        raiz = os.path.join(tmp, 'b')
        base = core.pasta_backups_save_completo(save, raiz)
        inicio = datetime.datetime(2026, 1, 1, 10, 0)
        pastas = [_backup_falso(base, f's{i}', inicio + datetime.timedelta(hours=i), pasta, completo=True)
                  for i in range(5)]
        # restaurar o 2º mais antigo, com o limite cheio: ele não pode ser apagado pela limpeza
        lista = core.listar_backups_save(save, raiz)
        segundo = [b for b in lista if b.pasta == pastas[1]][0]
        core.restaurar_save_completo(save, segundo, raiz)
        restantes = [b.pasta for b in core.listar_backups_save(save, raiz)]
        assert len(restantes) == core.LIMITE_SAVE == 5, restantes
        assert pastas[0] in restantes and pastas[1] in restantes and pastas[2] not in restantes, restantes
        # sobras de uma restauração interrompida não aparecem como saves
        shutil.copytree(pasta, pasta + '.anterior_tmp')
        achados = core.encontrar_saves([os.path.join(tmp, 'Documentos')])
        assert [a.pasta for a in achados] == [pasta], achados


@teste
def backups_da_v15_vao_para_a_pasta_nova():
    with tempfile.TemporaryDirectory() as tmp:
        docs = os.path.join(tmp, 'Documentos')
        velho = os.path.join(docs, core.PASTA_ANTIGA_2, 'Steam - 76561190000000000')
        _backup_falso(os.path.join(velho, 'Backups'), '2026-11-18 21-34-36 - Antes de resetar Intisuyu',
                      __import__('datetime').datetime(2026, 11, 18, 21, 34, 36), COMPLETO)
        open(os.path.join(velho, 'mapas_resetados.json'), 'w').write('{"21": {"total": 94}}')
        open(os.path.join(docs, core.PASTA_ANTIGA_2, 'LEIA-ME.txt'), 'w').write('x')
        raiz = os.path.join(docs, core.PASTA_PROGRAMA)
        core.migrar_pasta_antiga(raiz, [docs])
        assert not os.path.exists(os.path.join(docs, core.PASTA_ANTIGA_2))
        assert sorted(os.listdir(raiz)) == ['LEIA-ME.txt', 'Steam - 76561190000000000'], os.listdir(raiz)
        save = core.descrever_pasta(os.path.join(docs, '76561190000000000'))
        (b,) = core.listar_backups(save, raiz)
        assert os.path.dirname(b.pasta).endswith('Backups_MISSIONS') and md5(b.arquivo) == md5(COMPLETO)
        assert core._ler_registro(save, raiz) == {'21': {'total': 94}}
        assert raiz.endswith('.BKP_ResetMissions_Saves_COTW')


@teste
def sugestao_de_backup_completo_antes_do_reset():
    import cotw_app
    from unittest import mock
    for resposta, espera_backup, espera_reset in ((True, 1, True), (False, 0, True), (None, 0, False)):
        with tempfile.TemporaryDirectory() as tmp:
            save = core.descrever_pasta(save_falso(tmp))
            perguntas = []
            with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
                 mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
                 mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
                 mock.patch.object(cotw_app.messagebox, 'askyesnocancel',
                                   lambda t, m, **k: perguntas.append(m) or resposta), \
                 mock.patch.object(cotw_app.messagebox, 'askyesno', lambda *a, **k: True), \
                 mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
                app = cotw_app.App()
                app.withdraw()
                app.iniciar()
                app.lista.selection_set('21')
                app.resetar()
                n_save = len(core.listar_backups_save(save, app.raiz))
                resetado = app.mapas[21].resetado
                # com backup completo já feito, a sugestão não aparece de novo
                if resposta:
                    perguntas.clear()
                    app.lista.selection_set('10')
                    app.resetar()
                    assert perguntas == [], perguntas
                app.destroy()
            assert n_save == espera_backup and resetado == espera_reset, (resposta, n_save, resetado)


@teste
def aviso_aparece_sempre_e_introducao_so_na_primeira_vez():
    import cotw_app
    from unittest import mock
    idiomas.salvar_config(intro_vista=False)
    cotw_app.App.mostrar_aviso_ao_abrir = True
    try:
        with tempfile.TemporaryDirectory() as tmp:
            save = core.descrever_pasta(save_falso(tmp))
            with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
                 mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
                 mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None):
                app = cotw_app.App()
                app.withdraw()
                app.iniciar()                # agenda o aviso, como ao abrir o programa
                app.after(400)
                app.update()
                janelas = lambda tipo: [w for w in app.winfo_children() if isinstance(w, tipo)]
                (aviso,) = janelas(cotw_app.JanelaAviso)
                textos = [w.cget('text') for w in aviso.winfo_children()[0].winfo_children()
                          if isinstance(w, cotw_app.ttk.Label)]
                assert any('criado por um jogador' in x and cotw_app.LINK_GITHUB in x
                           and 'github.com/Sheeerpha/ResetMissionsCOTW' in x
                           and '"Fazer backup do save completo"' in x and 'troféus' in x for x in textos), textos
                assert janelas(cotw_app.JanelaIntro) == []
                aviso.fechar()
                app.update()
                app.after(300)
                app.update()
                (intro,) = janelas(cotw_app.JanelaIntro)
                paginas = []
                for _ in range(cotw_app.JanelaIntro.TOTAL):
                    paginas.append((intro.contador.cget('text'), intro.titulo.cget('text'),
                                    intro.bt_proximo.cget('text'), intro.texto.cget('text')))
                    intro.proximo()
                assert not intro.winfo_exists()
                assert idiomas.ler_config()['intro_vista'] is True
                # abrir o programa de novo: o aviso aparece outra vez, a introdução não
                app.mostrar_boas_vindas()
                (aviso2,) = janelas(cotw_app.JanelaAviso)
                aviso2.fechar()
                app.update()
                app.after(300)
                app.update()
                assert janelas(cotw_app.JanelaAviso) == [] and janelas(cotw_app.JanelaIntro) == []
                app.mostrar_intro()         # mas o botão "Como usar" abre de novo
                app.mostrar_intro()         # (e não abre duas)
                assert len(janelas(cotw_app.JanelaIntro)) == 1
                app.destroy()
        assert paginas[0][0] == '1 de 6' and paginas[-1][0] == '6 de 6', paginas
        assert paginas[-1][2] == 'Começar!' and paginas[0][2] == 'Próximo  →', paginas
        assert '"Resetar missões do(s) mapa(s) selecionado(s)"' in paginas[3][3], paginas[3][3]
        assert 'Fazer backup do save completo' in paginas[4][3] and '50' in paginas[4][3], paginas[4][3]
        assert not any('{' in p[3] for p in paginas), 'sobrou campo sem preencher'
    finally:
        idiomas.salvar_config(intro_vista=True)
        cotw_app.App.mostrar_aviso_ao_abrir = False


@teste
def janela_de_restaurar_save_completo():
    import cotw_app
    from unittest import mock
    with tempfile.TemporaryDirectory() as tmp:
        pasta = save_falso(tmp)
        save = core.descrever_pasta(pasta)
        with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
             mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
             mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
             mock.patch.object(cotw_app.messagebox, 'askyesno', lambda *a, **k: True), \
             mock.patch.object(cotw_app.messagebox, 'showinfo', lambda *a, **k: None):
            app = cotw_app.App()
            app.withdraw()
            app.iniciar()
            info_antes = app.info.cget('text')
            assert app.fazer_backup_save()
            info_depois = app.info.cget('text')
            open(os.path.join(pasta, 'extra'), 'wb').write(b'x')
            jan = cotw_app.JanelaRestaurarSave(app, core.listar_backups_save(save, app.raiz))
            linha = jan.lista.item('0')['values']
            jan.restaurar()
            app.destroy()
        assert 'Nenhum backup do save completo' in info_antes and '1 backup(s) do save completo' in info_depois
        assert '🔒' in linha[2] and linha[2].startswith('Backup feito por você') and 'MB' in linha[3], linha
        assert not os.path.exists(os.path.join(pasta, 'extra'))


@teste
def link_do_github_no_rodape_abre_a_pagina():
    import cotw_app
    from unittest import mock
    abertos = []
    with tempfile.TemporaryDirectory() as tmp:
        save = core.descrever_pasta(save_falso(tmp))
        with mock.patch.object(core, 'encontrar_saves', lambda: [save]), \
             mock.patch.object(core, 'pasta_do_programa_padrao', lambda: os.path.join(tmp, 'b')), \
             mock.patch.object(core, 'migrar_pasta_antiga', lambda raiz: None), \
             mock.patch('webbrowser.open', lambda url, *a, **k: abertos.append(url)):
            app = cotw_app.App()
            app.iniciar()
            app.update()
            link = app.link_github
            texto, cursor = link.cget('text'), str(link.cget('cursor'))
            link.event_generate('<Button-1>', x=3, y=3)
            app.update()
            app.destroy()
    assert texto == 'GitHub' and cursor == 'hand2', (texto, cursor)
    assert abertos == ['https://github.com/Sheeerpha/ResetMissionsCOTW'], abertos


print()
if pulados:
    print(f'{pulados} teste(s) pulado(s) por falta dos saves de exemplo')
print('TUDO CERTO' if falhas == 0 else f'{falhas} TESTE(S) FALHARAM')
sys.exit(1 if falhas else 0)
