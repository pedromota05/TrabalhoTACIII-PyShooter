"""
entities/environment.py — Elementos interativos e decorativos do cenário.
"""

import pygame
from config import TILE_SIZE


class Decoration(pygame.sprite.Sprite):
    """Sprite estático de decoração no cenário."""

    def __init__(self, img: pygame.Surface, x: int, y: int):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    """Tile de água estático ou animado com dano fatal ao jogador."""

    def __init__(self, x: int, y: int, images_list: list[pygame.Surface]):
        super().__init__()
        self.animation_list = images_list
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll

        # Animação (apenas se houver mais de 1 frame)
        if len(self.animation_list) > 1:
            if pygame.time.get_ticks() - self.update_time > 150:
                self.update_time = pygame.time.get_ticks()
                self.frame_index += 1
                if self.frame_index >= len(self.animation_list):
                    self.frame_index = 0
                self.image = self.animation_list[self.frame_index]


class Exit(pygame.sprite.Sprite):
    """Gatilho de transição de fase quando o jogador toca nele."""

    def __init__(self, img: pygame.Surface, x: int, y: int):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll
