"""
ui/screens/pause.py — Menu de pausa (overlay sobre o gameplay congelado).
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK
from asset_manager import AssetManager
from game_state import GameState


class PauseOverlay:
    """Gerencia a tela de pausa exibida por cima do jogo pausado."""

    def __init__(self, assets: AssetManager, title_font: pygame.font.Font):
        self.assets = assets
        self.title_font = title_font

        btn_width = 280
        center_x = SCREEN_WIDTH // 2 - btn_width // 2
        center_y = SCREEN_HEIGHT // 2

        self.pause_resume_btn = button.Button(center_x, center_y - 120, self.assets.get_image('resume_btn'), 1)
        self.pause_options_btn = button.Button(center_x, center_y, self.assets.get_image('options_btn'), 1)
        self.pause_exit_btn = button.Button(center_x, center_y + 120, self.assets.get_image('exit_btn'), 1)

    def update(self, screen: pygame.Surface, game) -> None:
        # Desenha o jogo congelado
        game._draw_game_entities()

        # Fundo escurecido semi-transparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Título grande com sombra
        center_y = SCREEN_HEIGHT // 2
        shadow_surf = self.title_font.render('PAUSED', True, BLACK)
        shadow_rect = shadow_surf.get_rect(centerx=SCREEN_WIDTH // 2 + 4, top=center_y - 216)
        screen.blit(shadow_surf, shadow_rect)

        paused_surf = self.title_font.render('PAUSED', True, WHITE)
        paused_rect = paused_surf.get_rect(centerx=SCREEN_WIDTH // 2, top=center_y - 220)
        screen.blit(paused_surf, paused_rect)

        # Botões de ação
        if self.pause_resume_btn.draw(screen):
            game.state = GameState.PLAYING
        elif self.pause_options_btn.draw(screen):
            game.previous_state = game.state
            game.state = GameState.OPTIONS
        elif self.pause_exit_btn.draw(screen):
            game.state = GameState.LEVEL_SELECT
            game.bg_scroll = 0
            game.start_intro = True
            game._load_level(game.level)
