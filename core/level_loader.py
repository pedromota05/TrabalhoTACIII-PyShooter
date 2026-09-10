"""Carregamento de matrizes CSV e construção do mundo."""

import csv
import os

from config import COLS, LEVELS_DIR, ROWS
from entities import World


def reset_groups(game) -> None:
    """Esvazia os grupos de sprites pertencentes à sessão atual."""
    game.enemy_group.empty()
    game.boss_group.empty()
    game.bullet_group.empty()
    game.grenade_group.empty()
    game.explosion_group.empty()
    game.item_box_group.empty()
    game.decoration_group.empty()
    game.water_group.empty()
    game.exit_group.empty()


def load_level(game, level_number: int) -> None:
    """Carrega o CSV solicitado e recria o mundo e suas entidades."""
    reset_groups(game)
    world_data = [[-1] * COLS for _ in range(ROWS)]

    level_file = os.path.join(LEVELS_DIR, f'level{level_number}_data.csv')
    if not os.path.exists(level_file):
        level_file = f'level{level_number}_data.csv'

    with open(level_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for x, row in enumerate(reader):
            for y, tile in enumerate(row):
                world_data[x][y] = int(tile)

    game.world = World()
    game.player, game.health_bar = game.world.process_data(
        world_data,
        game.enemy_group,
        game.item_box_group,
        game.decoration_group,
        game.water_group,
        game.exit_group,
        game.boss_group,
        level_number,
    )
