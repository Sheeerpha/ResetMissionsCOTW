"""Textos do programa em português (Brasil), inglês e espanhol.

Para mudar uma frase, edite aqui. Cada chave precisa existir nos três idiomas,
com os mesmos {campos} (o teste 'textos_completos_nos_tres_idiomas' confere).
"""
import ctypes
import json
import os

IDIOMAS = {'pt': 'Português (Brasil)', 'en': 'English', 'es': 'Español'}
PADRAO = 'en'  # para quem não usa Windows em português nem em espanhol

# A escolha de idioma fica fora de Documentos (que pode ser protegida pelo Windows).
ARQUIVO_PREF = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                            'ResetMissionsCOTW', 'config.json')

_atual = 'pt'


def atual():
    return _atual


def definir(cod):
    global _atual
    _atual = cod if cod in IDIOMAS else PADRAO


def detectar_idioma_do_windows():
    """Idioma da interface do Windows: português -> pt, espanhol -> es, outros -> en."""
    try:
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except Exception:
        return PADRAO
    return idioma_do_langid(langid)


def idioma_do_langid(langid):
    """0x0416 = português (Brasil), 0x0816 = português (Portugal), 0x0C0A = espanhol (Espanha),
    0x080A = espanhol (México) etc. Só o idioma principal (10 bits de baixo) importa."""
    return {0x16: 'pt', 0x0A: 'es'}.get(langid & 0x3FF, PADRAO)


def ler_config():
    """Preferências do usuário (idioma, tema). Devolve {} se não houver."""
    try:
        with open(ARQUIVO_PREF, encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        return {}


def salvar_config(**valores):
    """Grava só os valores passados, mantendo os outros."""
    cfg = ler_config()
    cfg.update(valores)
    try:
        os.makedirs(os.path.dirname(ARQUIVO_PREF), exist_ok=True)
        with open(ARQUIVO_PREF, 'w', encoding='utf-8') as f:
            json.dump(cfg, f)
    except OSError:
        pass  # sem preferência salva, o programa só detecta de novo na próxima vez


def carregar_preferencia():
    cod = ler_config().get('idioma')
    return cod if cod in IDIOMAS else None


def salvar_preferencia(cod):
    salvar_config(idioma=cod)


def iniciar():
    definir(carregar_preferencia() or detectar_idioma_do_windows())


def t(id_texto, /, **campos):
    texto = TEXTOS[_atual].get(id_texto)
    if texto is None:
        texto = TEXTOS['pt'][id_texto]
    return texto.format(**campos) if campos else texto


def tamanho(n_bytes):
    """Ex.: 13,1 MB (vírgula em português/espanhol, ponto em inglês)."""
    texto = f'{n_bytes / 1048576:.1f} MB'
    return texto if _atual == 'en' else texto.replace('.', ',')


def sem_icone(texto):
    """'💾  Fazer backup' -> 'Fazer backup' (para citar um botão dentro de um texto)."""
    partes = texto.split('  ', 1)
    if len(partes) == 2 and not partes[0][:1].isalnum():
        return partes[1]
    return texto


def data(dt):
    return dt.strftime(t('formato_data'))


def data_hora(dt, segundos=False):
    return dt.strftime(t('formato_data') + ' ' + ('%H:%M:%S' if segundos else '%H:%M'))


TEXTOS = {
    # =====================================================================
    'pt': {
        'formato_data': '%d/%m/%Y',
        'titulo_janela': 'ResetMissionsCOTW - Reset de Missões por Mapa  v{versao}',

        # faixa do Acesso Controlado a Pastas
        'faixa_bloqueio': '⚠  O Windows está bloqueando este programa de gravar na pasta Documentos '
                          '(proteção "Acesso Controlado a Pastas").\n'
                          'Libere o programa para poder resetar ou restaurar. Enquanto isso, nada é alterado.',
        'faixa_erro': '⚠  Não consegui gravar na pasta Documentos ({erro}).\n'
                      'Enquanto isso não for resolvido, o programa não altera nada.',
        'bt_como_liberar': 'Como liberar (passo a passo)',
        'bt_abrir_seguranca': 'Abrir a Segurança do Windows',
        'bt_copiar_caminho': 'Copiar caminho do programa',
        'bt_testar_de_novo': 'Já liberei, testar de novo',
        'dica_copiar': 'Dica: o botão "Copiar caminho do programa" copia o caminho acima; na janela de escolher '
                       'o aplicativo, cole na caixa "Nome" e clique em Abrir.',
        'nao_abriu_seguranca': 'Não consegui abrir sozinho. Procure "Segurança do Windows" no menu Iniciar.',
        'caminho_copiado': 'Caminho copiado:\n\n{caminho}',
        'tudo_certo': 'Tudo certo! O programa já consegue gravar. Pode usar normalmente.',
        'ainda_bloqueado': 'Ainda está bloqueado. Confira se adicionou o programa certo:\n\n{caminho}',
        'msg_acesso_controlado':
            'O Windows bloqueou a gravação na pasta Documentos.\n\n'
            'Isso costuma ser o "Acesso Controlado a Pastas" (proteção contra ransomware do Windows Defender). '
            'Para liberar este programa:\n\n'
            '1. Abra "Segurança do Windows" (procure no menu Iniciar).\n'
            '2. Clique em "Proteção contra vírus e ameaças".\n'
            '3. Em "Proteção contra ransomware", clique em "Gerenciar proteção contra ransomware".\n'
            '4. Clique em "Permitir um aplicativo pelo Acesso Controlado a Pastas" e depois em "Sim".\n'
            '5. Clique em "Adicionar um aplicativo permitido" > "Procurar todos os aplicativos" e escolha:\n'
            '{exe}\n\n'
            'Importante: a liberação vale para o programa NESSE local. Se você mover o programa para outra '
            'pasta, precisa liberar de novo. Não rode o programa de dentro de um arquivo .zip: extraia antes.',
        'nada_alterado': 'Nada foi alterado no seu save.',
        'detalhe_tecnico': 'Detalhe técnico: {erro}',
        'erro_ao_gravar': 'Erro ao gravar:\n\n{erro}',

        # topo
        'rotulo_plataforma': 'Plataforma:',
        'plat_outra': 'Outra',
        'rotulo_save': 'Save:',
        'bt_escolher_pasta': 'Escolher pasta...',
        'bt_procurar': 'Procurar de novo',
        'radio_nenhum': '{plat} (nenhum save encontrado)',
        'radio_um': '{plat} (1 save)',
        'radio_varios': '{plat} ({n} saves)',
        'aviso_varios_saves': '⚠  Há {n} saves da {plat} neste PC. O mais recente já vem escolhido; '
                              'confira na lista "Save" se é o seu antes de resetar.',
        'aviso_outra_plataforma': 'Este PC também tem save da {plat}. Para usar, troque em "Plataforma".',
        'nao_encontrei_save': 'Não encontrei o save automaticamente. Clique em "Escolher pasta..." e aponte a '
                              'pasta que tem o arquivo missions_missiondata_adf.',
        'titulo_escolher_pasta': 'Escolha a pasta do save (a que tem missions_missiondata_adf)',
        'pasta_sem_arquivo': 'Essa pasta não tem o arquivo {arquivo}.',
        'pasta_slots': 'Essa é uma pasta "slots" (cópia de segurança do próprio jogo). Escolha a pasta '
                       'principal do save, uma acima de "slots".',
        'nao_li_save': 'Não consegui ler o save: {erro}',
        'steam_cloud_ativo': 'Steam Cloud ativo',
        'n_backups': '{n} backup(s) de missões',
        'nenhum_backup_ainda': 'Nenhum backup de missões ainda',
        'n_backups_save': '{n} backup(s) do save completo',
        'nenhum_backup_save': '⚠ Nenhum backup do save completo ainda',
        'data_desconhecida': 'data desconhecida',
        'jogado_em': 'jogado em {quando}',
        'save_descricao': 'Conta {id}  —  {quando}   ({pasta})',
        'save_nome_curto': '{plat} - conta {id} ({quando})',

        # lista de mapas
        'col_mapa': 'Mapa',
        'col_concluidas': 'Missões concluídas',
        'col_andamento': 'Em andamento',
        'col_total': 'Total',
        'sufixo_resetado': 'Missões resetadas',
        'mapa_desconhecido': 'Mapa desconhecido (chave {chave})',
        'dica_selecao': 'Selecione um mapa (ou vários, segurando Ctrl) e clique em "Resetar missões".',
        'bt_resetar': 'Resetar missões do(s) mapa(s) selecionado(s)',
        'bt_restaurar': 'Restaurar backup de missões...',
        'bt_abrir_pasta': 'Abrir pasta',
        'rotulo_linha_missoes': 'Missões:',
        'rotulo_linha_save': 'Save completo:',
        'bt_backup_save': '💾  Fazer backup do save completo',
        'bt_restaurar_save': 'Restaurar save completo...',
        'como_funciona': 'Como funciona: as missões do mapa escolhido são apagadas do save. Na próxima vez que '
                         'você entrar nesse mapa, o jogo cria as missões do zero. Os outros mapas não mudam. Um '
                         'backup é feito automaticamente antes de qualquer alteração.\n'
                         'Antes de usar: feche o jogo. Se usar Steam Cloud ou Epic Cloud e aparecer um aviso de '
                         'conflito ao abrir o jogo, escolha a versão LOCAL (deste computador).',
        'credito': 'Criado por {autor}   •   versão {versao}',
        'bt_apoiar': '☕  Apoiar o projeto',
        'bt_tema_escuro': '🌙  Tema escuro',
        'bt_tema_claro': '☀  Tema claro',

        # reset
        'aviso_usar_faixa': 'O Windows está bloqueando o programa. Use os botões da faixa amarela no topo da '
                            'janela para liberar.',
        'jogo_aberto': 'O theHunter: Call of the Wild está aberto.\n\nFeche o jogo completamente e tente de novo.',
        'nenhum_save_escolhido': 'Nenhum save escolhido.',
        'selecione_mapa': 'Selecione na lista o mapa que você quer resetar.',
        'ja_resetados': 'As missões desse(s) mapa(s) já estão resetadas. O jogo cria as missões do zero quando '
                        'você entrar no mapa.',
        'linha_detalhe': '  • {nome}: {c} concluídas, {a} em andamento, {t} no total',
        'ignorados': '(Ignorado(s), já resetado(s): {nomes})',
        'confirmar_reset': 'Save: {save}\n\nResetar TODAS as missões de:\n\n{detalhes}\n\n'
                           'O progresso das missões desse(s) mapa(s) será perdido. Os outros mapas não mudam.\n'
                           'Um backup será feito antes, e você pode desfazer em "Restaurar backup de missões...".\n\n'
                           'Continuar?',
        'nao_foi_possivel_resetar': 'Não foi possível resetar.\n\n{texto}\n\nO save não foi alterado.',
        'reset_ok': 'Pronto! Missões resetadas:\n\n{nomes}\n\n'
                    'Foi feito um backup do save anterior. Para desfazer, use "Restaurar backup de missões...".\n\n'
                    'Ao entrar nesse mapa no jogo, as missões vão começar do zero.',
        'sem_backups': 'Ainda não existe nenhum backup deste save.',
        'sem_backups_explica': 'Ainda não existe nenhum backup deste save.\n\n'
                               'O programa cria um backup automaticamente antes de cada reset.',

        # restaurar
        'rest_titulo': 'Restaurar backup de missões',
        'rest_intro': 'Cada backup é uma cópia do seu save de missões, feita automaticamente antes de um reset ou '
                      'de uma restauração. Restaurar devolve o progresso de missões de TODOS os mapas para como '
                      'estava naquele momento.',
        'rest_passo1': '1. Escolha o backup (o mais recente está em cima):',
        'col_data': 'Data',
        'col_hora': 'Hora',
        'col_motivo': 'Motivo do backup',
        'rest_passo2': '2. Confira como cada mapa vai ficar (linhas amarelas são as que vão mudar):',
        'col_agora': 'Agora',
        'col_depois': 'Depois de restaurar',
        'bt_restaurar_este': '3. Restaurar este backup',
        'bt_abrir_pasta_backup': 'Abrir pasta deste backup',
        'bt_fechar': 'Fechar',
        'txt_sem_missoes': 'sem missões no save',
        'txt_resetado': 'resetado (0 de {t})',
        'txt_progresso': '{c} de {t} concluídas, {a} em and.',
        'backup_ilegivel': 'Este backup não pôde ser lido: {erro}',
        'nenhum_muda': 'Nenhum mapa muda: este backup é igual ao save atual.',
        'n_mudam': '{n} mapa(s) vão mudar se você restaurar este backup.',
        'confirmar_restaurar': 'Save: {save}\n\nRestaurar o backup de {quando}?\n({titulo})\n\n'
                               'As missões de todos os mapas voltam a ficar como na coluna "Depois de restaurar".\n'
                               'O save atual também é guardado num backup antes, então dá para voltar atrás.',
        'nao_foi_possivel_restaurar': 'Não foi possível restaurar.\n\n{texto}',
        'backup_restaurado': 'Backup restaurado.',
        'titulo_reset': 'Antes de resetar {nomes}',
        'titulo_restauracao': 'Antes de restaurar o backup de {quando}',
        'titulo_backup': 'Backup',

        # apoio
        'apoio_titulo': 'Apoiar o projeto',
        'apoio_pergunta': '☕  Gostou do programa?',
        'apoio_texto': 'O {programa} é gratuito, feito por um jogador para a comunidade de '
                       'theHunter: Call of the Wild.\n\n'
                       'Se ele te ajudou e você quiser apoiar o desenvolvimento, qualquer valor é bem-vindo. '
                       'Obrigado!',
        'em_breve': '(em breve)',

        # erros do arquivo
        'erro_jogo_aberto': 'O jogo está aberto. Feche o theHunter: Call of the Wild e tente de novo.',
        'erro_mapa_ausente': 'O mapa {mapa} não tem missões neste save.',
        'erro_incompleto': 'O arquivo de missões está incompleto.',
        'erro_tabela': 'A tabela de mapas do arquivo está corrompida ou num formato inesperado (código {codigo}).',
        'erro_nao_e_save': 'Este arquivo não parece um save de missões do COTW.',
        'erro_descompactar': 'Não consegui descompactar o arquivo de missões (ele pode estar corrompido).',
        'erro_tamanho': 'O tamanho registrado no arquivo não confere com o conteúdo.',
        'erro_formato': 'O conteúdo do arquivo não está no formato esperado.',
        'erro_conferencia': 'A conferência de segurança falhou: o arquivo gerado não ficou como esperado '
                            '(código {codigo}). Nada foi alterado.',
        'erro_backup_diferente': 'O backup não ficou igual ao original. Nada foi alterado.',
        'erro_pos_gravacao': 'Depois de gravar, o arquivo não está igual ao esperado. Use "Restaurar backup de missões...".',

        # pasta do programa
        # backup do save completo
        'erro_copia_save': 'A cópia do save não ficou igual ao original. Nada foi alterado.',
        'erro_backup_save_invalido': 'Este backup do save completo está incompleto ou danificado.',
        'erro_pasta_em_uso': 'Não consegui trocar a pasta do save (talvez ela esteja aberta no Explorador de '
                             'Arquivos ou em outro programa). Feche e tente de novo. O save continua como estava.'
                             '\n\nDetalhe técnico: {erro}',
        'titulo_save_manual': 'Backup feito por você',
        'titulo_save_antes_restaurar': 'Antes de restaurar o save de {quando}',
        'titulo_save_sobra': 'Save anterior guardado de uma restauração interrompida',
        'erro_desfazer_falhou': 'A restauração falhou no meio e o programa não conseguiu desfazê-la sozinho.\n\n'
                                'O seu save anterior NÃO foi perdido: ele está guardado nesta pasta:\n{pasta}\n\n'
                                'Não apague essa pasta. Feche Steam, OneDrive e o Explorador de Arquivos e abra '
                                'o programa de novo: ele guarda essa pasta como backup automaticamente.\n\n'
                                'Detalhe técnico: {erro}',
        'backup_protegido': '🔒 o mais antigo, nunca é apagado',
        'limite_backups': 'São guardados até {n} backups. Passando disso, o mais antigo é apagado sozinho, menos '
                          'o primeiro (🔒), que é sempre mantido.',
        'backup_save_ok': 'Backup do save completo criado!\n\n{arquivos} arquivos ({tamanho}).\n\n{pasta}',
        'nao_foi_possivel_backup_save': 'Não foi possível fazer o backup do save completo.\n\n{texto}',
        'sugerir_backup_save': 'Este save ainda não tem nenhum backup completo.\n\n'
                               'Antes de alterar o save, recomendamos fazer um backup completo: ele guarda TODOS os '
                               'arquivos do save, não só as missões.\n\n'
                               'Sim: fazer o backup completo agora e continuar.\n'
                               'Não: continuar sem o backup completo.\n'
                               'Cancelar: voltar.',
        'sem_backups_save': 'Ainda não existe nenhum backup do save completo.\n\n'
                            'Use o botão "{bt}" para criar um.',
        'rest_save_titulo': 'Restaurar save completo',
        'rest_save_intro': 'Cada backup completo é uma cópia da pasta INTEIRA do save (missões, animais, armas, '
                           'dinheiro, troféus, tudo). Restaurar devolve o save inteiro para como estava naquele '
                           'momento: todo o progresso feito depois disso, em qualquer parte do jogo, será perdido.\n'
                           'Antes de restaurar, o save atual também é guardado num backup completo, então dá para '
                           'voltar atrás.',
        'col_tamanho': 'Tamanho',
        'bt_restaurar_save_este': 'Restaurar este backup',
        'confirmar_restaurar_save': 'Save: {save}\n\nRestaurar o save COMPLETO do backup de {quando}?\n({titulo})\n\n'
                                    'TODOS os arquivos do save voltam a ficar como naquele momento, não só as '
                                    'missões. O save atual é guardado num backup completo antes.',
        'save_restaurado': 'Save completo restaurado.',
        'nome_instrucoes_save': 'COMO RESTAURAR MANUALMENTE.txt',
        'instrucoes_save': 'COMO RESTAURAR O SAVE COMPLETO MANUALMENTE\n'
                           '==========================================\n\n'
                           'O jeito mais fácil é usar o botão "Restaurar save completo..." do programa.\n'
                           'Se preferir fazer à mão:\n\n'
                           '1. Feche o jogo (e, se possível, o Steam ou o Epic Games Launcher).\n'
                           '2. Escolha, nesta pasta, o backup que quer devolver. O nome de cada um tem a data e a hora.\n'
                           '3. Dentro dele, abra a pasta "{subpasta}". Ela é uma cópia da pasta inteira do seu save.\n'
                           '4. Por segurança, renomeie a pasta do save atual (por exemplo, acrescente "_antigo" no fim\n'
                           '   do nome). A pasta do save é:\n'
                           '   {pasta_jogo}\n'
                           '5. Copie a pasta "{subpasta}" do backup para o mesmo lugar e renomeie-a com o nome original\n'
                           '   da pasta do save (o número da conta).\n'
                           '6. Abra o jogo. Se aparecer um aviso de conflito na nuvem (Steam Cloud / Epic Cloud),\n'
                           '   escolha a versão LOCAL.\n'
                           '7. Se tudo estiver certo, pode apagar a pasta "_antigo".\n',

        # aviso da primeira vez
        'aviso_titulo': '⚠  Antes de começar',
        'aviso_texto': 'Este programa foi criado por um jogador, de forma independente. Ele é gratuito e de código '
                       'aberto: {link}\n\n'
                       'Ele NÃO é oficial e pode ter falhas. Por isso, antes de qualquer alteração no save, '
                       'recomendamos fazer o backup completo do save usando a opção "{bt_backup}" do próprio '
                       'programa.\n\n'
                       'O programa altera SOMENTE o progresso das missões dos mapas que você escolher. Ele não altera '
                       'perfil, dinheiro, habilidades, vantagens, armas, animais, troféus nem nada além disso.',
        'link_em_breve': '(o link do GitHub será adicionado em breve)',
        'aviso_entendi': 'Entendi',

        # introdução
        'bt_ajuda': '❔  Como usar',
        'intro_titulo': 'Como usar',
        'intro_pular': 'Pular',
        'intro_voltar': '←  Voltar',
        'intro_proximo': 'Próximo  →',
        'intro_comecar': 'Começar!',
        'intro_pagina': '{n} de {total}',
        'intro_titulo_1': 'Bem-vindo ao ResetMissionsCOTW!',
        'intro_texto_1': 'Este programa reseta as missões de UM mapa do theHunter: Call of the Wild, sem mexer no '
                         'progresso dos outros mapas.\n\n'
                         'No jogo, a única forma de resetar as missões apaga as de TODOS os mapas. Aqui você escolhe '
                         'qual mapa quer recomeçar.\n\n'
                         'Veja em 1 minuto como usar, ou clique em "Pular".',
        'intro_titulo_2': 'Escolha o seu save',
        'intro_texto_2': 'No topo da janela:\n\n'
                         '•  Plataforma: escolha Steam ou Epic.\n'
                         '•  Save: a conta daquela plataforma. O save jogado mais recentemente já vem escolhido.\n'
                         '•  {procurar}: procura os saves de novo.\n'
                         '•  {escolher_pasta}: use se o programa não encontrar o seu save sozinho.',
        'intro_titulo_3': 'A lista de mapas',
        'intro_texto_3': 'Para cada mapa, a lista mostra quantas missões estão concluídas, quantas estão em andamento '
                         'e o total.\n\n'
                         'Mapas em verde, com "{resetadas}", já foram resetados: as missões deles começam do zero '
                         'quando você entrar no mapa no jogo.',
        'intro_titulo_4': 'Resetar missões',
        'intro_texto_4': '1.  Feche o jogo.\n'
                         '2.  Clique no mapa que quer recomeçar (segure Ctrl para escolher vários).\n'
                         '3.  Clique em "{resetar}" e confirme.\n'
                         '4.  Abra o jogo e entre no mapa: as missões começam do zero.\n\n'
                         'Um backup das missões é feito sozinho antes de cada reset. Se usar Steam Cloud ou Epic Cloud '
                         'e aparecer um aviso de conflito ao abrir o jogo, escolha a versão LOCAL.',
        'intro_titulo_5': 'Backups: sua rede de segurança',
        'intro_texto_5': '•  {backup_save}: guarda uma cópia do save INTEIRO. Recomendado antes de usar o programa '
                         'pela primeira vez.\n'
                         '•  {restaurar_save}: devolve o save inteiro a partir de um backup completo.\n'
                         '•  {restaurar}: desfaz um reset, devolvendo só as missões. As linhas amarelas mostram o '
                         'que vai mudar antes de você confirmar.\n'
                         '•  {abrir_pasta}: abre a pasta onde ficam as cópias.\n\n'
                         'São guardados até {limite_missoes} backups de missões e {limite_save} do save completo. '
                         'O mais antigo de cada tipo nunca é apagado.',
        'intro_titulo_6': 'Detalhes no rodapé',
        'intro_texto_6': 'Na parte de baixo da janela:\n\n'
                         '•  🌐 Idioma: português, inglês ou espanhol.\n'
                         '•  {tema_escuro} / {tema_claro}: muda as cores da janela.\n'
                         '•  {apoiar}: se quiser ajudar o desenvolvimento.\n'
                         '•  {ajuda}: mostra esta introdução de novo quando quiser.\n\n'
                         'Boa caçada!',

        # verificação antes de começar
        'verif_titulo': 'Verificação antes de começar',
        'verif_explicacao': 'Para evitar erros e perda de progresso, o programa confere se algum programa pode '
                            'atrapalhar a edição do save. Programas como Steam, Epic, OneDrive e Google Drive podem '
                            'estar usando ou sincronizando os arquivos ao mesmo tempo. Isso pode bloquear a alteração '
                            'ou sobrescrever o save com uma versão antiga da nuvem.\n'
                            'Esta verificação acontece só no seu computador: nada é enviado para a internet.',
        'verif_tudo_pronto': '✔  Tudo pronto: nada deve atrapalhar.',
        'verif_impede': '⛔  Precisa resolver',
        'verif_atencao': '⚠  Atenção',
        'status_ok': '✔ Verificação: tudo pronto',
        'status_avisos': '⚠ Verificação: {n} aviso(s)',
        'status_impede': '⛔ Verificação: {n} problema(s) impede(m) alterações',
        'bt_ver_verificacao': 'Ver verificação',
        'bt_verificar_de_novo': 'Verificar de novo',
        'bt_continuar': 'Continuar',
        'bt_continuar_mesmo_assim': 'Continuar mesmo assim',
        'bt_cancelar': 'Cancelar',
        'confirmar_continuar_risco': 'Continuar mesmo assim pode fazer a alteração falhar ou ser desfeita pela '
                                     'nuvem.\n\nO programa sempre faz backup antes e desfaz tudo se algo der errado '
                                     'no meio, mas o risco existe.\n\nContinuar?',
        'item_jogo': 'O jogo está aberto. Feche o jogo normalmente (pelo menu do jogo) e clique em "Verificar de '
                     'novo".',
        'item_em_uso': 'Arquivos do save estão sendo usados por: {programa}. Feche esse programa e clique em '
                       '"Verificar de novo".',
        'item_somente_leitura': '{n} arquivo(s)/pasta(s) do save ou dos backups estão marcados como "somente '
                                'leitura". Isso pode impedir a troca ou a limpeza dos arquivos.',
        'item_nuvem': 'A pasta do save fica dentro do {servico}. Ele pode bloquear arquivos enquanto sincroniza ou '
                      'trazer de volta uma versão antiga.',
        'item_steam': 'O Steam está aberto. Normalmente não atrapalha, mas o Steam Cloud pode sincronizar o save '
                      'quando o jogo abre ou fecha.',
        'item_epic': 'O Epic Games Launcher está aberto. A Epic Cloud pode sincronizar o save.',
        'item_onedrive': 'O OneDrive está aberto e pode estar sincronizando os arquivos.',
        'item_googledrive': 'O Google Drive está aberto e pode estar sincronizando os arquivos.',
        'item_dropbox': 'O Dropbox está aberto e pode estar sincronizando os arquivos.',
        'bt_fechar_steam': 'Fechar Steam',
        'bt_fechar_epic': 'Fechar Epic',
        'bt_fechar_onedrive': 'Fechar OneDrive',
        'bt_reabrir_onedrive': 'Reabrir OneDrive',
        'bt_fechar_googledrive': 'Fechar Google Drive',
        'bt_fechar_dropbox': 'Fechar Dropbox',
        'bt_corrigir': 'Corrigir',
        'fechando': 'Fechando {programa}… aguarde.',
        'nao_fechou': '{programa} não fechou sozinho. Clique no ícone dele perto do relógio do Windows (canto '
                      'inferior direito) e escolha "Sair".',
        'nao_achei_programa': 'Não encontrei o {programa} para fechá-lo. Feche-o pelo ícone perto do relógio do '
                              'Windows.',
        'corrigidos': 'Marcação "somente leitura" retirada de {n} item(ns). O conteúdo dos arquivos não mudou.',
        'perguntar_reabrir_onedrive': 'O OneDrive foi fechado pela verificação. Quer abri-lo de novo agora, para a '
                                      'sincronização continuar?',
        'aviso_limpeza_falhou': '⚠ {n} backup(s) antigo(s) não puderam ser apagados agora. Isso não atrapalha o '
                                'uso; o programa tenta de novo depois (detalhes no log).',
        'aviso_sobra_guardada': 'Foi encontrada uma pasta temporária de uma restauração anterior. Ela foi guardada '
                                'como backup completo ("{titulo}").',
        'aviso_sobra_falhou': '⚠ Uma pasta temporária de uma restauração anterior não pôde ser guardada agora '
                              '(detalhes no log). Isso não impede o uso.',

        # erros e log
        'erro_titulo': 'Algo deu errado',
        'erro_causa_encontrada': 'Causa encontrada:',
        'erro_causas_possiveis': 'Causas possíveis:',
        'bt_copiar_detalhes': 'Copiar detalhes',
        'detalhes_copiados': 'Detalhes copiados. Cole (Ctrl+V) no seu relato ou na "Issue" do GitHub.',
        'bt_logs': '📄  Logs',
        'bt_abrir_pasta_logs': 'Abrir pasta de logs',
        'sem_logs': 'Ainda não há logs.',
        'causa_somente_leitura': 'O arquivo ou pasta está marcado como "somente leitura": {caminho}',
        'causa_em_uso': 'O arquivo ou pasta está sendo usado por: {programas}',
        'causa_nuvem': 'A pasta fica dentro do {servico}, que pode estar sincronizando ou bloqueando os arquivos.',
        'causa_cfa_confirmado': 'O Windows Defender registrou um bloqueio deste programa ("Acesso Controlado a '
                                'Pastas").',
        'causa_cfa_possivel': 'O "Acesso Controlado a Pastas" do Windows Defender está ligado e pode ter bloqueado '
                              'a gravação.',
        'causa_desconhecida': 'Outro programa pode ter segurado os arquivos por alguns instantes (OneDrive, Steam, '
                              'antivírus ou o Explorador de Arquivos). Feche-os e tente de novo.',
        'faixa_erro_causa': '⚠  Não consegui gravar na pasta Documentos. {causa}\n'
                            'Enquanto isso não for resolvido, o programa não altera nada.',

        'nome_leia_me': 'LEIA-ME.txt',
        'leia_me_pasta': 'Pasta do programa "ResetMissionsCOTW - Reset de Missões por Mapa".\n\n'
                         'Aqui ficam os backups automáticos do arquivo de missões (missions_missiondata_adf),\n'
                         'feitos antes de cada reset ou restauração, separados por save.\n\n'
                         'Para devolver um backup, use o botão "Restaurar backup de missões..." do programa.\n'
                         'Se preferir fazer à mão: feche o jogo e copie o arquivo missions_missiondata_adf\n'
                         'de dentro da pasta do backup para a pasta do save do jogo.\n\n'
                         'Esta pasta fica oculta para não atrapalhar sua pasta Documentos.\n'
                         'Pode apagar backups antigos, se quiser.\n',
    },

    # =====================================================================
    'en': {
        'formato_data': '%m/%d/%Y',
        'titulo_janela': 'ResetMissionsCOTW - Per-Map Mission Reset  v{versao}',

        'faixa_bloqueio': '⚠  Windows is blocking this program from writing to the Documents folder '
                          '("Controlled folder access" protection).\n'
                          'Allow the program to be able to reset or restore. Until then, nothing is changed.',
        'faixa_erro': '⚠  Could not write to the Documents folder ({erro}).\n'
                      'Until this is solved, the program does not change anything.',
        'bt_como_liberar': 'How to allow it (step by step)',
        'bt_abrir_seguranca': 'Open Windows Security',
        'bt_copiar_caminho': 'Copy program path',
        'bt_testar_de_novo': 'Done, test again',
        'dica_copiar': 'Tip: the "Copy program path" button copies the path above; in the window for choosing '
                       'the app, paste it into the "File name" box and click Open.',
        'nao_abriu_seguranca': 'Could not open it automatically. Search for "Windows Security" in the Start menu.',
        'caminho_copiado': 'Path copied:\n\n{caminho}',
        'tudo_certo': 'All set! The program can write now. You can use it normally.',
        'ainda_bloqueado': 'Still blocked. Check that you added the right program:\n\n{caminho}',
        'msg_acesso_controlado':
            'Windows blocked writing to the Documents folder.\n\n'
            'This is usually "Controlled folder access" (Windows Defender ransomware protection). '
            'To allow this program:\n\n'
            '1. Open "Windows Security" (search for it in the Start menu).\n'
            '2. Click "Virus & threat protection".\n'
            '3. Under "Ransomware protection", click "Manage ransomware protection".\n'
            '4. Click "Allow an app through Controlled folder access", then "Yes".\n'
            '5. Click "Add an allowed app" > "Browse all apps" and choose:\n'
            '{exe}\n\n'
            'Important: the permission is for the program in THIS location. If you move the program to another '
            'folder, you need to allow it again. Do not run the program from inside a .zip file: extract it first.',
        'nada_alterado': 'Nothing was changed in your save.',
        'detalhe_tecnico': 'Technical detail: {erro}',
        'erro_ao_gravar': 'Error while writing:\n\n{erro}',

        'rotulo_plataforma': 'Platform:',
        'plat_outra': 'Other',
        'rotulo_save': 'Save:',
        'bt_escolher_pasta': 'Choose folder...',
        'bt_procurar': 'Search again',
        'radio_nenhum': '{plat} (no save found)',
        'radio_um': '{plat} (1 save)',
        'radio_varios': '{plat} ({n} saves)',
        'aviso_varios_saves': '⚠  There are {n} {plat} saves on this PC. The most recent one is already selected; '
                              'check in the "Save" list that it is yours before resetting.',
        'aviso_outra_plataforma': 'This PC also has a save on {plat}. To use it, switch in "Platform".',
        'nao_encontrei_save': 'Could not find the save automatically. Click "Choose folder..." and select the '
                              'folder that has the missions_missiondata_adf file.',
        'titulo_escolher_pasta': 'Choose the save folder (the one with missions_missiondata_adf)',
        'pasta_sem_arquivo': 'This folder does not have the {arquivo} file.',
        'pasta_slots': 'This is a "slots" folder (the game\'s own backup copy). Choose the main save folder, one '
                       'level above "slots".',
        'nao_li_save': 'Could not read the save: {erro}',
        'steam_cloud_ativo': 'Steam Cloud on',
        'n_backups': '{n} missions backup(s)',
        'nenhum_backup_ainda': 'No missions backups yet',
        'n_backups_save': '{n} full save backup(s)',
        'nenhum_backup_save': '⚠ No full save backup yet',
        'data_desconhecida': 'unknown date',
        'jogado_em': 'played on {quando}',
        'save_descricao': 'Account {id}  —  {quando}   ({pasta})',
        'save_nome_curto': '{plat} - account {id} ({quando})',

        'col_mapa': 'Map',
        'col_concluidas': 'Completed missions',
        'col_andamento': 'In progress',
        'col_total': 'Total',
        'sufixo_resetado': 'Missions reset',
        'mapa_desconhecido': 'Unknown map (key {chave})',
        'dica_selecao': 'Select a map (or several, holding Ctrl) and click "Reset missions".',
        'bt_resetar': 'Reset missions of the selected map(s)',
        'bt_restaurar': 'Restore missions backup...',
        'bt_abrir_pasta': 'Open folder',
        'rotulo_linha_missoes': 'Missions:',
        'rotulo_linha_save': 'Full save:',
        'bt_backup_save': '💾  Back up the full save',
        'bt_restaurar_save': 'Restore full save...',
        'como_funciona': 'How it works: the missions of the chosen map are removed from the save. The next time '
                         'you enter that map, the game creates its missions from scratch. Other maps do not '
                         'change. A backup is made automatically before any change.\n'
                         'Before using: close the game. If you use Steam Cloud or Epic Cloud and a sync conflict '
                         'warning shows up when opening the game, choose the LOCAL version (this computer).',
        'credito': 'Created by {autor}   •   version {versao}',
        'bt_apoiar': '☕  Support the project',
        'bt_tema_escuro': '🌙  Dark theme',
        'bt_tema_claro': '☀  Light theme',

        'aviso_usar_faixa': 'Windows is blocking the program. Use the buttons in the yellow bar at the top of '
                            'the window to allow it.',
        'jogo_aberto': 'theHunter: Call of the Wild is open.\n\nClose the game completely and try again.',
        'nenhum_save_escolhido': 'No save selected.',
        'selecione_mapa': 'Select the map you want to reset in the list.',
        'ja_resetados': 'The missions of this map (these maps) are already reset. The game creates the missions '
                        'from scratch when you enter the map.',
        'linha_detalhe': '  • {nome}: {c} completed, {a} in progress, {t} in total',
        'ignorados': '(Skipped, already reset: {nomes})',
        'confirmar_reset': 'Save: {save}\n\nReset ALL missions of:\n\n{detalhes}\n\n'
                           'The mission progress of this map (these maps) will be lost. Other maps do not change.\n'
                           'A backup is made first, and you can undo it with "Restore missions backup...".\n\n'
                           'Continue?',
        'nao_foi_possivel_resetar': 'Could not reset.\n\n{texto}\n\nThe save was not changed.',
        'reset_ok': 'Done! Missions reset:\n\n{nomes}\n\n'
                    'A backup of the previous save was made. To undo, use "Restore missions backup...".\n\n'
                    'When you enter this map in the game, its missions will start from scratch.',
        'sem_backups': 'There are no backups of this save yet.',
        'sem_backups_explica': 'There are no backups of this save yet.\n\n'
                               'The program makes a backup automatically before each reset.',

        'rest_titulo': 'Restore missions backup',
        'rest_intro': 'Each backup is a copy of your missions save, made automatically before a reset or a '
                      'restore. Restoring brings the mission progress of ALL maps back to how it was at that '
                      'moment.',
        'rest_passo1': '1. Choose the backup (the most recent is at the top):',
        'col_data': 'Date',
        'col_hora': 'Time',
        'col_motivo': 'Backup reason',
        'rest_passo2': '2. Check how each map will look (yellow rows are the ones that will change):',
        'col_agora': 'Now',
        'col_depois': 'After restoring',
        'bt_restaurar_este': '3. Restore this backup',
        'bt_abrir_pasta_backup': 'Open this backup\'s folder',
        'bt_fechar': 'Close',
        'txt_sem_missoes': 'no missions in the save',
        'txt_resetado': 'reset (0 of {t})',
        'txt_progresso': '{c} of {t} completed, {a} in prog.',
        'backup_ilegivel': 'This backup could not be read: {erro}',
        'nenhum_muda': 'No map changes: this backup is the same as the current save.',
        'n_mudam': '{n} map(s) will change if you restore this backup.',
        'confirmar_restaurar': 'Save: {save}\n\nRestore the backup from {quando}?\n({titulo})\n\n'
                               'The missions of all maps go back to the "After restoring" column.\n'
                               'The current save is also backed up first, so you can go back.',
        'nao_foi_possivel_restaurar': 'Could not restore.\n\n{texto}',
        'backup_restaurado': 'Backup restored.',
        'titulo_reset': 'Before resetting {nomes}',
        'titulo_restauracao': 'Before restoring the backup from {quando}',
        'titulo_backup': 'Backup',

        'apoio_titulo': 'Support the project',
        'apoio_pergunta': '☕  Enjoying the program?',
        'apoio_texto': '{programa} is free, made by a player for the theHunter: Call of the Wild community.\n\n'
                       'If it helped you and you would like to support its development, any amount is welcome. '
                       'Thank you!',
        'em_breve': '(coming soon)',

        'erro_jogo_aberto': 'The game is open. Close theHunter: Call of the Wild and try again.',
        'erro_mapa_ausente': 'The map {mapa} has no missions in this save.',
        'erro_incompleto': 'The missions file is incomplete.',
        'erro_tabela': 'The map table in the file is corrupted or in an unexpected format (code {codigo}).',
        'erro_nao_e_save': 'This file does not look like a COTW missions save.',
        'erro_descompactar': 'Could not decompress the missions file (it may be corrupted).',
        'erro_tamanho': 'The size recorded in the file does not match its content.',
        'erro_formato': 'The file content is not in the expected format.',
        'erro_conferencia': 'The safety check failed: the generated file is not as expected (code {codigo}). '
                            'Nothing was changed.',
        'erro_backup_diferente': 'The backup does not match the original. Nothing was changed.',
        'erro_pos_gravacao': 'After writing, the file is not as expected. Use "Restore missions backup...".',

        'erro_copia_save': 'The save copy does not match the original. Nothing was changed.',
        'erro_backup_save_invalido': 'This full save backup is incomplete or damaged.',
        'erro_pasta_em_uso': 'Could not swap the save folder (it may be open in File Explorer or in another '
                             'program). Close it and try again. The save is unchanged.'
                             '\n\nTechnical detail: {erro}',
        'titulo_save_manual': 'Backup made by you',
        'titulo_save_antes_restaurar': 'Before restoring the save from {quando}',
        'titulo_save_sobra': 'Previous save kept from an interrupted restore',
        'erro_desfazer_falhou': 'The restore failed halfway and the program could not undo it by itself.\n\n'
                                'Your previous save was NOT lost: it is kept in this folder:\n{pasta}\n\n'
                                'Do not delete that folder. Close Steam, OneDrive and File Explorer and open the '
                                'program again: it keeps that folder as a backup automatically.\n\n'
                                'Technical detail: {erro}',
        'backup_protegido': '🔒 the oldest, never deleted',
        'limite_backups': 'Up to {n} backups are kept. Beyond that, the oldest one is deleted automatically, except '
                          'the first one (🔒), which is always kept.',
        'backup_save_ok': 'Full save backup created!\n\n{arquivos} files ({tamanho}).\n\n{pasta}',
        'nao_foi_possivel_backup_save': 'Could not back up the full save.\n\n{texto}',
        'sugerir_backup_save': 'This save has no full backup yet.\n\n'
                               'Before changing the save, we recommend making a full backup: it keeps ALL the save '
                               'files, not just the missions.\n\n'
                               'Yes: make the full backup now and continue.\n'
                               'No: continue without the full backup.\n'
                               'Cancel: go back.',
        'sem_backups_save': 'There is no full save backup yet.\n\n'
                            'Use the "{bt}" button to create one.',
        'rest_save_titulo': 'Restore full save',
        'rest_save_intro': 'Each full backup is a copy of the ENTIRE save folder (missions, animals, weapons, money, '
                           'trophies, everything). Restoring brings the whole save back to how it was at that moment: '
                           'all progress made after that, in any part of the game, will be lost.\n'
                           'Before restoring, the current save is also kept in a full backup, so you can go back.',
        'col_tamanho': 'Size',
        'bt_restaurar_save_este': 'Restore this backup',
        'confirmar_restaurar_save': 'Save: {save}\n\nRestore the FULL save from the backup of {quando}?\n({titulo})\n\n'
                                    'ALL save files go back to how they were at that moment, not just the missions. '
                                    'The current save is kept in a full backup first.',
        'save_restaurado': 'Full save restored.',
        'nome_instrucoes_save': 'HOW TO RESTORE MANUALLY.txt',
        'instrucoes_save': 'HOW TO RESTORE THE FULL SAVE MANUALLY\n'
                           '======================================\n\n'
                           'The easiest way is the program\'s "Restore full save..." button.\n'
                           'If you prefer to do it by hand:\n\n'
                           '1. Close the game (and, if possible, Steam or the Epic Games Launcher).\n'
                           '2. In this folder, choose the backup you want to bring back. Each name has the date and time.\n'
                           '3. Inside it, open the "{subpasta}" folder. It is a copy of your entire save folder.\n'
                           '4. To be safe, rename the current save folder (for example, add "_old" to the end of the\n'
                           '   name). The save folder is:\n'
                           '   {pasta_jogo}\n'
                           '5. Copy the "{subpasta}" folder from the backup to the same place and rename it to the\n'
                           '   original name of the save folder (the account number).\n'
                           '6. Open the game. If a cloud conflict warning shows up (Steam Cloud / Epic Cloud),\n'
                           '   choose the LOCAL version.\n'
                           '7. If everything is fine, you can delete the "_old" folder.\n',

        'aviso_titulo': '⚠  Before you start',
        'aviso_texto': 'This program was made by a player, independently. It is free and open source: {link}\n\n'
                       'It is NOT official and it may have bugs. So, before any change to your save, we recommend '
                       'making a full backup of the save using the program\'s own "{bt_backup}" option.\n\n'
                       'The program changes ONLY the mission progress of the maps you choose. It does not change your '
                       'profile, money, skills, perks, weapons, animals, trophies or anything else.',
        'link_em_breve': '(the GitHub link will be added soon)',
        'aviso_entendi': 'Got it',

        'bt_ajuda': '❔  How to use',
        'intro_titulo': 'How to use',
        'intro_pular': 'Skip',
        'intro_voltar': '←  Back',
        'intro_proximo': 'Next  →',
        'intro_comecar': 'Let\'s go!',
        'intro_pagina': '{n} of {total}',
        'intro_titulo_1': 'Welcome to ResetMissionsCOTW!',
        'intro_texto_1': 'This program resets the missions of ONE map in theHunter: Call of the Wild, without '
                         'touching the progress of the other maps.\n\n'
                         'In the game, the only way to reset missions resets the missions of ALL maps. Here you '
                         'choose which map you want to start over.\n\n'
                         'See how to use it in 1 minute, or click "Skip".',
        'intro_titulo_2': 'Choose your save',
        'intro_texto_2': 'At the top of the window:\n\n'
                         '•  Platform: choose Steam or Epic.\n'
                         '•  Save: the account on that platform. The most recently played save is already selected.\n'
                         '•  {procurar}: looks for the saves again.\n'
                         '•  {escolher_pasta}: use it if the program cannot find your save by itself.',
        'intro_titulo_3': 'The map list',
        'intro_texto_3': 'For each map, the list shows how many missions are completed, how many are in progress '
                         'and the total.\n\n'
                         'Green maps, marked "{resetadas}", have already been reset: their missions start from '
                         'scratch when you enter the map in the game.',
        'intro_titulo_4': 'Reset missions',
        'intro_texto_4': '1.  Close the game.\n'
                         '2.  Click the map you want to start over (hold Ctrl to choose several).\n'
                         '3.  Click "{resetar}" and confirm.\n'
                         '4.  Open the game and enter the map: its missions start from scratch.\n\n'
                         'A missions backup is made automatically before each reset. If you use Steam Cloud or Epic '
                         'Cloud and a conflict warning shows up when opening the game, choose the LOCAL version.',
        'intro_titulo_5': 'Backups: your safety net',
        'intro_texto_5': '•  {backup_save}: keeps a copy of the ENTIRE save. Recommended before using the program '
                         'for the first time.\n'
                         '•  {restaurar_save}: brings the entire save back from a full backup.\n'
                         '•  {restaurar}: undoes a reset, bringing back only the missions. The yellow rows show what '
                         'will change before you confirm.\n'
                         '•  {abrir_pasta}: opens the folder where the copies are kept.\n\n'
                         'Up to {limite_missoes} missions backups and {limite_save} full save backups are kept. '
                         'The oldest of each type is never deleted.',
        'intro_titulo_6': 'Footer details',
        'intro_texto_6': 'At the bottom of the window:\n\n'
                         '•  🌐 Language: Portuguese, English or Spanish.\n'
                         '•  {tema_escuro} / {tema_claro}: changes the window colors.\n'
                         '•  {apoiar}: if you would like to help the development.\n'
                         '•  {ajuda}: shows this introduction again whenever you want.\n\n'
                         'Happy hunting!',

        'verif_titulo': 'Check before you start',
        'verif_explicacao': 'To avoid errors and lost progress, the program checks whether another program could '
                            'interfere with editing the save. Programs such as Steam, Epic, OneDrive and Google Drive '
                            'may be using or syncing the files at the same time. This can block the change or '
                            'overwrite the save with an old version from the cloud.\n'
                            'This check happens only on your computer: nothing is sent to the internet.',
        'verif_tudo_pronto': '✔  All set: nothing should get in the way.',
        'verif_impede': '⛔  Needs fixing',
        'verif_atencao': '⚠  Heads-up',
        'status_ok': '✔ Check: all set',
        'status_avisos': '⚠ Check: {n} warning(s)',
        'status_impede': '⛔ Check: {n} problem(s) blocking changes',
        'bt_ver_verificacao': 'View check',
        'bt_verificar_de_novo': 'Check again',
        'bt_continuar': 'Continue',
        'bt_continuar_mesmo_assim': 'Continue anyway',
        'bt_cancelar': 'Cancel',
        'confirmar_continuar_risco': 'Continuing anyway may make the change fail or be undone by the cloud.\n\n'
                                     'The program always makes a backup first and undoes everything if something '
                                     'goes wrong halfway, but the risk exists.\n\nContinue?',
        'item_jogo': 'The game is open. Close the game normally (from the game menu) and click "Check again".',
        'item_em_uso': 'Save files are being used by: {programa}. Close that program and click "Check again".',
        'item_somente_leitura': '{n} file(s)/folder(s) of the save or of the backups are marked as "read-only". '
                                'This can prevent swapping or cleaning up the files.',
        'item_nuvem': 'The save folder is inside {servico}. It may lock files while syncing or bring back an old '
                      'version.',
        'item_steam': 'Steam is open. It usually does not interfere, but Steam Cloud may sync the save when the game '
                      'opens or closes.',
        'item_epic': 'Epic Games Launcher is open. Epic Cloud may sync the save.',
        'item_onedrive': 'OneDrive is open and may be syncing the files.',
        'item_googledrive': 'Google Drive is open and may be syncing the files.',
        'item_dropbox': 'Dropbox is open and may be syncing the files.',
        'bt_fechar_steam': 'Close Steam',
        'bt_fechar_epic': 'Close Epic',
        'bt_fechar_onedrive': 'Close OneDrive',
        'bt_reabrir_onedrive': 'Reopen OneDrive',
        'bt_fechar_googledrive': 'Close Google Drive',
        'bt_fechar_dropbox': 'Close Dropbox',
        'bt_corrigir': 'Fix',
        'fechando': 'Closing {programa}… please wait.',
        'nao_fechou': '{programa} did not close by itself. Click its icon near the Windows clock (bottom right '
                      'corner) and choose "Quit"/"Exit".',
        'nao_achei_programa': 'Could not find {programa} to close it. Close it from its icon near the Windows clock.',
        'corrigidos': '"Read-only" mark removed from {n} item(s). The file contents did not change.',
        'perguntar_reabrir_onedrive': 'OneDrive was closed by the check. Do you want to open it again now, so '
                                      'syncing continues?',
        'aviso_limpeza_falhou': '⚠ {n} old backup(s) could not be deleted right now. This does not affect use; the '
                                'program tries again later (details in the log).',
        'aviso_sobra_guardada': 'A temporary folder from a previous restore was found. It was kept as a full backup '
                                '("{titulo}").',
        'aviso_sobra_falhou': '⚠ A temporary folder from a previous restore could not be kept right now (details in '
                              'the log). This does not prevent use.',

        'erro_titulo': 'Something went wrong',
        'erro_causa_encontrada': 'Cause found:',
        'erro_causas_possiveis': 'Possible causes:',
        'bt_copiar_detalhes': 'Copy details',
        'detalhes_copiados': 'Details copied. Paste them (Ctrl+V) into your report or GitHub "Issue".',
        'bt_logs': '📄  Logs',
        'bt_abrir_pasta_logs': 'Open logs folder',
        'sem_logs': 'There are no logs yet.',
        'causa_somente_leitura': 'The file or folder is marked as "read-only": {caminho}',
        'causa_em_uso': 'The file or folder is being used by: {programas}',
        'causa_nuvem': 'The folder is inside {servico}, which may be syncing or locking the files.',
        'causa_cfa_confirmado': 'Windows Defender recorded a block of this program ("Controlled folder access").',
        'causa_cfa_possivel': 'Windows Defender "Controlled folder access" is on and may have blocked writing.',
        'causa_desconhecida': 'Another program may have held the files for a few moments (OneDrive, Steam, '
                              'antivirus or File Explorer). Close them and try again.',
        'faixa_erro_causa': '⚠  Could not write to the Documents folder. {causa}\n'
                            'Until this is solved, the program does not change anything.',

        'nome_leia_me': 'README.txt',
        'leia_me_pasta': 'Folder of the program "ResetMissionsCOTW - Per-Map Mission Reset".\n\n'
                         'This is where the automatic backups of the missions file (missions_missiondata_adf)\n'
                         'are kept, made before each reset or restore, separated by save.\n\n'
                         'To bring a backup back, use the program\'s "Restore missions backup..." button.\n'
                         'If you prefer to do it by hand: close the game and copy the missions_missiondata_adf\n'
                         'file from inside the backup folder into the game\'s save folder.\n\n'
                         'This folder is hidden so it does not clutter your Documents folder.\n'
                         'You may delete old backups if you want.\n',
    },

    # =====================================================================
    'es': {
        'formato_data': '%d/%m/%Y',
        'titulo_janela': 'ResetMissionsCOTW - Reinicio de Misiones por Mapa  v{versao}',

        'faixa_bloqueio': '⚠  Windows está bloqueando que este programa escriba en la carpeta Documentos '
                          '(protección "Acceso controlado a carpetas").\n'
                          'Permite el programa para poder reiniciar o restaurar. Mientras tanto, no se cambia nada.',
        'faixa_erro': '⚠  No se pudo escribir en la carpeta Documentos ({erro}).\n'
                      'Hasta que se resuelva, el programa no cambia nada.',
        'bt_como_liberar': 'Cómo permitirlo (paso a paso)',
        'bt_abrir_seguranca': 'Abrir Seguridad de Windows',
        'bt_copiar_caminho': 'Copiar ruta del programa',
        'bt_testar_de_novo': 'Ya lo permití, probar de nuevo',
        'dica_copiar': 'Consejo: el botón "Copiar ruta del programa" copia la ruta de arriba; en la ventana para '
                       'elegir la aplicación, pégala en el cuadro "Nombre" y haz clic en Abrir.',
        'nao_abriu_seguranca': 'No se pudo abrir automáticamente. Busca "Seguridad de Windows" en el menú Inicio.',
        'caminho_copiado': 'Ruta copiada:\n\n{caminho}',
        'tudo_certo': '¡Listo! El programa ya puede escribir. Puedes usarlo normalmente.',
        'ainda_bloqueado': 'Sigue bloqueado. Comprueba que agregaste el programa correcto:\n\n{caminho}',
        'msg_acesso_controlado':
            'Windows bloqueó la escritura en la carpeta Documentos.\n\n'
            'Suele ser el "Acceso controlado a carpetas" (protección contra ransomware de Windows Defender). '
            'Para permitir este programa:\n\n'
            '1. Abre "Seguridad de Windows" (búscalo en el menú Inicio).\n'
            '2. Haz clic en "Protección antivirus y contra amenazas".\n'
            '3. En "Protección contra ransomware", haz clic en "Administrar la protección contra ransomware".\n'
            '4. Haz clic en "Permitir una aplicación a través de Acceso controlado a carpetas" y luego en "Sí".\n'
            '5. Haz clic en "Agregar una aplicación permitida" > "Examinar todas las aplicaciones" y elige:\n'
            '{exe}\n\n'
            'Importante: el permiso vale para el programa en ESTA ubicación. Si mueves el programa a otra '
            'carpeta, tendrás que permitirlo de nuevo. No ejecutes el programa desde dentro de un archivo .zip: '
            'extráelo antes.',
        'nada_alterado': 'No se cambió nada en tu partida guardada.',
        'detalhe_tecnico': 'Detalle técnico: {erro}',
        'erro_ao_gravar': 'Error al escribir:\n\n{erro}',

        'rotulo_plataforma': 'Plataforma:',
        'plat_outra': 'Otra',
        'rotulo_save': 'Partida:',
        'bt_escolher_pasta': 'Elegir carpeta...',
        'bt_procurar': 'Buscar de nuevo',
        'radio_nenhum': '{plat} (no se encontró partida)',
        'radio_um': '{plat} (1 partida)',
        'radio_varios': '{plat} ({n} partidas)',
        'aviso_varios_saves': '⚠  Hay {n} partidas de {plat} en este PC. La más reciente ya está elegida; '
                              'comprueba en la lista "Partida" que es la tuya antes de reiniciar.',
        'aviso_outra_plataforma': 'Este PC también tiene una partida de {plat}. Para usarla, cambia en "Plataforma".',
        'nao_encontrei_save': 'No se encontró la partida automáticamente. Haz clic en "Elegir carpeta..." y elige '
                              'la carpeta que tiene el archivo missions_missiondata_adf.',
        'titulo_escolher_pasta': 'Elige la carpeta de la partida (la que tiene missions_missiondata_adf)',
        'pasta_sem_arquivo': 'Esta carpeta no tiene el archivo {arquivo}.',
        'pasta_slots': 'Esta es una carpeta "slots" (copia de seguridad del propio juego). Elige la carpeta '
                       'principal de la partida, un nivel por encima de "slots".',
        'nao_li_save': 'No se pudo leer la partida: {erro}',
        'steam_cloud_ativo': 'Steam Cloud activado',
        'n_backups': '{n} copia(s) de misiones',
        'nenhum_backup_ainda': 'Todavía no hay copias de misiones',
        'n_backups_save': '{n} copia(s) de la partida completa',
        'nenhum_backup_save': '⚠ Todavía no hay copia de la partida completa',
        'data_desconhecida': 'fecha desconocida',
        'jogado_em': 'jugada el {quando}',
        'save_descricao': 'Cuenta {id}  —  {quando}   ({pasta})',
        'save_nome_curto': '{plat} - cuenta {id} ({quando})',

        'col_mapa': 'Mapa',
        'col_concluidas': 'Misiones completadas',
        'col_andamento': 'En curso',
        'col_total': 'Total',
        'sufixo_resetado': 'Misiones reiniciadas',
        'mapa_desconhecido': 'Mapa desconocido (clave {chave})',
        'dica_selecao': 'Selecciona un mapa (o varios, manteniendo Ctrl) y haz clic en "Reiniciar misiones".',
        'bt_resetar': 'Reiniciar misiones de los mapas seleccionados',
        'bt_restaurar': 'Restaurar copia de misiones...',
        'bt_abrir_pasta': 'Abrir carpeta',
        'rotulo_linha_missoes': 'Misiones:',
        'rotulo_linha_save': 'Partida completa:',
        'bt_backup_save': '💾  Copia de seguridad de la partida completa',
        'bt_restaurar_save': 'Restaurar partida completa...',
        'como_funciona': 'Cómo funciona: las misiones del mapa elegido se borran de la partida. La próxima vez que '
                         'entres en ese mapa, el juego crea las misiones desde cero. Los demás mapas no cambian. '
                         'Se hace una copia de seguridad automáticamente antes de cualquier cambio.\n'
                         'Antes de usarlo: cierra el juego. Si usas Steam Cloud o Epic Cloud y aparece un aviso de '
                         'conflicto al abrir el juego, elige la versión LOCAL (de este equipo).',
        'credito': 'Creado por {autor}   •   versión {versao}',
        'bt_apoiar': '☕  Apoyar el proyecto',
        'bt_tema_escuro': '🌙  Tema oscuro',
        'bt_tema_claro': '☀  Tema claro',

        'aviso_usar_faixa': 'Windows está bloqueando el programa. Usa los botones de la barra amarilla en la '
                            'parte superior de la ventana para permitirlo.',
        'jogo_aberto': 'theHunter: Call of the Wild está abierto.\n\nCierra el juego por completo e inténtalo de nuevo.',
        'nenhum_save_escolhido': 'No hay ninguna partida elegida.',
        'selecione_mapa': 'Selecciona en la lista el mapa que quieres reiniciar.',
        'ja_resetados': 'Las misiones de este(s) mapa(s) ya están reiniciadas. El juego crea las misiones desde '
                        'cero cuando entres en el mapa.',
        'linha_detalhe': '  • {nome}: {c} completadas, {a} en curso, {t} en total',
        'ignorados': '(Omitido(s), ya reiniciado(s): {nomes})',
        'confirmar_reset': 'Partida: {save}\n\n¿Reiniciar TODAS las misiones de estos mapas?\n\n{detalhes}\n\n'
                           'Se perderá el progreso de las misiones de este(s) mapa(s). Los demás mapas no cambian.\n'
                           'Antes se hace una copia de seguridad, y puedes deshacerlo en "Restaurar copia de '
                           'misiones...".\n\n¿Continuar?',
        'nao_foi_possivel_resetar': 'No se pudo reiniciar.\n\n{texto}\n\nLa partida no se modificó.',
        'reset_ok': '¡Listo! Misiones reiniciadas:\n\n{nomes}\n\n'
                    'Se hizo una copia de seguridad de las misiones anteriores. Para deshacerlo, usa "Restaurar copia '
                    'de misiones...".\n\n'
                    'Al entrar en ese mapa en el juego, las misiones empezarán desde cero.',
        'sem_backups': 'Todavía no hay copias de seguridad de esta partida.',
        'sem_backups_explica': 'Todavía no hay copias de seguridad de esta partida.\n\n'
                               'El programa hace una copia automáticamente antes de cada reinicio.',

        'rest_titulo': 'Restaurar copia de misiones',
        'rest_intro': 'Cada copia de seguridad es una copia de tu archivo de misiones, hecha automáticamente antes '
                      'de un reinicio o de una restauración. Restaurar devuelve el progreso de misiones de TODOS '
                      'los mapas a como estaba en ese momento.',
        'rest_passo1': '1. Elige la copia de seguridad (la más reciente está arriba):',
        'col_data': 'Fecha',
        'col_hora': 'Hora',
        'col_motivo': 'Motivo de la copia',
        'rest_passo2': '2. Comprueba cómo quedará cada mapa (las filas amarillas son las que cambiarán):',
        'col_agora': 'Ahora',
        'col_depois': 'Después de restaurar',
        'bt_restaurar_este': '3. Restaurar esta copia',
        'bt_abrir_pasta_backup': 'Abrir carpeta de esta copia',
        'bt_fechar': 'Cerrar',
        'txt_sem_missoes': 'sin misiones en la partida',
        'txt_resetado': 'reiniciado (0 de {t})',
        'txt_progresso': '{c} de {t} completadas, {a} en curso',
        'backup_ilegivel': 'No se pudo leer esta copia: {erro}',
        'nenhum_muda': 'Ningún mapa cambia: esta copia es igual a la partida actual.',
        'n_mudam': '{n} mapa(s) cambiarán si restauras esta copia.',
        'confirmar_restaurar': 'Partida: {save}\n\n¿Restaurar la copia del {quando}?\n({titulo})\n\n'
                               'Las misiones de todos los mapas vuelven a quedar como en la columna "Después de '
                               'restaurar".\nAntes también se guarda una copia de la partida actual, así que '
                               'puedes volver atrás.',
        'nao_foi_possivel_restaurar': 'No se pudo restaurar.\n\n{texto}',
        'backup_restaurado': 'Copia de seguridad restaurada.',
        'titulo_reset': 'Antes de reiniciar {nomes}',
        'titulo_restauracao': 'Antes de restaurar la copia del {quando}',
        'titulo_backup': 'Copia de seguridad',

        'apoio_titulo': 'Apoyar el proyecto',
        'apoio_pergunta': '☕  ¿Te gustó el programa?',
        'apoio_texto': '{programa} es gratuito, hecho por un jugador para la comunidad de '
                       'theHunter: Call of the Wild.\n\n'
                       'Si te ayudó y quieres apoyar su desarrollo, cualquier cantidad es bienvenida. ¡Gracias!',
        'em_breve': '(próximamente)',

        'erro_jogo_aberto': 'El juego está abierto. Cierra theHunter: Call of the Wild e inténtalo de nuevo.',
        'erro_mapa_ausente': 'El mapa {mapa} no tiene misiones en esta partida.',
        'erro_incompleto': 'El archivo de misiones está incompleto.',
        'erro_tabela': 'La tabla de mapas del archivo está dañada o en un formato inesperado (código {codigo}).',
        'erro_nao_e_save': 'Este archivo no parece una partida de misiones de COTW.',
        'erro_descompactar': 'No se pudo descomprimir el archivo de misiones (puede estar dañado).',
        'erro_tamanho': 'El tamaño registrado en el archivo no coincide con su contenido.',
        'erro_formato': 'El contenido del archivo no tiene el formato esperado.',
        'erro_conferencia': 'La comprobación de seguridad falló: el archivo generado no quedó como se esperaba '
                            '(código {codigo}). No se cambió nada.',
        'erro_backup_diferente': 'La copia de seguridad no quedó igual al original. No se cambió nada.',
        'erro_pos_gravacao': 'Después de escribir, el archivo no quedó como se esperaba. Usa "Restaurar copia de '
                             'misiones...".',

        'erro_copia_save': 'La copia de la partida no quedó igual al original. No se cambió nada.',
        'erro_backup_save_invalido': 'Esta copia de la partida completa está incompleta o dañada.',
        'erro_pasta_em_uso': 'No se pudo cambiar la carpeta de la partida (quizá esté abierta en el Explorador de '
                             'archivos o en otro programa). Ciérrala e inténtalo de nuevo. La partida sigue como '
                             'estaba.\n\nDetalle técnico: {erro}',
        'titulo_save_manual': 'Copia hecha por ti',
        'titulo_save_antes_restaurar': 'Antes de restaurar la partida del {quando}',
        'titulo_save_sobra': 'Partida anterior guardada de una restauración interrumpida',
        'erro_desfazer_falhou': 'La restauración falló a medias y el programa no pudo deshacerla solo.\n\n'
                                'Tu partida anterior NO se perdió: está guardada en esta carpeta:\n{pasta}\n\n'
                                'No borres esa carpeta. Cierra Steam, OneDrive y el Explorador de archivos y vuelve '
                                'a abrir el programa: guardará esa carpeta como copia de seguridad automáticamente.'
                                '\n\nDetalle técnico: {erro}',
        'backup_protegido': '🔒 la más antigua, nunca se borra',
        'limite_backups': 'Se guardan hasta {n} copias. A partir de ahí, la más antigua se borra sola, excepto la '
                          'primera (🔒), que siempre se conserva.',
        'backup_save_ok': '¡Copia de la partida completa creada!\n\n{arquivos} archivos ({tamanho}).\n\n{pasta}',
        'nao_foi_possivel_backup_save': 'No se pudo hacer la copia de la partida completa.\n\n{texto}',
        'sugerir_backup_save': 'Esta partida todavía no tiene ninguna copia completa.\n\n'
                               'Antes de modificar la partida, te recomendamos hacer una copia completa: guarda TODOS '
                               'los archivos de la partida, no solo las misiones.\n\n'
                               'Sí: hacer la copia completa ahora y continuar.\n'
                               'No: continuar sin la copia completa.\n'
                               'Cancelar: volver.',
        'sem_backups_save': 'Todavía no hay ninguna copia de la partida completa.\n\n'
                            'Usa el botón "{bt}" para crear una.',
        'rest_save_titulo': 'Restaurar partida completa',
        'rest_save_intro': 'Cada copia completa es una copia de la carpeta ENTERA de la partida (misiones, animales, '
                           'armas, dinero, trofeos, todo). Restaurar devuelve la partida entera a como estaba en ese '
                           'momento: se perderá todo el progreso hecho después, en cualquier parte del juego.\n'
                           'Antes de restaurar, la partida actual también se guarda en una copia completa, así que '
                           'puedes volver atrás.',
        'col_tamanho': 'Tamaño',
        'bt_restaurar_save_este': 'Restaurar esta copia',
        'confirmar_restaurar_save': 'Partida: {save}\n\n¿Restaurar la partida COMPLETA de la copia del {quando}?\n'
                                    '({titulo})\n\n'
                                    'TODOS los archivos de la partida vuelven a como estaban en ese momento, no solo '
                                    'las misiones. Antes se guarda una copia completa de la partida actual.',
        'save_restaurado': 'Partida completa restaurada.',
        'nome_instrucoes_save': 'CÓMO RESTAURAR MANUALMENTE.txt',
        'instrucoes_save': 'CÓMO RESTAURAR LA PARTIDA COMPLETA MANUALMENTE\n'
                           '===============================================\n\n'
                           'Lo más fácil es usar el botón "Restaurar partida completa..." del programa.\n'
                           'Si prefieres hacerlo a mano:\n\n'
                           '1. Cierra el juego (y, si puedes, Steam o Epic Games Launcher).\n'
                           '2. En esta carpeta, elige la copia que quieres devolver. Cada nombre tiene la fecha y la hora.\n'
                           '3. Dentro de ella, abre la carpeta "{subpasta}". Es una copia de la carpeta entera de tu partida.\n'
                           '4. Por seguridad, cambia el nombre de la carpeta de la partida actual (por ejemplo, añade\n'
                           '   "_antigua" al final del nombre). La carpeta de la partida es:\n'
                           '   {pasta_jogo}\n'
                           '5. Copia la carpeta "{subpasta}" de la copia al mismo lugar y ponle el nombre original de la\n'
                           '   carpeta de la partida (el número de la cuenta).\n'
                           '6. Abre el juego. Si aparece un aviso de conflicto en la nube (Steam Cloud / Epic Cloud),\n'
                           '   elige la versión LOCAL.\n'
                           '7. Si todo está bien, puedes borrar la carpeta "_antigua".\n',

        'aviso_titulo': '⚠  Antes de empezar',
        'aviso_texto': 'Este programa fue creado por un jugador, de forma independiente. Es gratuito y de código '
                       'abierto: {link}\n\n'
                       'NO es oficial y puede tener fallos. Por eso, antes de cualquier cambio en la partida, te '
                       'recomendamos hacer una copia de seguridad de la partida completa con la opción "{bt_backup}" '
                       'del propio programa.\n\n'
                       'El programa modifica SOLO el progreso de las misiones de los mapas que elijas. No modifica el '
                       'perfil, el dinero, las habilidades, las ventajas, las armas, los animales, los trofeos ni nada más.',
        'link_em_breve': '(el enlace de GitHub se añadirá pronto)',
        'aviso_entendi': 'Entendido',

        'bt_ajuda': '❔  Cómo usar',
        'intro_titulo': 'Cómo usar',
        'intro_pular': 'Omitir',
        'intro_voltar': '←  Atrás',
        'intro_proximo': 'Siguiente  →',
        'intro_comecar': '¡Empezar!',
        'intro_pagina': '{n} de {total}',
        'intro_titulo_1': '¡Bienvenido a ResetMissionsCOTW!',
        'intro_texto_1': 'Este programa reinicia las misiones de UN mapa de theHunter: Call of the Wild, sin tocar el '
                         'progreso de los demás mapas.\n\n'
                         'En el juego, la única forma de reiniciar las misiones reinicia las de TODOS los mapas. Aquí '
                         'eliges qué mapa quieres empezar de nuevo.\n\n'
                         'Mira cómo usarlo en 1 minuto, o haz clic en "Omitir".',
        'intro_titulo_2': 'Elige tu partida',
        'intro_texto_2': 'En la parte superior de la ventana:\n\n'
                         '•  Plataforma: elige Steam o Epic.\n'
                         '•  Partida: la cuenta de esa plataforma. La partida jugada más recientemente ya viene elegida.\n'
                         '•  {procurar}: busca las partidas de nuevo.\n'
                         '•  {escolher_pasta}: úsalo si el programa no encuentra tu partida solo.',
        'intro_titulo_3': 'La lista de mapas',
        'intro_texto_3': 'Para cada mapa, la lista muestra cuántas misiones están completadas, cuántas están en curso '
                         'y el total.\n\n'
                         'Los mapas en verde, con "{resetadas}", ya se reiniciaron: sus misiones empiezan desde cero '
                         'cuando entres en el mapa en el juego.',
        'intro_titulo_4': 'Reiniciar misiones',
        'intro_texto_4': '1.  Cierra el juego.\n'
                         '2.  Haz clic en el mapa que quieres empezar de nuevo (mantén Ctrl para elegir varios).\n'
                         '3.  Haz clic en "{resetar}" y confirma.\n'
                         '4.  Abre el juego y entra en el mapa: las misiones empiezan desde cero.\n\n'
                         'Antes de cada reinicio se hace sola una copia de las misiones. Si usas Steam Cloud o Epic '
                         'Cloud y aparece un aviso de conflicto al abrir el juego, elige la versión LOCAL.',
        'intro_titulo_5': 'Copias de seguridad: tu red de seguridad',
        'intro_texto_5': '•  {backup_save}: guarda una copia de la partida ENTERA. Recomendado antes de usar el '
                         'programa por primera vez.\n'
                         '•  {restaurar_save}: devuelve la partida entera desde una copia completa.\n'
                         '•  {restaurar}: deshace un reinicio, devolviendo solo las misiones. Las filas amarillas '
                         'muestran lo que cambiará antes de que confirmes.\n'
                         '•  {abrir_pasta}: abre la carpeta donde se guardan las copias.\n\n'
                         'Se guardan hasta {limite_missoes} copias de misiones y {limite_save} de la partida completa. '
                         'La más antigua de cada tipo nunca se borra.',
        'intro_titulo_6': 'Detalles en la parte inferior',
        'intro_texto_6': 'En la parte de abajo de la ventana:\n\n'
                         '•  🌐 Idioma: portugués, inglés o español.\n'
                         '•  {tema_escuro} / {tema_claro}: cambia los colores de la ventana.\n'
                         '•  {apoiar}: si quieres ayudar al desarrollo.\n'
                         '•  {ajuda}: muestra esta introducción de nuevo cuando quieras.\n\n'
                         '¡Buena caza!',

        'verif_titulo': 'Comprobación antes de empezar',
        'verif_explicacao': 'Para evitar errores y pérdida de progreso, el programa comprueba si algún programa puede '
                            'estorbar la edición de la partida. Programas como Steam, Epic, OneDrive y Google Drive '
                            'pueden estar usando o sincronizando los archivos al mismo tiempo. Eso puede bloquear el '
                            'cambio o sobrescribir la partida con una versión antigua de la nube.\n'
                            'Esta comprobación ocurre solo en tu equipo: no se envía nada a internet.',
        'verif_tudo_pronto': '✔  Todo listo: nada debería estorbar.',
        'verif_impede': '⛔  Hay que resolverlo',
        'verif_atencao': '⚠  Atención',
        'status_ok': '✔ Comprobación: todo listo',
        'status_avisos': '⚠ Comprobación: {n} aviso(s)',
        'status_impede': '⛔ Comprobación: {n} problema(s) impide(n) cambios',
        'bt_ver_verificacao': 'Ver comprobación',
        'bt_verificar_de_novo': 'Comprobar de nuevo',
        'bt_continuar': 'Continuar',
        'bt_continuar_mesmo_assim': 'Continuar de todas formas',
        'bt_cancelar': 'Cancelar',
        'confirmar_continuar_risco': 'Continuar de todas formas puede hacer que el cambio falle o que la nube lo '
                                     'deshaga.\n\nEl programa siempre hace una copia antes y lo deshace todo si algo '
                                     'sale mal a medias, pero el riesgo existe.\n\n¿Continuar?',
        'item_jogo': 'El juego está abierto. Ciérralo normalmente (desde el menú del juego) y haz clic en "Comprobar '
                     'de nuevo".',
        'item_em_uso': 'Archivos de la partida están siendo usados por: {programa}. Cierra ese programa y haz clic '
                       'en "Comprobar de nuevo".',
        'item_somente_leitura': '{n} archivo(s)/carpeta(s) de la partida o de las copias están marcados como "solo '
                                'lectura". Eso puede impedir cambiar o limpiar los archivos.',
        'item_nuvem': 'La carpeta de la partida está dentro de {servico}. Puede bloquear archivos mientras sincroniza '
                      'o traer de vuelta una versión antigua.',
        'item_steam': 'Steam está abierto. Normalmente no estorba, pero Steam Cloud puede sincronizar la partida al '
                      'abrir o cerrar el juego.',
        'item_epic': 'Epic Games Launcher está abierto. Epic Cloud puede sincronizar la partida.',
        'item_onedrive': 'OneDrive está abierto y puede estar sincronizando los archivos.',
        'item_googledrive': 'Google Drive está abierto y puede estar sincronizando los archivos.',
        'item_dropbox': 'Dropbox está abierto y puede estar sincronizando los archivos.',
        'bt_fechar_steam': 'Cerrar Steam',
        'bt_fechar_epic': 'Cerrar Epic',
        'bt_fechar_onedrive': 'Cerrar OneDrive',
        'bt_reabrir_onedrive': 'Reabrir OneDrive',
        'bt_fechar_googledrive': 'Cerrar Google Drive',
        'bt_fechar_dropbox': 'Cerrar Dropbox',
        'bt_corrigir': 'Corregir',
        'fechando': 'Cerrando {programa}… espera.',
        'nao_fechou': '{programa} no se cerró solo. Haz clic en su icono cerca del reloj de Windows (esquina inferior '
                      'derecha) y elige "Salir".',
        'nao_achei_programa': 'No se encontró {programa} para cerrarlo. Ciérralo desde su icono cerca del reloj de '
                              'Windows.',
        'corrigidos': 'Se quitó la marca "solo lectura" de {n} elemento(s). El contenido de los archivos no cambió.',
        'perguntar_reabrir_onedrive': 'La comprobación cerró OneDrive. ¿Quieres abrirlo de nuevo ahora para que siga '
                                      'sincronizando?',
        'aviso_limpeza_falhou': '⚠ {n} copia(s) antigua(s) no se pudieron borrar ahora. No afecta el uso; el programa '
                                'lo intenta de nuevo después (detalles en el registro).',
        'aviso_sobra_guardada': 'Se encontró una carpeta temporal de una restauración anterior. Se guardó como copia '
                                'completa ("{titulo}").',
        'aviso_sobra_falhou': '⚠ Una carpeta temporal de una restauración anterior no se pudo guardar ahora (detalles '
                              'en el registro). No impide el uso.',

        'erro_titulo': 'Algo salió mal',
        'erro_causa_encontrada': 'Causa encontrada:',
        'erro_causas_possiveis': 'Causas posibles:',
        'bt_copiar_detalhes': 'Copiar detalles',
        'detalhes_copiados': 'Detalles copiados. Pégalos (Ctrl+V) en tu informe o en la "Issue" de GitHub.',
        'bt_logs': '📄  Registros',
        'bt_abrir_pasta_logs': 'Abrir carpeta de registros',
        'sem_logs': 'Todavía no hay registros.',
        'causa_somente_leitura': 'El archivo o la carpeta está marcado como "solo lectura": {caminho}',
        'causa_em_uso': 'El archivo o la carpeta está siendo usado por: {programas}',
        'causa_nuvem': 'La carpeta está dentro de {servico}, que puede estar sincronizando o bloqueando los archivos.',
        'causa_cfa_confirmado': 'Windows Defender registró un bloqueo de este programa ("Acceso controlado a '
                                'carpetas").',
        'causa_cfa_possivel': 'El "Acceso controlado a carpetas" de Windows Defender está activado y puede haber '
                              'bloqueado la escritura.',
        'causa_desconhecida': 'Otro programa puede haber retenido los archivos unos instantes (OneDrive, Steam, '
                              'antivirus o el Explorador de archivos). Ciérralos e inténtalo de nuevo.',
        'faixa_erro_causa': '⚠  No se pudo escribir en la carpeta Documentos. {causa}\n'
                            'Hasta que se resuelva, el programa no cambia nada.',

        'nome_leia_me': 'LEEME.txt',
        'leia_me_pasta': 'Carpeta del programa "ResetMissionsCOTW - Reinicio de Misiones por Mapa".\n\n'
                         'Aquí se guardan las copias de seguridad automáticas del archivo de misiones\n'
                         '(missions_missiondata_adf), hechas antes de cada reinicio o restauración, separadas '
                         'por partida.\n\n'
                         'Para devolver una copia, usa el botón "Restaurar copia de misiones..." del programa.\n'
                         'Si prefieres hacerlo a mano: cierra el juego y copia el archivo missions_missiondata_adf\n'
                         'de dentro de la carpeta de la copia a la carpeta de la partida del juego.\n\n'
                         'Esta carpeta está oculta para no desordenar tu carpeta Documentos.\n'
                         'Puedes borrar copias antiguas si quieres.\n',
    },
}
