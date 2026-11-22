"""entities/castle.py — Castelinho desenhado na saída da fase (estilo por fase)."""
import pygame
from config import TILE_SIZE
from entities.environment import Decoration

# (parede, sombra/linhas, porta, bandeira, detalhe do topo ou None)
CASTLE_THEMES = {
    1: ((150, 150, 160), (100, 100, 112), (25, 20, 30), (60, 200, 90), None),            # pedra
    2: ((125, 88, 52), (80, 55, 30), (20, 14, 8), (240, 200, 40), None),                 # madeira
    3: ((190, 225, 245), (120, 170, 210), (20, 40, 70), (40, 80, 200), (255, 255, 255)), # gelo + neve
}


def _draw_castle(theme, flag_frame: int) -> pygame.Surface:
    """Gera a superfície do castelo com estilo temático e frame da bandeira."""
    wall_color, shadow_color, door_color, flag_color, top_detail = theme
    w = 2 * TILE_SIZE
    h = int(2.6 * TILE_SIZE)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Retângulos principais
    body_y = int(0.40 * h)
    body_rect = pygame.Rect(int(0.15 * w), body_y, int(0.70 * w), h - body_y)

    side_w = int(0.22 * w)
    side_y = int(0.25 * h)
    side_h = h - side_y
    left_tower = pygame.Rect(0, side_y, side_w, side_h)
    right_tower = pygame.Rect(w - side_w, side_y, side_w, side_h)

    mid_w = int(0.30 * w)
    mid_x = (w - mid_w) // 2
    mid_y = int(0.15 * h)
    mid_tower = pygame.Rect(mid_x, mid_y, mid_w, h - mid_y)

    # Preenchimento das paredes
    pygame.draw.rect(surf, wall_color, body_rect)
    pygame.draw.rect(surf, wall_color, left_tower)
    pygame.draw.rect(surf, wall_color, right_tower)
    pygame.draw.rect(surf, wall_color, mid_tower)

    # Linhas de tijolo/tábua
    h_step = max(2, TILE_SIZE // 3)
    for r in (body_rect, left_tower, right_tower, mid_tower):
        for y in range(r.top + h_step, h, h_step):
            pygame.draw.line(surf, shadow_color, (r.left, y), (r.right - 1, y))

    # Para a fase 2 (madeira), também linhas verticais parecendo tábuas
    if theme == CASTLE_THEMES.get(2):
        v_step = max(2, TILE_SIZE // 2)
        for r in (body_rect, left_tower, right_tower, mid_tower):
            for x in range(r.left + v_step, r.right, v_step):
                pygame.draw.line(surf, shadow_color, (x, r.top), (x, h))

    # Contorno em volta de cada torre e do corpo
    for r in (body_rect, left_tower, right_tower, mid_tower):
        pygame.draw.rect(surf, shadow_color, r, 2)

    # Ameias no topo de cada torre
    merlon_size = max(2, int(0.06 * w))
    for tower in (left_tower, right_tower, mid_tower):
        fill = True
        x = tower.left
        while x < tower.right:
            cur_w = min(merlon_size, tower.right - x)
            if fill:
                m_rect = pygame.Rect(x, tower.top - merlon_size, cur_w, merlon_size)
                pygame.draw.rect(surf, wall_color, m_rect)
                pygame.draw.rect(surf, shadow_color, m_rect, 1)
            fill = not fill
            x += merlon_size

    # Neve (se definido no tema)
    if top_detail is not None:
        for tower in (left_tower, right_tower, mid_tower):
            pygame.draw.rect(surf, top_detail, (tower.left, tower.top, tower.width, 4))

    # Janelinhas nas torres laterais
    jw = max(2, int(0.06 * w))
    jh = max(2, int(0.10 * h))
    for tower in (left_tower, right_tower):
        jx = tower.centerx - jw // 2
        jy = tower.centery - jh // 2
        pygame.draw.rect(surf, door_color, (jx, jy, jw, jh))

    # Porta: arco escuro centrado embaixo
    door_w = int(0.8 * TILE_SIZE)
    door_h = int(1.15 * TILE_SIZE)
    door_x = (w - door_w) // 2
    door_top = h - door_h
    arc_h = door_w
    pygame.draw.ellipse(surf, door_color, (door_x, door_top, door_w, arc_h))
    rect_top = door_top + arc_h // 2
    pygame.draw.rect(surf, door_color, (door_x, rect_top, door_w, h - rect_top))

    # Mastro e bandeira
    mast_x = mid_tower.centerx
    mast_height = int(0.5 * TILE_SIZE)
    mast_top_y = mid_tower.top - mast_height
    pygame.draw.line(surf, shadow_color, (mast_x, mid_tower.top), (mast_x, mast_top_y), 2)

    flag_w = int(0.4 * TILE_SIZE)
    flag_h = int(0.3 * TILE_SIZE)
    tip_y = mast_top_y + flag_h // 2
    if flag_frame == 1:
        tip_y += 3
    flag_points = [
        (mast_x + 1, mast_top_y),
        (mast_x + 1 + flag_w, tip_y),
        (mast_x + 1, mast_top_y + flag_h),
    ]
    pygame.draw.polygon(surf, flag_color, flag_points)

    return surf


class Castle(Decoration):
    """Castelinho decorativo centrado na porta (rect da Exit)."""

    def __init__(self, level: int, door_rect: pygame.Rect):
        theme = CASTLE_THEMES.get(level, CASTLE_THEMES[1])
        self.frames = [_draw_castle(theme, 0), _draw_castle(theme, 1)]
        pygame.sprite.Sprite.__init__(self)
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=door_rect.midbottom)
        self.tick = 0

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll
        self.tick += 1
        self.image = self.frames[(self.tick // 20) % 2]


def _draw_finish_line() -> pygame.Surface:
    """Pórtico de chegada: dois postes com faixa quadriculada em cima e no chão."""
    w = int(1.6 * TILE_SIZE)
    h = int(2.6 * TILE_SIZE)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    post_w = 6
    post = (70, 70, 80)
    pygame.draw.rect(surf, post, (0, 0, post_w, h))
    pygame.draw.rect(surf, post, (w - post_w, 0, post_w, h))
    sq = 6  # tamanho do quadradinho
    for row, (y, rows) in enumerate(((4, 3), (h - sq, 1))):  # faixa de cima (3 linhas) e do chão
        for r in range(rows):
            for c in range(post_w // sq, (w - post_w) // sq + 1):
                x = c * sq
                if x + sq > w - post_w:
                    break
                color = (20, 20, 20) if (r + c) % 2 else (245, 245, 245)
                pygame.draw.rect(surf, color, (x, y + r * sq, sq, sq))
    pygame.draw.rect(surf, (20, 20, 20), (post_w, 4, w - 2 * post_w, 3 * sq), 1)
    return surf


class FinishLine(Decoration):
    """Linha de chegada (só desenho) com o pé apoiado em `bottom`."""

    def __init__(self, center_x: int, bottom: int):
        pygame.sprite.Sprite.__init__(self)
        self.image = _draw_finish_line()
        self.rect = self.image.get_rect(midbottom=(center_x, bottom))
