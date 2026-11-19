"""
ui/screens/victory.py — Tela de vitória exibida ao concluir a campanha.
"""

import pygame
import button
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, FONT_NAME, WHITE, YELLOW, BLACK,
    MENU_SCALE,
)
from asset_manager import AssetManager
from core import progress
from core.gameplay import sync_multiplayer_level
from game_state import GameState
from ui.screens.common import draw_text_with_outline

GOLD = (255, 200, 40)
OVERLAY_MAX_ALPHA = 170   # opacidade final do véu escuro
OVERLAY_STEP = 6          # quanto o véu escurece por quadro


def format_time(frames: int) -> str:
    """Converte quadros (a 60 FPS) em 'mm:ss.d'."""
    total = frames / FPS
    minutes, seconds = divmod(total, 60)
    return f'{int(minutes):02d}:{seconds:04.1f}'


class VictoryScreen:
    """Véu escuro que surge aos poucos sobre o jogo congelado, título 'VITÓRIA!', tempo e botão MENU."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.fill(BLACK)
        self.alpha = 0
        self.title_font = pygame.font.SysFont(FONT_NAME, 96, bold=True)
        self.info_font = pygame.font.SysFont(FONT_NAME, 40, bold=True)

        self.menu_button = button.Button(
            0, 0, self.assets.get_image('lan_back_btn'), MENU_SCALE,
        )
        self.menu_button.rect.midtop = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)

    def update(self, screen: pygame.Surface, game) -> None:
        # No multiplayer o Host continua anunciando a vitória (UDP pode perder pacotes).
        sync_multiplayer_level(game)
        # Cenário congelado ao fundo; o véu escurece até OVERLAY_MAX_ALPHA.
        game.screen_scroll = 0
        game._draw_game_entities()
        self.alpha = min(self.alpha + OVERLAY_STEP, OVERLAY_MAX_ALPHA)
        self.overlay.set_alpha(self.alpha)
        screen.blit(self.overlay, (0, 0))
        if self.alpha < OVERLAY_MAX_ALPHA:
            return

        draw_text_with_outline(screen, 'VITÓRIA!', self.title_font, GOLD,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200, thickness=4)
        if getattr(game, 'challenge_mode', False):
            self._draw_challenge_info(screen, game)
        else:
            draw_text_with_outline(screen, 'Campanha concluída', self.info_font, WHITE,
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)
            draw_text_with_outline(screen, f'Tempo: {format_time(game.run_frames)}',
                                   self.info_font, YELLOW,
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)

        if self.menu_button.draw(screen):
            self.alpha = 0
            game.challenge_mode = False
            if getattr(game, 'is_multiplayer', False):
                game.clean_multiplayer()
            game.level = 1
            game.start_intro = True
            game._load_level(game.level)
            game.state = GameState.MENU

    def _draw_challenge_info(self, screen: pygame.Surface, game) -> None:
        """Textos do Desafio: tempo da maratona, recorde salvo e aviso de novo recorde."""
        draw_text_with_outline(screen, 'Desafio concluído', self.info_font, WHITE,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 110)
        draw_text_with_outline(screen, f'Tempo: {format_time(game.run_frames)}',
                               self.info_font, YELLOW,
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 55)
        record = progress.carregar()['recorde_desafio']
        if record is not None:
            draw_text_with_outline(screen, f'Recorde: {format_time(int(round(record * FPS)))}',
                                   self.info_font, WHITE,
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        if getattr(game, 'challenge_new_record', False):
            draw_text_with_outline(screen, 'NOVO RECORDE!', self.info_font, GOLD,
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, thickness=3)
