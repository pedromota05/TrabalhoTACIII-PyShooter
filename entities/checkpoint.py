"""
entities/checkpoint.py — Bandeira de checkpoint (desenhada com pygame.draw).

Fica cinza até o jogador passar por ela; depois fica verde. A posição de
mundo (`world_x`, `ground_y`) é guardada para o renascimento.
"""

import pygame
from config import TILE_SIZE

POLE_COLOR = (70, 50, 35)
FLAG_OFF = (150, 150, 150)
FLAG_ON = (60, 220, 90)
POLE_HEIGHT = 70
FLAG_SIZE = (30, 20)


def _flag_image(color: tuple) -> pygame.Surface:
    w, h = FLAG_SIZE[0] + 8, POLE_HEIGHT
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (0, 0, 0), (1, 0, 6, h))           # contorno do mastro
    pygame.draw.rect(surf, POLE_COLOR, (2, 1, 4, h - 1))
    pygame.draw.circle(surf, (230, 200, 60), (4, 3), 3)        # ponta do mastro
    tip = (6 + FLAG_SIZE[0], 6 + FLAG_SIZE[1] // 2)
    points = [(6, 6), tip, (6, 6 + FLAG_SIZE[1])]                # bandeira triangular
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, (0, 0, 0), points, 2)
    return surf


class CheckpointFlag(pygame.sprite.Sprite):
    """Bandeira na coluna `col`, apoiada no chão em `ground_y` (coordenadas de mundo)."""

    _images: dict = {}

    def __init__(self, col: int, ground_y: int):
        super().__init__()
        if not CheckpointFlag._images:
            CheckpointFlag._images = {False: _flag_image(FLAG_OFF), True: _flag_image(FLAG_ON)}
        self.col = col
        self.world_x = col * TILE_SIZE + TILE_SIZE // 2
        self.ground_y = ground_y
        self.active = False
        self.image = CheckpointFlag._images[False]
        self.rect = self.image.get_rect(midbottom=(self.world_x, ground_y))

    def activate(self) -> None:
        self.active = True
        self.image = CheckpointFlag._images[True]

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll
