"""
entities/effects.py — Efeitos visuais, textos flutuantes e tremor de tela.
"""

import random
import pygame
from config import FONT_NAME

_fonts: dict[int, pygame.font.Font] = {}


def _get_font(size: int) -> pygame.font.Font:
    """Cache simples de fontes do Pygame por tamanho."""
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(FONT_NAME, size, bold=True)
    return _fonts[size]


class FloatingText(pygame.sprite.Sprite):
    """Texto flutuante com contorno preto que sobe e some em 40 quadros."""

    def __init__(self, text: str, x: int, y: int, color: tuple, size: int = 20):
        super().__init__()
        font = _get_font(size)
        fg = font.render(text, True, color)
        bg = font.render(text, True, (0, 0, 0))

        w = fg.get_width() + 4
        h = fg.get_height() + 4
        base = pygame.Surface((w, h), pygame.SRCALPHA)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx != 0 or dy != 0:
                    base.blit(bg, (2 + dx, 2 + dy))
        base.blit(fg, (2, 2))

        self.base = base
        self.image = self.base.copy()
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.timer = 40

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll
        self.rect.y -= 1
        self.timer -= 1
        if self.timer <= 20:
            self.image = self.base.copy()
            self.image.set_alpha(max(0, int(255 * self.timer / 20)))
        if self.timer <= 0:
            self.kill()


# Estado do tremor de tela [quadros, intensidade]
_shake = [0, 0]


def shake(frames: int, power: int) -> None:
    """Aciona ou acumula tremor de tela, guardando o maior tempo e intensidade."""
    _shake[0] = max(_shake[0], frames)
    _shake[1] = max(_shake[1], power)


def shake_offset() -> tuple[int, int]:
    """Retorna deslocamento aleatório (dx, dy) e decrementa a contagem de quadros."""
    if _shake[0] <= 0 or _shake[1] <= 0:
        _shake[0] = 0
        _shake[1] = 0
        return (0, 0)
    _shake[0] -= 1
    power = _shake[1]
    dx = random.randint(-power, power)
    dy = random.randint(-power, power)
    if _shake[0] <= 0:
        _shake[1] = 0
    return (dx, dy)


def reset_shake() -> None:
    """Zera o tremor de tela imediatamente."""
    _shake[0] = 0
    _shake[1] = 0


# Fila de textos flutuantes pendentes gerados fora do loop de gameplay
_texts: list[FloatingText] = []


def damage_text(x: int, y: int, amount: int) -> None:
    """Adiciona um texto de dano flutuante à fila global."""
    _texts.append(FloatingText(str(amount), x, y, (255, 230, 90), 18))


def pop_texts() -> list[FloatingText]:
    """Retorna todos os textos pendentes e esvazia a fila."""
    res = list(_texts)
    _texts.clear()
    return res
