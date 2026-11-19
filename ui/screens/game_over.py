"""
ui/screens/game_over.py — Tela de Game Over com animação GIF e botão de reinício.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, PINK, GAME_OVER_BUTTON_SCALE, FONT_NAME, WHITE
from asset_manager import AssetManager
from game_state import GameState
from ui.transitions import ScreenFade
from ui.screens.common import load_gif_frames, draw_text_with_outline
from ui.screens.victory import format_time

CHALLENGE_RED = (230, 50, 40)
from core.level_loader import respawn
from core.gameplay import respawn_multiplayer


class GameOverScreen:
    """Gerencia a transição de morte, reprodução do GIF de Game Over e reinício de fase."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.death_fade = ScreenFade(2, PINK, 35)

        # Escala uniforme (preserva a proporção da arte) e centralização pelo
        # próprio rect, em vez de um deslocamento fixo de -100 px.
        self.restart_button = button.Button(
            0, 0, self.assets.get_image('restart_btn'), GAME_OVER_BUTTON_SCALE,
        )
        self.restart_button.rect.midtop = (SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 50)

        self.go_frames = load_gif_frames('img/icons/game-over-game.gif', max_width=SCREEN_WIDTH * 0.8)
        self.go_frame_index = 0
        self.go_last_update = pygame.time.get_ticks()
        self.go_anim_cooldown = 100
        self.challenge_font = pygame.font.SysFont(FONT_NAME, 56, bold=True)
        self.info_font = pygame.font.SysFont(FONT_NAME, 30, bold=True)

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

            challenge = getattr(game, 'challenge_mode', False)
            if challenge:
                draw_text_with_outline(screen, 'DESAFIO ENCERRADO', self.challenge_font, CHALLENGE_RED,
                                       SCREEN_WIDTH // 2, 40, thickness=3)
                total = len(game.challenge_levels)
                draw_text_with_outline(
                    screen, f'Fase {game.challenge_index + 1}/{total}  -  {format_time(game.run_frames)}',
                    self.info_font, WHITE, SCREEN_WIDTH // 2, 110)

            if self.restart_button.draw(screen):
                self.restart(game)

    def restart(self, game) -> None:
        """Ação do botão Restart (também usada pelo teste automático do multiplayer)."""
        self.death_fade.fade_counter = 0
        if getattr(game, 'challenge_mode', False):
            game.start_challenge()  # Desafio recomeça da fase 1
            return
        if getattr(game, 'is_multiplayer', False):
            respawn_multiplayer(game)  # renasce ao lado do parceiro, fase continua
            game.state = GameState.PLAYING
            return
        game.start_intro = True
        game.bg_scroll = 0
        respawn(game)  # volta na última bandeira ou, sem checkpoint, no início
        game.state = GameState.PLAYING
