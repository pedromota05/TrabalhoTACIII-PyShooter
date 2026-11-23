"""
ui/screens/common.py — Funções utilitárias de renderização visual e texto para as telas.
"""

from PIL import Image, ImageSequence
import pygame
from asset_manager import AssetManager
from config import PLAYER_COLORS, PLAYER_SCALE, WHITE
from core import progress


def render_text_with_spacing(text: str, font: pygame.font.Font, color: tuple, spacing: int) -> pygame.Surface:
    """Renderiza texto com espaçamento customizado entre caracteres."""
    total_width = sum([font.size(char)[0] for char in text]) + spacing * (len(text) - 1)
    height = font.size(text)[1]

    surface = pygame.Surface((total_width, height), pygame.SRCALPHA)
    current_x = 0
    for char in text:
        char_surface = font.render(char, True, color)
        surface.blit(char_surface, (current_x, 0))
        current_x += char_surface.get_width() + spacing

    return surface


def draw_text_with_shadow(screen: pygame.Surface, text: str, font: pygame.font.Font,
                          text_color: tuple, x: int, y: int):
    """Desenha texto com sombra preta deslocada (+3, +3)."""
    shadow_surf = font.render(text, True, (0, 0, 0))
    shadow_rect = shadow_surf.get_rect(centerx=x + 3, top=y + 3)
    screen.blit(shadow_surf, shadow_rect)

    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(centerx=x, top=y)
    screen.blit(text_surf, text_rect)


def draw_text_with_outline(screen: pygame.Surface, text: str, font: pygame.font.Font,
                           text_color: tuple, x: int, y: int,
                           outline_color: tuple = (0, 0, 0), thickness: int = 2) -> pygame.Rect:
    """Desenha texto centralizado em x (topo em y) com contorno (stroke) sólido.

    O contorno é feito desenhando o texto na cor do contorno deslocado
    `thickness` px nas 4 direções cardeais (cima, baixo, esquerda, direita)
    e nas 4 diagonais, que fecham os cantos das letras. Por fim, o texto
    principal é desenhado por cima, sem deslocamento.
    """
    outline_surf = font.render(text, True, outline_color)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(centerx=x, top=y)

    t = thickness
    for dx, dy in ((-t, 0), (t, 0), (0, -t), (0, t),
                   (-t, -t), (-t, t), (t, -t), (t, t)):
        screen.blit(outline_surf, text_rect.move(dx, dy))

    screen.blit(text_surf, text_rect)
    return text_rect


def draw_volume_bar(screen: pygame.Surface, x: int, y: int, current_vol: int, max_vol: int,
                    base_img: pygame.Surface, fill_img: pygame.Surface, knob_img: pygame.Surface) -> pygame.Rect:
    """Desenha a barra de volume com fundo, preenchimento proporcional e botão deslizante (knob)."""
    screen.blit(base_img, (x, y))

    fill_width = int((current_vol / max_vol) * fill_img.get_width())
    crop_rect = pygame.Rect(0, 0, fill_width, fill_img.get_height())
    screen.blit(fill_img, (x, y), crop_rect)

    knob_x = x + fill_width - (knob_img.get_width() // 2)
    knob_y = y + (base_img.get_height() // 2) - (knob_img.get_height() // 2)
    screen.blit(knob_img, (knob_x, knob_y))

    return pygame.Rect(x, y, base_img.get_width(), base_img.get_height())


def load_gif_frames(filename: str, max_width: float = None) -> list[pygame.Surface]:
    """Carrega todos os frames de um arquivo GIF e os converte em superfícies Pygame."""
    pil_image = Image.open(filename)
    frames = []
    for frame in ImageSequence.Iterator(pil_image):
        frame_rgba = frame.convert('RGBA')
        pygame_image = pygame.image.fromstring(frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode)

        if max_width and pygame_image.get_width() > max_width:
            ratio = max_width / pygame_image.get_width()
            new_w = int(pygame_image.get_width() * ratio)
            new_h = int(pygame_image.get_height() * ratio)
            pygame_image = pygame.transform.scale(pygame_image, (new_w, new_h))

        frames.append(pygame_image)
    return frames


class ColorPicker:
    """Seletor de cor do soldado reutilizável para menus (Multiplayer e Level Select)."""

    def __init__(self, center: tuple[int, int], font_bold: pygame.font.Font, title: str = "COR DO BONECO"):
        self.center = center
        self.font_bold = font_bold
        self.title = title
        self.color = progress.carregar().get('cor_jogador', 0) % len(PLAYER_COLORS)

        panel_x, panel_y = center
        self.color_left = pygame.Rect(0, 0, 40, 40)
        self.color_left.center = (panel_x - 65, panel_y)
        self.color_right = pygame.Rect(0, 0, 40, 40)
        self.color_right.center = (panel_x + 65, panel_y)

        self._previews: dict[int, pygame.Surface] = {}

    def reload(self) -> None:
        """Relê a cor salva no progresso."""
        self.color = progress.carregar().get('cor_jogador', 0) % len(PLAYER_COLORS)

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Processa clique nas setas esquerda/direita."""
        if self.color_left.collidepoint(pos):
            self.color = (self.color - 1) % len(PLAYER_COLORS)
            progress.salvar_cor(self.color)
            return True
        elif self.color_right.collidepoint(pos):
            self.color = (self.color + 1) % len(PLAYER_COLORS)
            progress.salvar_cor(self.color)
            return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        """Desenha título, prévia do boneco, setas e nome da cor."""
        panel_x, panel_y = self.center
        if self.title:
            draw_text_with_shadow(screen, self.title, self.font_bold, WHITE, panel_x, panel_y - 70)

        if self.color not in self._previews:
            anim = AssetManager().load_character_animations('player', PLAYER_SCALE * 1.5, self.color)
            self._previews[self.color] = anim[0][0]

        preview_surf = self._previews[self.color]
        preview_rect = preview_surf.get_rect(center=(panel_x, panel_y))
        screen.blit(preview_surf, preview_rect)

        pygame.draw.rect(screen, (30, 35, 45), self.color_left, border_radius=6)
        pygame.draw.rect(screen, (140, 140, 160), self.color_left, 2, border_radius=6)
        lx, ly = self.color_left.center
        left_tri = [(lx - 6, ly), (lx + 5, ly - 7), (lx + 5, ly + 7)]
        pygame.draw.polygon(screen, (0, 0, 0), [(x + 1, y + 1) for x, y in left_tri])
        pygame.draw.polygon(screen, WHITE, left_tri)

        pygame.draw.rect(screen, (30, 35, 45), self.color_right, border_radius=6)
        pygame.draw.rect(screen, (140, 140, 160), self.color_right, 2, border_radius=6)
        rx, ry = self.color_right.center
        right_tri = [(rx + 6, ry), (rx - 5, ry - 7), (rx - 5, ry + 7)]
        pygame.draw.polygon(screen, (0, 0, 0), [(x + 1, y + 1) for x, y in right_tri])
        pygame.draw.polygon(screen, WHITE, right_tri)

        color_name = PLAYER_COLORS[self.color][0]
        draw_text_with_shadow(screen, color_name, self.font_bold, WHITE, panel_x, panel_y + 70)
