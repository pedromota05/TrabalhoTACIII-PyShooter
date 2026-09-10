"""
world/level_builder.py — Processador da matriz de tiles e construtor do mundo.
"""

import pygame
from config import TILE_SIZE
from asset_manager import AssetManager
from entities.player import Player
from entities.enemies import Enemy, Sniper, RobotEnemy, SkeletonEnemy, DragonBoss, Boss
from entities.items import ItemBox
from entities.environment import Decoration, Water, Exit
from ui.hud import HealthBar


class World:
    """Carrega o mapa a partir da matriz CSV, cria as instâncias de entidades e desenha os tiles."""

    def __init__(self):
        self.obstacle_list = []
        self.ramp_list = []
        self.level_length = 0

    def process_data(self, data, enemy_group, item_box_group,
                     decoration_group, water_group, exit_group, boss_group, level: int = 1):
        """Lê a matriz de tiles e cria todas as entidades do nível.

        Retorna uma tupla (player, health_bar).
        """
        assets = AssetManager()
        self.level_length = len(data[0])
        player = None
        health_bar = None

        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile == 87:
                    mid_x = x * TILE_SIZE + (TILE_SIZE // 2)
                    bottom_y = y * TILE_SIZE + TILE_SIZE
                    boss_group.add(DragonBoss(mid_x, bottom_y))
                    continue

                if 0 <= tile < len(assets.tile_images):
                    img = assets.tile_images[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    # A imagem 'cresce' para cima se for maior que o TILE_SIZE
                    img_rect.y = y * TILE_SIZE + (TILE_SIZE - img.get_height())
                    tile_data = (img, img_rect)

                    if ((0 <= tile <= 8) or (24 <= tile <= 35) or
                            tile in (12, 47, 48, 50, 58, 59, 60, 61, 65, 66, 73, 74, 75, 76, 77, 83, 84)):
                        # Obstáculo sólido
                        self.obstacle_list.append(tile_data)
                    elif tile == 85:
                        # Rampa inclinada (colisão em rampa de 45 graus)
                        self.ramp_list.append(tile_data)
                    elif tile == 70:                 # Inimigo Esqueleto
                        skeleton = SkeletonEnemy(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(skeleton)
                    elif tile in (51, 52, 53, 54, 55):  # Água de superfície animada (Fase 2)
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [
                            assets.tile_images[51],
                            assets.tile_images[52],
                            assets.tile_images[53],
                            assets.tile_images[54],
                            assets.tile_images[55]
                        ])
                        water_group.add(water)
                    elif tile in (9, 62, 63, 64, 67):  # Água de superfície animada (Fase 1/Pântano)
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [
                            assets.tile_images[9],
                            assets.tile_images[62],
                            assets.tile_images[63],
                            assets.tile_images[64],
                            assets.tile_images[67]
                        ])
                        water_group.add(water)
                    elif tile in (10, 56, 57, 68):     # Água profunda estática (Fase 1/2)
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [assets.tile_images[tile]])
                        water_group.add(water)
                    elif tile in (11, 13, 14, 71, 72, 78, 79, 80, 81, 82):  # Decorações
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:                 # Ponto de Spawn do jogador
                        player = Player(x * TILE_SIZE, y * TILE_SIZE)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:                 # Spawn de soldado inimigo
                        enemy = Enemy(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(enemy)
                    elif tile == 17:                 # Caixa de munição
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:                 # Caixa de granada
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:                 # Caixa de vida
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile in (20, 41):           # Saída da fase (Fase 1/2 e Fase 3)
                        exit_obj = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit_obj)
                    elif tile == 21:                 # Sniper (Fase 3)
                        sniper = Sniper(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(sniper)
                    elif tile == 69:                 # Inimigo Robô
                        robot = RobotEnemy(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(robot)
                    elif tile == 22:                 # Caixa de Speed Boost
                        item_box = ItemBox('Speed', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 23:                 # Placa de Aviso (Warning Sign)
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile in (36, 40, 42, 49):   # Decorações de neve (boneco, placa, árvores)
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile in (37, 38, 43, 44, 45):  # Água gelada de superfície
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [
                            assets.tile_images[37],
                            assets.tile_images[43],
                            assets.tile_images[44],
                            assets.tile_images[45]
                        ])
                        water_group.add(water)
                    elif tile in (39, 46):            # Água gelada profunda
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [assets.tile_images[tile]])
                        water_group.add(water)
                    elif tile == 86:                  # Boss Demônio
                        mid_x = x * TILE_SIZE + (TILE_SIZE // 2)
                        bottom_y = y * TILE_SIZE + TILE_SIZE
                        boss = Boss(mid_x, bottom_y)
                        boss_group.add(boss)

        return player, health_bar

    def draw(self, screen: pygame.Surface, screen_scroll: int):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])
        for tile in self.ramp_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])
