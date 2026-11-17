"""
ui/screens/menu.py — Tela de Menu Principal do PyShooter.

Atende integralmente ao Trabalho 2 com opções completas de navegação:
Novo Jogo, Multiplayer LAN, Editor de Fases, Instruções, Configurações e Sair.
"""

import pygame
import button
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE,
    MENU_SCALE, MENU_MARGIN_X, MENU_SPACING_Y, MENU_START_Y, SETTINGS_BTN_SCALE, FONT_NAME,
)
from asset_manager import AssetManager
from game_state import GameState
from ui.screens.common import draw_text_with_shadow

# Limite inferior da área reservada ao título; a grade de botões é
# centralizada verticalmente no espaço restante abaixo dele.
TITLE_AREA_BOTTOM = 110


class MainMenuScreen:
    """Gerencia os botões e navegação do Menu Principal."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.title_font = pygame.font.SysFont(FONT_NAME, 54, bold=True)

        # Grade 2x3 (linha a linha): (atributo, chave do asset).
        # Coluna esquerda = índice 0, coluna direita = índice 1.
        menu_grid = [
            [('start_button',        'menu_start_btn'),      # Novo Jogo
             ('multiplayer_button',  'menu_multi_btn')],     # Multiplayer LAN
            [('editor_button',       'menu_editor_btn'),     # Editor de Fases
             ('instructions_button', 'menu_controls_btn')],  # Controles
            [('options_button',      'menu_options_btn'),    # Opções
             ('exit_button',         'menu_exit_btn')],      # Sair
        ]

        # 1) Instancia todos com a MESMA escala uniforme (proporção intacta).
        #    A posição é definida depois, quando as alturas reais são conhecidas.
        rows = []
        for row in menu_grid:
            row_buttons = []
            for attr, asset_key in row:
                btn = button.Button(0, 0, self.assets.get_image(asset_key), MENU_SCALE)
                setattr(self, attr, btn)
                row_buttons.append(btn)
            rows.append(row_buttons)

        # 2) Altura de cada linha = maior botão da linha (as artes variam
        #    entre ~134 e ~142 px na escala 0.45, então não usamos só o Start).
        row_heights = [max(b.rect.height for b in row) for row in rows]
        grid_h = sum(row_heights) + MENU_SPACING_Y * (len(rows) - 1)

        # start_y fixo abaixo do título. Trava de segurança: se uma escala
        # futura fizer a grade passar da borda inferior, ela sobe o mínimo
        # necessário (sem invadir a área do título).
        row_y = min(MENU_START_Y, SCREEN_HEIGHT - grid_h - MENU_SPACING_Y)
        row_y = max(row_y, TITLE_AREA_BOTTOM)

        # 3) Posiciona: colunas espelhadas a MENU_MARGIN_X do centro da tela.
        #    left.right = centro - margem  ==  col_left = centro - btn_w - margem
        #    right.left = centro + margem  ==  col_right
        center_x = SCREEN_WIDTH // 2
        for row, row_h in zip(rows, row_heights):
            left, right = row
            row_center_y = row_y + row_h // 2  # centraliza verticalmente na linha
            left.rect.midright = (center_x - MENU_MARGIN_X, row_center_y)
            right.rect.midleft = (center_x + MENU_MARGIN_X, row_center_y)
            # Próxima linha: Y atual + altura escalada da linha + espaçamento
            row_y += row_h + MENU_SPACING_Y

        # Botão rápido de configurações no canto superior direito
        self.settings_button = button.Button(
            SCREEN_WIDTH - 80, 20,
            self.assets.get_image('settings_btn'), SETTINGS_BTN_SCALE,
        )

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
