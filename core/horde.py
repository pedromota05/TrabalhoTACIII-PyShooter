"""
core/horde.py — Gerenciador de hordas de inimigos na Fase 5 (Modo Desafio).
"""

import pygame
from asset_manager import AssetManager
from config import (
    HORDE_WAVES, HORDE_BANNER_FRAMES, HORDE_PAUSE_FRAMES,
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
)
from entities import Boss, DragonBoss, Enemy, Explosion, ItemBox, RobotEnemy, SkeletonEnemy, Sniper
from entities.spider import Spider


def start_horde(game) -> None:
    """Inicializa as variáveis de controle de horda para a Fase 5."""
    game.horde_active = True
    game.horde_wave = 0
    game.horde_total = len(HORDE_WAVES)
    game.horde_pause = 90  # 1,5 s antes da 1ª onda
    game.horde_banner = 0
    game.horde_done = False
    game.horde_idle = 0
    game.horde_last_alive = 0


def spawn_wave(game, n: int, base_x: float) -> None:
    """Cria os inimigos da onda `n` (1-indexed)."""
    # Remove sprites mortos antigos para não acumular
    for grp in (game.enemy_group, game.boss_group, getattr(game, 'spider_group', ())):
        for s in list(grp):
            if not getattr(s, 'alive', False):
                s.kill()

    if not (1 <= n <= len(HORDE_WAVES)):
        return

    wave_data = HORDE_WAVES[n - 1]
    k_left = 0
    k_right = 0

    for i, (tipo, lado) in enumerate(wave_data):
        target_id = 1000 + n * 50 + i

        if tipo == 'Boss':
            # Perto da borda direita da tela do Host (base_x é igual nos dois PCs)
            x_mundo = base_x + SCREEN_WIDTH * 3 // 4
            coluna = int(x_mundo // TILE_SIZE)
            tops = [r.top for _, r in game.world.obstacle_list
                    if (r.left + game.bg_scroll) // TILE_SIZE == coluna]
            y_pe = min(tops) if tops else 15 * TILE_SIZE
            x_tela = x_mundo - game.bg_scroll
            boss = Boss(x_tela, y_pe)
            boss.rect.midbottom = (int(x_tela), int(y_pe))
            boss.target_id = target_id
            game.boss_group.add(boss)

            rect = boss.rect
            points = [
                (rect.centerx, rect.centery),
                (rect.left + rect.width * 0.25, rect.top + rect.height * 0.25),
                (rect.right - rect.width * 0.25, rect.bottom - rect.height * 0.25),
            ]
            for px, py in points:
                game.explosion_group.add(Explosion(px, py, 2))
            try:
                AssetManager().get_sound('grenade').play()
            except Exception:
                pass

        elif tipo == 'DragonBoss':
            x_mundo = base_x + SCREEN_WIDTH // 2  # voa no meio da tela
            y_pe = 11 * TILE_SIZE
            x_tela = x_mundo - game.bg_scroll
            dragon = DragonBoss(x_tela, y_pe)
            dragon.activated = True  # na Horda o Dragão já nasce acordado (sem arena)
            dragon.rect.midbottom = (int(x_tela), int(y_pe))
            dragon.target_id = target_id
            game.boss_group.add(dragon)

            rect = dragon.rect
            points = [
                (rect.centerx, rect.centery),
                (rect.left + rect.width * 0.25, rect.top + rect.height * 0.25),
                (rect.right - rect.width * 0.25, rect.bottom - rect.height * 0.25),
            ]
            for px, py in points:
                game.explosion_group.add(Explosion(px, py, 2))
            try:
                AssetManager().get_sound('grenade').play()
            except Exception:
                pass

        else:
            if lado == -1:
                k = k_left
                k_left += 1
                x_mundo = base_x + 40 + 25 * k
            else:
                k = k_right
                k_right += 1
                x_mundo = base_x + SCREEN_WIDTH - 40 - 25 * k

            coluna = int(x_mundo // TILE_SIZE)
            tops = [rect.top for _, rect in game.world.obstacle_list if (rect.left + game.bg_scroll) // TILE_SIZE == coluna]
            y_pe = min(tops) if tops else SCREEN_HEIGHT - 2 * TILE_SIZE
            x_tela = x_mundo - game.bg_scroll

            if tipo == 'Spider':
                spider = Spider(x_tela, y_pe)
                if hasattr(game, 'spider_group'):
                    game.spider_group.add(spider)
            else:
                if tipo == 'Enemy':
                    enemy = Enemy(x_tela, y_pe)
                elif tipo == 'Sniper':
                    enemy = Sniper(x_tela, y_pe)
                elif tipo == 'RobotEnemy':
                    enemy = RobotEnemy(x_tela, y_pe)
                elif tipo == 'SkeletonEnemy':
                    enemy = SkeletonEnemy(x_tela, y_pe)
                else:
                    enemy = Enemy(x_tela, y_pe)

                enemy.rect.midbottom = (int(x_tela), int(y_pe))
                enemy.target_id = target_id
                game.enemy_group.add(enemy)


def update_horde(game) -> None:
    """Atualiza o ciclo de hordas a cada quadro de gameplay."""
    if not getattr(game, 'horde_active', False):
        return

    spiders = getattr(game, 'spider_group', ())
    n = (
        sum(1 for e in game.enemy_group if getattr(e, 'alive', False))
        + sum(1 for b in game.boss_group if getattr(b, 'alive', False))
        + sum(1 for s in spiders if getattr(s, 'alive', False))
    )
    last_alive = getattr(game, 'horde_last_alive', 0)
    if n == 0 or n < last_alive:
        game.horde_idle = 0
    else:
        game.horde_idle = getattr(game, 'horde_idle', 0) + 1
    game.horde_last_alive = n

    if getattr(game, 'horde_banner', 0) > 0:
        game.horde_banner -= 1

    is_mp = getattr(game, 'is_multiplayer', False)
    is_client = is_mp and not getattr(game, 'is_host', False)

    if is_client:
        net = getattr(game, 'network_client', None)
        if net:
            for lvl, n, base_x in net.pop_waves():
                if lvl == game.level and n > game.horde_wave:
                    game.horde_wave = n
                    spawn_wave(game, n, base_x)
                    game.horde_banner = HORDE_BANNER_FRAMES
    else:
        # Single Player ou Host
        has_alive = (
            any(e.alive for e in game.enemy_group)
            or any(b.alive for b in game.boss_group)
            or (hasattr(game, 'spider_group') and any(s.alive for s in game.spider_group))
        )
        if not has_alive:
            if getattr(game, 'horde_pause', 0) > 0:
                game.horde_pause -= 1
                if game.horde_pause == 0:
                    if game.horde_wave >= game.horde_total:
                        game.horde_done = True
                    else:
                        game.horde_wave += 1
                        spawn_wave(game, game.horde_wave, game.bg_scroll)
                        game.horde_banner = HORDE_BANNER_FRAMES
                        game.horde_pause = HORDE_PAUSE_FRAMES

                        # Suprimentos perto do jogador
                        if getattr(game, 'player', None):
                            box_ammo = ItemBox('Ammo', game.player.rect.centerx - 20, game.player.rect.bottom - TILE_SIZE)
                            box_ammo.rect.midbottom = (game.player.rect.centerx - 20, game.player.rect.bottom)
                            box_ammo.base_y = box_ammo.rect.y
                            box_ammo.dropped = True
                            game.item_box_group.add(box_ammo)

                            if game.horde_wave % 2 == 0:
                                box_hp = ItemBox('Health', game.player.rect.centerx + 20, game.player.rect.bottom - TILE_SIZE)
                                box_hp.rect.midbottom = (game.player.rect.centerx + 20, game.player.rect.bottom)
                                box_hp.base_y = box_hp.rect.y
                                box_hp.dropped = True
                                game.item_box_group.add(box_hp)

                        if is_mp and getattr(game, 'is_host', False) and getattr(game, 'network_client', None):
                            game.network_client.send_wave(game.level, game.horde_wave, int(game.bg_scroll))
