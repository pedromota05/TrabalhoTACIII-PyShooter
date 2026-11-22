"""
ui/screens/multiplayer_menu.py — Tela de Configuração e Conexão Multiplayer em LAN.

Permite hospedar um servidor local (Host) ou conectar-se como cliente (Join)
informando o IP do servidor na rede local.
"""

import pygame
import button
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, PINK, GREEN, RED, BLACK,
    LAN_BUTTON_SCALE, LAN_SPACING_Y, FONT_NAME,
    PLAYER_COLORS, PLAYER_SCALE,
)
from asset_manager import AssetManager
from core import progress
from game_state import GameState
from ui.screens.common import draw_text_with_shadow, draw_text_with_outline, ColorPicker

SUBTITLE_TEXT = "Jogue cooperativamente em rede local via UDP (Porta 5555)"
SUBTITLE_Y = 120
HELP_TEXT = "Quem cria o servidor escolhe a fase (ou o Desafio)"
HELP_Y = 160
STACK_START_Y = 210   # topo do primeiro botão (abaixo do subtítulo e linha de ajuda)


class MultiplayerMenuScreen:
    """Gerencia a interface de seleção de modo de rede (Host ou Join)."""

    def __init__(self, assets: AssetManager, font: pygame.font.Font, font_bold: pygame.font.Font):
        self.assets = assets
        self.font = font
        self.font_bold = font_bold
        self.title_font = pygame.font.SysFont(FONT_NAME, 44, bold=True)
        self.status_msg = ""
        self.status_color = WHITE

        # Campo de entrada de IP
        self.ip_input = "127.0.0.1"
        self.input_active = False
        self.select_all = False  # clique no campo / Ctrl+A: próxima tecla troca o IP inteiro

        # Botões pixel-art: escala uniforme (proporção intacta), sem tamanho fixo.
        self.host_btn = button.Button(0, 0, self.assets.get_image('lan_host_btn'), LAN_BUTTON_SCALE)
        self.join_btn = button.Button(0, 0, self.assets.get_image('lan_join_btn'), LAN_BUTTON_SCALE)
        self.back_btn = button.Button(0, 0, self.assets.get_image('lan_back_btn'), LAN_BUTTON_SCALE)

        # Empilhamento vertical, centralizado em X:
        #   Y(próximo) = Y(atual) + rect.height + LAN_SPACING_Y
        # O bloco "rótulo + campo de IP" fica entre o Host e o Join, pois o
        # IP digitado é usado pelo botão Conectar.
        center_x = SCREEN_WIDTH // 2
        label_h = self.font.get_height()
        y = STACK_START_Y

        self.host_btn.rect.midtop = (center_x, y)
        y += self.host_btn.rect.height + LAN_SPACING_Y

        self.ip_label_y = y
        y += label_h + 6
        self.input_rect = pygame.Rect(0, 0, 320, 45)
        self.input_rect.midtop = (center_x, y)
        y += self.input_rect.height + LAN_SPACING_Y

        self.join_btn.rect.midtop = (center_x, y)
        y += self.join_btn.rect.height + LAN_SPACING_Y

        self.back_btn.rect.midtop = (center_x, y)

        # Seletor de cor do boneco (painel à direita da tela)
        panel_x = SCREEN_WIDTH - 150
        panel_y = STACK_START_Y + 110
        self.color_panel_center = (panel_x, panel_y)
        self.color_picker = ColorPicker(self.color_panel_center, self.font_bold, title="COR DO BONECO")
        self.color_left = self.color_picker.color_left
        self.color_right = self.color_picker.color_right
        self._last_update_tick = 0

        # Mensagem de status logo abaixo do último botão
        self.status_y = self.back_btn.rect.bottom + LAN_SPACING_Y

    @property
    def color(self) -> int:
        return self.color_picker.color

    @color.setter
    def color(self, value: int) -> None:
        self.color_picker.color = value % len(PLAYER_COLORS)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processa cliques e digitação no campo de IP e seletor de cor."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.color_picker.handle_click(event.pos):
                pass
            elif self.input_rect.collidepoint(event.pos):
                # Clicar no campo seleciona tudo: digitar ou apagar troca o IP inteiro.
                self.select_all = not self.input_active or not self.select_all
                self.input_active = True
            else:
                self.input_active = False
                self.select_all = False

        elif event.type == pygame.KEYDOWN and self.input_active:
            ctrl = event.mod & pygame.KMOD_CTRL
            if event.key == pygame.K_a and ctrl:
                self.select_all = True
            elif event.key == pygame.K_DELETE or (event.key == pygame.K_BACKSPACE and (ctrl or self.select_all)):
                self.ip_input = ""
                self.select_all = False
            elif event.key == pygame.K_BACKSPACE:
                self.ip_input = self.ip_input[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.input_active = False
                self.select_all = False
            elif event.key == pygame.K_v and ctrl:
                self._paste_ip()
                self.select_all = False
            elif event.unicode.isdigit() or event.unicode in ('.', ':'):
                if self.select_all:
                    self.ip_input = ""
                    self.select_all = False
                if len(self.ip_input) < 15:
                    self.ip_input += event.unicode
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END):
                self.select_all = False

    def _paste_ip(self) -> None:
        """Ctrl+V: troca o conteúdo do campo pelo IP da área de transferência.

        Mantém só dígitos, '.' e ':' (ex.: copiado do Radmin com espaços)."""
        try:
            text = pygame.scrap.get_text() or ""
        except Exception:
            return
        cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ".:")[:15]
        if cleaned:
            self.ip_input = cleaned

    def update(self, screen: pygame.Surface, game) -> None:
        """Renderiza a tela de configuração multiplayer."""
        game._draw_bg()

        now = pygame.time.get_ticks()
        if now - self._last_update_tick > 250:
            self.color_picker.reload()
        self._last_update_tick = now

        # Título principal
        draw_text_with_shadow(screen, "MULTIPLAYER EM LAN", self.title_font, WHITE, SCREEN_WIDTH // 2, 60)
        # Subtítulo: texto branco com contorno preto de 2 px (legível sobre as nuvens)
        draw_text_with_outline(
            screen, SUBTITLE_TEXT, self.font, WHITE, SCREEN_WIDTH // 2, SUBTITLE_Y,
            outline_color=BLACK, thickness=2,
        )
        draw_text_with_outline(
            screen, HELP_TEXT, self.font, WHITE, SCREEN_WIDTH // 2, HELP_Y,
            outline_color=BLACK, thickness=2,
        )

        # 1. Botão Host
        if self.host_btn.draw(screen):
            self.status_msg = ""
            game.mp_host_pick = True
            game.state = GameState.LEVEL_SELECT

        # Caixa de texto para o IP do Host
        draw_text_with_shadow(screen, "IP do Servidor Host:", self.font, WHITE, SCREEN_WIDTH // 2, self.ip_label_y)
        input_border_color = GREEN if self.input_active else (140, 140, 160)
        pygame.draw.rect(screen, (30, 35, 45), self.input_rect, border_radius=6)
        pygame.draw.rect(screen, input_border_color, self.input_rect, 2, border_radius=6)

        text_pos = (self.input_rect.x + 12, self.input_rect.centery - self.font_bold.get_height() // 2)
        if self.select_all and self.ip_input:
            # Texto selecionado: fundo azul, como num campo de texto comum
            sel = self.font_bold.render(self.ip_input, True, WHITE)
            pygame.draw.rect(screen, (50, 100, 200), sel.get_rect(topleft=text_pos).inflate(4, 2))
            screen.blit(sel, text_pos)
        else:
            ip_display = self.ip_input + ("|" if self.input_active and (pygame.time.get_ticks() // 400) % 2 == 0 else "")
            screen.blit(self.font_bold.render(ip_display, True, WHITE), text_pos)

        # 2. Botão Join
        if self.join_btn.draw(screen):
            target_ip = self.ip_input.strip() if self.ip_input.strip() else "127.0.0.1"
            self.status_msg = f"Conectando a {target_ip}..."
            self.status_color = (255, 255, 100)
            if game.start_multiplayer_client(target_ip):
                self.status_msg = "Conectado! Entrando na partida..."
            else:
                self.status_msg = f"Erro ao conectar com {target_ip}."
                self.status_color = RED

        # 3. Botão Voltar
        if self.back_btn.draw(screen):
            game.state = GameState.MENU

        # Seletor de cor do soldado (painel à direita da tela)
        self.color_picker.draw(screen)

        # Mensagem de status
        if self.status_msg:
            draw_text_with_shadow(screen, self.status_msg, self.font_bold, self.status_color, SCREEN_WIDTH // 2, self.status_y)
        else:
            draw_text_with_shadow(screen, "Pressione ESC para voltar ao menu", self.font, PINK, SCREEN_WIDTH // 2, self.status_y)
