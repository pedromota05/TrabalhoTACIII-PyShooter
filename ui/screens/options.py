"""
ui/screens/options.py — Tela de Opções (volume de música/efeitos e tela cheia).
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, PINK
from asset_manager import AssetManager
from ui.screens.common import (
    render_text_with_spacing,
    draw_text_with_shadow,
    draw_volume_bar,
)


class OptionsScreen:
    """Gerencia sliders de volume para Música e SFX com suporte a clique e arrasto."""

    def __init__(self, assets: AssetManager, font_bold: pygame.font.Font):
        self.assets = assets
        self.font_bold = font_bold
        self._click_lock = False

    def update(self, screen: pygame.Surface, game) -> None:
        game._draw_bg()

        opt_bg = self.assets.get_image('opt_bg')
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        bg_x = center_x - (opt_bg.get_width() // 2)
        bg_y = center_y - (opt_bg.get_height() // 2)
        screen.blit(opt_bg, (bg_x, bg_y))

        # Título na Aba com Letter Spacing
        options_surf = render_text_with_spacing('OPTIONS', self.font_bold, WHITE, 5)
        options_text_rect = options_surf.get_rect(topleft=(bg_x + 30, bg_y + 20))
        screen.blit(options_surf, options_text_rect)

        bar_base = self.assets.get_image('bar_base')
        bar_fill = self.assets.get_image('bar_fill')
        slider_knob = self.assets.get_image('slider_knob')
        # Conjunto [ícone 40 px + 30 px espaço + barra 400 px] = 470 px centralizado em center_x
        icon_offset = 50  # distância do centro do ícone até bar_x
        group_width = bar_base.get_width() + icon_offset + 20  # 470 px
        bar_x = center_x - (group_width // 2) + icon_offset + 20

        # MÚSICA
        music_y = bg_y + 115
        music_rect = draw_volume_bar(
            screen, bar_x, music_y, game.music_vol, 12, bar_base, bar_fill, slider_knob
        )
        music_icon = self.assets.get_image('music_on') if game.music_vol > 0 else self.assets.get_image('music_off')
        music_icon_rect = music_icon.get_rect(center=(bar_x - icon_offset, music_y + 20))
        screen.blit(music_icon, music_icon_rect)

        # SFX
        sfx_y = bg_y + 205
        sfx_rect = draw_volume_bar(
            screen, bar_x, sfx_y, game.sfx_vol, 12, bar_base, bar_fill, slider_knob
        )
        sfx_icon = self.assets.get_image('sound_on') if game.sfx_vol > 0 else self.assets.get_image('sound_off')
        sfx_icon_rect = sfx_icon.get_rect(center=(bar_x - icon_offset, sfx_y + 20))
        screen.blit(sfx_icon, sfx_icon_rect)

        # TELA CHEIA (alinhado à largura do conjunto ícone + slider, com folga uniforme)
        ligada = getattr(game, 'fullscreen', False)
        fs_rect = pygame.Rect(0, 0, group_width, 46)
        fs_rect.center = (center_x, bg_y + 318)
        mouse_sobre = fs_rect.collidepoint(pygame.mouse.get_pos())
        cor_fundo = (60, 140, 70) if ligada else (110, 50, 50)
        if mouse_sobre:
            cor_fundo = tuple(min(255, c + 30) for c in cor_fundo)
        pygame.draw.rect(screen, cor_fundo, fs_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, fs_rect, 2, border_radius=8)
        fs_txt = self.font_bold.render(
            f"TELA CHEIA: {'LIGADA' if ligada else 'DESLIGADA'} (F11)", True, WHITE)
        screen.blit(fs_txt, fs_txt.get_rect(center=fs_rect.center))

        # Lógica de interação com mouse
        pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()[0]

        if left_click:
            # Arrastar barra
            if music_rect.collidepoint(pos):
                game.music_vol = int(((pos[0] - music_rect.left) / music_rect.width) * 12)
                game.music_vol = max(0, min(game.music_vol, 12))
                pygame.mixer.music.set_volume(game.music_vol / 12.0)
            elif sfx_rect.collidepoint(pos):
                game.sfx_vol = int(((pos[0] - sfx_rect.left) / sfx_rect.width) * 12)
                game.sfx_vol = max(0, min(game.sfx_vol, 12))
                self.assets.set_sfx_volume(game.sfx_vol / 12.0)

            # Clique único nos ícones (Mute/Unmute)
            if not self._click_lock:
                self._click_lock = True
                if music_icon_rect.collidepoint(pos):
                    game.music_vol = 0 if game.music_vol > 0 else 12
                    pygame.mixer.music.set_volume(game.music_vol / 12.0)
                elif sfx_icon_rect.collidepoint(pos):
                    game.sfx_vol = 0 if game.sfx_vol > 0 else 12
                    self.assets.set_sfx_volume(game.sfx_vol / 12.0)
                elif fs_rect.collidepoint(pos) and hasattr(game, 'toggle_fullscreen'):
                    game.toggle_fullscreen()
        else:
            self._click_lock = False

        draw_text_with_shadow(
            screen, 'Pressione ESC para voltar', self.font_bold, PINK, center_x, bg_y + opt_bg.get_height() + 20
        )
