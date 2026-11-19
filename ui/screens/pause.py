"""
ui/screens/pause.py — Menu de pausa (overlay sobre o gameplay congelado).
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, MENU_SCALE

OVERLAY_ALPHA = 150      # opacidade do véu preto sobre o jogo (0-255)
PAUSE_SPACING_Y = 20     # espaço vertical entre os botões
TITLE_GAP = 30           # distância entre o título 'PAUSED' e o 1º botão
from asset_manager import AssetManager
from game_state import GameState


class PauseOverlay:
    """Gerencia a tela de pausa exibida por cima do jogo pausado."""

    def __init__(self, assets: AssetManager, title_font: pygame.font.Font):
        self.assets = assets
        self.title_font = title_font

        # Véu escuro pré-criado uma única vez (evita alocar uma Surface por frame)
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.set_alpha(OVERLAY_ALPHA)
        self.overlay.fill(BLACK)

        # Título 'PAUSED'
        self.title_top = SCREEN_HEIGHT // 2 - 220

        # Mesma escala geométrica dos demais botões coloridos (proporção intacta)
        self.pause_resume_btn = button.Button(0, 0, self.assets.get_image('resume_btn'), MENU_SCALE)
        self.pause_options_btn = button.Button(0, 0, self.assets.get_image('options_btn'), MENU_SCALE)
        self.pause_exit_btn = button.Button(0, 0, self.assets.get_image('exit_btn'), MENU_SCALE)

        # Empilhamento: Y(próximo) = Y(atual) + rect.height + espaçamento; X centralizado
        y = self.title_top + self.title_font.get_height() + TITLE_GAP
        for btn in (self.pause_resume_btn, self.pause_options_btn, self.pause_exit_btn):
            btn.rect.midtop = (SCREEN_WIDTH // 2, y)
            y += btn.rect.height + PAUSE_SPACING_Y

    def update(self, screen: pygame.Surface, game) -> None:
        # Desenha o jogo congelado
        game._draw_game_entities()

        # Véu preto semi-transparente sobre a tela inteira, ANTES do título e botões
        screen.blit(self.overlay, (0, 0))

        # Título grande com sombra
        shadow_surf = self.title_font.render('PAUSED', True, BLACK)
        shadow_rect = shadow_surf.get_rect(centerx=SCREEN_WIDTH // 2 + 4, top=self.title_top + 4)
        screen.blit(shadow_surf, shadow_rect)

        paused_surf = self.title_font.render('PAUSED', True, WHITE)
        paused_rect = paused_surf.get_rect(centerx=SCREEN_WIDTH // 2, top=self.title_top)
        screen.blit(paused_surf, paused_rect)

        # Botões de ação
        if self.pause_resume_btn.draw(screen):
            game.state = GameState.PLAYING
        elif self.pause_options_btn.draw(screen):
            game.previous_state = game.state
            game.state = GameState.OPTIONS
        elif self.pause_exit_btn.draw(screen):
            game.challenge_mode = False
            game.state = GameState.LEVEL_SELECT
            game.bg_scroll = 0
            game.start_intro = True
            game._load_level(game.level)
