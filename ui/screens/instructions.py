"""
ui/screens/instructions.py — Tela de Instruções e Controles do Jogo.

Layout em 2 colunas (MOVIMENTAÇÃO | COMBATE E ITENS) dentro de cartões
semi-transparentes, com o atalho [ESC] centralizado no rodapé.
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, FONT_NAME
from asset_manager import AssetManager
from ui.screens.common import draw_text_with_shadow

# Paleta
SOFT_RED = (255, 120, 120)
SUBTITLE_COLOR = (255, 215, 120)
SHADOW_COLOR = (0, 0, 0)

# Geometria (tela 1200×640)
TITLE_Y = 38
PANEL_TOP = 125
PANEL_HEIGHT = 380
PANEL_GAP = 30
PANEL_MARGIN_X = 30
PANEL_RADIUS = 14
SUBTITLE_OFFSET = 22          # topo do subtítulo em relação ao topo do painel
FIRST_ROW_OFFSET = 120        # centery da 1ª linha em relação ao topo do painel
ROW_SPACING = 70
ICON_GAP = 12                 # espaço entre ícones e o "ou"
COLON_GAP = 14                # espaço entre o último ícone e o ":"
FOOTER_MARGIN = 42            # distância da base visível do [ESC] até a borda inferior


def _blit_shadow_text(screen: pygame.Surface, text: str, font: pygame.font.Font,
                      color: tuple, offset: int = 2, **rect_kwargs) -> pygame.Rect:
    """Desenha texto com sombra projetada, posicionado por kwargs de Rect (midleft, center...)."""
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(**rect_kwargs)
    screen.blit(font.render(text, True, SHADOW_COLOR), rect.move(offset, offset))
    screen.blit(text_surf, rect)
    return rect


class InstructionsScreen:
    """Renderiza a tela com todos os controles do jogador e suas respectivas ações."""

    def __init__(self, assets: AssetManager, font: pygame.font.Font, font_bold: pygame.font.Font):
        self.assets = assets
        self.font = font
        self.font_bold = font_bold
        self.title_font = pygame.font.SysFont(FONT_NAME, 46, bold=True)
        self._layer: pygame.Surface | None = None  # camada estática (cache)

    # ------------------------------------------------------------------ #
    # Helpers de layout
    # ------------------------------------------------------------------ #
    def _row_items(self, keys: list[str]) -> list:
        """Converte ['A', 'LEFT'] em [surf_A, 'ou', surf_LEFT]."""
        items = []
        for i, key in enumerate(keys):
            if i:
                items.append('ou')
            items.append(self.assets.keys_ui[key])
        return items

    def _items_width(self, items: list) -> int:
        """Largura visível de um grupo de ícones (usa o bounding rect dos sprites)."""
        width = 0
        for i, item in enumerate(items):
            if i:
                width += ICON_GAP
            if isinstance(item, str):
                width += self.font.size(item)[0]
            else:
                width += item.get_bounding_rect().width
        return width

    def _draw_items_right_aligned(self, screen: pygame.Surface, items: list, right: int, cy: int) -> None:
        """Desenha ícones/“ou” da direita para a esquerda, com centery alinhado ao texto."""
        x = right
        for item in reversed(items):
            if isinstance(item, str):
                rect = _blit_shadow_text(screen, item, self.font, WHITE, midright=(x, cy))
                x = rect.left - ICON_GAP
            else:
                visible = item.get_bounding_rect()
                # Posiciona pelo retângulo visível (ignora o padding transparente do sprite)
                pos = (x - visible.right, cy - visible.centery)
                screen.blit(item, pos)
                x = pos[0] + visible.left - ICON_GAP

    def _draw_panel(self, screen: pygame.Surface, rect: pygame.Rect, title: str, rows: list) -> None:
        """Desenha um cartão com subtítulo e linhas [ícones] : descrição, centralizadas no cartão."""
        card = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(card, (10, 14, 24, 150), card.get_rect(), border_radius=PANEL_RADIUS)
        pygame.draw.rect(card, (255, 255, 255, 45), card.get_rect(), 2, border_radius=PANEL_RADIUS)
        # Divisória sob o subtítulo
        line_y = SUBTITLE_OFFSET + self.font_bold.get_height() + 14
        pygame.draw.line(card, (90, 100, 120, 200), (40, line_y), (rect.width - 40, line_y), 1)
        screen.blit(card, rect.topleft)

        # Subtítulo
        draw_text_with_shadow(screen, title, self.font_bold, SUBTITLE_COLOR, rect.centerx, rect.top + SUBTITLE_OFFSET)

        # Calcula as colunas internas para alinhar os ":" e centralizar o bloco no cartão
        prepared = [(self._row_items(keys), ": " + desc, color) for keys, desc, color in rows]
        icons_w = max(self._items_width(items) for items, _, _ in prepared)
        desc_w = max(self.font.size(desc)[0] for _, desc, _ in prepared)
        block_w = icons_w + COLON_GAP + desc_w
        colon_x = rect.centerx - block_w // 2 + icons_w + COLON_GAP

        for i, (items, desc, color) in enumerate(prepared):
            cy = rect.top + FIRST_ROW_OFFSET + i * ROW_SPACING
            self._draw_items_right_aligned(screen, items, colon_x - COLON_GAP, cy)
            _blit_shadow_text(screen, desc, self.font, color, midleft=(colon_x, cy))

    def _build_layer(self, size: tuple[int, int]) -> pygame.Surface:
        """Monta a camada estática (overlay, título, cartões e rodapé) uma única vez."""
        layer = pygame.Surface(size, pygame.SRCALPHA)
        layer.fill((0, 0, 0, 150))

        # Título
        draw_text_with_shadow(layer, 'CONTROLES DO JOGO', self.title_font, WHITE, SCREEN_WIDTH // 2, TITLE_Y)

        # Cartões
        panel_w = (SCREEN_WIDTH - 2 * PANEL_MARGIN_X - PANEL_GAP) // 2
        left_rect = pygame.Rect(PANEL_MARGIN_X, PANEL_TOP, panel_w, PANEL_HEIGHT)
        right_rect = pygame.Rect(left_rect.right + PANEL_GAP, PANEL_TOP, panel_w, PANEL_HEIGHT)

        self._draw_panel(layer, left_rect, 'MOVIMENTAÇÃO', [
            (['A', 'LEFT'], 'Mover para a esquerda', WHITE),
            (['D', 'RIGHT'], 'Mover para a direita', WHITE),
            (['W', 'UP'], 'Pular', WHITE),
            (['SPACE'], 'Dash', WHITE),
        ])
        self._draw_panel(layer, right_rect, 'COMBATE E ITENS', [
            (['MOUSE_LEFT'], 'Atirar (Mouse: Mirar)', WHITE),
            (['MOUSE_RIGHT'], 'Golpe com a arma (quebra caixas)', WHITE),
            (['Q', 'G'], 'Lançar granada', WHITE),
            (['HEART'], '+1 vida (até 5)', SOFT_RED),
        ])

        # Rodapé: [ESC] : Voltar ao menu (centralizado)
        esc = [self.assets.keys_ui['ESC']]
        esc_desc = ': Voltar ao menu'
        esc_icon_w = self._items_width(esc)
        footer_w = esc_icon_w + COLON_GAP + self.font.size(esc_desc)[0]
        footer_cy = SCREEN_HEIGHT - FOOTER_MARGIN - esc[0].get_bounding_rect().height // 2
        colon_x = SCREEN_WIDTH // 2 - footer_w // 2 + esc_icon_w + COLON_GAP
        self._draw_items_right_aligned(layer, esc, colon_x - COLON_GAP, footer_cy)
        _blit_shadow_text(layer, esc_desc, self.font, WHITE, midleft=(colon_x, footer_cy))

        return layer

    # ------------------------------------------------------------------ #
    def update(self, screen: pygame.Surface, game) -> None:
        game._draw_bg()

        if self._layer is None or self._layer.get_size() != screen.get_size():
            self._layer = self._build_layer(screen.get_size())
        screen.blit(self._layer, (0, 0))
