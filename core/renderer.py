"""Renderização do cenário, entidades e HUD."""

from config import BG_COLOR, MAX_LEVELS, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, YELLOW


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

    game.health_bar.draw(game.screen, game.player.health)
    draw_text(game, 'MUNIÇÃO: ', WHITE, 10, 35)
    bullet_img = game.assets.get_image('bullet')
    for x in range(game.player.ammo):
        game.screen.blit(bullet_img, (125 + (x * 10), 40))

    draw_text(game, 'GRANADA: ', WHITE, 10, 60)
    grenade_img = game.assets.get_image('grenade')
    for x in range(game.player.grenades):
        game.screen.blit(grenade_img, (135 + (x * 15), 60))

    if game.player.speed_boost:
        draw_text(game, 'SPEED BOOST!', YELLOW, 10, 85, game.font_bold)

    if getattr(game, 'challenge_mode', False):
        draw_challenge_hud(game)
    else:
        fase, total = level_label(game)
        _blit_shadowed(game, f'FASE {fase}/{total}', WHITE, game.font_bold,
                       SCREEN_WIDTH // 2, 8)
    draw_level_banner(game)

    if getattr(game, 'checkpoint_msg_frames', 0) > 0:
        msg = game.title_font.render('CHECKPOINT!', True, (60, 220, 90))
        shadow = game.title_font.render('CHECKPOINT!', True, (0, 0, 0))
        rect = msg.get_rect(centerx=SCREEN_WIDTH // 2, top=90)
        game.screen.blit(shadow, rect.move(3, 3))
        game.screen.blit(msg, rect)


def _blit_shadowed(game, text: str, color: tuple, font, center_x: int, top: int) -> None:
    """Texto centralizado com sombra preta (legível sobre qualquer cenário)."""
    shadow = font.render(text, True, (0, 0, 0))
    image = font.render(text, True, color)
    rect = image.get_rect(centerx=center_x, top=top)
    game.screen.blit(shadow, rect.move(2, 2))
    game.screen.blit(image, rect)


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

