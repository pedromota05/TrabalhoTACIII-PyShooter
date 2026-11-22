"""Carregamento de matrizes CSV e construção do mundo."""

import csv
import os

import pygame

from config import CHECKPOINTS, COLS, LEVEL_BANNER_FRAMES, LEVELS_DIR, ROWS, SCREEN_WIDTH, TILE_SIZE, SIGN_TEXTS, SIGN_DEFAULT_TEXT
from entities.castle import Castle, CASTLE_THEMES, FinishLine
from entities.checkpoint import CheckpointFlag
from entities.sign import Sign
from world.level_builder import World


def reset_groups(game) -> None:
    """Esvazia os grupos de sprites pertencentes à sessão atual."""
    game.enemy_group.empty()
    game.boss_group.empty()
    game.bullet_group.empty()
    game.grenade_group.empty()
    game.explosion_group.empty()
    game.item_box_group.empty()
    fx_grp = getattr(game, 'item_fx_group', None)
    if fx_grp is not None:
        fx_grp.empty()
    game.decoration_group.empty()
    game.water_group.empty()
    game.exit_group.empty()
    if hasattr(game, 'checkpoint_group'):
        game.checkpoint_group.empty()
    if hasattr(game, 'remote_players_group'):
        game.remote_players_group.empty()
    if hasattr(game, 'remote_players_map'):
        game.remote_players_map.clear()


def checkpoints_enabled(game) -> bool:
    """Checkpoints valem só na campanha solo (não no Desafio nem em LAN)."""
    return not (getattr(game, 'challenge_mode', False) or getattr(game, 'is_multiplayer', False))


def load_level(game, level_number: int, keep_checkpoint: bool = False) -> None:
    """Carrega o CSV solicitado e recria o mundo e suas entidades.

    Sem `keep_checkpoint`, o checkpoint salvo é descartado (troca de fase,
    menu, reinício normal)."""
    reset_groups(game)
    if not keep_checkpoint:
        game.checkpoint = None
    game.checkpoint_msg_frames = 0
    # Aviso "FASE N" só quando a fase começa do zero (não ao renascer no checkpoint).
    game.level_banner_frames = 0 if keep_checkpoint else LEVEL_BANNER_FRAMES
    # Zera a câmera: sem isso, o screen_scroll do último quadro da fase
    # anterior desloca o mundo novo no primeiro quadro (bg_scroll já é 0).
    game.screen_scroll = 0
    game.bg_scroll = 0
    game.boss_clear_frames = 0
    # Renascer na posição segura só vale dentro da mesma fase
    game.safe_pos = None
    game.respawn_pending = False
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

    # Atribui IDs determinísticos para inimigos e chefes para sincronização em rede
    target_id = 0
    for enemy in game.enemy_group:
        enemy.target_id = target_id
        target_id += 1
    for boss in game.boss_group:
        boss.target_id = target_id
        target_id += 1

    if hasattr(game, 'checkpoint_group') and checkpoints_enabled(game):
        for col in CHECKPOINTS.get(level_number, []):
            game.checkpoint_group.add(CheckpointFlag(col, _ground_top(game.world, col)))

    # Castelinho na saída (fases com tema). A Exit continua sendo o gatilho;
    # a imagem dela fica invisível e o castelo é só desenho (decoração).
    if level_number in CASTLE_THEMES:
        for ex in game.exit_group:
            game.decoration_group.add(Castle(level_number, ex.rect))
            # Linha de chegada no chão, 6 blocos antes do castelo
            game.decoration_group.add(FinishLine(ex.rect.centerx - 6 * TILE_SIZE, ex.rect.bottom))
            ex.image = pygame.Surface(ex.rect.size, pygame.SRCALPHA)

    # Placas: textos pela ordem da esquerda para a direita
    signs = sorted((d for d in game.decoration_group if isinstance(d, Sign)), key=lambda s: s.rect.x)
    texts = SIGN_TEXTS.get(level_number, [])
    for i, sign in enumerate(signs):
        sign.text = texts[i] if i < len(texts) else SIGN_DEFAULT_TEXT
    game.signs = signs
    game.near_sign = None
    game.open_sign = None
    game.sign_toggle = False


def _ground_top(world, col: int) -> int:
    """Topo do bloco sólido mais alto na coluna (mundo recém-carregado, bg_scroll = 0)."""
    tops = [rect.top for _, rect in world.obstacle_list if rect.left // TILE_SIZE == col]
    return min(tops) if tops else 0


def shift_world(game, offset: int) -> None:
    """Move a câmera `offset` px para a direita num mundo recém-carregado
    (bg_scroll = 0): desloca blocos e sprites e ajusta bg_scroll."""
    for _, rect in game.world.obstacle_list + game.world.ramp_list:
        rect.x -= offset
    groups = (game.enemy_group, game.boss_group, game.item_box_group,
              game.decoration_group, game.water_group, game.exit_group,
              game.checkpoint_group)
    for group in groups:
        for sprite in group:
            sprite.rect.x -= offset
    game.player.rect.x -= offset
    game.bg_scroll = offset


def respawn(game) -> None:
    """Renasce no último checkpoint: recarrega a fase, remove inimigos já
    mortos, posiciona a câmera e o jogador na bandeira com vida cheia e a
    munição guardada. Sem checkpoint, apenas recarrega a fase."""
    cp = getattr(game, 'checkpoint', None)
    load_level(game, game.level, keep_checkpoint=cp is not None)
    if cp is None:
        return

    for group in (game.enemy_group, game.boss_group):
        for enemy in list(group):
            if enemy.target_id in cp['inimigos_mortos']:
                enemy.kill()
    for flag in game.checkpoint_group:
        if flag.col <= cp['col']:
            flag.activate()

    max_offset = max(0, game.world.level_length * TILE_SIZE - SCREEN_WIDTH)
    offset = min(max(0, cp['x'] - SCREEN_WIDTH // 3), max_offset)
    shift_world(game, offset)

    player = game.player
    player.rect.midbottom = (cp['x'] - offset, cp['y'])
    player.vel_y = 0
    player.in_air = False
    player.health = player.max_health
    player.ammo = cp['ammo']
    player.grenades = cp['grenades']
    player.invincible = 60


def move_camera(game, world_x: float, level_px: int | None = None) -> None:
    """Leva a câmera para mostrar `world_x` a 1/3 da tela, em qualquer ponto
    da fase (diferente de shift_world, que exige bg_scroll = 0)."""
    if level_px is None:
        level_px = game.world.level_length * TILE_SIZE
    new_bg = int(min(max(0, world_x - SCREEN_WIDTH // 3), max(0, level_px - SCREEN_WIDTH)))
    delta = new_bg - game.bg_scroll
    if delta == 0:
        return
    for _, rect in game.world.obstacle_list + game.world.ramp_list:
        rect.x -= delta
    groups = (game.enemy_group, game.boss_group, game.item_box_group,
              game.decoration_group, game.water_group, game.exit_group,
              game.checkpoint_group, game.bullet_group, game.grenade_group,
              game.explosion_group)
    for group in groups:
        for sprite in group:
            sprite.rect.x -= delta
    game.player.rect.x -= delta
    game.bg_scroll = new_bg
