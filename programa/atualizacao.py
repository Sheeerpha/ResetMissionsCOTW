"""Aviso de versão nova.

Ao abrir, o programa pergunta à página pública de Releases do GitHub qual é a última
versão publicada (toda vez que abre). Se for mais nova que esta, a janela mostra
um aviso com o link para baixar. Nada é baixado nem trocado sozinho.

- Não envia nenhum dado pessoal: é só uma consulta à página pública do projeto.
- Sem internet ou com qualquer erro, simplesmente não mostra nada.
- "Agora não" esconde o aviso daquela versão; a próxima versão avisa de novo.
"""
import datetime
import json
import re
import threading
import urllib.request

import idiomas

REPOSITORIO = 'Sheeerpha/ResetMissionsCOTW'
URL_API = f'https://api.github.com/repos/{REPOSITORIO}/releases/latest'
PAGINA = f'https://github.com/{REPOSITORIO}/releases/latest'


def numero(texto):
    """'v0.9.7-beta' -> (0, 9, 7); '0.9.7 (Beta)' -> (0, 9, 7); sem número -> ()."""
    m = re.search(r'(\d+(?:\.\d+)*)', texto or '')
    return tuple(int(x) for x in m.group(1).split('.')) if m else ()


def mais_nova(remota, local):
    return bool(numero(remota)) and numero(remota) > numero(local)


def consultar(tempo_limite=6):
    """(tag, link) da última Release publicada no GitHub."""
    pedido = urllib.request.Request(URL_API, headers={'User-Agent': 'ResetMissionsCOTW',
                                                      'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(pedido, timeout=tempo_limite) as resposta:
        dados = json.load(resposta)
    return str(dados.get('tag_name') or ''), str(dados.get('html_url') or '')


def link_seguro(link):
    """Só abre links da página do próprio projeto."""
    return link if link.startswith(f'https://github.com/{REPOSITORIO}/') else PAGINA


def verificar(versao_local, hoje=None):
    """Devolve (tag, link) se houver versão mais nova e ainda não ignorada; senão None.
    Consulta o GitHub TODA vez que o programa abre (desde a 0.9.9: antes era 1 vez por dia, e uma
    versão publicada no mesmo dia não era avisada)."""
    cfg = idiomas.ler_config()
    hoje = (hoje or datetime.date.today()).isoformat()
    try:
        tag, link = consultar()
    except Exception:
        return None          # sem internet, GitHub fora do ar etc.: tenta na próxima vez
    idiomas.salvar_config(atualizacao_consultada_em=hoje, atualizacao_tag=tag, atualizacao_link=link)
    if not mais_nova(tag, versao_local) or cfg.get('atualizacao_ignorada') == tag:
        return None
    return tag, link_seguro(link)


def ignorar(tag):
    idiomas.salvar_config(atualizacao_ignorada=tag)


class Consulta:
    """Faz a consulta sem travar a janela. A janela olha .pronto e .resultado de tempos em tempos."""

    def __init__(self, versao_local):
        self.pronto = False
        self.resultado = None
        threading.Thread(target=self._rodar, args=(versao_local,), daemon=True).start()

    def _rodar(self, versao_local):
        try:
            self.resultado = verificar(versao_local)
        except Exception:
            self.resultado = None
        self.pronto = True
