"""Renderização do cenário, entidades e HUD."""

from config import BG_COLOR, SCREEN_HEIGHT, WHITE, YELLOW


def draw_background(game) -> None:
    """Desenha o background com parallax conforme a fase atual."""
    game.screen.fill(BG_COLOR)

    if game.level == 4:
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

    game.player.draw(game.screen)
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
