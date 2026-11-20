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
        'faixa_erro': '⚠  Não consegui gravar na pasta Documentos ({erro}).\n'
                      'Enquanto isso não for resolvido, o programa não altera nada.',
        'bt_como_liberar': 'Como liberar (passo a passo)',
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
        'bt_apoiar': '☕  Apoiar o projeto',

        # reset
        'jogo_aberto': 'O theHunter: Call of the Wild está aberto.\n\nFeche o jogo completamente e tente de novo.',
        'nenhum_save_escolhido': 'Nenhum save escolhido.',
        'ja_resetados': 'As missões desse(s) mapa(s) já estão resetadas. O jogo cria as missões do zero quando '
                        'você entrar no mapa.',
        'linha_detalhe': '  • {nome}: {c} concluídas, {a} em andamento, {t} no total',
        'ignorados': '(Ignorado(s), já resetado(s): {nomes})',
        'nao_foi_possivel_resetar': 'Não foi possível resetar.\n\n{texto}\n\nO save não foi alterado.',
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
        'intro_voltar': '←  Voltar',
        'intro_proximo': 'Próximo  →',
        'intro_comecar': 'Começar!',
        'intro_pagina': '{n} de {total}',

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

        'nome_leia_me': 'LEIA-ME.txt',
        'leia_me_pasta': 'Pasta do programa "ResetMissionsCOTW - Reset de Missões por Mapa".\n\n'
                         'Aqui ficam os backups automáticos do arquivo de missões (missions_missiondata_adf),\n'
                         'feitos antes de cada reset ou restauração, separados por save.\n\n'
                         'Para devolver um backup, use o botão "Restaurar backup de missões..." do programa.\n'
                         'Se preferir fazer à mão: feche o jogo e copie o arquivo missions_missiondata_adf\n'
                         'de dentro da pasta do backup para a pasta do save do jogo.\n\n'
                         'Esta pasta fica oculta para não atrapalhar sua pasta Documentos.\n'
                         'Pode apagar backups antigos, se quiser.\n',
        # ---- visual novo (0.9.7): janela em 4 passos
        'cabecalho': 'Reset de missões por mapa',
        'link_como_usar': 'Como usar',
        'link_logs': 'Logs',
        'link_detalhes': 'detalhes',
        'bt_tema_escuro': '☾  Tema escuro',
        'bt_tema_claro': '☀  Tema claro',
        'status_ok': '●  Tudo pronto: nada está usando os arquivos do save',
        'status_avisos': '●  {n} aviso(s) antes de começar',
        'status_impede': '●  {n} problema(s) impede(m) alterações',
        'credito': 'Feito por {autor}  ·  v{versao}',
        'pilula_apoiar': 'Gostou? Apoie o projeto',
        'update_disponivel': 'Nova versão disponível: {versao}',
        'link_baixar': 'Baixar',
        'link_agora_nao': 'Agora não',
        'passo1_titulo': 'Escolha o save',
        'passo1_resumo': '{plat}  ·  conta {id}  ·  {quando}',
        'link_trocar': 'Trocar',
        'link_escolher_pasta': 'Escolher pasta',
        'link_procurar': 'Procurar de novo',
        'nao_encontrei_save': 'Não encontrei o save sozinho. Clique em "Escolher pasta" e aponte a pasta que tem o '
                              'arquivo missions_missiondata_adf.',
        'passo2_titulo': 'Faça um backup do save completo',
        'recomendado': '(recomendado)',
        'passo2_sub': 'Guarda uma cópia de TODOS os arquivos do save, não só as missões. Leva poucos segundos.',
        'passo2_feito': 'Backup feito {quando}  ·  {tamanho}',
        'hoje_as': 'hoje às {hora}',
        'ontem_as': 'ontem às {hora}',
        'dia_as': 'em {data} às {hora}',
        'link_fazer_outro': 'Fazer outro',
        'passo3_titulo': 'Escolha os mapas que quer recomeçar',
        'passo3_sub': 'Marque um ou mais. A barra mostra quanto você já avançou nas missões de cada mapa.',
        'passo3_sem_save': 'Escolha um save no passo 1 para ver os mapas.',
        'passo3_vazio': 'Este save ainda não tem missões em nenhum mapa.',
        'mapa_resetado_curto': '↺ resetado',
        'dica_mapa': '{c} concluídas  ·  {a} em andamento  ·  {t} no total',
        'dica_mapa_resetado': 'Missões resetadas ({t} no total). Elas começam do zero quando você entrar nesse mapa '
                              'no jogo.',
        'passo4_titulo': 'Resetar',
        'bt_resetar_nenhum': 'Resetar',
        'bt_resetar_um': 'Resetar 1 mapa',
        'bt_resetar_varios': 'Resetar {n} mapas',
        'passo4_nenhum': 'Marque pelo menos um mapa no passo 3.',
        'passo4_resumo': '{nomes}. Os outros mapas não mudam.',
        'conjuncao_e': ' e ',
        'link_restaurar_missoes': 'Restaurar missões',
        'link_restaurar_save': 'Restaurar save completo',
        'link_pasta_backups': 'Pasta de backups',
        'selecione_mapa': 'Marque na lista (passo 3) o mapa que você quer resetar.',
        'aviso_usar_faixa': 'O Windows está bloqueando o programa. Use o aviso amarelo no topo da janela para '
                            'liberar.',
        'confirmar_reset': 'Save: {save}\n\nResetar TODAS as missões de:\n\n{detalhes}\n\n'
                           'O progresso das missões desse(s) mapa(s) será perdido. Os outros mapas não mudam.\n'
                           'Um backup será feito antes, e você pode desfazer em "Restaurar missões".\n\n'
                           'Continuar?',
        'reset_ok': 'Pronto! Missões resetadas:\n\n{nomes}\n\n'
                    'Agora abra o jogo. Se o Steam Cloud ou a Epic Cloud perguntar qual versão usar, escolha a '
                    'LOCAL (deste computador). Ao entrar nesse mapa, as missões começam do zero.\n\n'
                    'Foi feito um backup antes. Para desfazer, use "Restaurar missões".',
        'erro_pos_gravacao': 'Depois de gravar, o arquivo não está igual ao esperado. Use "Restaurar missões".',

        # faixa e guia do Windows Defender
        'faixa_titulo_cfa': 'O Windows está impedindo o programa de salvar arquivos',
        'faixa_bloqueio': 'A proteção "Acesso Controlado a Pastas" do Windows Defender está bloqueando a pasta '
                          'Documentos, onde fica o seu save. Nada foi alterado. Libere o programa uma vez e pronto: '
                          'leva cerca de 1 minuto.',
        'faixa_titulo_erro': 'Não consegui gravar na pasta Documentos',
        'faixa_erro_causa': '{causa}\nEnquanto isso não for resolvido, o programa não altera nada.',
        'bt_abrir_seguranca': '↗  Abrir a Segurança do Windows',
        'guia_titulo': 'Liberar o programa no Windows Defender',
        'guia_intro': 'Você só precisa fazer isso uma vez. Leva cerca de 1 minuto.',
        'guia_contador': 'PASSO {n} DE {total}',
        'guia_passo_1': 'Abrir a Segurança do Windows',
        'guia_passo_2': 'Proteção contra vírus e ameaças',
        'guia_passo_3': 'Proteção contra ransomware',
        'guia_passo_4': 'Permitir um aplicativo',
        'guia_passo_5': 'Escolher este programa',
        'guia_texto_1': 'Clique em "Abrir a Segurança do Windows", aqui embaixo. Ele já tenta abrir direto na página '
                        'certa (passo 4). Se não abrir, procure "Segurança do Windows" no menu Iniciar.',
        'guia_texto_2': 'Se abriu na tela inicial, clique em "Proteção contra vírus e ameaças" (o ícone de escudo).',
        'guia_texto_3': 'Role a página até "Proteção contra ransomware" e clique em "Gerenciar a proteção contra '
                        'ransomware".',
        'guia_texto_4': 'Em "Acesso controlado a pastas", clique em "Permitir um aplicativo pelo Acesso controlado a '
                        'pastas". Se o Windows perguntar se quer permitir alterações, clique em "Sim".',
        'guia_texto_5': 'Clique em "+ Adicionar um aplicativo permitido" e depois em "Procurar todos os aplicativos". '
                        'Na janela que abrir, cole o caminho abaixo na caixa "Nome" (Ctrl+V) e clique em "Abrir". '
                        'Depois clique em "Já liberei, testar de novo".',
        'guia_caminho': 'Caminho deste programa (para colar no passo 5):',
        'bt_copiar': 'Copiar',
        'copiado': '✓ Copiado! Agora é só colar (Ctrl+V).',
        'win_seguranca': 'Segurança do Windows',
        'win_melhor': 'MELHOR CORRESPONDÊNCIA',
        'win_inicio': 'Início',
        'win_virus': 'Proteção contra vírus e ameaças',
        'win_conta': 'Proteção da conta',
        'win_firewall': 'Firewall e proteção de rede',
        'win_aplicativos': 'Controle de aplicativos e do navegador',
        'win_seguranca_rapida': 'Segurança em um piscar de olhos',
        'win_ransomware_titulo': 'Proteção contra ransomware',
        'win_ransomware': 'Gerenciar a proteção contra ransomware',
        'win_cfa': 'Acesso controlado a pastas',
        'win_ligado': 'Ativado',
        'win_historico': 'Histórico de bloqueios  ·  Pastas protegidas',
        'win_permitir': 'Permitir um aplicativo pelo Acesso controlado a pastas',
        'win_adicionar': 'Adicionar um aplicativo permitido',
        'win_recentes': 'Aplicativos bloqueados recentemente',
        'win_procurar': 'Procurar todos os aplicativos',

        # "Antes de começar"
        'aviso_titulo': 'Antes de começar',
        'aviso_intro': 'Este programa foi criado por um jogador, de forma independente. Ele é gratuito, de código '
                       'aberto e NÃO é oficial.',
        'aviso_ponto_1': 'Altera SOMENTE as missões dos mapas que você escolher. Perfil, dinheiro, habilidades, '
                         'armas, animais e troféus não mudam.',
        'aviso_ponto_3': 'Pode ter falhas. Antes de alterar o save, recomendamos fazer o backup completo do save '
                         '("{bt_backup}") e fechar o jogo.',
        'aviso_apoio': 'O programa é gratuito e sempre vai ser. Se ele te ajudar, considere apoiar o projeto.',
        'bt_apoiar_curto': '☕  Apoiar',
        'aviso_github': 'Código aberto no GitHub',
        'bt_backup_agora': 'Fazer backup agora',

        # "Apoiar o projeto"
        'apoio_pergunta': 'Gostou do {programa}?',
        'apoio_texto': 'Ele é gratuito e feito por um jogador para a comunidade de theHunter: Call of the Wild. '
                       'Se ele te ajudou, qualquer valor ajuda a manter o projeto vivo.',
        'apoio_bmc_sub': 'Cartão ou PayPal  ·  do mundo todo',
        'apoio_livepix_sub': 'Pix  ·  Brasil',
        'apoio_sem_dinheiro': 'Sem dinheiro sobrando? Também ajuda:',
        'apoio_estrela': '⭐ estrela no GitHub',
        'apoio_compartilhar': 'compartilhar com amigos',
        'apoio_erros': 'avisar sobre erros',
        'apoio_obrigado': 'Obrigado! ♥  — {autor}',
        'apoio_link_copiado': 'Link copiado! Cole para os seus amigos.',

        # tutorial
        'intro_pular': 'Pular tutorial',
        'il_mantem': '✓ continua igual',
        'il_recomeca': '↺ recomeça',
        'il_clique_caixinha': 'Clique na caixinha para marcar o mapa',
        'il_abra_jogo': 'Abra o jogo normalmente',
        'il_local': 'A nuvem perguntou? Escolha a versão LOCAL',
        'il_entre_mapa': 'Entre no mapa: as missões começam do zero',
        # ---- 0.9.8: verificação como passo 1, desfazer, confirmação, "Pronto!", apelido, tutoriais
        'passo_verif_titulo': 'Verificação antes de começar',
        'link_verificar_de_novo': 'Verificar de novo',
        'status_bloqueado': '●  O Windows está bloqueando o programa: veja o aviso amarelo acima',
        'bt_novo_backup': '💾  Fazer novo backup',
        'passo2_velho': 'Último backup há {dias} dias  ·  {tamanho}. Faça um novo antes de alterar o save.',
        'link_marcar_todos': 'Marcar todos',
        'link_desmarcar_todos': 'Desmarcar todos',
        'desfazer': 'Precisa desfazer?',
        'link_como_desfazer': 'Como funciona?',
        'desfazer_sub': 'Mudou de ideia ou algo saiu errado? Dá para voltar atrás. Escolha o que você quer '
                        'devolver:',
        'bt_restaurar_missoes': '↺  Restaurar missões',
        'desc_restaurar_missoes': 'Volta SÓ as missões para como estavam num backup automático. Inclui o '
                                  'backup original 🔒, de antes do primeiro uso.',
        'bt_restaurar_save_curto': '↺  Restaurar save completo',
        'desc_restaurar_save': 'Volta o save INTEIRO (tudo do jogo) para como estava num backup completo '
                               'feito por você.',
        'espaco_backups': 'Backups ocupam {tamanho}',
        'agradecimento': 'Muito obrigado aos amigos que contribuíram com testes, feedbacks e sugestões',
        'backup_original': 'Backup original (antes do primeiro uso)',
        'rest_original_nota': '🔒 O backup original guarda as suas missões como estavam antes de usar o programa '
                              'pela primeira vez. Ele nunca é apagado.',
        'backup_protegido_save': '🔒 protegido (até {dias} dias)',
        'limite_backups_save': 'São guardados até {n} backups completos. O mais antigo fica protegido (🔒) por até '
                               '{dias} dias; depois disso, a proteção passa para o próximo. O backup mais recente '
                               'nunca é apagado.',
        'aviso_ponto_2': 'Faz um backup sozinho antes de cada alteração e guarda PARA SEMPRE o backup original das '
                         'suas missões, de antes do primeiro uso. Dá para desfazer quando quiser.',

        # confirmação do reset
        'conf_janela': 'Confirmar o reset',
        'conf_titulo_um': 'Resetar as missões de 1 mapa?',
        'conf_titulo_varios': 'Resetar as missões de {n} mapas?',
        'conf_save': 'Save: {save}',
        'conf_hoje': 'hoje: {c} de {t} concluídas',
        'conf_zero': 'começa do zero',
        'conf_mais': '+ {n} outro(s) mapa(s)',
        'conf_outros': 'Os outros {n} mapa(s) não mudam.',
        'conf_backup': 'Um backup das missões é feito antes, automaticamente.',
        'conf_desfazer': 'Mudou de ideia depois? Use "{restaurar}", no quadro "Precisa desfazer?".',
        'conf_sim_um': '↺  Sim, resetar 1 mapa',
        'conf_sim_varios': '↺  Sim, resetar {n} mapas',

        # "Pronto!"
        'pronto_janela': 'Pronto!',
        'pronto_titulo_um': 'Pronto! As missões de 1 mapa foram resetadas.',
        'pronto_titulo_varios': 'Pronto! As missões de {n} mapas foram resetadas.',
        'pronto_sub': 'Os outros mapas continuam como estavam, e um backup foi guardado.',
        'pronto_agora': 'O que fazer agora',
        'pronto_outros': 'Resetar outros mapas',
        'pronto_desfazer': 'Desfazer este reset',

        # apelido do backup completo
        'apelido_janela': 'Backup do save completo',
        'apelido_titulo': 'Dar um nome a este backup?',
        'apelido_texto': 'Opcional: um nome ajuda a reconhecer este backup depois, na hora de restaurar. Pode '
                         'deixar em branco.',
        'apelido_exemplo': 'Exemplo: antes de resetar Yukon, antes de comprar o DLC…',
        'apelido_fazer': '💾  Fazer backup',

        # tutorial geral (7 telas)
        'intro_ultimo_botao': 'Começar!',
        'intro_passo_1': 'BEM-VINDO',
        'intro_passo_2': 'PASSO 1',
        'intro_passo_3': 'PASSO 2',
        'intro_passo_4': 'PASSO 3',
        'intro_passo_5': 'PASSO 4',
        'intro_passo_6': 'PASSO 5',
        'intro_passo_7': 'DEPOIS DO RESET',
        'intro_titulo_1': 'Recomece só o mapa que você quiser',
        'intro_texto_1': 'No jogo, resetar as missões apaga as de TODOS os mapas. Com este programa você escolhe '
                         'quais mapas recomeçam, e o progresso dos outros continua como está.\n\n'
                         'A janela tem 5 passos, de cima para baixo. Veja em 1 minuto como usar.',
        'intro_titulo_2': 'Verificação antes de começar',
        'intro_texto_2': 'O programa confere sozinho se o jogo, o Steam ou outro programa está usando os arquivos '
                         'do save. Com tudo certo, o passo fica com ✓ verde.\n\n'
                         'Se algo atrapalhar, ele fica amarelo: clique em "{detalhes}" para ver o que é e resolver, '
                         'e depois em "{verificar}".',
        'intro_titulo_3': 'Escolha o save',
        'intro_texto_3': 'O programa encontra o seu save sozinho (Steam ou Epic) e já escolhe o que você jogou por '
                         'último.\n\n'
                         'Tem mais de um save? Clique em "{trocar}" para escolher outro. Se ele não encontrar nada, '
                         'use "{escolher_pasta}".',
        'intro_titulo_4': 'Faça um backup do save completo',
        'intro_texto_4': 'Recomendado, principalmente na primeira vez: guarda uma cópia de TODOS os arquivos do '
                         'save. Você pode dar um nome ao backup, para reconhecer depois.\n\n'
                         'Se o último backup tiver mais de {dias} dias, o passo fica amarelo para lembrar você de '
                         'fazer outro em "{novo_backup}".',
        'intro_titulo_5': 'Marque os mapas que quer recomeçar',
        'intro_texto_5': 'Clique na caixinha (ou no nome) de cada mapa, ou use "Marcar todos". A barrinha mostra '
                         'quanto você já avançou nas missões daquele mapa.\n\n'
                         'Mapas com "{resetado}" já estão prontos: as missões começam do zero quando você entrar '
                         'no mapa.',
        'intro_titulo_6': 'Resetar',
        'intro_texto_6': 'Feche o jogo, clique no botão verde "{resetar}" e confira na tela de confirmação o que '
                         'vai mudar. Antes, o programa faz um backup das missões sozinho.\n\n'
                         'Logo abaixo fica o quadro "{desfazer}", com os botões para voltar atrás e o link '
                         '"{como_desfazer}", que ensina passo a passo.',
        'intro_titulo_7': 'Depois do reset',
        'intro_texto_7': 'Abra o jogo normalmente. Se o Steam Cloud ou a Epic Cloud perguntar qual versão usar, '
                         'escolha a LOCAL (deste computador). Entre no mapa: as missões começam do zero.\n\n'
                         'Quer ver este tutorial de novo? Clique em "{ajuda}", no topo da janela. Boa caçada!',
        'il_verif_1': 'Jogo fechado',
        'il_verif_2': 'Nada está usando os arquivos do save',
        'il_verif_3': 'Steam aberto: normalmente não atrapalha',

        # tutorial "Como desfazer" (6 telas)
        'desfazer_janela': 'Como desfazer',
        'desfazer_ultimo_botao': 'Entendi',
        'desfazer_passo_1': 'COMO DESFAZER',
        'desfazer_passo_2': 'RESTAURAR MISSÕES · 1',
        'desfazer_passo_3': 'RESTAURAR MISSÕES · 2',
        'desfazer_passo_4': 'BACKUP ORIGINAL',
        'desfazer_passo_5': 'SAVE COMPLETO',
        'desfazer_passo_6': 'DEPOIS DE RESTAURAR',
        'desfazer_titulo_1': 'Dois jeitos de voltar atrás',
        'desfazer_texto_1': 'No quadro "{desfazer}", embaixo do botão de resetar:\n'
                            '•  "{restaurar}": volta SÓ as missões. Use para desfazer um reset.\n'
                            '•  "{restaurar_save}": volta o save INTEIRO (dinheiro, armas, animais, tudo). Use só '
                            'se algo deu muito errado.',
        'desfazer_titulo_2': 'Escolha o backup',
        'desfazer_titulo_3': 'Confira e confirme',
        'desfazer_texto_3': 'Embaixo, a tabela mostra cada mapa "Agora" e "Depois de restaurar". As linhas '
                            'AMARELAS são as que vão mudar.\n\n'
                            'Se estiver certo, clique em "Restaurar este backup" e confirme. O save atual também é '
                            'guardado antes, então dá para voltar atrás de novo.',
        'desfazer_titulo_4': 'O seu backup original 🔒',
        'desfazer_texto_4': 'Na primeira vez que você usa o programa, ele guarda as suas missões como estavam. Esse '
                            'backup original fica PARA SEMPRE, não importa quantos resets você faça depois.\n\n'
                            'Para recuperar tudo como era: "{restaurar}" → escolha a linha verde "🔒 Backup '
                            'original", sempre no topo da lista → "Restaurar este backup".',
        'desfazer_titulo_5': 'Restaurar o save completo',
        'desfazer_texto_5': 'Clique em "{restaurar_save}" e escolha um backup completo (o nome que você deu aparece '
                            'na lista).\n\n'
                            'Atenção: TUDO o que você jogou depois desse backup volta atrás, não só as missões. O save '
                            'atual é guardado antes, por segurança.',
        'desfazer_titulo_6': 'Depois de restaurar',
        'desfazer_texto_6': 'Abra o jogo normalmente. Se o Steam Cloud ou a Epic Cloud perguntar qual versão usar, '
                            'escolha a LOCAL (deste computador). Se escolher a da nuvem, a restauração é desfeita.\n\n'
                            'Pronto: tudo volta a ficar como estava no backup escolhido.',
        'il_amarelo': 'Amarelo = vai mudar',
        'il_original_sempre': '🔒 Sempre no topo, nunca é apagado',
        'il_apelido_exemplo': 'antes do DLC',
        'il_save_aviso': 'Tudo o que foi jogado depois desse backup volta atrás',
        'il_restaurado': 'Tudo volta como estava no backup',
        'desfazer_texto_2': 'Clique em "{restaurar}". Abre a lista de backups das missões: o 🔒 backup original fica '
                            'sempre em cima e, logo abaixo, os outros, do mais recente para o mais antigo. Cada um diz '
                            'por que foi feito (ex.: "Antes de resetar Te Awaroa").\n\n'
                            'Para desfazer o último reset, escolha o primeiro logo abaixo do 🔒.',
    },

    # =====================================================================
    'en': {
        'formato_data': '%m/%d/%Y',
        'titulo_janela': 'ResetMissionsCOTW - Per-Map Mission Reset  v{versao}',

        'faixa_erro': '⚠  Could not write to the Documents folder ({erro}).\n'
                      'Until this is solved, the program does not change anything.',
        'bt_como_liberar': 'How to allow it (step by step)',
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
        'bt_apoiar': '☕  Support the project',

        'jogo_aberto': 'theHunter: Call of the Wild is open.\n\nClose the game completely and try again.',
        'nenhum_save_escolhido': 'No save selected.',
        'ja_resetados': 'The missions of this map (these maps) are already reset. The game creates the missions '
                        'from scratch when you enter the map.',
        'linha_detalhe': '  • {nome}: {c} completed, {a} in progress, {t} in total',
        'ignorados': '(Skipped, already reset: {nomes})',
        'nao_foi_possivel_resetar': 'Could not reset.\n\n{texto}\n\nThe save was not changed.',
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

        'aviso_texto': 'This program was made by a player, independently. It is free and open source: {link}\n\n'
                       'It is NOT official and it may have bugs. So, before any change to your save, we recommend '
                       'making a full backup of the save using the program\'s own "{bt_backup}" option.\n\n'
                       'The program changes ONLY the mission progress of the maps you choose. It does not change your '
                       'profile, money, skills, perks, weapons, animals, trophies or anything else.',
        'link_em_breve': '(the GitHub link will be added soon)',
        'aviso_entendi': 'Got it',

        'bt_ajuda': '❔  How to use',
        'intro_titulo': 'How to use',
        'intro_voltar': '←  Back',
        'intro_proximo': 'Next  →',
        'intro_comecar': 'Let\'s go!',
        'intro_pagina': '{n} of {total}',

        'verif_titulo': 'Check before you start',
        'verif_explicacao': 'To avoid errors and lost progress, the program checks whether another program could '
                            'interfere with editing the save. Programs such as Steam, Epic, OneDrive and Google Drive '
                            'may be using or syncing the files at the same time. This can block the change or '
                            'overwrite the save with an old version from the cloud.\n'
                            'This check happens only on your computer: nothing is sent to the internet.',
        'verif_tudo_pronto': '✔  All set: nothing should get in the way.',
        'verif_impede': '⛔  Needs fixing',
        'verif_atencao': '⚠  Heads-up',
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

        'nome_leia_me': 'README.txt',
        'leia_me_pasta': 'Folder of the program "ResetMissionsCOTW - Per-Map Mission Reset".\n\n'
                         'This is where the automatic backups of the missions file (missions_missiondata_adf)\n'
                         'are kept, made before each reset or restore, separated by save.\n\n'
                         'To bring a backup back, use the program\'s "Restore missions backup..." button.\n'
                         'If you prefer to do it by hand: close the game and copy the missions_missiondata_adf\n'
                         'file from inside the backup folder into the game\'s save folder.\n\n'
                         'This folder is hidden so it does not clutter your Documents folder.\n'
                         'You may delete old backups if you want.\n',
        # ---- new look (0.9.7): window in 4 steps
        'cabecalho': 'Per-map mission reset',
        'link_como_usar': 'How to use',
        'link_logs': 'Logs',
        'link_detalhes': 'details',
        'bt_tema_escuro': '☾  Dark theme',
        'bt_tema_claro': '☀  Light theme',
        'status_ok': '●  All set: nothing is using the save files',
        'status_avisos': '●  {n} warning(s) before you start',
        'status_impede': '●  {n} problem(s) prevent changes',
        'credito': 'Made by {autor}  ·  v{versao}',
        'pilula_apoiar': 'Like it? Support the project',
        'update_disponivel': 'New version available: {versao}',
        'link_baixar': 'Download',
        'link_agora_nao': 'Not now',
        'passo1_titulo': 'Choose the save',
        'passo1_resumo': '{plat}  ·  account {id}  ·  {quando}',
        'link_trocar': 'Change',
        'link_escolher_pasta': 'Choose folder',
        'link_procurar': 'Search again',
        'nao_encontrei_save': 'Could not find the save automatically. Click "Choose folder" and select the folder '
                              'that has the missions_missiondata_adf file.',
        'passo2_titulo': 'Back up the full save',
        'recomendado': '(recommended)',
        'passo2_sub': 'Keeps a copy of ALL the save files, not just the missions. It takes a few seconds.',
        'passo2_feito': 'Backup made {quando}  ·  {tamanho}',
        'hoje_as': 'today at {hora}',
        'ontem_as': 'yesterday at {hora}',
        'dia_as': 'on {data} at {hora}',
        'link_fazer_outro': 'Make another',
        'passo3_titulo': 'Choose the maps you want to start over',
        'passo3_sub': 'Tick one or more. The bar shows how far you have got in the missions of each map.',
        'passo3_sem_save': 'Choose a save in step 1 to see the maps.',
        'passo3_vazio': 'This save has no missions in any map yet.',
        'mapa_resetado_curto': '↺ reset',
        'dica_mapa': '{c} completed  ·  {a} in progress  ·  {t} in total',
        'dica_mapa_resetado': 'Missions reset ({t} in total). They start from scratch when you enter this map in the '
                              'game.',
        'passo4_titulo': 'Reset',
        'bt_resetar_nenhum': 'Reset',
        'bt_resetar_um': 'Reset 1 map',
        'bt_resetar_varios': 'Reset {n} maps',
        'passo4_nenhum': 'Tick at least one map in step 3.',
        'passo4_resumo': '{nomes}. Other maps do not change.',
        'conjuncao_e': ' and ',
        'link_restaurar_missoes': 'Restore missions',
        'link_restaurar_save': 'Restore full save',
        'link_pasta_backups': 'Backups folder',
        'selecione_mapa': 'Tick the map you want to reset in the list (step 3).',
        'aviso_usar_faixa': 'Windows is blocking the program. Use the yellow notice at the top of the window to '
                            'allow it.',
        'confirmar_reset': 'Save: {save}\n\nReset ALL missions of:\n\n{detalhes}\n\n'
                           'The mission progress of this map (these maps) will be lost. Other maps do not change.\n'
                           'A backup is made first, and you can undo it with "Restore missions".\n\n'
                           'Continue?',
        'reset_ok': 'Done! Missions reset:\n\n{nomes}\n\n'
                    'Now open the game. If Steam Cloud or Epic Cloud asks which version to use, choose the LOCAL one '
                    '(this computer). When you enter this map, its missions start from scratch.\n\n'
                    'A backup was made first. To undo, use "Restore missions".',
        'erro_pos_gravacao': 'After writing, the file is not as expected. Use "Restore missions".',

        'faixa_titulo_cfa': 'Windows is preventing the program from saving files',
        'faixa_bloqueio': 'The Windows Defender "Controlled folder access" protection is blocking the Documents '
                          'folder, where your save is. Nothing was changed. Allow the program once and you are done: '
                          'it takes about 1 minute.',
        'faixa_titulo_erro': 'Could not write to the Documents folder',
        'faixa_erro_causa': '{causa}\nUntil this is solved, the program does not change anything.',
        'bt_abrir_seguranca': '↗  Open Windows Security',
        'guia_titulo': 'Allow the program in Windows Defender',
        'guia_intro': 'You only need to do this once. It takes about 1 minute.',
        'guia_contador': 'STEP {n} OF {total}',
        'guia_passo_1': 'Open Windows Security',
        'guia_passo_2': 'Virus & threat protection',
        'guia_passo_3': 'Ransomware protection',
        'guia_passo_4': 'Allow an app',
        'guia_passo_5': 'Choose this program',
        'guia_texto_1': 'Click "Open Windows Security" below. It tries to open the right page directly (step 4). If '
                        'it does not, search for "Windows Security" in the Start menu.',
        'guia_texto_2': 'If it opened on the home screen, click "Virus & threat protection" (the shield icon).',
        'guia_texto_3': 'Scroll down to "Ransomware protection" and click "Manage ransomware protection".',
        'guia_texto_4': 'Under "Controlled folder access", click "Allow an app through Controlled folder access". If '
                        'Windows asks whether to allow changes, click "Yes".',
        'guia_texto_5': 'Click "+ Add an allowed app" and then "Browse all apps". In the window that opens, paste the '
                        'path below into the "File name" box (Ctrl+V) and click "Open". Then click "Done, test '
                        'again".',
        'guia_caminho': 'Path of this program (to paste in step 5):',
        'bt_copiar': 'Copy',
        'copiado': '✓ Copied! Now just paste it (Ctrl+V).',
        'win_seguranca': 'Windows Security',
        'win_melhor': 'BEST MATCH',
        'win_inicio': 'Home',
        'win_virus': 'Virus & threat protection',
        'win_conta': 'Account protection',
        'win_firewall': 'Firewall & network protection',
        'win_aplicativos': 'App & browser control',
        'win_seguranca_rapida': 'Security at a glance',
        'win_ransomware_titulo': 'Ransomware protection',
        'win_ransomware': 'Manage ransomware protection',
        'win_cfa': 'Controlled folder access',
        'win_ligado': 'On',
        'win_historico': 'Block history  ·  Protected folders',
        'win_permitir': 'Allow an app through Controlled folder access',
        'win_adicionar': 'Add an allowed app',
        'win_recentes': 'Recently blocked apps',
        'win_procurar': 'Browse all apps',

        'aviso_titulo': 'Before you start',
        'aviso_intro': 'This program was created by a player, independently. It is free, open source and NOT '
                       'official.',
        'aviso_ponto_1': 'It changes ONLY the missions of the maps you choose. Profile, money, skills, weapons, '
                         'animals and trophies do not change.',
        'aviso_ponto_3': 'It may have bugs. Before changing the save, we recommend backing up the full save '
                         '("{bt_backup}") and closing the game.',
        'aviso_apoio': 'The program is free and always will be. If it helps you, please consider supporting the '
                       'project.',
        'bt_apoiar_curto': '☕  Support',
        'aviso_github': 'Open source on GitHub',
        'bt_backup_agora': 'Back up now',

        'apoio_pergunta': 'Do you like {programa}?',
        'apoio_texto': 'It is free and made by a player for the theHunter: Call of the Wild community. If it helped '
                       'you, any amount helps keep the project alive.',
        'apoio_bmc_sub': 'Card or PayPal  ·  worldwide',
        'apoio_livepix_sub': 'Pix  ·  Brazil',
        'apoio_sem_dinheiro': 'No money to spare? This helps too:',
        'apoio_estrela': '⭐ star on GitHub',
        'apoio_compartilhar': 'share with friends',
        'apoio_erros': 'report bugs',
        'apoio_obrigado': 'Thank you! ♥  — {autor}',
        'apoio_link_copiado': 'Link copied! Paste it to your friends.',

        'intro_pular': 'Skip tutorial',
        'il_mantem': '✓ stays the same',
        'il_recomeca': '↺ starts over',
        'il_clique_caixinha': 'Click the box to tick the map',
        'il_abra_jogo': 'Open the game normally',
        'il_local': 'Cloud asked? Choose the LOCAL version',
        'il_entre_mapa': 'Enter the map: missions start from scratch',
        # ---- 0.9.8
        'passo_verif_titulo': 'Check before you start',
        'link_verificar_de_novo': 'Check again',
        'status_bloqueado': '●  Windows is blocking the program: see the yellow notice above',
        'bt_novo_backup': '💾  Make a new backup',
        'passo2_velho': 'Last backup {dias} days ago  ·  {tamanho}. Make a new one before changing the save.',
        'link_marcar_todos': 'Tick all',
        'link_desmarcar_todos': 'Untick all',
        'desfazer': 'Need to undo?',
        'link_como_desfazer': 'How does it work?',
        'desfazer_sub': 'Changed your mind or something went wrong? You can go back. Choose what you want to bring '
                        'back:',
        'bt_restaurar_missoes': '↺  Restore missions',
        'desc_restaurar_missoes': 'Brings ONLY the missions back to how they were in an automatic backup. Includes '
                                  'the original backup 🔒, from before the first use.',
        'bt_restaurar_save_curto': '↺  Restore full save',
        'desc_restaurar_save': 'Brings the WHOLE save (everything in the game) back to how it was in a full backup '
                               'you made.',
        'espaco_backups': 'Backups use {tamanho}',
        'agradecimento': 'Many thanks to the friends who helped with tests, feedback and suggestions',
        'backup_original': 'Original backup (before the first use)',
        'rest_original_nota': '🔒 The original backup keeps your missions as they were before you used the program '
                              'for the first time. It is never deleted.',
        'backup_protegido_save': '🔒 protected (up to {dias} days)',
        'limite_backups_save': 'Up to {n} full backups are kept. The oldest one stays protected (🔒) for up to '
                               '{dias} days; after that, the protection moves to the next one. The most recent backup '
                               'is never deleted.',
        'aviso_ponto_2': 'It makes a backup on its own before every change and keeps the ORIGINAL backup of your '
                         'missions, from before the first use, FOREVER. You can undo whenever you want.',

        'conf_janela': 'Confirm the reset',
        'conf_titulo_um': 'Reset the missions of 1 map?',
        'conf_titulo_varios': 'Reset the missions of {n} maps?',
        'conf_save': 'Save: {save}',
        'conf_hoje': 'today: {c} of {t} completed',
        'conf_zero': 'starts from scratch',
        'conf_mais': '+ {n} more map(s)',
        'conf_outros': 'The other {n} map(s) do not change.',
        'conf_backup': 'A missions backup is made first, automatically.',
        'conf_desfazer': 'Changed your mind later? Use "{restaurar}" in the "Need to undo?" box.',
        'conf_sim_um': '↺  Yes, reset 1 map',
        'conf_sim_varios': '↺  Yes, reset {n} maps',

        'pronto_janela': 'Done!',
        'pronto_titulo_um': 'Done! The missions of 1 map were reset.',
        'pronto_titulo_varios': 'Done! The missions of {n} maps were reset.',
        'pronto_sub': 'The other maps stay as they were, and a backup was kept.',
        'pronto_agora': 'What to do now',
        'pronto_outros': 'Reset other maps',
        'pronto_desfazer': 'Undo this reset',

        'apelido_janela': 'Full save backup',
        'apelido_titulo': 'Give this backup a name?',
        'apelido_texto': 'Optional: a name helps you recognize this backup later, when restoring. You can leave it '
                         'blank.',
        'apelido_exemplo': 'Example: before resetting Yukon, before buying the DLC…',
        'apelido_fazer': '💾  Back up',

        'intro_ultimo_botao': 'Get started!',
        'intro_passo_1': 'WELCOME',
        'intro_passo_2': 'STEP 1',
        'intro_passo_3': 'STEP 2',
        'intro_passo_4': 'STEP 3',
        'intro_passo_5': 'STEP 4',
        'intro_passo_6': 'STEP 5',
        'intro_passo_7': 'AFTER THE RESET',
        'intro_titulo_1': 'Start over only the map you want',
        'intro_texto_1': 'In the game, resetting missions wipes them on ALL maps. With this program you choose which '
                         'maps start over, and the progress of the others stays as it is.\n\n'
                         'The window has 5 steps, from top to bottom. See how to use it in 1 minute.',
        'intro_titulo_2': 'Check before you start',
        'intro_texto_2': 'The program checks on its own whether the game, Steam or another program is using the save '
                         'files. When everything is fine, the step gets a green ✓.\n\n'
                         'If something gets in the way, it turns yellow: click "{detalhes}" to see what it is and '
                         'fix it, then "{verificar}".',
        'intro_titulo_3': 'Choose the save',
        'intro_texto_3': 'The program finds your save on its own (Steam or Epic) and picks the one you played last.'
                         '\n\n'
                         'Have more than one save? Click "{trocar}" to pick another. If it finds nothing, use '
                         '"{escolher_pasta}".',
        'intro_titulo_4': 'Back up the full save',
        'intro_texto_4': 'Recommended, especially the first time: it keeps a copy of ALL the save files. You can give '
                         'the backup a name to recognize it later.\n\n'
                         'If the last backup is more than {dias} days old, the step turns yellow to remind you to '
                         'make another one with "{novo_backup}".',
        'intro_titulo_5': 'Tick the maps you want to start over',
        'intro_texto_5': 'Click the box (or the name) of each map, or use "Tick all". The small bar shows how far you '
                         'have got in the missions of that map.\n\n'
                         'Maps marked "{resetado}" are ready: their missions start from scratch when you enter the '
                         'map.',
        'intro_titulo_6': 'Reset',
        'intro_texto_6': 'Close the game, click the green "{resetar}" button and check on the confirmation screen what '
                         'will change. The program first backs up the missions on its own.\n\n'
                         'Right below is the "{desfazer}" box, with the buttons to go back and the "{como_desfazer}" '
                         'link, which teaches it step by step.',
        'intro_titulo_7': 'After the reset',
        'intro_texto_7': 'Open the game normally. If Steam Cloud or Epic Cloud asks which version to use, choose the '
                         'LOCAL one (this computer). Enter the map: its missions start from scratch.\n\n'
                         'Want to see this tutorial again? Click "{ajuda}" at the top of the window. Happy hunting!',
        'il_verif_1': 'Game closed',
        'il_verif_2': 'Nothing is using the save files',
        'il_verif_3': 'Steam open: usually not a problem',

        'desfazer_janela': 'How to undo',
        'desfazer_ultimo_botao': 'Got it',
        'desfazer_passo_1': 'HOW TO UNDO',
        'desfazer_passo_2': 'RESTORE MISSIONS · 1',
        'desfazer_passo_3': 'RESTORE MISSIONS · 2',
        'desfazer_passo_4': 'ORIGINAL BACKUP',
        'desfazer_passo_5': 'FULL SAVE',
        'desfazer_passo_6': 'AFTER RESTORING',
        'desfazer_titulo_1': 'Two ways to go back',
        'desfazer_texto_1': 'In the "{desfazer}" box, below the reset button:\n'
                            '•  "{restaurar}": brings back ONLY the missions. Use it to undo a reset.\n'
                            '•  "{restaurar_save}": brings back the WHOLE save (money, weapons, animals, everything). '
                            'Use it only if something went really wrong.',
        'desfazer_titulo_2': 'Choose the backup',
        'desfazer_titulo_3': 'Check and confirm',
        'desfazer_texto_3': 'Below, the table shows each map "Now" and "After restoring". The YELLOW rows are the ones '
                            'that will change.\n\n'
                            'If it looks right, click "Restore this backup" and confirm. The current save is kept '
                            'first, so you can go back again.',
        'desfazer_titulo_4': 'Your original backup 🔒',
        'desfazer_texto_4': 'The first time you use the program, it keeps your missions as they were. This original '
                            'backup stays FOREVER, no matter how many resets you do afterwards.\n\n'
                            'To get everything back as it was: "{restaurar}" → choose the green "🔒 Original backup" '
                            'row, always at the top of the list → "Restore this backup".',
        'desfazer_titulo_5': 'Restore the full save',
        'desfazer_texto_5': 'Click "{restaurar_save}" and choose a full backup (the name you gave it shows in the '
                            'list).\n\n'
                            'Warning: EVERYTHING you played after that backup goes back, not just the missions. The '
                            'current save is kept first, just in case.',
        'desfazer_titulo_6': 'After restoring',
        'desfazer_texto_6': 'Open the game normally. If Steam Cloud or Epic Cloud asks which version to use, choose the '
                            'LOCAL one (this computer). If you choose the cloud one, the restore is undone.\n\n'
                            'Done: everything is back as it was in the chosen backup.',
        'il_amarelo': 'Yellow = will change',
        'il_original_sempre': '🔒 Always at the top, never deleted',
        'il_apelido_exemplo': 'before the DLC',
        'il_save_aviso': 'Everything played after this backup goes back',
        'il_restaurado': 'Everything is back as it was in the backup',
        'desfazer_texto_2': 'Click "{restaurar}". The list of mission backups opens: the 🔒 original backup is always '
                            'at the top and, right below, the others, from the most recent to the oldest. Each one says '
                            'why it was made (e.g. "Before resetting Te Awaroa").\n\n'
                            'To undo the last reset, choose the first one right below the 🔒.',
    },

    # =====================================================================
    'es': {
        'formato_data': '%d/%m/%Y',
        'titulo_janela': 'ResetMissionsCOTW - Reinicio de Misiones por Mapa  v{versao}',

        'faixa_erro': '⚠  No se pudo escribir en la carpeta Documentos ({erro}).\n'
                      'Hasta que se resuelva, el programa no cambia nada.',
        'bt_como_liberar': 'Cómo permitirlo (paso a paso)',
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
        'bt_apoiar': '☕  Apoyar el proyecto',

        'jogo_aberto': 'theHunter: Call of the Wild está abierto.\n\nCierra el juego por completo e inténtalo de nuevo.',
        'nenhum_save_escolhido': 'No hay ninguna partida elegida.',
        'ja_resetados': 'Las misiones de este(s) mapa(s) ya están reiniciadas. El juego crea las misiones desde '
                        'cero cuando entres en el mapa.',
        'linha_detalhe': '  • {nome}: {c} completadas, {a} en curso, {t} en total',
        'ignorados': '(Omitido(s), ya reiniciado(s): {nomes})',
        'nao_foi_possivel_resetar': 'No se pudo reiniciar.\n\n{texto}\n\nLa partida no se modificó.',
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
        'intro_voltar': '←  Atrás',
        'intro_proximo': 'Siguiente  →',
        'intro_comecar': '¡Empezar!',
        'intro_pagina': '{n} de {total}',

        'verif_titulo': 'Comprobación antes de empezar',
        'verif_explicacao': 'Para evitar errores y pérdida de progreso, el programa comprueba si algún programa puede '
                            'estorbar la edición de la partida. Programas como Steam, Epic, OneDrive y Google Drive '
                            'pueden estar usando o sincronizando los archivos al mismo tiempo. Eso puede bloquear el '
                            'cambio o sobrescribir la partida con una versión antigua de la nube.\n'
                            'Esta comprobación ocurre solo en tu equipo: no se envía nada a internet.',
        'verif_tudo_pronto': '✔  Todo listo: nada debería estorbar.',
        'verif_impede': '⛔  Hay que resolverlo',
        'verif_atencao': '⚠  Atención',
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
        # ---- nuevo aspecto (0.9.7): ventana en 4 pasos
        'cabecalho': 'Reinicio de misiones por mapa',
        'link_como_usar': 'Cómo usar',
        'link_logs': 'Registros',
        'link_detalhes': 'detalles',
        'bt_tema_escuro': '☾  Tema oscuro',
        'bt_tema_claro': '☀  Tema claro',
        'status_ok': '●  Todo listo: nada está usando los archivos de la partida',
        'status_avisos': '●  {n} aviso(s) antes de empezar',
        'status_impede': '●  {n} problema(s) impide(n) cambios',
        'credito': 'Hecho por {autor}  ·  v{versao}',
        'pilula_apoiar': '¿Te gustó? Apoya el proyecto',
        'update_disponivel': 'Nueva versión disponible: {versao}',
        'link_baixar': 'Descargar',
        'link_agora_nao': 'Ahora no',
        'passo1_titulo': 'Elige la partida',
        'passo1_resumo': '{plat}  ·  cuenta {id}  ·  {quando}',
        'link_trocar': 'Cambiar',
        'link_escolher_pasta': 'Elegir carpeta',
        'link_procurar': 'Buscar de nuevo',
        'nao_encontrei_save': 'No se encontró la partida automáticamente. Haz clic en "Elegir carpeta" y elige la '
                              'carpeta que tiene el archivo missions_missiondata_adf.',
        'passo2_titulo': 'Haz una copia de seguridad de la partida completa',
        'recomendado': '(recomendado)',
        'passo2_sub': 'Guarda una copia de TODOS los archivos de la partida, no solo las misiones. Tarda unos '
                      'segundos.',
        'passo2_feito': 'Copia hecha {quando}  ·  {tamanho}',
        'hoje_as': 'hoy a las {hora}',
        'ontem_as': 'ayer a las {hora}',
        'dia_as': 'el {data} a las {hora}',
        'link_fazer_outro': 'Hacer otra',
        'passo3_titulo': 'Elige los mapas que quieres empezar de nuevo',
        'passo3_sub': 'Marca uno o más. La barra muestra cuánto has avanzado en las misiones de cada mapa.',
        'passo3_sem_save': 'Elige una partida en el paso 1 para ver los mapas.',
        'passo3_vazio': 'Esta partida todavía no tiene misiones en ningún mapa.',
        'mapa_resetado_curto': '↺ reiniciado',
        'dica_mapa': '{c} completadas  ·  {a} en curso  ·  {t} en total',
        'dica_mapa_resetado': 'Misiones reiniciadas ({t} en total). Empiezan desde cero cuando entres en este mapa en '
                              'el juego.',
        'passo4_titulo': 'Reiniciar',
        'bt_resetar_nenhum': 'Reiniciar',
        'bt_resetar_um': 'Reiniciar 1 mapa',
        'bt_resetar_varios': 'Reiniciar {n} mapas',
        'passo4_nenhum': 'Marca al menos un mapa en el paso 3.',
        'passo4_resumo': '{nomes}. Los demás mapas no cambian.',
        'conjuncao_e': ' y ',
        'link_restaurar_missoes': 'Restaurar misiones',
        'link_restaurar_save': 'Restaurar partida completa',
        'link_pasta_backups': 'Carpeta de copias',
        'selecione_mapa': 'Marca en la lista (paso 3) el mapa que quieres reiniciar.',
        'aviso_usar_faixa': 'Windows está bloqueando el programa. Usa el aviso amarillo de la parte superior de la '
                            'ventana para permitirlo.',
        'confirmar_reset': 'Partida: {save}\n\n¿Reiniciar TODAS las misiones de estos mapas?\n\n{detalhes}\n\n'
                           'Se perderá el progreso de las misiones de este(s) mapa(s). Los demás mapas no cambian.\n'
                           'Antes se hace una copia de seguridad, y puedes deshacerlo en "Restaurar misiones".\n\n'
                           '¿Continuar?',
        'reset_ok': '¡Listo! Misiones reiniciadas:\n\n{nomes}\n\n'
                    'Ahora abre el juego. Si Steam Cloud o Epic Cloud pregunta qué versión usar, elige la LOCAL '
                    '(de este ordenador). Al entrar en ese mapa, las misiones empiezan desde cero.\n\n'
                    'Antes se hizo una copia de seguridad. Para deshacerlo, usa "Restaurar misiones".',
        'erro_pos_gravacao': 'Después de escribir, el archivo no quedó como se esperaba. Usa "Restaurar misiones".',

        'faixa_titulo_cfa': 'Windows está impidiendo que el programa guarde archivos',
        'faixa_bloqueio': 'La protección "Acceso controlado a carpetas" de Windows Defender está bloqueando la carpeta '
                          'Documentos, donde está tu partida. No se cambió nada. Permite el programa una vez y listo: '
                          'tarda cerca de 1 minuto.',
        'faixa_titulo_erro': 'No se pudo escribir en la carpeta Documentos',
        'faixa_erro_causa': '{causa}\nHasta que se resuelva, el programa no cambia nada.',
        'bt_abrir_seguranca': '↗  Abrir Seguridad de Windows',
        'guia_titulo': 'Permitir el programa en Windows Defender',
        'guia_intro': 'Solo tienes que hacerlo una vez. Tarda cerca de 1 minuto.',
        'guia_contador': 'PASO {n} DE {total}',
        'guia_passo_1': 'Abrir Seguridad de Windows',
        'guia_passo_2': 'Protección antivirus y contra amenazas',
        'guia_passo_3': 'Protección contra ransomware',
        'guia_passo_4': 'Permitir una aplicación',
        'guia_passo_5': 'Elegir este programa',
        'guia_texto_1': 'Haz clic en "Abrir Seguridad de Windows", aquí abajo. Intenta abrir directamente la página '
                        'correcta (paso 4). Si no se abre, busca "Seguridad de Windows" en el menú Inicio.',
        'guia_texto_2': 'Si se abrió en la pantalla de inicio, haz clic en "Protección antivirus y contra amenazas" '
                        '(el icono del escudo).',
        'guia_texto_3': 'Baja hasta "Protección contra ransomware" y haz clic en "Administrar la protección contra '
                        'ransomware".',
        'guia_texto_4': 'En "Acceso controlado a carpetas", haz clic en "Permitir una aplicación a través del Acceso '
                        'controlado a carpetas". Si Windows pregunta si quieres permitir cambios, haz clic en "Sí".',
        'guia_texto_5': 'Haz clic en "+ Agregar una aplicación permitida" y luego en "Examinar todas las '
                        'aplicaciones". En la ventana que se abre, pega la ruta de abajo en el cuadro "Nombre" '
                        '(Ctrl+V) y haz clic en "Abrir". Después haz clic en "Ya lo permití, probar de nuevo".',
        'guia_caminho': 'Ruta de este programa (para pegar en el paso 5):',
        'bt_copiar': 'Copiar',
        'copiado': '✓ ¡Copiado! Ahora solo pégalo (Ctrl+V).',
        'win_seguranca': 'Seguridad de Windows',
        'win_melhor': 'MEJOR COINCIDENCIA',
        'win_inicio': 'Inicio',
        'win_virus': 'Protección antivirus y contra amenazas',
        'win_conta': 'Protección de cuentas',
        'win_firewall': 'Firewall y protección de red',
        'win_aplicativos': 'Control de aplicaciones y navegador',
        'win_seguranca_rapida': 'Seguridad de un vistazo',
        'win_ransomware_titulo': 'Protección contra ransomware',
        'win_ransomware': 'Administrar la protección contra ransomware',
        'win_cfa': 'Acceso controlado a carpetas',
        'win_ligado': 'Activado',
        'win_historico': 'Historial de bloqueos  ·  Carpetas protegidas',
        'win_permitir': 'Permitir una aplicación a través del Acceso controlado a carpetas',
        'win_adicionar': 'Agregar una aplicación permitida',
        'win_recentes': 'Aplicaciones bloqueadas recientemente',
        'win_procurar': 'Examinar todas las aplicaciones',

        'aviso_titulo': 'Antes de empezar',
        'aviso_intro': 'Este programa fue creado por un jugador, de forma independiente. Es gratuito, de código '
                       'abierto y NO es oficial.',
        'aviso_ponto_1': 'Cambia SOLO las misiones de los mapas que elijas. Perfil, dinero, habilidades, armas, '
                         'animales y trofeos no cambian.',
        'aviso_ponto_3': 'Puede tener fallos. Antes de modificar la partida, te recomendamos hacer la copia de la '
                         'partida completa ("{bt_backup}") y cerrar el juego.',
        'aviso_apoio': 'El programa es gratuito y siempre lo será. Si te ayuda, considera apoyar el proyecto.',
        'bt_apoiar_curto': '☕  Apoyar',
        'aviso_github': 'Código abierto en GitHub',
        'bt_backup_agora': 'Hacer copia ahora',

        'apoio_pergunta': '¿Te gustó {programa}?',
        'apoio_texto': 'Es gratuito y lo hizo un jugador para la comunidad de theHunter: Call of the Wild. Si te '
                       'ayudó, cualquier cantidad ayuda a mantener vivo el proyecto.',
        'apoio_bmc_sub': 'Tarjeta o PayPal  ·  todo el mundo',
        'apoio_livepix_sub': 'Pix  ·  Brasil',
        'apoio_sem_dinheiro': '¿Sin dinero de sobra? También ayuda:',
        'apoio_estrela': '⭐ estrella en GitHub',
        'apoio_compartilhar': 'compartir con amigos',
        'apoio_erros': 'avisar de errores',
        'apoio_obrigado': '¡Gracias! ♥  — {autor}',
        'apoio_link_copiado': '¡Enlace copiado! Pégalo para tus amigos.',

        'intro_pular': 'Saltar tutorial',
        'il_mantem': '✓ sigue igual',
        'il_recomeca': '↺ empieza de nuevo',
        'il_clique_caixinha': 'Haz clic en la casilla para marcar el mapa',
        'il_abra_jogo': 'Abre el juego normalmente',
        'il_local': '¿Preguntó la nube? Elige la versión LOCAL',
        'il_entre_mapa': 'Entra en el mapa: las misiones empiezan de cero',
        # ---- 0.9.8
        'passo_verif_titulo': 'Comprobación antes de empezar',
        'link_verificar_de_novo': 'Comprobar de nuevo',
        'status_bloqueado': '●  Windows está bloqueando el programa: mira el aviso amarillo de arriba',
        'bt_novo_backup': '💾  Hacer una copia nueva',
        'passo2_velho': 'Última copia hace {dias} días  ·  {tamanho}. Haz una nueva antes de modificar la partida.',
        'link_marcar_todos': 'Marcar todos',
        'link_desmarcar_todos': 'Desmarcar todos',
        'desfazer': '¿Necesitas deshacer?',
        'link_como_desfazer': '¿Cómo funciona?',
        'desfazer_sub': '¿Cambiaste de idea o algo salió mal? Puedes volver atrás. Elige qué quieres recuperar:',
        'bt_restaurar_missoes': '↺  Restaurar misiones',
        'desc_restaurar_missoes': 'Devuelve SOLO las misiones a como estaban en una copia automática. Incluye la '
                                  'copia original 🔒, de antes del primer uso.',
        'bt_restaurar_save_curto': '↺  Restaurar partida completa',
        'desc_restaurar_save': 'Devuelve la partida ENTERA (todo el juego) a como estaba en una copia completa hecha '
                               'por ti.',
        'espaco_backups': 'Las copias ocupan {tamanho}',
        'agradecimento': 'Muchas gracias a los amigos que ayudaron con pruebas, comentarios y sugerencias',
        'backup_original': 'Copia original (antes del primer uso)',
        'rest_original_nota': '🔒 La copia original guarda tus misiones como estaban antes de usar el programa por '
                              'primera vez. Nunca se borra.',
        'backup_protegido_save': '🔒 protegida (hasta {dias} días)',
        'limite_backups_save': 'Se guardan hasta {n} copias completas. La más antigua queda protegida (🔒) hasta '
                               '{dias} días; después, la protección pasa a la siguiente. La copia más reciente nunca '
                               'se borra.',
        'aviso_ponto_2': 'Hace una copia sola antes de cada cambio y guarda PARA SIEMPRE la copia original de tus '
                         'misiones, de antes del primer uso. Puedes deshacer cuando quieras.',

        'conf_janela': 'Confirmar el reinicio',
        'conf_titulo_um': '¿Reiniciar las misiones de 1 mapa?',
        'conf_titulo_varios': '¿Reiniciar las misiones de {n} mapas?',
        'conf_save': 'Partida: {save}',
        'conf_hoje': 'hoy: {c} de {t} completadas',
        'conf_zero': 'empieza desde cero',
        'conf_mais': '+ {n} mapa(s) más',
        'conf_outros': 'Los otros {n} mapa(s) no cambian.',
        'conf_backup': 'Antes se hace una copia de las misiones, automáticamente.',
        'conf_desfazer': '¿Cambias de idea después? Usa "{restaurar}" en el cuadro "¿Necesitas deshacer?".',
        'conf_sim_um': '↺  Sí, reiniciar 1 mapa',
        'conf_sim_varios': '↺  Sí, reiniciar {n} mapas',

        'pronto_janela': '¡Listo!',
        'pronto_titulo_um': '¡Listo! Se reiniciaron las misiones de 1 mapa.',
        'pronto_titulo_varios': '¡Listo! Se reiniciaron las misiones de {n} mapas.',
        'pronto_sub': 'Los demás mapas siguen como estaban, y se guardó una copia de seguridad.',
        'pronto_agora': 'Qué hacer ahora',
        'pronto_outros': 'Reiniciar otros mapas',
        'pronto_desfazer': 'Deshacer este reinicio',

        'apelido_janela': 'Copia de la partida completa',
        'apelido_titulo': '¿Ponerle un nombre a esta copia?',
        'apelido_texto': 'Opcional: un nombre te ayuda a reconocer esta copia después, al restaurar. Puedes dejarlo '
                         'en blanco.',
        'apelido_exemplo': 'Ejemplo: antes de reiniciar Yukon, antes de comprar el DLC…',
        'apelido_fazer': '💾  Hacer copia',

        'intro_ultimo_botao': '¡Empezar!',
        'intro_passo_1': 'BIENVENIDO',
        'intro_passo_2': 'PASO 1',
        'intro_passo_3': 'PASO 2',
        'intro_passo_4': 'PASO 3',
        'intro_passo_5': 'PASO 4',
        'intro_passo_6': 'PASO 5',
        'intro_passo_7': 'DESPUÉS DEL REINICIO',
        'intro_titulo_1': 'Empieza de nuevo solo el mapa que quieras',
        'intro_texto_1': 'En el juego, reiniciar las misiones las borra en TODOS los mapas. Con este programa eliges '
                         'qué mapas empiezan de nuevo, y el progreso de los demás se queda como está.\n\n'
                         'La ventana tiene 5 pasos, de arriba abajo. Mira en 1 minuto cómo usarla.',
        'intro_titulo_2': 'Comprobación antes de empezar',
        'intro_texto_2': 'El programa comprueba solo si el juego, Steam u otro programa está usando los archivos de la '
                         'partida. Si todo está bien, el paso lleva un ✓ verde.\n\n'
                         'Si algo estorba, se pone amarillo: haz clic en "{detalhes}" para ver qué es y resolverlo, '
                         'y después en "{verificar}".',
        'intro_titulo_3': 'Elige la partida',
        'intro_texto_3': 'El programa encuentra tu partida solo (Steam o Epic) y elige la que jugaste por última vez.'
                         '\n\n'
                         '¿Tienes más de una? Haz clic en "{trocar}" para elegir otra. Si no encuentra nada, usa '
                         '"{escolher_pasta}".',
        'intro_titulo_4': 'Haz una copia de la partida completa',
        'intro_texto_4': 'Recomendable, sobre todo la primera vez: guarda una copia de TODOS los archivos de la '
                         'partida. Puedes ponerle un nombre para reconocerla después.\n\n'
                         'Si la última copia tiene más de {dias} días, el paso se pone amarillo para recordarte que '
                         'hagas otra con "{novo_backup}".',
        'intro_titulo_5': 'Marca los mapas que quieres empezar de nuevo',
        'intro_texto_5': 'Haz clic en la casilla (o en el nombre) de cada mapa, o usa "Marcar todos". La barrita '
                         'muestra cuánto has avanzado en las misiones de ese mapa.\n\n'
                         'Los mapas con "{resetado}" ya están listos: sus misiones empiezan desde cero cuando entres '
                         'en el mapa.',
        'intro_titulo_6': 'Reiniciar',
        'intro_texto_6': 'Cierra el juego, haz clic en el botón verde "{resetar}" y revisa en la pantalla de '
                         'confirmación lo que va a cambiar. Antes, el programa hace solo una copia de las misiones.'
                         '\n\n'
                         'Justo debajo está el cuadro "{desfazer}", con los botones para volver atrás y el enlace '
                         '"{como_desfazer}", que lo explica paso a paso.',
        'intro_titulo_7': 'Después del reinicio',
        'intro_texto_7': 'Abre el juego normalmente. Si Steam Cloud o Epic Cloud pregunta qué versión usar, elige la '
                         'LOCAL (de este ordenador). Entra en el mapa: las misiones empiezan desde cero.\n\n'
                         '¿Quieres ver este tutorial otra vez? Haz clic en "{ajuda}", arriba en la ventana. ¡Buena '
                         'caza!',
        'il_verif_1': 'Juego cerrado',
        'il_verif_2': 'Nada está usando los archivos de la partida',
        'il_verif_3': 'Steam abierto: normalmente no estorba',

        'desfazer_janela': 'Cómo deshacer',
        'desfazer_ultimo_botao': 'Entendido',
        'desfazer_passo_1': 'CÓMO DESHACER',
        'desfazer_passo_2': 'RESTAURAR MISIONES · 1',
        'desfazer_passo_3': 'RESTAURAR MISIONES · 2',
        'desfazer_passo_4': 'COPIA ORIGINAL',
        'desfazer_passo_5': 'PARTIDA COMPLETA',
        'desfazer_passo_6': 'DESPUÉS DE RESTAURAR',
        'desfazer_titulo_1': 'Dos formas de volver atrás',
        'desfazer_texto_1': 'En el cuadro "{desfazer}", debajo del botón de reiniciar:\n'
                            '•  "{restaurar}": devuelve SOLO las misiones. Úsalo para deshacer un reinicio.\n'
                            '•  "{restaurar_save}": devuelve la partida ENTERA (dinero, armas, animales, todo). Úsalo '
                            'solo si algo salió muy mal.',
        'desfazer_titulo_2': 'Elige la copia',
        'desfazer_titulo_3': 'Revisa y confirma',
        'desfazer_texto_3': 'Abajo, la tabla muestra cada mapa "Ahora" y "Después de restaurar". Las filas '
                            'AMARILLAS son las que van a cambiar.\n\n'
                            'Si está bien, haz clic en "Restaurar esta copia" y confirma. Antes se guarda la partida '
                            'actual, así que puedes volver atrás de nuevo.',
        'desfazer_titulo_4': 'Tu copia original 🔒',
        'desfazer_texto_4': 'La primera vez que usas el programa, guarda tus misiones como estaban. Esa copia original '
                            'se queda PARA SIEMPRE, no importa cuántos reinicios hagas después.\n\n'
                            'Para recuperarlo todo como era: "{restaurar}" → elige la fila verde "🔒 Copia original", '
                            'siempre arriba en la lista → "Restaurar esta copia".',
        'desfazer_titulo_5': 'Restaurar la partida completa',
        'desfazer_texto_5': 'Haz clic en "{restaurar_save}" y elige una copia completa (el nombre que le pusiste '
                            'aparece en la lista).\n\n'
                            'Atención: TODO lo que jugaste después de esa copia vuelve atrás, no solo las misiones. '
                            'Antes se guarda la partida actual, por seguridad.',
        'desfazer_titulo_6': 'Después de restaurar',
        'desfazer_texto_6': 'Abre el juego normalmente. Si Steam Cloud o Epic Cloud pregunta qué versión usar, elige la '
                            'LOCAL (de este ordenador). Si eliges la de la nube, la restauración se deshace.\n\n'
                            'Listo: todo vuelve a estar como en la copia elegida.',
        'il_amarelo': 'Amarillo = va a cambiar',
        'il_original_sempre': '🔒 Siempre arriba, nunca se borra',
        'il_apelido_exemplo': 'antes del DLC',
        'il_save_aviso': 'Todo lo jugado después de esa copia vuelve atrás',
        'il_restaurado': 'Todo vuelve como estaba en la copia',
        'desfazer_texto_2': 'Haz clic en "{restaurar}". Se abre la lista de copias de las misiones: la 🔒 copia '
                            'original siempre está arriba y, justo debajo, las demás, de la más reciente a la más '
                            'antigua. Cada una dice por qué se hizo (ej.: "Antes de reiniciar Te Awaroa").\n\n'
                            'Para deshacer el último reinicio, elige la primera justo debajo del 🔒.',
    },
}
