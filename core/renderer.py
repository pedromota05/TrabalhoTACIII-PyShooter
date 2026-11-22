"""Renderização do cenário, entidades e HUD."""

import math
import pygame

from config import (
    BG_COLOR, MAX_LEVELS, SCREEN_HEIGHT, SCREEN_WIDTH,
    WHITE, YELLOW, RED, BLACK, DASH_COOLDOWN, SHARED_LIVES,
    COMBO_WINDOW_FRAMES, HORDE_HINT_FRAMES,
)
from game_state import GameState


def draw_background(game) -> None:
    """Desenha o background com parallax conforme a fase atual."""
    game.screen.fill(BG_COLOR)

    if game.level >= 4:
        bg_swamp = game.assets.get_image('bg_swamp')
        swamp_width = bg_swamp.get_width()
        for i in range(5):
            game.screen.blit(bg_swamp, ((i * swamp_width) - game.bg_scroll * 0.5, 0))
    elif game.level == 2:
        bg2 = game.assets.get_image('back')
        width = bg2.get_width()
        for x in range(5):
            game.screen.blit(bg2, ((x * width) - game.bg_scroll * 0.5, 0))
    else:
        sky = game.assets.get_image('sky')
        mountain = game.assets.get_image('mountain')
        pine1 = game.assets.get_image('pine1')
        pine2 = game.assets.get_image('pine2')
        width = sky.get_width()
        for x in range(5):
            game.screen.blit(sky, ((x * width) - game.bg_scroll * 0.5, 0))
            game.screen.blit(mountain, ((x * width) - game.bg_scroll * 0.6,
                                        SCREEN_HEIGHT - mountain.get_height() - 300))
            game.screen.blit(pine1, ((x * width) - game.bg_scroll * 0.7,
                                     SCREEN_HEIGHT - pine1.get_height() - 150))
            game.screen.blit(pine2, ((x * width) - game.bg_scroll * 0.8,
                                     SCREEN_HEIGHT - pine2.get_height()))


def draw_text(game, text: str, text_col: tuple, x: int, y: int, custom_font=None) -> None:
    """Desenha texto usando a fonte padrão ou uma fonte informada."""
    font = custom_font if custom_font else game.font
    image = font.render(text, True, text_col)
    game.screen.blit(image, (x, y))


def draw_game_entities(game) -> None:
    """Desenha mundo, entidades ativas e HUD da sessão."""
    draw_background(game)
    game.world.draw(game.screen, game.screen_scroll)
    game.checkpoint_group.draw(game.screen)

    game.player.draw(game.screen)
    if getattr(game, 'is_multiplayer', False) and hasattr(game, 'remote_players_group'):
        for remote in game.remote_players_group:
            remote.draw(game.screen)

    for enemy in game.enemy_group:
        enemy.draw(game.screen)

    if hasattr(game, 'spider_group'):
        for spider in game.spider_group:
            spider.draw(game.screen)

    for boss in game.boss_group:
        boss.draw(game.screen)
        if hasattr(boss, 'draw_health_bar'):
            boss.draw_health_bar(game.screen)

    game.bullet_group.draw(game.screen)
    game.grenade_group.draw(game.screen)
    game.explosion_group.draw(game.screen)
    game.item_box_group.draw(game.screen)
    item_fx = getattr(game, 'item_fx_group', None)
    if item_fx is not None:
        item_fx.draw(game.screen)
    game.decoration_group.draw(game.screen)
    game.water_group.draw(game.screen)
    game.exit_group.draw(game.screen)
    if hasattr(game, 'fun_fx_group') and game.fun_fx_group is not None:
        game.fun_fx_group.draw(game.screen)

    game.health_bar.draw(game.screen, game.player.health)
    draw_text(game, 'MUNIÇÃO: ', WHITE, 10, 35)
    bullet_img = game.assets.get_image('bullet')
    for x in range(game.player.ammo):
        game.screen.blit(bullet_img, (125 + (x * 10), 40))

    draw_text(game, 'GRANADA: ', WHITE, 10, 60)
    grenade_img = game.assets.get_image('grenade')
    for x in range(game.player.grenades):
        game.screen.blit(grenade_img, (135 + (x * 15), 60))

    draw_text(game, f'PONTOS: {game.score}', WHITE, 10, 85, game.font_bold)
    if getattr(game, 'combo', 0) >= 2:
        score_w = game.font_bold.size(f'PONTOS: {game.score}')[0]
        combo_x = 10 + score_w + 15
        draw_text(game, f'COMBO x{game.combo}', YELLOW, combo_x, 85, game.font_bold)
        timer_ratio = max(0.0, min(1.0, game.combo_timer / COMBO_WINDOW_FRAMES))
        bar_w = int(60 * timer_ratio)
        pygame.draw.rect(game.screen, (50, 50, 50), pygame.Rect(combo_x, 108, 60, 4))
        if bar_w > 0:
            pygame.draw.rect(game.screen, YELLOW, pygame.Rect(combo_x, 108, bar_w, 4))

    if game.player.speed_boost:
        draw_text(game, 'SPEED BOOST!', YELLOW, 10, 110, game.font_bold)

    if getattr(game, 'challenge_mode', False):
        draw_challenge_hud(game)
    else:
        fase, total = level_label(game)
        _blit_shadowed(game, f'FASE {fase}/{total}', WHITE, game.font_bold,
                       SCREEN_WIDTH // 2, 8)
        # Vidas alinhadas à direita, terminando antes do botão de pausa
        # (SCREEN_WIDTH - 60); antes as bolinhas ficavam por baixo dele.
        vidas_w = game.font_bold.size('VIDAS:')[0]
        slots = max(SHARED_LIVES, getattr(game, 'lives', 0))
        right = SCREEN_WIDTH - 75
        start_x = right - (vidas_w + 14 + (slots - 1) * 22 + 8)
        draw_text(game, 'VIDAS:', WHITE, start_x, 10, game.font_bold)
        for i in range(slots):
            cx = start_x + vidas_w + 14 + (i * 22)
            if i < getattr(game, 'lives', 0):
                pygame.draw.circle(game.screen, RED, (cx, 22), 8)
            pygame.draw.circle(game.screen, BLACK, (cx, 22), 8, 2)

    if getattr(game, 'boss_stage_total', 0) >= 2 and not getattr(game, 'horde_active', False):
        _blit_shadowed(game, f'CHEFE {game.boss_stage}/{game.boss_stage_total}', WHITE,
                       game.font_bold, SCREEN_WIDTH // 2, 40)

    if getattr(game, 'horde_active', False):
        total = getattr(game, 'horde_total', 5)
        wave = getattr(game, 'horde_wave', 0)
        _blit_shadowed(game, f'ONDA {wave}/{total}', WHITE, game.font_bold,
                       SCREEN_WIDTH // 2, 92)
        has_alive = (
            any(e.alive for e in game.enemy_group)
            or any(b.alive for b in game.boss_group)
            or (hasattr(game, 'spider_group') and any(s.alive for s in game.spider_group))
        )
        if not has_alive and wave < total and getattr(game, 'horde_pause', 0) > 0:
            secs = max(1, (game.horde_pause + 59) // 60)
            _blit_shadowed(game, f'PRÓXIMA ONDA EM {secs}s', YELLOW, game.font_bold,
                           SCREEN_WIDTH // 2, 114)
        draw_enemy_arrow(game)

    if getattr(game, 'challenge_spectating', False):
        _blit_shadowed(game, 'VOCÊ CAIU!', (235, 60, 50), game.title_font, SCREEN_WIDTH // 2, 150)
        _blit_shadowed(game, 'Desafio: uma vida só. Aguardando o parceiro terminar a fase...',
                       WHITE, game.font_bold, SCREEN_WIDTH // 2, 210)
    if getattr(game, 'color_msg_frames', 0) > 0:
        _blit_shadowed(game, getattr(game, 'color_msg', ''), YELLOW, game.font_bold,
                       SCREEN_WIDTH // 2, 120)
    draw_level_banner(game)

    if getattr(game, 'boss_stage_banner', 0) > 0 and not getattr(game, 'horde_active', False):
        _blit_shadowed(game, f'ETAPA {game.boss_stage}/{game.boss_stage_total}', (235, 60, 50),
                       game.title_font, SCREEN_WIDTH // 2, 150)
        _blit_shadowed(game, 'Um novo chefe apareceu!', WHITE,
                       game.font_bold, SCREEN_WIDTH // 2, 210)

    if getattr(game, 'horde_active', False) and getattr(game, 'horde_banner', 0) > 0:
        total = getattr(game, 'horde_total', 5)
        wave = getattr(game, 'horde_wave', 0)
        title = 'ONDA FINAL!' if wave >= total else f'ONDA {wave}'
        _blit_shadowed(game, title, (235, 60, 50),
                       game.title_font, SCREEN_WIDTH // 2, 150)
        sub = 'Prepare-se!' if wave < total else 'Derrote os chefes!'
        _blit_shadowed(game, sub, WHITE,
                       game.font_bold, SCREEN_WIDTH // 2, 210)

    if getattr(game, 'life_lost_frames', 0) > 0:
        # Aviso de vida perdida (o jogador renasce sozinho, sem tela de Game Over)
        _blit_shadowed(game, '-1 VIDA', (235, 60, 50), game.title_font, SCREEN_WIDTH // 2, 150)
        lives = getattr(game, 'lives', 0)
        sub = 'Última vida!' if lives == 0 else f'Restam {lives}'
        _blit_shadowed(game, sub, WHITE, game.font_bold, SCREEN_WIDTH // 2, 210)

    if getattr(game, 'checkpoint_msg_frames', 0) > 0:
        msg = game.title_font.render('CHECKPOINT!', True, (60, 220, 90))
        shadow = game.title_font.render('CHECKPOINT!', True, (0, 0, 0))
        rect = msg.get_rect(centerx=SCREEN_WIDTH // 2, top=90)
        game.screen.blit(shadow, rect.move(3, 3))
        game.screen.blit(msg, rect)

    draw_sign_ui(game)


def _blit_shadowed(game, text: str, color: tuple, font, center_x: int, top: int) -> None:
    """Texto centralizado com sombra preta (legível sobre qualquer cenário)."""
    shadow = font.render(text, True, (0, 0, 0))
    image = font.render(text, True, color)
    rect = image.get_rect(centerx=center_x, top=top)
    game.screen.blit(shadow, rect.move(2, 2))
    game.screen.blit(image, rect)


def draw_enemy_arrow(game) -> None:
    """Mostra seta apontando para o inimigo mais próximo se o jogador demorar a matar na horda."""
    if not getattr(game, 'horde_active', False):
        return
    if getattr(game, 'horde_idle', 0) < HORDE_HINT_FRAMES:
        return
    player = getattr(game, 'player', None)
    if player is None or not getattr(player, 'alive', False):
        return

    candidates = []
    for grp in (getattr(game, 'enemy_group', ()), getattr(game, 'boss_group', ()), getattr(game, 'spider_group', ())):
        for e in grp:
            if getattr(e, 'alive', False) and hasattr(e, 'rect'):
                candidates.append(e)

    if not candidates:
        return

    px, py = player.rect.center
    closest = min(candidates, key=lambda e: math.hypot(e.rect.centerx - px, e.rect.centery - py))
    tx, ty = closest.rect.center

    angle = math.atan2(ty - py, tx - px)
    dist = 60.0 + 5.0 * math.sin(pygame.time.get_ticks() / 150.0)
    cx = px + dist * math.cos(angle)
    cy = py + dist * math.sin(angle)

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    tip = (cx + 13.0 * cos_a, cy + 13.0 * sin_a)
    base_center_x = cx - 13.0 * cos_a
    base_center_y = cy - 13.0 * sin_a
    left = (base_center_x - 9.0 * sin_a, base_center_y + 9.0 * cos_a)
    right = (base_center_x + 9.0 * sin_a, base_center_y - 9.0 * cos_a)

    points = [tip, left, right]
    pygame.draw.polygon(game.screen, YELLOW, points)
    pygame.draw.polygon(game.screen, BLACK, points, 2)

    _blit_shadowed(game, 'Siga a seta!', YELLOW, game.font_bold, SCREEN_WIDTH // 2, 136)


def draw_challenge_hud(game) -> None:
    """Cronômetro (mm:ss.d) e 'FASE x/5' no topo central durante o Modo Desafio."""
    from ui.screens.victory import format_time  # import tardio evita ciclo com ui.screens
    total = len(game.challenge_levels)
    _blit_shadowed(game, format_time(game.run_frames), YELLOW, game.title_font, SCREEN_WIDTH // 2, 8)
    fase = min(game.challenge_index + 1, total)  # após a última fase o índice passa do total
    _blit_shadowed(game, f'FASE {fase}/{total}', WHITE, game.font_bold,
                   SCREEN_WIDTH // 2, 68)


def level_label(game) -> tuple[int, int]:
    """(fase atual, total) para o HUD: no Desafio conta pela lista do desafio."""
    if getattr(game, 'challenge_mode', False):
        total = len(game.challenge_levels)
        return min(game.challenge_index + 1, total), total
    return game.level, MAX_LEVELS


def draw_level_banner(game) -> None:
    """Aviso grande 'FASE N' centralizado enquanto level_banner_frames > 0."""
    if getattr(game, 'level_banner_frames', 0) <= 0:
        return
    fase, total = level_label(game)
    _blit_shadowed(game, f'FASE {fase}', WHITE, game.title_font,
                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)
    _blit_shadowed(game, f'de {total}', WHITE, game.font_bold,
                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


def draw_sign_ui(game) -> None:
    """'E' sobre a placa próxima; balão com a dica quando aberta."""
    sign = getattr(game, 'near_sign', None)
    if sign is None:
        return
    if getattr(game, 'open_sign', None) is not sign:
        key = game.font_bold.render('E', True, WHITE)
        box = key.get_rect(midbottom=(sign.rect.centerx, sign.rect.top - 6)).inflate(12, 6)
        pygame.draw.rect(game.screen, (20, 20, 30), box, border_radius=5)
        pygame.draw.rect(game.screen, WHITE, box, 2, border_radius=5)
        game.screen.blit(key, key.get_rect(center=box.center))
        return
    # Balão no topo da tela com quebra de linha
    width = 620
    words, lines, line = sign.text.split(), [], ''
    for w in words:
        test = (line + ' ' + w).strip()
        if game.font.size(test)[0] > width - 30:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    lh = game.font.get_height() + 4
    height = 20 + lh * len(lines) + lh
    rect = pygame.Rect(0, 0, width, height)
    rect.midtop = (SCREEN_WIDTH // 2, 70)
    pygame.draw.rect(game.screen, (245, 232, 200), rect, border_radius=10)
    pygame.draw.rect(game.screen, (90, 60, 30), rect, 3, border_radius=10)
    y = rect.top + 10
    for text in lines:
        surf = game.font.render(text, True, (40, 25, 10))
        game.screen.blit(surf, surf.get_rect(midtop=(rect.centerx, y)))
        y += lh
    hint = game.font.render('E para fechar', True, (110, 80, 50))
    game.screen.blit(hint, hint.get_rect(midtop=(rect.centerx, y)))


def draw_crosshair(game) -> None:
    """Desenha a mira do mouse e a barra de cooldown do dash."""
    aim = (
        game.state == GameState.PLAYING
        and getattr(game, 'use_mouse_aim', False)
        and game.player is not None
        and game.player.alive
    )

    if getattr(game, '_cursor_hidden', None) != aim:
        pygame.mouse.set_visible(not aim)
        game._cursor_hidden = aim

    if not aim:
        return

    mx, my = pygame.mouse.get_pos()
    circle_color = (255, 220, 60) if game.player.shoot_cooldown > 0 else WHITE

    # Círculo de raio 10 e espessura 2 (contorno preto primeiro com espessura +2 = 4)
    pygame.draw.circle(game.screen, BLACK, (mx, my), 10, 4)
    pygame.draw.circle(game.screen, circle_color, (mx, my), 10, 2)

    # 4 tracinhos de 6 px saindo do círculo (cima, baixo, esquerda, direita)
    tracos = [
        ((mx, my - 10), (mx, my - 16)),
        ((mx, my + 10), (mx, my + 16)),
        ((mx - 10, my), (mx - 16, my)),
        ((mx + 10, my), (mx + 16, my)),
    ]
    for start, end in tracos:
        pygame.draw.line(game.screen, BLACK, start, end, 4)
    for start, end in tracos:
        pygame.draw.line(game.screen, circle_color, start, end, 2)

    # Ponto central de raio 2 (contorno preto primeiro)
    pygame.draw.circle(game.screen, BLACK, (mx, my), 4)
    pygame.draw.circle(game.screen, circle_color, (mx, my), 2)

    # Barrinha de recarga do dash (24x4 px, centralizada, 16 px abaixo)
    dash_cd = getattr(game.player, 'dash_cooldown', 0)
    if dash_cd > 0:
        bar_x = mx - 12
        bar_y = my + 16
        pygame.draw.rect(game.screen, (50, 50, 50), pygame.Rect(bar_x, bar_y, 24, 4))
        prog = max(0.0, min(1.0, 1.0 - (dash_cd / DASH_COOLDOWN)))
        fill_w = int(24 * prog)
        if fill_w > 0:
            pygame.draw.rect(game.screen, (90, 160, 255), pygame.Rect(bar_x, bar_y, fill_w, 4))


