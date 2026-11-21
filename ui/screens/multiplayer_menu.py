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
)
from asset_manager import AssetManager
from game_state import GameState
from ui.screens.common import draw_text_with_shadow, draw_text_with_outline

SUBTITLE_TEXT = "Jogue cooperativamente em rede local via UDP (Porta 5555)"
SUBTITLE_Y = 120
STACK_START_Y = 190   # topo do primeiro botão (abaixo do subtítulo)


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

        # Mensagem de status logo abaixo do último botão
        self.status_y = self.back_btn.rect.bottom + LAN_SPACING_Y

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processa cliques e digitação no campo de IP."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_rect.collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False

        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_BACKSPACE:
                self.ip_input = self.ip_input[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.input_active = False
            elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                self._paste_ip()
            elif len(self.ip_input) < 15 and (event.unicode.isdigit() or event.unicode in ('.', ':')):
                self.ip_input += event.unicode

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

        # Título principal
        draw_text_with_shadow(screen, "MULTIPLAYER EM LAN", self.title_font, WHITE, SCREEN_WIDTH // 2, 60)
        # Subtítulo: texto branco com contorno preto de 2 px (legível sobre as nuvens)
        draw_text_with_outline(
            screen, SUBTITLE_TEXT, self.font, WHITE, SCREEN_WIDTH // 2, SUBTITLE_Y,
            outline_color=BLACK, thickness=2,
        )

        # 1. Botão Host
        if self.host_btn.draw(screen):
            self.status_msg = "Iniciando Servidor Host..."
            self.status_color = GREEN
            if game.start_multiplayer_host():
                self.status_msg = "Servidor ativo! Entrando na partida..."
            else:
                self.status_msg = "Erro ao iniciar o servidor na porta 5555."
                self.status_color = RED

        # Caixa de texto para o IP do Host
        draw_text_with_shadow(screen, "IP do Servidor Host:", self.font, WHITE, SCREEN_WIDTH // 2, self.ip_label_y)
        input_border_color = GREEN if self.input_active else (140, 140, 160)
        pygame.draw.rect(screen, (30, 35, 45), self.input_rect, border_radius=6)
        pygame.draw.rect(screen, input_border_color, self.input_rect, 2, border_radius=6)

        ip_display = self.ip_input + ("|" if self.input_active and (pygame.time.get_ticks() // 400) % 2 == 0 else "")
        ip_surf = self.font_bold.render(ip_display, True, WHITE)
        screen.blit(ip_surf, (self.input_rect.x + 12, self.input_rect.centery - ip_surf.get_height() // 2))

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

        # Mensagem de status
        if self.status_msg:
            draw_text_with_shadow(screen, self.status_msg, self.font_bold, self.status_color, SCREEN_WIDTH // 2, self.status_y)
        else:
            draw_text_with_shadow(screen, "Pressione ESC para voltar ao menu", self.font, PINK, SCREEN_WIDTH // 2, self.status_y)
