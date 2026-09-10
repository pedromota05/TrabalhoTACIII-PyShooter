"""
ui/screens/instructions.py — Tela de Instruções e Controles do Jogo.
"""

import pygame
from config import SCREEN_WIDTH, WHITE
from asset_manager import AssetManager
from ui.screens.common import draw_text_with_shadow


class InstructionsScreen:
    """Renderiza a tela com todos os controles do jogador e suas respectivas ações."""

    def __init__(self, assets: AssetManager, font: pygame.font.Font, font_bold: pygame.font.Font):
        self.assets = assets
        self.font = font
        self.font_bold = font_bold

    def update(self, screen: pygame.Surface, game) -> None:
        game._draw_bg()

        # Fundo semi-transparente
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Título
        draw_text_with_shadow(screen, 'CONTROLES DO JOGO', self.font_bold, WHITE, SCREEN_WIDTH // 2, 100)

        center_x = SCREEN_WIDTH // 2
        keys_ui = self.assets.keys_ui
        font = self.font

        # A ou ESQUERDA
        y_pos = 200
        desc_surf = font.render(": Mover para a esquerda", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['LEFT'].get_rect(midright=(center_x - 10, y_pos))
        screen.blit(keys_ui['LEFT'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['A'].get_rect(midright=(ou_rect.left - 15, y_pos))
        screen.blit(keys_ui['A'], key1_rect)

        # D ou DIREITA
        y_pos = 270
        desc_surf = font.render(": Mover para a direita", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['RIGHT'].get_rect(midright=(center_x - 10, y_pos))
        screen.blit(keys_ui['RIGHT'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['D'].get_rect(midright=(ou_rect.left - 15, y_pos))
        screen.blit(keys_ui['D'], key1_rect)

        # W ou CIMA
        y_pos = 340
        desc_surf = font.render(": Pular", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['UP'].get_rect(midright=(center_x - 10, y_pos))
        screen.blit(keys_ui['UP'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['W'].get_rect(midright=(ou_rect.left - 15, y_pos))
        screen.blit(keys_ui['W'], key1_rect)

        # ESPAÇO
        y_pos = 410
        desc_surf = font.render(": Atirar", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        screen.blit(desc_surf, desc_rect)

        key_rect = keys_ui['SPACE'].get_rect(midright=(center_x - 10, y_pos))
        screen.blit(keys_ui['SPACE'], key_rect)

        # Q ou G
        y_pos = 480
        desc_surf = font.render(": Lançar granada", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['G'].get_rect(midright=(center_x - 10, y_pos))
        screen.blit(keys_ui['G'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['Q'].get_rect(midright=(ou_rect.left - 15, y_pos))
        screen.blit(keys_ui['Q'], key1_rect)

        # ESC
        y_pos = 550
        desc_surf = font.render(": Voltar ao menu", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        screen.blit(desc_surf, desc_rect)

        key_rect = keys_ui['ESC'].get_rect(midright=(center_x - 10, y_pos))
        screen.blit(keys_ui['ESC'], key_rect)
