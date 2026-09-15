"""Atualização de entidades, combate e transições de fase."""

import pygame

from config import BLACK, MAX_LEVELS
from entities import DragonBoss, Grenade
from game_state import GameState


def update_game_entities(game) -> None:
    """Atualiza a física e a lógica de todas as entidades ativas."""
    game.player.update(game.enemy_group)

    for enemy in game.enemy_group:
        enemy.ai(
            game.player, game.screen_scroll,
            game.world.obstacle_list, game.water_group,
            game.bullet_group,
        )
        enemy.update()

    for boss in game.boss_group:
        boss.rect.x += game.screen_scroll
        if isinstance(boss, DragonBoss):
            boss.update(
                game.player,
                game.world.obstacle_list,
                bullet_group=game.bullet_group,
            )
        else:
            boss.update(game.player, game.world.obstacle_list, 0.75)

    game.bullet_group.update(
        game.screen_scroll, game.world.obstacle_list,
        game.player, game.bullet_group, game.enemy_group, game.boss_group,
    )
    game.grenade_group.update(
        game.screen_scroll, game.world.obstacle_list,
        game.player, game.enemy_group, game.explosion_group,
        game.boss_group,
    )
    game.explosion_group.update(game.screen_scroll)
    game.item_box_group.update(game.screen_scroll, game.player)
    game.decoration_group.update(game.screen_scroll)
    game.water_group.update(game.screen_scroll)
    game.exit_group.update(game.screen_scroll)


def update_playing(game) -> None:
    """Executa um frame de gameplay ativo."""
    game._update_game_entities()
    game._draw_game_entities()

    if game.start_intro:
        if game.intro_fade.fade(game.screen):
            game.start_intro = False
            game.intro_fade.fade_counter = 0

    if game.player.alive:
        if game.shoot:
            game.player.shoot(game.bullet_group)
        elif game.grenade_input and not game.grenade_thrown and game.player.grenades > 0:
            grenade_obj = Grenade(
                game.player.rect.centerx + (0.5 * game.player.rect.size[0] * game.player.direction),
                game.player.rect.top,
                game.player.direction,
            )
            game.grenade_group.add(grenade_obj)
            game.player.grenades -= 1
            game.grenade_thrown = True

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
        )
        game.bg_scroll -= game.screen_scroll

        if level_complete:
            game.state = GameState.LEVEL_TRANSITION
    else:
        game.screen_scroll = 0
        game.state = GameState.GAME_OVER

    if game.pause_button.draw(game.screen):
        game.state = GameState.PAUSE


def update_level_transition(game) -> None:
    """Carrega a próxima fase ou retorna ao menu ao fim da campanha."""
    game.screen.fill(BLACK)
    game.start_intro = True
    game.level += 1
    game.bg_scroll = 0
    if game.level <= MAX_LEVELS:
        game._load_level(game.level)
        game.state = GameState.PLAYING
    else:
        game.level = 3
        game._load_level(game.level)
        game.state = GameState.MENU
