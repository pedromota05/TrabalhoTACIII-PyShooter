"""
ui/hud.py — Barra de vida e elementos do HUD.
"""

import pygame
from config import BLACK, RED, GREEN


class HealthBar:
    """Barra de vida visual desenhada na tela."""

    def __init__(self, x: int, y: int, health: int, max_health: int):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, screen: pygame.Surface, health: int):
        self.health = health
        ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))
