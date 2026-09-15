"""
ui/screens/level_select.py — Tela de Seleção de Fase do PyShooter.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, PINK
from asset_manager import AssetManager
from game_state import GameState
from ui.screens.common import draw_text_with_shadow


class LevelSelectScreen:
    """Gerencia a seleção e carregamento de fases pelo jogador."""

    def __init__(self, assets: AssetManager, font: pygame.font.Font, font_bold: pygame.font.Font):
        self.assets = assets
        self.font = font
        self.font_bold = font_bold
        self.level_buttons: list[button.Button] = []

        gamepad_spacing = 20
        sample_img = self.assets.get_image('gamepad1')
        total_width = (sample_img.get_width() * 4) + (gamepad_spacing * 3)
        start_x = (SCREEN_WIDTH - total_width) // 2
        btn_y = SCREEN_HEIGHT // 2 - sample_img.get_height() // 2

        for i in range(1, 5):
            btn_x = start_x + (i - 1) * (sample_img.get_width() + gamepad_spacing)
            btn = button.Button(
                btn_x, btn_y,
                self.assets.get_image(f'gamepad{i}'), 1,
            )
            self.level_buttons.append(btn)

    def update(self, screen: pygame.Surface, game) -> None:
        game._draw_bg()

        # Título centralizado
        draw_text_with_shadow(screen, 'SELECIONE A FASE', self.font_bold, WHITE, SCREEN_WIDTH // 2, 80)

        # Rótulos das fases acima de cada botão
        for i, btn in enumerate(self.level_buttons):
            label = f'Fase {i + 1}'
            draw_text_with_shadow(screen, label, self.font, WHITE, btn.rect.centerx, btn.rect.top - 35)

        # Desenhar botões e checar cliques
        for i, btn in enumerate(self.level_buttons):
            if btn.draw(screen):
                game.level = i + 1
                game.bg_scroll = 0
                game.start_intro = True
                game._load_level(game.level)
                game.state = GameState.PLAYING

        # Dica para voltar
        draw_text_with_shadow(
            screen, 'Pressione ESC para voltar ao menu', self.font_bold, PINK, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60
        )
