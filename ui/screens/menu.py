"""
ui/screens/menu.py — Tela de Menu Principal do PyShooter.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from asset_manager import AssetManager
from game_state import GameState


class MainMenuScreen:
    """Gerencia os botões e transições do Menu Principal."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        btn_width = 280
        center_x = SCREEN_WIDTH // 2 - btn_width // 2
        center_y = SCREEN_HEIGHT // 2

        self.start_button = button.Button(
            center_x, center_y - 120,
            self.assets.get_image('start_btn'), 1,
        )
        self.instructions_button = button.Button(
            center_x, center_y,
            self.assets.get_image('instructions_btn'), 1,
        )
        self.exit_button = button.Button(
            center_x, center_y + 120,
            self.assets.get_image('exit_btn'), 1,
        )
        self.settings_button = button.Button(
            SCREEN_WIDTH - 80, 20,
            self.assets.get_image('settings_btn'), 1,
        )

    def update(self, screen: pygame.Surface, game) -> None:
        """Desenha os botões e processa cliques de navegação."""
        game._draw_bg()

        if self.start_button.draw(screen):
            game.state = GameState.LEVEL_SELECT
        elif self.instructions_button.draw(screen):
            game.state = GameState.INSTRUCTIONS
        elif self.exit_button.draw(screen):
            game.running = False
        elif self.settings_button.draw(screen):
            game.previous_state = game.state
            game.state = GameState.OPTIONS
