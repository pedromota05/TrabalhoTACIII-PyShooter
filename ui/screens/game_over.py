"""
ui/screens/game_over.py — Tela de Game Over com animação GIF e botão de reinício.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, PINK
from asset_manager import AssetManager
from game_state import GameState
from ui.transitions import ScreenFade
from ui.screens.common import load_gif_frames


class GameOverScreen:
    """Gerencia a transição de morte, reprodução do GIF de Game Over e reinício de fase."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.death_fade = ScreenFade(2, PINK, 35)

        self.restart_button = button.Button(
            SCREEN_WIDTH // 2 - 100, (SCREEN_HEIGHT // 2) + 50,
            self.assets.get_image('restart_btn'), 2,
        )

        self.go_frames = load_gif_frames('img/icons/game-over-game.gif', max_width=SCREEN_WIDTH * 0.8)
        self.go_frame_index = 0
        self.go_last_update = pygame.time.get_ticks()
        self.go_anim_cooldown = 100

    def update(self, screen: pygame.Surface, game) -> None:
        game.screen_scroll = 0
        game._update_game_entities()
        game._draw_game_entities()

        if self.death_fade.fade(screen):
            current_time = pygame.time.get_ticks()
            if current_time - self.go_last_update >= self.go_anim_cooldown:
                self.go_frame_index += 1
                self.go_last_update = current_time
                if self.go_frame_index >= len(self.go_frames):
                    self.go_frame_index = 0

            current_go_img = self.go_frames[self.go_frame_index]
            go_rect = current_go_img.get_rect()
            go_rect.centerx = SCREEN_WIDTH // 2
            go_rect.centery = (SCREEN_HEIGHT // 2) - 100
            screen.blit(current_go_img, go_rect)

            if self.restart_button.draw(screen):
                self.death_fade.fade_counter = 0
                game.start_intro = True
                game.bg_scroll = 0
                game._load_level(game.level)
                game.state = GameState.PLAYING
