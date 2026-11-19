"""Log do programa: um arquivo por vez que o programa é aberto.

- Fica em %LOCALAPPDATA%\\ResetMissionsCOTW\\logs (fora de Documentos, para o Acesso
  Controlado a Pastas e o OneDrive não atrapalharem o próprio log).
- São guardados os MAXIMO mais recentes; o mais antigo é apagado ao abrir o programa.
- Dados pessoais são mascarados antes de gravar (a pessoa vai ENVIAR este arquivo):
  a pasta do usuário vira %USERPROFILE%, o nome de usuário e o nome do PC somem e o
  número da conta Steam aparece só pelo final (7656…4881).
- O log nunca derruba o programa: se não der para gravar, ele simplesmente desliga.
"""
import datetime
import os
import platform
import re
import sys
import traceback

PASTA = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ResetMissionsCOTW', 'logs')
MAXIMO = 5
PREFIXO = 'ResetMissionsCOTW_'

_arquivo = None


def pasta():
    return PASTA


def arquivo_atual():
    return _arquivo


def mascarar(texto):
    texto = str(texto)
    perfil = os.environ.get('USERPROFILE', '')
    if perfil:
        texto = re.sub(re.escape(perfil), '%USERPROFILE%', texto, flags=re.IGNORECASE)
        texto = re.sub(re.escape(perfil.replace('\\', '/')), '%USERPROFILE%', texto, flags=re.IGNORECASE)
    usuario = os.environ.get('USERNAME', '')
    if len(usuario) >= 3:
        texto = re.sub(r'(?<=[\\/])' + re.escape(usuario) + r'(?=[\\/])', '<usuario>', texto, flags=re.IGNORECASE)
    pc = os.environ.get('COMPUTERNAME', '')
    if len(pc) >= 3:
        texto = re.sub(re.escape(pc), '<pc>', texto, flags=re.IGNORECASE)
    # contas Steam (76561...): mostra só o final
    texto = re.sub(r'7656119\d{10}', lambda m: '7656…' + m.group(0)[-4:], texto)
    return texto


def _logs_existentes(base):
    try:
        return sorted(os.path.join(base, n) for n in os.listdir(base)
                      if n.startswith(PREFIXO) and n.endswith('.log'))
    except OSError:
        return []


def iniciar(versao, base=None):
    """Começa o log desta abertura do programa (e apaga os mais antigos)."""
    global _arquivo, PASTA
    if base:
        PASTA = base
    try:
        os.makedirs(PASTA, exist_ok=True)
        existentes = _logs_existentes(PASTA)
        while len(existentes) >= MAXIMO:            # deixa espaço para o novo
            try:
                os.remove(existentes.pop(0))
            except OSError:
                break
        agora = datetime.datetime.now()
        nome = os.path.join(PASTA, f'{PREFIXO}{agora:%Y-%m-%d_%H-%M-%S}.log')
        n = 2
        while os.path.exists(nome):
            nome = os.path.join(PASTA, f'{PREFIXO}{agora:%Y-%m-%d_%H-%M-%S}_{n}.log')
            n += 1
        _arquivo = nome
        with open(_arquivo, 'w', encoding='utf-8') as f:
            f.write(f'ResetMissionsCOTW {versao}\n')
            f.write(f'Aberto em: {agora:%Y-%m-%d %H:%M:%S}\n')
            f.write(f'Windows: {platform.platform()}\n')
            f.write(f'Python: {sys.version.split()[0]}  |  .exe: {getattr(sys, "frozen", False)}\n')
            f.write('-' * 70 + '\n')
    except OSError:
        _arquivo = None
    return _arquivo


def log(mensagem, nivel='INFO'):
    if not _arquivo:
        return
    try:
        with open(_arquivo, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now():%H:%M:%S} [{nivel}] {mascarar(mensagem)}\n')
    except OSError:
        pass


def log_erro(mensagem, erro):
    log(f'{mensagem}: {erro!r}', 'ERRO')
    if _arquivo and isinstance(erro, BaseException):
        detalhes = ''.join(traceback.format_exception(type(erro), erro, erro.__traceback__))
        log('Detalhes técnicos:\n' + detalhes.rstrip(), 'ERRO')


def conteudo_atual(limite=20000):
    """Texto do log desta abertura (o final, se for muito grande), para "Copiar detalhes"."""
    if not _arquivo:
        return ''
    try:
        with open(_arquivo, encoding='utf-8') as f:
            texto = f.read()
        return texto if len(texto) <= limite else '…\n' + texto[-limite:]
    except OSError:
        return ''
