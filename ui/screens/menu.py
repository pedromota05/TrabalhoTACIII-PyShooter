"""
ui/screens/menu.py — Tela de Menu Principal do PyShooter.

Atende integralmente ao Trabalho 2 com opções completas de navegação:
Novo Jogo, Multiplayer LAN, Editor de Fases, Instruções, Configurações e Sair.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN, RED, BLACK
from asset_manager import AssetManager
from game_state import GameState
from ui.screens.common import draw_text_with_shadow


class MainMenuScreen:
    """Gerencia os botões e navegação do Menu Principal."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.title_font = pygame.font.SysFont('Futura', 54, bold=True)
        self.btn_font = pygame.font.SysFont('Futura', 26, bold=True)

        btn_w = 300
        btn_h = 52
        center_x = SCREEN_WIDTH // 2 - btn_w // 2
        start_y = 160
        spacing = 64

        # 1. Novo Jogo
        start_img = pygame.transform.scale(self.assets.get_image('start_btn'), (btn_w, btn_h))
        self.start_button = button.Button(center_x, start_y, start_img, 1.0)

        # 2. Multiplayer LAN
        multi_surf = self._create_menu_surf("MULTIPLAYER LAN", (30, 90, 160), btn_w, btn_h)
        self.multiplayer_button = button.Button(center_x, start_y + spacing, multi_surf, 1.0)

        # 3. Editor de Fases
        editor_surf = self._create_menu_surf("EDITOR DE FASES", (140, 90, 30), btn_w, btn_h)
        self.editor_button = button.Button(center_x, start_y + spacing * 2, editor_surf, 1.0)

        # 4. Instruções / Controles
        instr_img = pygame.transform.scale(self.assets.get_image('instructions_btn'), (btn_w, btn_h))
        self.instructions_button = button.Button(center_x, start_y + spacing * 3, instr_img, 1.0)

        # 5. Configurações / Opções
        opt_img = pygame.transform.scale(self.assets.get_image('options_btn'), (btn_w, btn_h))
        self.options_button = button.Button(center_x, start_y + spacing * 4, opt_img, 1.0)

        # 6. Sair
        exit_img = pygame.transform.scale(self.assets.get_image('exit_btn'), (btn_w, btn_h))
        self.exit_button = button.Button(center_x, start_y + spacing * 5, exit_img, 1.0)

        # Botão rápido de configurações no canto superior direito
        self.settings_button = button.Button(
            SCREEN_WIDTH - 80, 20,
            self.assets.get_image('settings_btn'), 1.0,
        )

    def _create_menu_surf(self, text: str, bg_color: tuple, w: int, h: int) -> pygame.Surface:
        """Cria uma superfície de botão estilizada para itens novos de menu."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg_color, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(surf, (240, 240, 240), (0, 0, w, h), 2, border_radius=8)

        # Texto centralizado com leve sombra
        shadow_surf = self.btn_font.render(text, True, BLACK)
        surf.blit(shadow_surf, shadow_surf.get_rect(center=(w // 2 + 2, h // 2 + 2)))

        text_surf = self.btn_font.render(text, True, WHITE)
        surf.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
        return surf

    def update(self, screen: pygame.Surface, game) -> None:
        """Desenha o menu principal e despacha cliques para os estados correspondentes."""
        game._draw_bg()

        # Título principal
        draw_text_with_shadow(screen, "PYSHOOTER - TAC III", self.title_font, WHITE, SCREEN_WIDTH // 2, 70)

        if self.start_button.draw(screen):
            game.is_multiplayer = False
            game.state = GameState.LEVEL_SELECT
        elif self.multiplayer_button.draw(screen):
            game.state = GameState.MULTIPLAYER_MENU
        elif self.editor_button.draw(screen):
            game.editor_screen.on_enter(game)
            game.state = GameState.EDITOR
        elif self.instructions_button.draw(screen):
            game.state = GameState.INSTRUCTIONS
        elif self.options_button.draw(screen):
            game.previous_state = game.state
            game.state = GameState.OPTIONS
        elif self.exit_button.draw(screen):
            game.running = False
        elif self.settings_button.draw(screen):
            game.previous_state = game.state
            game.state = GameState.OPTIONS
