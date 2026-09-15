"""
ui/transitions.py — Efeitos de transição visual de tela (ScreenFade).
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class ScreenFade:
    """Efeito de fade visual para entrada e saída de fase ou morte do jogador."""

    def __init__(self, direction: int, colour: tuple[int, int, int], speed: int):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self, screen: pygame.Surface) -> bool:
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:     # Fade "abrindo" (4 retângulos)
            pygame.draw.rect(screen, self.colour,
                             (0 - self.fade_counter, 0,
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour,
                             (SCREEN_WIDTH // 2 + self.fade_counter, 0,
                              SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour,
                             (0, 0 - self.fade_counter,
                              SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour,
                             (0, SCREEN_HEIGHT // 2 + self.fade_counter,
                              SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:     # Fade vertical (cortina)
            pygame.draw.rect(screen, self.colour,
                             (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete
