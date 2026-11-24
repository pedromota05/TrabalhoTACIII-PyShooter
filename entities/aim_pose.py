"""
entities/aim_pose.py — Pose de mira do soldado (local e remoto).

A arma faz parte do desenho do jogador. Para ela acompanhar a mira sem cortar
o boneco, cada quadro é separado em duas camadas pela cor dos pixels:
- arma: tons azuis do cano/coronha, o laranja da ponta, o contorno e as luvas
  dentro do retângulo da arma;
- corpo: o resto, com o buraco que a arma deixou no peito preenchido com a cor
  do próprio corpo.
O corpo é desenhado parado e a arma gira em torno da empunhadura até o ângulo
exato da mira. As camadas ficam em cache por (ação, quadro, cor, escala).
"""

import math

import pygame

from config import PLAYER_COLORS, PLAYER_SCALE

ANIM_FOLDERS = ['Idle', 'Run', 'Jump', 'Death']
DEATH_ACTION = 3

# Cores do sprite original (antes de trocar a cor do uniforme).
GUN_COLORS = {(119, 156, 186), (143, 185, 219), (98, 121, 157), (80, 101, 134), (255, 106, 0)}
MUZZLE_COLOR = (255, 106, 0)
OUTLINE = (78, 79, 85)
GLOVES = {(90, 92, 101), (108, 110, 121), (136, 139, 158)}
BODY_FALLBACK = (107, 173, 88)

_cache: dict = {}


def _raw_frame(action: int, frame_index: int, color: int) -> pygame.Surface | None:
    """Quadro original (sem escala) já com a cor do uniforme."""
    from asset_manager import recolor_surface  # import local evita ciclo
    try:
        img = pygame.image.load(f'img/player/{ANIM_FOLDERS[action]}/{frame_index}.png')
        img = img.convert_alpha() if pygame.display.get_surface() else img
    except (pygame.error, FileNotFoundError, IndexError):
        return None
    if 0 < color < len(PLAYER_COLORS) and PLAYER_COLORS[color][1] is not None:
        img = recolor_surface(img, PLAYER_COLORS[color][1])
    return img


def _split(raw: pygame.Surface, base: pygame.Surface):
    """Separa `raw` (colorido) em corpo e arma usando as cores de `base` (original).

    Devolve (corpo, arma, pivô, cano) em coordenadas do quadro original, ou None
    se o quadro não tem arma (ex.: morte)."""
    w, h = base.get_size()

    def rgb(x, y):
        c = base.get_at((x, y))
        return (c[0], c[1], c[2]) if c[3] else None

    gun = [(x, y) for y in range(h) for x in range(w) if rgb(x, y) in GUN_COLORS]
    if not gun:
        return None
    minx = min(p[0] for p in gun) - 1
    maxx = max(p[0] for p in gun) + 1
    miny = min(p[1] for p in gun) - 1
    maxy = max(p[1] for p in gun) + 1
    keep = GUN_COLORS | GLOVES | {OUTLINE}
    mask = {(x, y) for y in range(max(0, miny), min(h, maxy + 1))
            for x in range(max(0, minx), min(w, maxx + 1)) if rgb(x, y) in keep}

    # Borda direita da barriga logo abaixo da arma: até ali o peito é corpo.
    edge = max((x for yy in (maxy + 1, maxy + 2) if 0 <= yy < h
                for x in range(w) if base.get_at((x, yy))[3]), default=minx)
    # Dedos da mão da frente (pixels do uniforme à direita da barriga) vão com a arma.
    for y in range(max(0, miny), min(h, maxy + 1)):
        for x in range(edge + 1, min(w, maxx + 1)):
            if rgb(x, y) is not None:
                mask.add((x, y))

    gun_layer = pygame.Surface((w, h), pygame.SRCALPHA)
    body = raw.copy()
    for x, y in mask:
        gun_layer.set_at((x, y), raw.get_at((x, y)))
        body.set_at((x, y), (0, 0, 0, 0))

    for y in range(max(0, miny), min(h, maxy + 1)):
        left = None
        for x in range(0, min(w, edge + 1)):
            c = body.get_at((x, y))
            if c[3] and (x, y) not in mask:
                left = c
            elif (x, y) in mask or not c[3]:
                if x < minx:
                    continue
                if x == edge:
                    body.set_at((x, y), (*OUTLINE, 255))
                else:
                    body.set_at((x, y), left if left is not None else (*BODY_FALLBACK, 255))

    muzzle_pts = [p for p in gun if rgb(*p) == MUZZLE_COLOR] or gun
    muzzle = (max(p[0] for p in muzzle_pts) + 0.5, sum(p[1] for p in muzzle_pts) / len(muzzle_pts) + 0.5)
    pivot = (minx + 4.5, (miny + maxy) / 2 + 0.5)  # empunhadura / ombro
    return body, gun_layer, pivot, muzzle


def _layers(action: int, frame_index: int, color: int, scale: float):
    key = (action, frame_index, color, round(scale, 3))
    if key in _cache:
        return _cache[key]
    result = None
    if action != DEATH_ACTION:
        base = _raw_frame(action, frame_index, 0)
        raw = _raw_frame(action, frame_index, color) if color else base
        if base is not None and raw is not None:
            parts = _split(raw, base)
            if parts:
                body, gun, pivot, muzzle = parts
                size = (int(base.get_width() * scale), int(base.get_height() * scale))
                result = (pygame.transform.scale(body, size), pygame.transform.scale(gun, size),
                          (pivot[0] * scale, pivot[1] * scale), (muzzle[0] * scale, muzzle[1] * scale))
    _cache[key] = result
    return result


def _local_degrees(aim_angle: float, direction: int) -> float:
    """Ângulo da mira em relação ao lado para onde o soldado olha (graus,
    positivo = para cima), limitado a ±89."""
    local = math.atan2(math.sin(aim_angle), math.cos(aim_angle) * direction)
    return max(-89.0, min(89.0, -math.degrees(local)))


def _geometry(rect: pygame.Rect, layers, direction: int, aim_angle: float):
    body, gun, pivot, muzzle = layers
    w = body.get_width()
    px = pivot[0] if direction == 1 else w - pivot[0]
    pivot_screen = (rect.x + px, rect.y + pivot[1])
    deg = _local_degrees(aim_angle, direction)
    rot = deg if direction == 1 else -deg  # imagem espelhada gira ao contrário
    return pivot_screen, rot


def has_pose(action: int, frame_index: int, color: int, scale: float = PLAYER_SCALE) -> bool:
    return _layers(action, frame_index, color, scale) is not None


def draw_aiming(screen: pygame.Surface, rect: pygame.Rect, direction: int, aim_angle: float,
                action: int, frame_index: int, color: int, scale: float = PLAYER_SCALE) -> bool:
    """Desenha corpo parado + arma girada para a mira. Devolve False se este
    quadro não tem pose (o chamador desenha o sprite normal)."""
    layers = _layers(action, frame_index, color, scale)
    if layers is None:
        return False
    body, gun, pivot, _ = layers
    flip = direction == -1
    body_img = pygame.transform.flip(body, flip, False)
    gun_img = pygame.transform.flip(gun, flip, False)
    screen.blit(body_img, (rect.x, rect.y))

    pivot_screen, rot = _geometry(rect, layers, direction, aim_angle)
    rotated = pygame.transform.rotate(gun_img, rot)
    w, h = gun_img.get_size()
    offset = pygame.math.Vector2(rect.x + w / 2 - pivot_screen[0],
                                 rect.y + h / 2 - pivot_screen[1]).rotate(-rot)
    screen.blit(rotated, rotated.get_rect(center=(pivot_screen[0] + offset.x, pivot_screen[1] + offset.y)))
    return True


def muzzle_point(rect: pygame.Rect, direction: int, aim_angle: float, action: int = 0,
                 frame_index: int = 0, color: int = 0,
                 scale: float = PLAYER_SCALE) -> tuple[float, float]:
    """Posição na tela da ponta do cano com a arma girada para a mira."""
    layers = _layers(action, frame_index, color, scale) or _layers(0, 0, 0, scale)
    if layers is None:
        return rect.centerx + rect.width * 0.9 * direction, rect.centery - 5
    _, _, pivot, muzzle = layers
    pivot_screen, rot = _geometry(rect, layers, direction, aim_angle)
    vec = pygame.math.Vector2((muzzle[0] - pivot[0]) * direction, muzzle[1] - pivot[1]).rotate(-rot)
    return pivot_screen[0] + vec.x, pivot_screen[1] + vec.y
