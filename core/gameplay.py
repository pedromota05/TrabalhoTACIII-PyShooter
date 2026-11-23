"""Atualização de entidades, combate e transições de fase."""

import random
import pygame

from asset_manager import AssetManager
from config import (
    BLACK, CHECKPOINT_MSG_FRAMES, FPS, MAX_LEVELS, PLAYER_COLORS, PLAYER_START_AMMO, SIGN_RANGE_X,
    SHARED_LIVES, MAX_LIVES, LIVES_RESET_FRAMES, TILE_SIZE, SCREEN_WIDTH,
    KILL_POINTS, COMBO_WINDOW_FRAMES, COMBO_MAX, DROP_CHANCES,
    MELEE_DAMAGE, CRATE_DROPS, ARENA_MSG_FRAMES,
)
from core import progress
from entities import Boss, DragonBoss, Explosion, Grenade, RemotePlayer, effects
from entities.spider import Spider
from entities.combat.projectiles import Bullet, SniperBullet, Arrow, RobotBullet, DragonFire
from entities.items import ItemBox
from game_state import GameState
from core.horde import update_horde

# Quantos quadros de chão firme a posição de renascimento fica "atrasada".


# Espera após a morte do último chefe antes de concluir a fase (animação de morte).
BOSS_DEATH_DELAY_FRAMES = int(1.5 * FPS)
# Multiplayer: o Host repete o anúncio da fase a cada LEVEL_ANNOUNCE_FRAMES
# (UDP pode perder pacotes) e o cliente repete o pedido de troca de fase.
LEVEL_ANNOUNCE_FRAMES = 30
# Morte com vida sobrando: espera a animação de morte e renasce sozinho,
# mostrando o aviso "-1 VIDA" (sem a tela vermelha de Game Over).
RESPAWN_DELAY_FRAMES = int(1.0 * FPS)
LIFE_LOST_MSG_FRAMES = int(2.0 * FPS)


def sync_multiplayer_level(game) -> None:
    """Mantém Host e cliente na mesma fase.

    Host: anuncia a fase (mensagem "level") e atende pedidos "levelreq" dos
    clientes que chegaram à saída. Cliente: carrega a fase anunciada pelo
    Host (ou vai para a vitória). Chamado a cada quadro, inclusive na tela
    de Game Over e na de vitória."""
    net = game.network_client
    if not getattr(game, 'is_multiplayer', False) or net is None:
        return
    game.net_frames = getattr(game, 'net_frames', 0) + 1
    if game.is_host:
        victory = game.state == GameState.VICTORY
        if game.net_frames % LEVEL_ANNOUNCE_FRAMES == 1:
            net.send_level(game.level, victory, challenge=getattr(game, 'challenge_mode', False))
        for level in net.pop_level_requests():
            if level == game.level and game.state in (GameState.PLAYING, GameState.GAME_OVER):
                game.state = GameState.LEVEL_TRANSITION
        for pid, seq in net.pop_deaths():
            if (pid, seq) not in game.processed_deaths and not getattr(game, 'challenge_mode', False):
                game.processed_deaths.add((pid, seq))
                game.lives = max(0, game.lives - 1)
                net.send_lives(game.lives, game.lives_reset_counter)
        if game.net_frames % LEVEL_ANNOUNCE_FRAMES == 1:
            net.send_lives(game.lives, game.lives_reset_counter)
        # Sem vidas e todos mortos: recomeça a fase para todos
        everyone_dead = (game.state == GameState.GAME_OVER and not game.player.alive
                         and all(not r.alive for r in game.remote_players_group))
        if everyone_dead and game.lives == 0 and not getattr(game, 'challenge_mode', False):
            game.lives_reset_frames += 1
            if game.lives_reset_frames >= LIVES_RESET_FRAMES:
                restart_level_with_lives(game)
                game.lives_reset_counter += 1
                net.send_lives(game.lives, game.lives_reset_counter)
                net.send_level(game.level, challenge=getattr(game, 'challenge_mode', False))
        else:
            game.lives_reset_frames = 0
        return

    lives_info = net.get_host_lives()
    if lives_info is not None:
        game.lives, reset = lives_info
        if reset > game.lives_reset_seen:
            game.lives_reset_seen = reset
            if net.get_host_challenge():
                game.start_challenge()  # Host recomeçou o Desafio da fase 1
                game.game_over_screen.death_fade.fade_counter = 0
            else:
                restart_level_with_lives(game)

    announced = net.get_host_level()
    if announced is None or game.state == GameState.LEVEL_TRANSITION:
        return
    level, victory = announced
    challenge = net.get_host_challenge()
    mode_changed = challenge != getattr(game, 'challenge_mode', False)
    if mode_changed:
        game.challenge_mode = challenge
        if challenge:
            game.run_frames = 0
    if challenge and level in game.challenge_levels:
        game.challenge_index = game.challenge_levels.index(level)
    if victory:
        if game.state != GameState.VICTORY:
            game.state = GameState.VICTORY
    elif level != game.level or mode_changed:
        game.level = level
        game.level_request_frames = 0
        game.start_intro = True
        game._load_level(level)
        game.game_over_screen.death_fade.fade_counter = 0
        game.state = GameState.PLAYING


def register_death(game) -> None:
    """Gasta uma vida (campanha). No cliente, o Host confirma pelo anúncio 'lives'."""
    if getattr(game, 'challenge_mode', False):
        game.death_had_life = True  # Desafio tem regra própria
        return
    game.death_had_life = game.lives > 0
    game.lives = max(0, game.lives - 1)
    net = game.network_client if getattr(game, 'is_multiplayer', False) else None
    if net is None:
        return
    if game.is_host:
        net.send_lives(game.lives, game.lives_reset_counter)
    else:
        game.death_seq += 1
        net.send_death(game.death_seq)


def restart_level_with_lives(game) -> None:
    """Recomeça a fase atual do zero (sem checkpoint) com as vidas cheias."""
    game.lives = SHARED_LIVES
    game.lives_reset_frames = 0
    game.start_intro = True
    game._load_level(game.level)
    game.game_over_screen.death_fade.fade_counter = 0
    game.state = GameState.PLAYING


def restart_challenge_multiplayer(game) -> None:
    """Host: recomeça o Desafio da fase 1 para os dois jogadores."""
    game.start_challenge()
    game.game_over_screen.death_fade.fade_counter = 0
    net = game.network_client
    if net is not None:
        game.lives_reset_counter += 1
        net.send_lives(game.lives, game.lives_reset_counter)
        net.send_level(game.level, challenge=True)


def respawn_multiplayer(game) -> None:
    """Restart no multiplayer: renasce ao lado do outro jogador sem recarregar
    a fase (os inimigos e o progresso do parceiro continuam). Sem parceiro
    vivo, recarrega a fase."""
    from core.level_loader import respawn
    partners = [r for r in game.remote_players_group if r.alive]
    if not partners:
        respawn(game)
        return
    partner = partners[0]
    # world_x/world_y do parceiro são o centro dele no mundo
    _revive_at(game, partner.world_x, center_y=partner.world_y)


def respawn_after_life_lost(game) -> None:
    """Renasce na hora, sem recarregar a fase: logo depois da última bandeira
    de checkpoint ativada ou, sem bandeira, exatamente no início da fase
    (single e multiplayer; regra de 2026-11-21)."""
    from core.level_loader import respawn
    point = respawn_point(game)
    if point is None:
        respawn(game)
        return
    _revive_at(game, point[0], bottom_y=point[1])


def respawn_point(game) -> tuple[float, float] | None:
    """Ponto (x do mundo, pé) para renascer: um bloco depois da última
    bandeira ativada, ou o início da fase."""
    cp = getattr(game, 'checkpoint', None)
    if cp:
        x = cp['x'] + TILE_SIZE
        top = _ground_top_world(game, int(x // TILE_SIZE))
        if top is None:
            return (cp['x'], cp['y'])
        return (x, top)
    return getattr(game, 'level_start', None)


def _ground_top_world(game, col: int) -> int | None:
    """Topo do bloco sólido mais alto na coluna `col` do mundo (com a câmera em qualquer ponto)."""
    tops = [rect.top for _, rect in game.world.obstacle_list
            if (rect.left + game.bg_scroll) // TILE_SIZE == col]
    return min(tops) if tops else None


def _revive_at(game, world_x: float, center_y: float | None = None,
               bottom_y: float | None = None) -> None:
    """Põe o jogador de volta, vivo, na posição do mundo dada."""
    from core.level_loader import move_camera
    move_camera(game, world_x)
    player = game.player
    if bottom_y is not None:
        player.rect.midbottom = (int(world_x - game.bg_scroll), int(bottom_y))
    else:
        player.rect.center = (int(world_x - game.bg_scroll), int(center_y))
    player.vel_y = 0
    player.in_air = True
    player.alive = True
    player.health = player.max_health
    player.speed = player.base_speed
    player.ammo = max(player.ammo, PLAYER_START_AMMO)
    player.invincible = 120
    player.update_action(0)


def is_level_complete(game, touched_exit: bool) -> bool:
    """A fase termina ao tocar a saída ou, numa fase de chefes sem saída,
    cerca de 1,5 s depois que todos os chefes morrem."""
    if getattr(game, 'horde_active', False):
        if getattr(game, 'is_multiplayer', False) and not getattr(game, 'is_host', False):
            return False
        return getattr(game, 'horde_done', False)
    if touched_exit:
        # Portal de saída trancado enquanto houver chefe (Boss ou DragonBoss) vivo
        if bosses_remaining(game):
            show_arena_message(game, 'Derrote todos os chefes para liberar a saída!',
                               (255, 210, 90), big=False)
            return False
        return True
    if len(game.exit_group) or not len(game.boss_group):
        return False
    if getattr(game, 'boss_queue', None):
        return False
    if any(boss.alive for boss in game.boss_group):
        game.boss_clear_frames = 0
        return False
    game.boss_clear_frames = getattr(game, 'boss_clear_frames', 0) + 1
    return game.boss_clear_frames >= BOSS_DEATH_DELAY_FRAMES


def update_checkpoints(game) -> None:
    """Ativa a bandeira quando o jogador passa por ela e guarda o estado para renascer."""
    if game.checkpoint_msg_frames > 0:
        game.checkpoint_msg_frames -= 1
    if getattr(game, 'level_banner_frames', 0) > 0:
        game.level_banner_frames -= 1
    # No multiplayer a bandeira vale para a dupla: ativa quando qualquer um passa.
    xs = [game.player.rect.centerx + game.bg_scroll]
    if getattr(game, 'is_multiplayer', False):
        xs += [r.world_x for r in game.remote_players_group]
    front_x = max(xs)
    for flag in game.checkpoint_group:
        if flag.active or front_x < flag.world_x:
            continue
        flag.activate()
        mortos = {e.target_id for grp in (game.enemy_group, game.boss_group)
                  for e in grp if not e.alive}
        if game.checkpoint:
            mortos |= game.checkpoint['inimigos_mortos']
        game.checkpoint = {
            'col': flag.col, 'x': flag.world_x, 'y': flag.ground_y,
            'ammo': game.player.ammo, 'grenades': game.player.grenades,
            'inimigos_mortos': mortos,
        }
        game.checkpoint_msg_frames = CHECKPOINT_MSG_FRAMES


def update_signs(game) -> None:
    """Marca a placa perto do jogador e abre/fecha o balão com a tecla E."""
    player = game.player
    near = None
    for sign in getattr(game, 'signs', []):
        if (abs(sign.rect.centerx - player.rect.centerx) <= SIGN_RANGE_X
                and abs(sign.rect.bottom - player.rect.bottom) <= 80):
            near = sign
            break
    game.near_sign = near
    if near is None:
        game.open_sign = None
    if getattr(game, 'sign_toggle', False):
        game.sign_toggle = False
        if near is not None:
            game.open_sign = None if game.open_sign is near else near


def update_fun(game) -> None:
    """Atualiza pontuação, combo, drops e efeitos visuais a cada quadro."""
    all_enemies = list(game.enemy_group) + list(game.boss_group) + list(getattr(game, 'spider_group', []))
    for s in all_enemies:
        if not s.alive and not getattr(s, '_counted', False):
            s._counted = True
            base = KILL_POINTS.get(type(s).__name__, 100)
            if getattr(game, 'combo_timer', 0) > 0:
                game.combo = min(COMBO_MAX, getattr(game, 'combo', 0) + 1)
            else:
                game.combo = 1
            game.combo_timer = COMBO_WINDOW_FRAMES
            ganho = base * game.combo
            game.score += ganho
            game.level_score += ganho

            if game.combo >= 2:
                txt = f"+{ganho}  x{game.combo}"
                cor = (255, 230, 90)
            else:
                txt = f"+{ganho}"
                cor = (255, 255, 255)
            game.fun_fx_group.add(effects.FloatingText(txt, s.rect.centerx, s.rect.top, cor, 20))

            if s in game.boss_group:
                effects.shake(30, 10)
            elif hasattr(s, 'target_id') and (not hasattr(game, 'spider_group') or s not in game.spider_group):
                rng = random.Random(s.target_id * 7919 + game.level)
                r = rng.random()
                cum = 0.0
                for tipo, chance in DROP_CHANCES:
                    cum += chance
                    if r < cum:
                        box = ItemBox(tipo, s.rect.x, s.rect.y)
                        box.rect.midbottom = s.rect.midbottom
                        box.base_y = box.rect.y
                        box.dropped = True
                        game.item_box_group.add(box)
                        break

    if getattr(game, 'combo_timer', 0) > 0:
        game.combo_timer -= 1
        if game.combo_timer == 0:
            game.combo = 0

    for txt in effects.pop_texts():
        game.fun_fx_group.add(txt)
    game.fun_fx_group.update(game.screen_scroll)


def break_crate(game, crate: dict, sync: bool = True) -> None:
    """Quebra uma caixa de madeira (tile 12), solta lascas e sorteia o conteúdo."""
    if hasattr(game, 'world'):
        if crate.get('tile') in game.world.obstacle_list:
            game.world.obstacle_list.remove(crate['tile'])
        if crate in getattr(game.world, 'crates', []):
            game.world.crates.remove(crate)

    crate_rect = crate['tile'][1]

    # Partículas: 8 lascas marrons no fun_fx_group
    if hasattr(game, 'fun_fx_group') and game.fun_fx_group is not None:
        for _ in range(8):
            game.fun_fx_group.add(effects.Debris(crate_rect.centerx, crate_rect.centery))

    # Conteúdo sorteado deterministicamente (igual no Host e Cliente)
    rng = random.Random(crate['col'] * 1000 + crate['row'] + game.level * 7)
    r = rng.random()
    cum = 0.0
    chosen = None
    for tipo, chance in CRATE_DROPS:
        cum += chance
        if r < cum:
            chosen = tipo
            break

    if chosen in ('Ammo', 'Grenade', 'Health', 'Life'):
        # Criada com a posição do MUNDO para o item_id ser igual nos dois PCs;
        # sem `dropped`, quem pegar primeiro faz o item sumir no outro PC.
        box = ItemBox(chosen, crate['col'] * TILE_SIZE, crate['row'] * TILE_SIZE)
        box.rect.midbottom = crate_rect.midbottom
        box.base_y = box.rect.y
        game.item_box_group.add(box)
    elif chosen == 'Spider' and hasattr(game, 'spider_group'):
        spider = Spider(crate_rect.centerx, crate_rect.bottom)
        game.spider_group.add(spider)

    if sync and getattr(game, 'is_multiplayer', False) and getattr(game, 'network_client', None):
        game.network_client.send_crate(game.level, crate['col'], crate['row'])


def update_melee(game) -> None:
    """Processa o golpe com a arma (botão direito) contra inimigos, chefes, aranhas e caixas."""
    if not getattr(game, 'melee_input', False):
        return
    game.melee_input = False

    if not (game.player and game.player.alive and game.player.start_melee()):
        return

    m_rect = game.player.melee_rect()
    effects.shake(6, 4)

    is_mp = getattr(game, 'is_multiplayer', False)
    is_host = getattr(game, 'is_host', False)
    net = game.network_client if is_mp else None

    # Inimigos
    for enemy in game.enemy_group:
        if enemy.alive and m_rect.colliderect(enemy.rect):
            if is_mp and not is_host and net and hasattr(enemy, 'target_id'):
                net.send_enemy_hit(enemy.target_id, MELEE_DAMAGE)
                effects.damage_text(enemy.rect.centerx, enemy.rect.top, MELEE_DAMAGE)
                enemy.hit_flash = 6
            else:
                enemy.health -= MELEE_DAMAGE
                effects.damage_text(enemy.rect.centerx, enemy.rect.top, MELEE_DAMAGE)
                enemy.hit_flash = 6
                if enemy.health <= 0:
                    enemy.health = 0
                    enemy.alive = False
                    if hasattr(enemy, 'update_action'):
                        enemy.update_action(3)
                elif hasattr(enemy, 'animation_list') and len(enemy.animation_list) > 4:
                    enemy.update_action(4)

    # Chefes
    for boss in game.boss_group:
        if boss.alive and getattr(boss, 'activated', True) and m_rect.colliderect(boss.rect):
            if is_mp and not is_host and net and hasattr(boss, 'target_id'):
                net.send_enemy_hit(boss.target_id, MELEE_DAMAGE)
                effects.damage_text(boss.rect.centerx, boss.rect.top, MELEE_DAMAGE)
                boss.hit_flash = 6
            else:
                boss.health -= MELEE_DAMAGE
                effects.damage_text(boss.rect.centerx, boss.rect.top, MELEE_DAMAGE)
                boss.hit_flash = 6
                if boss.health <= 0:
                    boss.health = 0
                    boss.alive = False
                    if hasattr(boss, 'update_action'):
                        boss.update_action(3)

    # Aranhas (locais em cada PC)
    if hasattr(game, 'spider_group'):
        for spider in game.spider_group:
            if spider.alive and m_rect.colliderect(spider.rect):
                spider.health -= MELEE_DAMAGE
                effects.damage_text(spider.rect.centerx, spider.rect.top, MELEE_DAMAGE)
                spider.hit_flash = 6
                if spider.health <= 0:
                    spider.health = 0
                    spider.alive = False
                    spider.death_timer = 20

    # Caixas quebráveis
    if hasattr(game, 'world') and hasattr(game.world, 'crates'):
        for crate in list(game.world.crates):
            if m_rect.colliderect(crate['tile'][1]):
                break_crate(game, crate, sync=True)


def show_arena_message(game, text: str, color: tuple = (255, 255, 255), big: bool = True) -> None:
    """Mostra um aviso temporário (~3 s) no topo/centro da tela (desenhado pelo renderer)."""
    game.arena_msg = text
    game.arena_msg_color = color
    game.arena_msg_big = big
    game.arena_msg_frames = ARENA_MSG_FRAMES


def reset_arena_state(game) -> None:
    """Zera as flags da Arena de Chefes (chamado ao carregar/reiniciar a fase)."""
    game.gate_opened = False
    game.arena_msg = ''
    game.arena_msg_frames = 0


def bosses_remaining(game) -> bool:
    """True se ainda existe algum chefe vivo na fase (inclusive na fila de reserva)."""
    groups = (game.boss_group, getattr(game, 'boss_reserve_group', ()))
    return any(boss.alive for grp in groups for boss in grp) or bool(getattr(game, 'boss_queue', None))


def demons_alive(game) -> bool:
    """True se algum Boss Demônio da fase ainda está vivo."""
    groups = (game.boss_group, getattr(game, 'boss_reserve_group', ()))
    return any(isinstance(b, Boss) and b.alive for grp in groups for b in grp)


def update_boss_arena(game) -> None:
    """Arena de Chefes: abre o Portão quando todos os Demônios morrem e
    atualiza o contador 'CHEFE x/y' conforme os chefes caem."""
    if getattr(game, 'horde_active', False) or not hasattr(game, 'world'):
        return

    world = game.world
    demons = [b for b in game.boss_group if isinstance(b, Boss)]
    if (world.boss_gate_tiles and demons and not getattr(game, 'gate_opened', False)
            and all(not b.alive for b in demons)):
        removed = world.open_boss_gate()
        game.gate_opened = True
        AssetManager().get_sound('grenade').play()
        effects.shake(20, 8)
        targets = removed if len(removed) <= 6 else removed[::2]
        for rect in targets:
            game.explosion_group.add(Explosion(rect.centerx, rect.centery, 1.5))
        show_arena_message(game, 'PASSAGEM LIBERADA!', (90, 230, 120))

    # Sem fila sequencial (arena), a etapa acompanha quantos chefes já caíram
    if not getattr(game, 'boss_queue', None) and getattr(game, 'boss_stage_total', 0) >= 2:
        dead = sum(1 for b in game.boss_group if not b.alive)
        game.boss_stage = min(game.boss_stage_total, 1 + dead)


def update_boss_stages(game) -> None:
    """Avança as etapas dos chefes em fases com múltiplos chefes sequenciais."""
    if getattr(game, 'horde_active', False):
        return

    if getattr(game, 'boss_stage_banner', 0) > 0:
        game.boss_stage_banner -= 1

    boss_queue = getattr(game, 'boss_queue', None)
    if boss_queue and len(game.boss_group) and not any(boss.alive for boss in game.boss_group):
        game.boss_stage_frames = getattr(game, 'boss_stage_frames', 0) + 1
        if game.boss_stage_frames >= BOSS_DEATH_DELAY_FRAMES:
            next_boss = game.boss_queue.pop(0)
            if hasattr(game, 'boss_reserve_group'):
                game.boss_reserve_group.remove(next_boss)
            game.boss_group.add(next_boss)
            game.boss_stage = getattr(game, 'boss_stage', 1) + 1
            game.boss_stage_banner = 150
            game.boss_stage_frames = 0
            rect = next_boss.rect
            points = [
                (rect.centerx, rect.centery),
                (rect.left + rect.width * 0.25, rect.top + rect.height * 0.25),
                (rect.right - rect.width * 0.25, rect.bottom - rect.height * 0.25),
            ]
            for px, py in points:
                game.explosion_group.add(Explosion(px, py, 2))
            AssetManager().get_sound('grenade').play()
    elif any(boss.alive for boss in game.boss_group):
        game.boss_stage_frames = 0


def get_target_player(entity, local_player, remote_players_group):
    """Retorna o jogador vivo mais próximo da entidade (seja local ou remoto)."""
    candidates = []
    if getattr(local_player, 'alive', False):
        dist = abs(entity.rect.centerx - local_player.rect.centerx)
        candidates.append((dist, local_player))
    for remote in remote_players_group:
        if getattr(remote, 'alive', False):
            dist = abs(entity.rect.centerx - remote.rect.centerx)
            candidates.append((dist, remote))
    if not candidates:
        return local_player
    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]


def update_game_entities(game) -> None:
    """Atualiza a física e a lógica de todas as entidades ativas."""
    is_multiplayer = getattr(game, 'is_multiplayer', False)
    is_host = getattr(game, 'is_host', False)
    net_client = game.network_client if is_multiplayer else None

    sync_multiplayer_level(game)

    # Atualiza o jogador local
    game.player.update(game.enemy_group)

    # Jogador morto (tela de Game Over) continua mandando sinal de vida ao
    # servidor; sem isso ele cai por timeout após 5 s e deixa de receber a
    # partida (inimigos, troca de fase).
    if is_multiplayer and net_client and not game.player.alive:
        net_client.send_state(
            game.player.rect.centerx + game.bg_scroll, game.player.rect.centery,
            3, game.player.direction, False, 0,
        )

    # ------------------------------------------------------------------
    # Sincronização de Inimigos e Bosses
    # ------------------------------------------------------------------
    if is_multiplayer and not is_host and net_client:
        # === MODO CLIENTE: O Host é a autoridade sobre os inimigos ===
        # 1. Cria projéteis de inimigos disparados remotamente pelo Host
        for shoot_data in net_client.pop_enemy_shoots():
            b_type = shoot_data.get("bullet_type")
            sx = shoot_data["world_x"] - game.bg_scroll
            sy = shoot_data["world_y"]
            b_dir = shoot_data.get("direction", 1)

            if b_type == "bullet":
                game.bullet_group.add(Bullet(sx, sy, b_dir))
                AssetManager().get_sound('shot').play()
            elif b_type == "sniper":
                game.bullet_group.add(SniperBullet(sx, sy, shoot_data["vel_x"], shoot_data["vel_y"]))
                AssetManager().get_sound('shot').play()
            elif b_type == "arrow":
                tx = shoot_data["target_wx"] - game.bg_scroll
                ty = shoot_data["target_wy"]
                game.bullet_group.add(Arrow(sx, sy, tx, ty))
                AssetManager().get_sound('skeleton_bow').play()
            elif b_type == "robot":
                game.bullet_group.add(RobotBullet(sx, sy, shoot_data["vel_x"], shoot_data["vel_y"]))
                AssetManager().get_sound('robot_shoot').play()
            elif b_type == "dragon":
                tx = shoot_data["target_wx"] - game.bg_scroll
                ty = shoot_data["target_wy"]
                game.bullet_group.add(DragonFire(sx, sy, tx, ty))

        # 2. Interpola e sincroniza estado dos inimigos com a visão do Host
        net_client.pop_enemy_hits()  # acertos são do Host; aqui só esvazia a fila
        net_client.update_enemy_interpolation()
        enemies_snapshot = net_client.get_remote_enemies_snapshot()
        if net_client.get_enemies_level() != game.level:
            enemies_snapshot = {}  # lote ainda é da fase anterior

        for enemy in game.enemy_group:
            t_id = getattr(enemy, 'target_id', None)
            if t_id is not None and t_id in enemies_snapshot:
                e_data = enemies_snapshot[t_id]
                curr_wx, curr_wy = e_data["current"]
                enemy.rect.x = int(curr_wx - game.bg_scroll)
                enemy.rect.y = int(curr_wy)
                enemy.direction = e_data["direction"]
                enemy.flip = (enemy.direction == -1)
                enemy.health = e_data["health"]
                enemy.alive = e_data["alive"]
                if not enemy.alive or enemy.health <= 0:
                    enemy.alive = False
                    enemy.health = 0
                    if enemy.action != 3 and hasattr(enemy, 'update_action'):
                        enemy.update_action(3)
                else:
                    if enemy.action != e_data["action"] and hasattr(enemy, 'update_action'):
                        enemy.update_action(e_data["action"])
                if hasattr(enemy, 'update_animation'):
                    enemy.update_animation()
            else:
                enemy.rect.x += game.screen_scroll
                if hasattr(enemy, 'update_animation'):
                    enemy.update_animation()

        for boss in game.boss_group:
            t_id = getattr(boss, 'target_id', None)
            if t_id is not None and t_id in enemies_snapshot:
                b_data = enemies_snapshot[t_id]
                curr_wx, curr_wy = b_data["current"]
                boss.rect.x = int(curr_wx - game.bg_scroll)
                boss.rect.y = int(curr_wy)
                boss.direction = b_data["direction"]
                boss.flip = (boss.direction == -1)
                boss.health = b_data["health"]
                boss.alive = b_data["alive"]
                if not boss.alive or boss.health <= 0:
                    boss.alive = False
                    boss.health = 0
                    if boss.action != 3 and hasattr(boss, 'update_action'):
                        boss.update_action(3)
                else:
                    if boss.action != b_data["action"] and hasattr(boss, 'update_action'):
                        boss.update_action(b_data["action"])
                if hasattr(boss, 'update_animation'):
                    boss.update_animation(game.player)
            else:
                boss.rect.x += game.screen_scroll
                if hasattr(boss, 'update_animation'):
                    boss.update_animation(game.player)

            # O Host é quem roda a IA; aqui só espelhamos o "despertar" do Dragão
            # (para os tiros do cliente passarem a causar dano e mostrar o aviso).
            if isinstance(boss, DragonBoss) and not boss.activated and boss.alive:
                host_awake = t_id in enemies_snapshot and enemies_snapshot[t_id]["action"] in (1, 2)
                if host_awake:
                    boss.activated = True
                else:
                    boss.try_activate(game.player, not demons_alive(game))
                if boss.activated:
                    show_arena_message(game, 'CHEFE FINAL: DRAGÃO DESPERTOU!', (235, 60, 50))
            if isinstance(boss, DragonBoss) and boss.alive and not boss.enraged and boss.health <= boss.max_health * 0.5:
                boss.enraged = True
                show_arena_message(game, 'O DRAGÃO ENTROU EM FÚRIA!', (255, 120, 30))

    else:
        # === MODO HOST OU SINGLE PLAYER: Executa IA e Física Local ===
        if is_multiplayer and is_host and net_client:
            # Processa acertos de tiro/dano recebidos dos clientes da rede
            incoming_hits = net_client.pop_enemy_hits()
            if incoming_hits:
                target_map = {}
                for enemy in game.enemy_group:
                    if hasattr(enemy, 'target_id'):
                        target_map[enemy.target_id] = enemy
                for boss in game.boss_group:
                    if hasattr(boss, 'target_id'):
                        target_map[boss.target_id] = boss

                for target_id, damage in incoming_hits:
                    if target_id in target_map:
                        target = target_map[target_id]
                        if target.alive and getattr(target, 'activated', True):
                            target.health -= damage
                            if target.health <= 0:
                                target.health = 0
                                target.alive = False
                                if hasattr(target, 'update_action'):
                                    target.update_action(3)
                            else:
                                if hasattr(target, 'animation_list') and len(target.animation_list) > 4:
                                    target.update_action(4)

        for enemy in game.enemy_group:
            target_player = get_target_player(enemy, game.player, game.remote_players_group)
            enemy.ai(
                target_player, game.screen_scroll,
                game.world.obstacle_list, game.water_group,
                game.bullet_group,
                network_client=net_client if (is_multiplayer and is_host) else None,
                bg_scroll=game.bg_scroll,
            )
            enemy.update()

        can_wake_dragon = not demons_alive(game)
        for boss in game.boss_group:
            boss.rect.x += game.screen_scroll
            target_player = get_target_player(boss, game.player, game.remote_players_group)
            if isinstance(boss, DragonBoss):
                was_active = boss.activated
                was_enraged = boss.enraged
                # screen_scroll já foi aplicado acima (não passar de novo para não rolar em dobro)
                boss.update(
                    target_player,
                    game.world.obstacle_list,
                    bullet_group=game.bullet_group,
                    network_client=net_client if (is_multiplayer and is_host) else None,
                    bg_scroll=game.bg_scroll,
                    can_activate=can_wake_dragon,
                )
                if boss.activated and not was_active:
                    show_arena_message(game, 'CHEFE FINAL: DRAGÃO DESPERTOU!', (235, 60, 50))
                elif boss.enraged and not was_enraged:
                    show_arena_message(game, 'O DRAGÃO ENTROU EM FÚRIA!', (255, 120, 30))
            else:
                boss.update(target_player, game.world.obstacle_list, 0.75)

        # Se for Host no Multiplayer, envia lote de estado dos inimigos para os clientes
        if is_multiplayer and is_host and net_client:
            enemies_payload_list = []
            for enemy in game.enemy_group:
                t_id = getattr(enemy, 'target_id', 0)
                wx = enemy.rect.x + game.bg_scroll
                wy = enemy.rect.y
                alive_val = 1 if enemy.alive else 0
                enemies_payload_list.append(
                    f"{t_id}:{round(wx, 1)}:{round(wy, 1)}:{enemy.action}:{enemy.direction}:{enemy.health}:{alive_val}:0"
                )
            for boss in game.boss_group:
                t_id = getattr(boss, 'target_id', 0)
                wx = boss.rect.x + game.bg_scroll
                wy = boss.rect.y
                alive_val = 1 if boss.alive else 0
                enemies_payload_list.append(
                    f"{t_id}:{round(wx, 1)}:{round(wy, 1)}:{boss.action}:{boss.direction}:{boss.health}:{alive_val}:1"
                )
            if enemies_payload_list:
                net_client.send_enemies_state(enemies_payload_list, game.level)

    # ------------------------------------------------------------------
    # Atualização de grupos de projéteis e ambiente
    # ------------------------------------------------------------------
    game.bullet_group.update(
        game.screen_scroll, game.world.obstacle_list,
        game.player, game.bullet_group, game.enemy_group, game.boss_group,
    )
    if hasattr(game, 'spider_group'):
        for bullet in list(game.bullet_group):
            if getattr(bullet, 'has_hit', False) or getattr(bullet, 'visual_only', False):
                continue
            for spider in game.spider_group:
                if spider.alive and bullet.rect.colliderect(spider.rect):
                    bullet.kill()
                    spider.health -= 25
                    effects.damage_text(spider.rect.centerx, spider.rect.top, 25)
                    spider.hit_flash = 6
                    if spider.health <= 0:
                        spider.health = 0
                        spider.alive = False
                        spider.death_timer = 20
                    break
        game.spider_group.update(game.screen_scroll, game.player, game.world.obstacle_list)
    game.grenade_group.update(
        game.screen_scroll, game.world.obstacle_list,
        game.player, game.enemy_group, game.explosion_group,
        game.boss_group,
    )
    game.explosion_group.update(game.screen_scroll)
    net_items = game.network_client if getattr(game, 'is_multiplayer', False) else None
    if net_items is not None:
        # Caixas que o parceiro pegou somem aqui também (sem dar o efeito).
        for lvl, item_id in net_items.pop_item_pickups():
            if lvl != game.level:
                continue
            for box in list(game.item_box_group):
                if getattr(box, 'dropped', False):
                    continue
                if box.item_id == item_id:
                    box.kill()
    fx_group = getattr(game, 'item_fx_group', None)
    for box in list(game.item_box_group):
        box_net = None if getattr(box, 'dropped', False) else net_items
        box.update(game.screen_scroll, game.player, box_net, game.level, fx_group)
    if fx_group is not None:
        fx_group.update(game.screen_scroll)
    game.decoration_group.update(game.screen_scroll)
    game.water_group.update(game.screen_scroll)
    game.exit_group.update(game.screen_scroll)
    game.checkpoint_group.update(game.screen_scroll)
    if hasattr(game, 'boss_reserve_group'):
        for b in game.boss_reserve_group:
            b.rect.x += game.screen_scroll

    # ------------------------------------------------------------------
    # Sincronização e interpolação de jogadores remotos em LAN
    # ------------------------------------------------------------------
    if getattr(game, 'color_msg_frames', 0) > 0:
        game.color_msg_frames -= 1

    if is_multiplayer and net_client:
        net_client.update_interpolation()
        remote_data = net_client.get_remote_players_snapshot()

        for p_id, p_info in remote_data.items():
            if p_id not in game.remote_players_map:
                remote_sprite = RemotePlayer(p_id, p_info["current"][0], p_info["current"][1])
                game.remote_players_map[p_id] = remote_sprite
                game.remote_players_group.add(remote_sprite)

            game.remote_players_map[p_id].update_from_network(
                p_info, game.bg_scroll, game.bullet_group
            )
            rem_color = net_client.get_remote_color(p_id)
            game.remote_players_map[p_id].set_color(rem_color)

            # Cliente troca de cor automaticamente se o parceiro (Host) já estiver com ela
            if not game.is_host and net_client.has_remote_color(p_id):
                current_color = getattr(game.player, 'color', 0)
                if rem_color == current_color:
                    new_color = (current_color + 1) % len(PLAYER_COLORS)
                    while new_color == rem_color:
                        new_color = (new_color + 1) % len(PLAYER_COLORS)
                    color_name = PLAYER_COLORS[new_color][0]
                    game.player.set_color(new_color)
                    net_client.send_color(new_color)
                    game.color_msg = f"Cor trocada para {color_name}: o parceiro já usa essa"
                    game.color_msg_frames = 120

        for p_id in list(game.remote_players_map.keys()):
            if p_id not in remote_data:
                game.remote_players_map[p_id].kill()
                del game.remote_players_map[p_id]



def update_playing(game) -> None:
    """Executa um frame de gameplay ativo."""
    game.run_frames = getattr(game, 'run_frames', 0) + 1
    game._update_game_entities()
    game._draw_game_entities()

    if game.start_intro:
        if game.intro_fade.fade(game.screen):
            game.start_intro = False
            game.intro_fade.fade_counter = 0

    if game.player.alive:
        net_client = game.network_client if getattr(game, 'is_multiplayer', False) else None
        target = pygame.mouse.get_pos() if getattr(game, 'use_mouse_aim', False) else None
        if target:
            game.player.face_point(*target)

        if game.shoot:
            game.player.shoot(game.bullet_group, network_client=net_client, target=target)
        elif game.grenade_input and not game.grenade_thrown and game.player.grenades > 0:
            grenade_obj = Grenade(
                game.player.rect.centerx + (0.5 * game.player.rect.size[0] * game.player.direction),
                game.player.rect.top,
                game.player.direction,
                network_client=net_client,
            )
            game.grenade_group.add(grenade_obj)
            game.player.grenades -= 1
            game.grenade_thrown = True

        if getattr(game, 'dash_input', False):
            game.player.start_dash(game.moving_left, game.moving_right)
            game.dash_input = False

        if game.player.in_air:
            game.player.update_action(2)
        elif game.moving_left or game.moving_right:
            game.player.update_action(1)
        else:
            game.player.update_action(0)

        game.screen_scroll, level_complete = game.player.move(
            game.moving_left, game.moving_right,
            game.world.obstacle_list, game.water_group,
            game.exit_group, game.bg_scroll, game.world.level_length,
            game.world.ramp_list,
            game.remote_players_group if getattr(game, 'is_multiplayer', False) else None,
        )
        if target and getattr(game, 'use_mouse_aim', False):
            game.player.face_point(*target)

        game.bg_scroll -= game.screen_scroll
        update_checkpoints(game)
        update_boss_stages(game)
        update_boss_arena(game)
        update_horde(game)
        update_signs(game)
        update_fun(game)
        update_melee(game)

        # Processamento de caixas quebradas recebidas via rede
        if getattr(game, 'is_multiplayer', False) and getattr(game, 'network_client', None):
            for lvl, col, row in game.network_client.pop_crates():
                if lvl == game.level and hasattr(game, 'world') and hasattr(game.world, 'crates'):
                    for c in list(game.world.crates):
                        if c['col'] == col and c['row'] == row:
                            break_crate(game, c, sync=False)
                            break

        # Processamento de vida extra (coração / lifeup)
        net_life = game.network_client if getattr(game, 'is_multiplayer', False) else None
        if getattr(game, 'is_multiplayer', False) and getattr(game, 'is_host', False) and net_life:
            for _ in net_life.pop_lifeups():
                game.lives = min(MAX_LIVES, game.lives + 1)
                net_life.send_lives(game.lives, game.lives_reset_counter)
                if hasattr(game, 'fun_fx_group') and game.fun_fx_group is not None:
                    game.fun_fx_group.add(effects.FloatingText("+1 VIDA", game.player.rect.centerx, game.player.rect.top, (60, 220, 90), 22))

        if hasattr(game, 'player') and game.player is not None:
            while getattr(game.player, 'pending_life_up', 0) > 0:
                game.player.pending_life_up -= 1
                if getattr(game, 'is_multiplayer', False) and not getattr(game, 'is_host', False) and net_life:
                    net_life.send_lifeup()
                else:
                    game.lives = min(MAX_LIVES, game.lives + 1)
                    if getattr(game, 'is_multiplayer', False) and getattr(game, 'is_host', False) and net_life:
                        net_life.send_lives(game.lives, game.lives_reset_counter)
                if hasattr(game, 'fun_fx_group') and game.fun_fx_group is not None:
                    game.fun_fx_group.add(effects.FloatingText("+1 VIDA", game.player.rect.centerx, game.player.rect.top, (60, 220, 90), 22))

        # Envio periódico de estado via UDP em modo multiplayer
        if getattr(game, 'is_multiplayer', False) and getattr(game, 'network_client', None):
            local_world_x = game.player.rect.centerx + game.bg_scroll
            local_world_y = game.player.rect.centery
            game.network_client.send_state(
                local_world_x, local_world_y,
                game.player.action, game.player.direction,
                game.shoot, game.player.health,
                aim=getattr(game.player, 'aim_angle', 0.0)
            )
            if game.run_frames % 60 == 1:
                game.network_client.send_color(getattr(game.player, 'color', 0))

        if is_level_complete(game, level_complete):
            if getattr(game, 'is_multiplayer', False) and not game.is_host and game.network_client:
                # Cliente não troca de fase sozinho: pede ao Host, que avisa todos.
                game.level_request_frames = getattr(game, 'level_request_frames', 0) + 1
                if game.level_request_frames % LEVEL_ANNOUNCE_FRAMES == 1:
                    game.network_client.send_level_request(game.level)
            else:
                game.state = GameState.LEVEL_TRANSITION
    else:
        game.screen_scroll = 0
        update_fun(game)
        challenge_mp = (getattr(game, 'challenge_mode', False)
                        and getattr(game, 'is_multiplayer', False))
        partner_alive = any(r.alive for r in game.remote_players_group)             if getattr(game, 'is_multiplayer', False) else False
        if getattr(game, 'challenge_spectating', False):
            # Desafio em dupla: quem caiu assiste; se o parceiro também cair,
            # o Desafio acaba para os dois.
            if not partner_alive:
                game.challenge_spectating = False
                game.state = GameState.GAME_OVER
            else:
                # Câmera acompanha o parceiro aos poucos (o corpo caído vai junto)
                from core.level_loader import move_camera
                partner = next(r for r in game.remote_players_group if r.alive)
                focus = game.bg_scroll + SCREEN_WIDTH // 3
                move_camera(game, focus + (partner.world_x - focus) * 0.12)
        elif not getattr(game, 'respawn_pending', False):
            register_death(game)
            if challenge_mp and partner_alive:
                # Desafio = uma vida só: sem renascer e sem tela vermelha;
                # volta na próxima fase se o parceiro terminar esta.
                game.challenge_spectating = True
            elif game.death_had_life and not getattr(game, 'challenge_mode', False):
                # Ainda tem vida: só um aviso e renasce sozinho em 1 s.
                game.respawn_pending = True
                game.respawn_frames = RESPAWN_DELAY_FRAMES
                game.life_lost_frames = LIFE_LOST_MSG_FRAMES
            else:
                game.state = GameState.GAME_OVER
        else:
            game.respawn_frames -= 1
            if game.respawn_frames <= 0:
                game.respawn_pending = False
                respawn_after_life_lost(game)

    if getattr(game, 'life_lost_frames', 0) > 0:
        game.life_lost_frames -= 1
    if getattr(game, 'arena_msg_frames', 0) > 0:
        game.arena_msg_frames -= 1

    if game.pause_button.draw(game.screen):
        game.state = GameState.PAUSE


def update_challenge_transition(game) -> None:
    """Modo Desafio: avança para a próxima fase da lista levando vida, munição
    e granadas; depois da última, grava o tempo e mostra a vitória.
    Não marca fases nem a campanha como concluídas."""
    game.challenge_index += 1
    if game.challenge_index >= len(game.challenge_levels):
        game.challenge_new_record = False if getattr(game, 'challenge_cheat', False) else progress.registrar_tempo_desafio(game.run_frames / FPS)
        game.state = GameState.VICTORY
        return
    old = game.player
    carried = (old.health, old.ammo, old.grenades)
    game.level = game.challenge_levels[game.challenge_index]
    game._load_level(game.level)
    new = game.player
    new.health = min(carried[0], new.max_health)  # vida máxima continua 100
    if not old.alive or carried[0] <= 0:
        new.health = new.max_health // 2  # caiu no Desafio em dupla: volta com metade
    new.ammo, new.grenades = carried[1], carried[2]
    game.state = GameState.PLAYING


def update_level_transition(game) -> None:
    """Carrega a próxima fase ou vai para a tela de vitória ao fim da campanha."""
    game.screen.fill(BLACK)
    game.start_intro = True
    host_net = (game.network_client
                if getattr(game, 'is_multiplayer', False) and getattr(game, 'is_host', False) else None)
    if getattr(game, 'challenge_mode', False):
        update_challenge_transition(game)
        if host_net:
            host_net.send_level(game.level, game.state == GameState.VICTORY, challenge=True)
        return
    progress.marcar_fase(game.level)
    game.game_over_screen.death_fade.fade_counter = 0
    if game.level >= MAX_LEVELS:
        # Só conta como campanha zerada quando todas as fases já foram vencidas
        # (quem escolhe a fase 4 direto no menu não libera o Desafio).
        if set(range(1, MAX_LEVELS + 1)) <= set(progress.carregar()['fases_concluidas']):
            progress.marcar_campanha_zerada()
        game.state = GameState.VICTORY
        if host_net:
            host_net.send_level(game.level, True, challenge=getattr(game, 'challenge_mode', False))
        return
    game.level += 1
    game._load_level(game.level)
    game.state = GameState.PLAYING
    if host_net:
        host_net.send_level(game.level, challenge=getattr(game, 'challenge_mode', False))  # anúncio imediato; repetido a cada 0,5 s
