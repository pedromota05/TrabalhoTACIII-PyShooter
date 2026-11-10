"""
ui/screens/multiplayer_menu.py — Tela de Configuração e Conexão Multiplayer em LAN.

Permite hospedar um servidor local (Host) ou conectar-se como cliente (Join)
informando o IP do servidor na rede local.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, PINK, GREEN, RED, BLACK
from asset_manager import AssetManager
from game_state import GameState
from ui.screens.common import draw_text_with_shadow


class MultiplayerMenuScreen:
    """Gerencia a interface de seleção de modo de rede (Host ou Join)."""

    def __init__(self, assets: AssetManager, font: pygame.font.Font, font_bold: pygame.font.Font):
        self.assets = assets
        self.font = font
        self.font_bold = font_bold
        self.title_font = pygame.font.SysFont('Futura', 44, bold=True)
        self.status_msg = ""
        self.status_color = WHITE

        # Campo de entrada de IP
        self.ip_input = "127.0.0.1"
        self.input_active = False

        # Criação dos botões estilizados
        btn_w, btn_h = 320, 60
        center_x = SCREEN_WIDTH // 2 - btn_w // 2

        self.host_btn = button.Button(
            center_x, 220,
            self._create_styled_button_surf("1. CRIAR SERVIDOR (HOST)", (40, 140, 60), btn_w, btn_h),
            1.0,
        )

        self.join_btn = button.Button(
            center_x, 380,
            self._create_styled_button_surf("2. CONECTAR VIA IP", (40, 90, 180), btn_w, btn_h),
            1.0,
        )

        self.back_btn = button.Button(
            center_x, 480,
            self._create_styled_button_surf("<- VOLTAR AO MENU", (180, 50, 50), btn_w, btn_h),
            1.0,
        )

        self.input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 160, 315, 320, 45)

    def _create_styled_button_surf(self, text: str, bg_color: tuple, w: int, h: int) -> pygame.Surface:
        """Gera uma superfície estilizada para botões do menu multiplayer."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg_color, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(surf, WHITE, (0, 0, w, h), 2, border_radius=8)

        text_surf = self.font_bold.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=(w // 2, h // 2))
        surf.blit(text_surf, text_rect)
        return surf

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
            elif len(self.ip_input) < 15 and (event.unicode.isdigit() or event.unicode in ('.', ':')):
                self.ip_input += event.unicode

    def update(self, screen: pygame.Surface, game) -> None:
        """Renderiza a tela de configuração multiplayer."""
        game._draw_bg()

        # Título principal
        draw_text_with_shadow(screen, "MULTIPLAYER EM LAN", self.title_font, WHITE, SCREEN_WIDTH // 2, 60)
        draw_text_with_shadow(
            screen, "Jogue cooperativamente em rede local via UDP (Porta 5555)",
            self.font, (220, 220, 220), SCREEN_WIDTH // 2, 120
        )

        # Card de fundo central
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 170, 500, 390)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((15, 20, 30, 220))
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, (80, 100, 130), panel_rect, 2, border_radius=12)

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
        draw_text_with_shadow(screen, "IP do Servidor Host:", self.font, WHITE, SCREEN_WIDTH // 2, 290)
        input_border_color = GREEN if self.input_active else (140, 140, 160)
        pygame.draw.rect(screen, (30, 35, 45), self.input_rect, border_radius=6)
        pygame.draw.rect(screen, input_border_color, self.input_rect, 2, border_radius=6)

        ip_display = self.ip_input + ("|" if self.input_active and (pygame.time.get_ticks() // 400) % 2 == 0 else "")
        ip_surf = self.font_bold.render(ip_display, True, WHITE)
        screen.blit(ip_surf, (self.input_rect.x + 12, self.input_rect.y + 10))

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
            draw_text_with_shadow(screen, self.status_msg, self.font_bold, self.status_color, SCREEN_WIDTH // 2, 570)
        else:
            draw_text_with_shadow(screen, "Pressione ESC para voltar ao menu", self.font, PINK, SCREEN_WIDTH // 2, 575)
