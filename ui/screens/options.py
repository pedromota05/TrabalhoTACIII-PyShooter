"""
ui/screens/options.py — Tela de Opções (ajustes de volume e áudio).
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
        bar_x = center_x - (bar_base.get_width() // 2) + 20

        # MÚSICA
        music_y = bg_y + 140
        music_rect = draw_volume_bar(
            screen, bar_x, music_y, game.music_vol, 12, bar_base, bar_fill, slider_knob
        )
        music_icon = self.assets.get_image('music_on') if game.music_vol > 0 else self.assets.get_image('music_off')
        music_icon_rect = music_icon.get_rect(center=(bar_x - 50, music_y + 20))
        screen.blit(music_icon, music_icon_rect)

        # SFX
        sfx_y = bg_y + 260
        sfx_rect = draw_volume_bar(
            screen, bar_x, sfx_y, game.sfx_vol, 12, bar_base, bar_fill, slider_knob
        )
        sfx_icon = self.assets.get_image('sound_on') if game.sfx_vol > 0 else self.assets.get_image('sound_off')
        sfx_icon_rect = sfx_icon.get_rect(center=(bar_x - 50, sfx_y + 20))
        screen.blit(sfx_icon, sfx_icon_rect)

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
        else:
            self._click_lock = False

        draw_text_with_shadow(
            screen, 'Pressione ESC para voltar', self.font_bold, PINK, center_x, bg_y + opt_bg.get_height() + 20
        )
