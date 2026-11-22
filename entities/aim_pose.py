"""
entities/aim_pose.py — Pose de mira do soldado (local e remoto).

A arma faz parte do sprite do jogador. Para ela acompanhar a mira, o sprite é
cortado na cintura: as pernas ficam paradas e a parte de cima (tronco, cabeça e
arma) gira em torno da cintura, limitada a MAX_TILT graus para cima ou para baixo.
"""

import math

import pygame

from config import PLAYER_SCALE

# Coordenadas no sprite original (28x36 px, virado para a direita).
WAIST_Y = 22        # primeira linha das pernas (linha do corte)
PIVOT = (12, 21)    # ponto da cintura em torno do qual o tronco gira
MUZZLE = (27, 18)   # ponta do cano da arma
MAX_TILT = 55       # inclinação máxima do tronco, em graus


def tilt_degrees(aim_angle: float, direction: int) -> float:
    """Ângulo de rotação (graus, anti-horário no pygame) da parte de cima.

    aim_angle está em radianos no padrão da tela (0 = direita, positivo = para
    baixo). Virado para a esquerda, a imagem já está espelhada, então o giro
    também se inverte."""
    local = math.atan2(math.sin(aim_angle), math.cos(aim_angle) * direction)
    deg = max(-MAX_TILT, min(MAX_TILT, -math.degrees(local)))
    return deg if direction == 1 else -deg


def _pivot(rect: pygame.Rect, width: int, direction: int, scale: float) -> tuple[float, float]:
    px = PIVOT[0] * scale if direction == 1 else width - PIVOT[0] * scale
    return rect.x + px, rect.y + PIVOT[1] * scale


def draw_aiming(screen: pygame.Surface, image: pygame.Surface, rect: pygame.Rect,
                direction: int, aim_angle: float, scale: float = PLAYER_SCALE) -> None:
    """Desenha o soldado com o tronco e a arma inclinados para a mira.

    `image` já deve estar virada para o lado em que o soldado olha."""
    w, h = image.get_size()
    cut = min(h, int(WAIST_Y * scale))
    screen.blit(image.subsurface((0, cut, w, h - cut)), (rect.x, rect.y + cut))

    deg = tilt_degrees(aim_angle, direction)
    upper = image.subsurface((0, 0, w, cut))
    rotated = pygame.transform.rotate(upper, deg)
    pivot_x, pivot_y = _pivot(rect, w, direction, scale)
    # Centro da parte de cima em relação ao pivô, girado junto com a imagem.
    offset = pygame.math.Vector2(w / 2 - (pivot_x - rect.x), cut / 2 - (pivot_y - rect.y)).rotate(-deg)
    screen.blit(rotated, rotated.get_rect(center=(pivot_x + offset.x, pivot_y + offset.y)))


def muzzle_point(rect: pygame.Rect, direction: int, aim_angle: float,
                 scale: float = PLAYER_SCALE) -> tuple[float, float]:
    """Posição na tela da ponta do cano, já com a inclinação da mira."""
    deg = tilt_degrees(aim_angle, direction)
    pivot_x, pivot_y = _pivot(rect, rect.width, direction, scale)
    vec = pygame.math.Vector2((MUZZLE[0] - PIVOT[0]) * scale * direction,
                              (MUZZLE[1] - PIVOT[1]) * scale).rotate(-deg)
    return pivot_x + vec.x, pivot_y + vec.y
