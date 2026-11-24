"""
tools/teste_multiplayer.py — Teste automático do multiplayer LAN no mesmo PC.

Abre DOIS processos headless do jogo (sem janela e sem som), cada um guiado
pelo Bot de tools/bot_fases.py:
    - host:    Game.start_multiplayer_host(porta)        (P1)
    - cliente: Game.start_multiplayer_client('127.0.0.1') (P2)

Cada processo grava um log (JSON por linha) com o que vê da partida; no fim,
este script compara os dois logs e confere:
    1. os dois jogadores se veem;
    2. posições dos inimigos iguais nos dois lados (por target_id);
    3. o tiro do cliente chega ao Host e tira vida do inimigo;
    4. inimigo morto aparece morto nos dois lados;
    5. tiros dos inimigos aparecem no cliente;
    6. a morte de um jogador não derruba o outro (o cliente morre de propósito
       e usa o Restart);
    7. troca de fase e vitória acontecem nos dois lados.

Uso (na raiz do projeto):
    python tools/teste_multiplayer.py
    Opções: --porta 5555  --max-seg 900  --morte-cliente 25 (0 = não morre)
            --fase N (Host começa na fase N; o cliente deve segui-lo)
            --sem-god (bots tomam dano normal)  --saida PASTA (logs)
            --capturas PASTA (salva a tela do host e do cliente a cada 5 s,
                              no mesmo segundo do relógio, para comparar)
            --ip ENDERECO (cliente conecta por esse IP em vez de 127.0.0.1;
                           use o IPv4 do ipconfig para passar pela placa de rede)

Usa subprocess (sem fork), então funciona no Windows. Na primeira vez o
Firewall do Windows pode pedir permissão para o Python abrir a porta UDP:
pode permitir em "Redes privadas" ou cancelar (o teste usa só 127.0.0.1).
"""

import bisect
import json
import math
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.dirname(os.path.abspath(__file__))

HOST_ID = 'P1 (Host)'
CLIENTE_ID = 'P2 (Cliente)'
LOG_A_CADA = 6            # quadros entre registros no log (0,1 s)
FIM_APOS_VITORIA = 3.0    # segundos que cada lado continua depois da vitória
QUADRO_LENTO_MS = 50      # quadro mais lento que isso = travada (A* do bot)
JANELA_TRAVADA = 1.0      # segundos descartados na comparação após uma travada
ATRASOS_INTERP = (0, 0.05, 0.1, 0.15)  # atrasos testados no item 2 (s)


def _opt(argv, nome, padrao):
    if nome in argv:
        return type(padrao)(argv[argv.index(nome) + 1])
    return padrao


# ======================================================================
#  PAPEL: um processo do jogo (host ou cliente)
# ======================================================================
def rodar_papel(argv):
    papel = _opt(argv, '--papel', 'host')
    porta = _opt(argv, '--porta', 5555)
    log_path = _opt(argv, '--log', '')
    max_seg = _opt(argv, '--max-seg', 900)
    morte_em = _opt(argv, '--morte-cliente', 25) if papel == 'cliente' else 0
    fase_ini = _opt(argv, '--fase', 1)
    god = '--sem-god' not in argv
    capturas = _opt(argv, '--capturas', '')
    if capturas:
        os.makedirs(capturas, exist_ok=True)
    seg_capturado = None

    sys.path.insert(0, TOOLS)
    import bot_fases as bf  # define SDL dummy, PYSHOOTER_SAVE temporário e relógio por quadro
    import pygame
    from game_state import GameState

    log = open(log_path, 'w', encoding='utf-8')

    def escrever(reg):
        reg['t'] = time.time()
        reg['papel'] = papel
        log.write(json.dumps(reg, ensure_ascii=False) + '\n')
        log.flush()

    game = bf.novo_jogo()
    if papel == 'host':
        ok = game.start_multiplayer_host(porta)
        if ok and fase_ini != 1:
            game.level = fase_ini
            game._load_level(fase_ini)
    else:
        ok = game.start_multiplayer_client(_opt(argv, '--ip', '127.0.0.1'), porta)
    escrever({'evento': 'inicio', 'ok': ok})
    if not ok:
        log.close()
        return 2
    game.start_intro = False
    net = game.network_client

    # ---- Instrumentação: conta mensagens sem mudar o comportamento ----
    contagem = {'hits_enviados': [], 'hits_recebidos': [], 'eshoot_enviados': 0, 'eshoot_recebidos': 0}
    orig_hit, orig_pop_hits = net.send_enemy_hit, net.pop_enemy_hits
    orig_eshoot, orig_pop_eshoot = net.send_enemy_shoot, net.pop_enemy_shoots

    def send_hit(target_id, damage):
        contagem['hits_enviados'].append([target_id, damage, time.time(), game.level])
        orig_hit(target_id, damage)

    def pop_hits():
        hits = orig_pop_hits()
        if papel == 'host':
            for tid, dmg in hits:
                contagem['hits_recebidos'].append([tid, dmg, time.time(), game.level])
        return hits

    def send_eshoot(*a, **k):
        contagem['eshoot_enviados'] += 1
        orig_eshoot(*a, **k)

    def pop_eshoot():
        tiros = orig_pop_eshoot()
        contagem['eshoot_recebidos'] += len(tiros)
        return tiros

    net.send_enemy_hit, net.pop_enemy_hits = send_hit, pop_hits
    net.send_enemy_shoot, net.pop_enemy_shoots = send_eshoot, pop_eshoot

    bot = bf.Bot(game)
    inicio = time.time()
    t_vitoria = None
    t_game_over = None
    morreu_de_proposito = False
    voltou = False
    quadro = 0
    estado_ant, fase_ant = None, None
    lento_bot = lento_quadro = 0.0   # maior tempo (ms) do bot e do quadro desde a última foto
    try:
        while time.time() - inicio < max_seg:
            quadro += 1
            bf.FRAME[0] += 1
            # ritmo de 60 quadros por segundo de verdade (a rede depende do tempo real)
            atraso = inicio + quadro / 60 - time.time()
            if atraso > 0:
                time.sleep(atraso)

            t_quadro = time.perf_counter()
            seg = time.time() - inicio
            if (morte_em and not morreu_de_proposito and seg >= morte_em
                    and game.state == GameState.PLAYING):
                morreu_de_proposito = True
                voltou = False
                game.player.health = 0
                escrever({'evento': 'morte_proposital', 'fase': game.level})
            elif god and game.player.alive and game.state == GameState.PLAYING:
                game.player.health = 100

            if (morreu_de_proposito and not voltou and game.state == GameState.PLAYING
                    and game.player.alive and not getattr(game, 'respawn_pending', False)
                    and game.player.health > 0):
                # Com vida sobrando o jogador renasce sozinho (sem tela de Restart)
                voltou = True
                escrever({'evento': 'restart', 'fase': game.level})
            if game.state == GameState.PLAYING:
                t_bot = time.perf_counter()
                bot.tick()
                lento_bot = max(lento_bot, (time.perf_counter() - t_bot) * 1000)
                game._update_playing()
            elif game.state == GameState.LEVEL_TRANSITION:
                game._update_level_transition()
                game.start_intro = False
            elif game.state == GameState.GAME_OVER:
                if t_game_over is None:
                    t_game_over = time.time()
                game.game_over_screen.update(game.screen, game)  # inimigos e rede seguem
                if game.state == GameState.GAME_OVER and time.time() - t_game_over > 3.0:
                    game.game_over_screen.restart(game)  # mesmo código do botão Restart
                    voltou = True
                    escrever({'evento': 'restart', 'fase': game.level})
            elif game.state == GameState.VICTORY:
                game.victory_screen.update(game.screen, game)
                if t_vitoria is None:
                    t_vitoria = time.time()
                elif time.time() - t_vitoria > FIM_APOS_VITORIA:
                    break
            if game.state != GameState.GAME_OVER:
                t_game_over = None
            pygame.event.pump()
            agora = int(time.time())
            if (capturas and game.state == GameState.PLAYING and agora % 5 == 0
                    and agora != seg_capturado):
                seg_capturado = agora
                pygame.image.save(game.screen, os.path.join(
                    capturas, f'mp_{agora % 100000:05d}_{papel}_fase{game.level}.png'))
            lento_quadro = max(lento_quadro, (time.perf_counter() - t_quadro) * 1000)

            if game.state.name != estado_ant or game.level != fase_ant:
                escrever({'evento': 'estado', 'estado': game.state.name, 'fase': game.level})
                estado_ant, fase_ant = game.state.name, game.level

            if quadro % LOG_A_CADA == 0:
                p = game.player
                inimigos = {}
                for grp in (game.enemy_group, game.boss_group):
                    for e in grp:
                        inimigos[str(e.target_id)] = [e.rect.x + game.bg_scroll, e.rect.y,
                                                      e.health, bool(e.alive)]
                remotos = {r.player_id: [r.world_x, r.world_y, r.health]
                           for r in game.remote_players_group}
                escrever({'evento': 'foto', 'quadro': quadro, 'estado': game.state.name,
                          'fase': game.level, 'px': p.rect.centerx + game.bg_scroll,
                          'py': p.rect.centery, 'vida': p.health, 'vivo': bool(p.alive),
                          'inimigos': inimigos, 'remotos': remotos,
                          'ms_bot': round(lento_bot, 1), 'ms_quadro': round(lento_quadro, 1)})
                lento_bot = lento_quadro = 0.0
    finally:
        escrever({'evento': 'fim', 'estado': game.state.name, 'fase': game.level,
                  'contagem': contagem})
        game.clean_multiplayer()
        log.close()
        pygame.quit()
    return 0


# ======================================================================
#  ANÁLISE: compara os logs do host e do cliente
# ======================================================================
def ler_log(path):
    regs = []
    with open(path, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                regs.append(json.loads(linha))
    return regs


def _pct(valores, p):
    if not valores:
        return None
    v = sorted(valores)
    return v[min(len(v) - 1, int(p * len(v)))]


def analisar(host_log, cli_log, morte_cliente):
    H, C = ler_log(host_log), ler_log(cli_log)
    fotos_h = [r for r in H if r['evento'] == 'foto']
    fotos_c = [r for r in C if r['evento'] == 'foto']
    fim_h = next((r for r in H if r['evento'] == 'fim'), {})
    fim_c = next((r for r in C if r['evento'] == 'fim'), {})
    cont_h = fim_h.get('contagem', {})
    cont_c = fim_c.get('contagem', {})
    res = []

    def item(nome, ok, detalhe):
        res.append({'verificacao': nome, 'ok': bool(ok), 'detalhe': detalhe})

    # 1. os dois se veem (depois de 2 s, com os dois jogando)
    t0 = min(r['t'] for r in fotos_h + fotos_c) + 2 if fotos_h and fotos_c else 0
    jog_h = [r for r in fotos_h if r['t'] > t0 and r['estado'] == 'PLAYING']
    jog_c = [r for r in fotos_c if r['t'] > t0 and r['estado'] == 'PLAYING']
    ve_h = sum(CLIENTE_ID in r['remotos'] for r in jog_h) / max(len(jog_h), 1)
    ve_c = sum(HOST_ID in r['remotos'] for r in jog_c) / max(len(jog_c), 1)
    item('1. os dois jogadores se veem', ve_h > 0.9 and ve_c > 0.9,
         f'host vê o cliente em {ve_h:.0%} das fotos; cliente vê o host em {ve_c:.0%}')

    # pares de fotos (host, cliente) tirados quase ao mesmo tempo na mesma fase
    pares = []
    j = 0
    for fc in fotos_c:
        while j + 1 < len(fotos_h) and abs(fotos_h[j + 1]['t'] - fc['t']) <= abs(fotos_h[j]['t'] - fc['t']):
            j += 1
        if fotos_h and abs(fotos_h[j]['t'] - fc['t']) <= 0.03 and fotos_h[j]['fase'] == fc['fase']:
            pares.append((fotos_h[j], fc))

    # posição do jogador remoto x posição real (atraso da interpolação incluído)
    dif_jog = []
    for fh, fc in pares:
        if HOST_ID in fc['remotos'] and fh['vivo']:
            rx, ry, _ = fc['remotos'][HOST_ID]
            dif_jog.append(math.hypot(rx - fh['px'], ry - fh['py']))

    # 2. inimigos na mesma posição
    # O A* do bot às vezes leva até ~0,6 s num quadro (custo do robô de teste, não
    # do jogo). Nesse tempo o processo para de enviar/receber e a comparação fica
    # injusta; por isso descartamos o 1 s seguinte a um quadro lento (> 50 ms).
    travadas = [r['t'] for r in fotos_h + fotos_c if r.get('ms_quadro', 0) > QUADRO_LENTO_MS]
    # O cliente desenha o inimigo com atraso (LERP de 0,2 por quadro + rede), então
    # comparamos a foto do cliente com a do host um pouco antes e usamos o atraso
    # (0 a 0,15 s) que deixa as posições mais próximas.
    th = [r['t'] for r in fotos_h]

    def foto_host(t):
        k = bisect.bisect_left(th, t)
        cand = [x for x in (k - 1, k) if 0 <= x < len(fotos_h)]
        if not cand:
            return None
        m = min(cand, key=lambda x: abs(th[x] - t))
        return fotos_h[m] if abs(th[m] - t) <= 0.03 else None

    def comparar(atraso):
        dif, desc = [], 0
        for fc in fotos_c:
            fh = foto_host(fc['t'] - atraso)
            if not fh or fh['fase'] != fc['fase'] or fh['estado'] != 'PLAYING' or fc['estado'] != 'PLAYING':
                continue
            if any(0 <= fc['t'] - x <= JANELA_TRAVADA for x in travadas):
                desc += 1
                continue
            for tid, (hx, hy, _, hv) in fh['inimigos'].items():
                if tid in fc['inimigos'] and hv and fc['inimigos'][tid][3]:
                    cx, cy = fc['inimigos'][tid][:2]
                    dif.append(math.hypot(hx - cx, hy - cy))
        return dif, desc

    tentativas = [(a,) + comparar(a) for a in ATRASOS_INTERP]
    maior = max((len(x[1]) for x in tentativas), default=0)
    # ignora atrasos com poucas fotos coincidentes (amostra pequena engana)
    tentativas = [x for x in tentativas if x[1] and len(x[1]) >= 0.5 * maior]
    atraso, dif, pares_desc = min(tentativas, key=lambda x: _pct(x[1], 0.95)) if tentativas else (0, [], 0)
    p95 = _pct(dif, 0.95)
    item('2. posições dos inimigos iguais (por target_id)', dif and p95 <= 12,
         f'{len(dif)} comparações; mediana {statistics.median(dif) if dif else 0:.1f} px, '
         f'95% até {p95 if p95 is not None else 0:.1f} px, máx {max(dif) if dif else 0:.1f} px '
         f'(tolerância 12 px; atraso da interpolação do cliente: {atraso:.2f} s; '
         f'{pares_desc} fotos descartadas por {len(travadas)} travadas do bot). '
         f'Host visto pelo cliente: mediana {statistics.median(dif_jog) if dif_jog else 0:.1f} px')

    # 3. tiro do cliente tira vida no host
    enviados = cont_c.get('hits_enviados', [])
    recebidos = cont_h.get('hits_recebidos', [])
    confirmados = 0
    for tid, dmg, t, fase in enviados:
        antes = [r for r in fotos_h if r['fase'] == fase and t - 0.5 <= r['t'] <= t and str(tid) in r['inimigos']]
        depois = [r for r in fotos_h if r['fase'] == fase and t < r['t'] <= t + 0.6 and str(tid) in r['inimigos']]
        if antes and depois and depois[-1]['inimigos'][str(tid)][2] < antes[-1]['inimigos'][str(tid)][2]:
            confirmados += 1
    item('3. tiro do cliente tira vida do inimigo no host',
         enviados and len(recebidos) >= 0.9 * len(enviados) and confirmados >= 0.8 * len(enviados),
         f'cliente acertou {len(enviados)} vezes; host recebeu {len(recebidos)} avisos; '
         f'vida caiu no host em {confirmados} deles')

    # 4. morte do inimigo nos dois lados (última foto de cada fase)
    def ultima_por_fase(fotos, limite=None):
        d = {}
        for r in fotos:
            if r['estado'] == 'PLAYING' and (limite is None or r['t'] <= limite.get(r['fase'], 0)):
                d[r['fase']] = r
        return d
    # Compara os dois lados no mesmo instante: 0,5 s antes de o primeiro deles
    # sair da fase (um inimigo morto no último quadro da fase só aparece no
    # lado que tirou a foto depois do tiro).
    uh0, uc0 = ultima_por_fase(fotos_h), ultima_por_fase(fotos_c)
    limite = {f: min(uh0[f]['t'], uc0[f]['t']) - 0.5 for f in set(uh0) & set(uc0)}
    uh, uc = ultima_por_fase(fotos_h, limite), ultima_por_fase(fotos_c, limite)
    # folga para o outro lado registrar a morte (rede + fotos a cada 0,1 s)
    folga = {f: t + 0.4 for f, t in limite.items()}
    uh2, uc2 = ultima_por_fase(fotos_h, folga), ultima_por_fase(fotos_c, folga)

    def mortos(foto):
        return {t for t, v in foto['inimigos'].items() if not v[3]}
    total_mortos, divergentes = 0, []
    for fase in sorted(set(uh) & set(uc)):
        mortos_h, mortos_c = mortos(uh[fase]), mortos(uc[fase])
        total_mortos += len(mortos_h)
        so_host = sorted(mortos_h - mortos(uc2[fase]))
        so_cliente = sorted(mortos_c - mortos(uh2[fase]))
        if so_host or so_cliente:
            divergentes.append({'fase': fase, 'so_host': so_host, 'so_cliente': so_cliente})
    item('4. inimigo morto aparece nos dois lados', total_mortos > 0 and not divergentes,
         f'{total_mortos} inimigos mortos no host; divergências: {divergentes or "nenhuma"}')

    # 5. tiros dos inimigos no cliente
    env, rec = cont_h.get('eshoot_enviados', 0), cont_c.get('eshoot_recebidos', 0)
    item('5. tiros dos inimigos aparecem no cliente', env > 0 and rec >= 0.9 * env,
         f'host disparou {env}; cliente recebeu {rec}')

    # 6. morte de um jogador não derruba o outro
    if morte_cliente:
        ev_morte = next((r for r in C if r['evento'] == 'morte_proposital'), None)
        ev_restart = next((r for r in C if r['evento'] == 'restart'), None)
        if ev_morte and ev_restart:
            janela = [r for r in fotos_h if ev_morte['t'] <= r['t'] <= ev_restart['t']]
            host_ok = all(r['estado'] in ('PLAYING', 'LEVEL_TRANSITION', 'VICTORY') for r in janela)
            host_ve = sum(CLIENTE_ID in r['remotos'] for r in janela) / max(len(janela), 1)
            depois = [r for r in fotos_c if ev_restart['t'] < r['t'] <= ev_restart['t'] + 2]
            voltou = any(r['estado'] == 'PLAYING' and r['vivo'] for r in depois)
            item('6. morte de um jogador não derruba o outro', host_ok and voltou and host_ve > 0.9,
                 f'host seguiu jogando: {host_ok}; host continuou vendo o cliente morto em {host_ve:.0%} '
                 f'das fotos; cliente voltou após o Restart: {voltou}')
        else:
            item('6. morte de um jogador não derruba o outro', False,
                 f'morte proposital registrada: {bool(ev_morte)}; restart registrado: {bool(ev_restart)}')

    # 7. troca de fase e vitória nos dois lados
    def sequencia(regs):
        seq = []
        for r in regs:
            if r['evento'] == 'estado':
                marca = 'VITORIA' if r['estado'] == 'VICTORY' else r['fase']
                if not seq or seq[-1] != marca:
                    seq.append(marca)
        return seq
    seq_h, seq_c = sequencia(H), sequencia(C)
    # Com --fase N o cliente começa na fase 1 e só depois recebe o anúncio do Host.
    if seq_h and seq_h[0] in seq_c:
        seq_c = seq_c[seq_c.index(seq_h[0]):]
    item('7. troca de fase e vitória nos dois lados',
         seq_h == seq_c and seq_h and seq_h[-1] == 'VITORIA',
         f'host: {seq_h}; cliente: {seq_c}')
    return res


# ======================================================================
#  ORQUESTRADOR
# ======================================================================
def porta_livre(porta):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(('0.0.0.0', porta))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main(argv):
    if '--papel' in argv:
        return rodar_papel(argv)

    porta = _opt(argv, '--porta', 5555)
    max_seg = _opt(argv, '--max-seg', 900)
    morte = _opt(argv, '--morte-cliente', 25)
    pasta = _opt(argv, '--saida', '') or tempfile.mkdtemp(prefix='pyshooter_mp_')
    os.makedirs(pasta, exist_ok=True)
    if not porta_livre(porta):
        print(f'A porta UDP {porta} já está em uso. Feche o jogo ou use --porta.')
        return 2

    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYTHONIOENCODING='utf-8')
    extras = [a for a in argv if a in ('--sem-god',)]
    for opc in ('--fase', '--ip', '--capturas'):
        if opc in argv:
            extras += [opc, argv[argv.index(opc) + 1]]
    procs = {}
    for papel in ('host', 'cliente'):
        env_p = dict(env, PYSHOOTER_SAVE=os.path.join(pasta, f'progresso_{papel}.json'))
        cmd = [sys.executable, os.path.abspath(__file__), '--papel', papel,
               '--porta', str(porta), '--log', os.path.join(pasta, f'{papel}.jsonl'),
               '--max-seg', str(max_seg), '--morte-cliente', str(morte)] + extras
        saida = open(os.path.join(pasta, f'{papel}_console.txt'), 'w', encoding='utf-8')
        procs[papel] = (subprocess.Popen(cmd, cwd=RAIZ, env=env_p, stdout=saida,
                                         stderr=subprocess.STDOUT), saida)
        if papel == 'host':
            time.sleep(4)  # host abre o servidor antes do cliente conectar
    print(f'Rodando host e cliente (até {max_seg} s). Logs em: {pasta}')
    try:
        for papel, (p, saida) in procs.items():
            try:
                p.wait(timeout=max_seg + 60)
            except subprocess.TimeoutExpired:
                p.kill()
                print(f'{papel}: passou do tempo e foi encerrado.')
            saida.close()
    finally:
        for p, _ in procs.values():
            if p.poll() is None:
                p.kill()

    for papel, (p, _) in procs.items():
        if p.returncode not in (0, None):
            print(f'{papel} terminou com código {p.returncode}; veja {papel}_console.txt em {pasta}')
    try:
        res = analisar(os.path.join(pasta, 'host.jsonl'), os.path.join(pasta, 'cliente.jsonl'), morte)
    except (OSError, ValueError) as e:
        print(f'Não foi possível analisar os logs: {e}')
        return 1
    time.sleep(1)
    res.append({'verificacao': 'porta liberada ao final', 'ok': porta_livre(porta), 'detalhe': f'UDP {porta}'})
    with open(os.path.join(pasta, 'resultado.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    for r in res:
        print(('OK     ' if r['ok'] else 'FALHOU ') + r['verificacao'] + ' — ' + r['detalhe'])
    print(f'Resultado salvo em {os.path.join(pasta, "resultado.json")}')
    return 0 if all(r['ok'] for r in res) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
