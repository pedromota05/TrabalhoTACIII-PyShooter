"""
ui/screens/common.py — Funções utilitárias de renderização visual e texto para as telas.
"""

from PIL import Image, ImageSequence
import pygame


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
