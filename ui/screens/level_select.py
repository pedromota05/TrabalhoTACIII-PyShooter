"""
ui/screens/level_select.py — Tela de Seleção de Fase do PyShooter.

Mostra o progresso salvo (core/progress.py): selo "CONCLUÍDA" e contorno
verde nas fases já vencidas, o botão do Modo Desafio (liberado após zerar a
campanha) e opções de treino para iniciar o Desafio em qualquer fase após ter recorde.
"""

import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, PINK, RED, FONT_NAME, FPS, SHARED_LIVES
from asset_manager import AssetManager
from core import progress
from game_state import GameState
from ui.screens.common import draw_text_with_shadow, draw_text_with_outline, ColorPicker
from ui.screens.victory import format_time

DONE_GREEN = (60, 220, 90)
LOCKED_GREY = (110, 110, 110)
CHALLENGE_RED = (200, 45, 40)
CHALLENGE_SIZE = (300, 64)


def _challenge_surface(text: str, fill: tuple, font: pygame.font.Font) -> pygame.Surface:
    """Botão de texto: retângulo arredondado com borda escura e texto centralizado."""
    surf = pygame.Surface(CHALLENGE_SIZE, pygame.SRCALPHA)
    rect = surf.get_rect()
    pygame.draw.rect(surf, (20, 20, 20), rect, border_radius=12)
    pygame.draw.rect(surf, fill, rect.inflate(-6, -6), border_radius=10)
    label = font.render(text, True, WHITE)
    surf.blit(label, label.get_rect(center=rect.center))
    return surf


def _small_button_surface(text: str, fill: tuple, font: pygame.font.Font) -> pygame.Surface:
    """Botão de fase do treino: retângulo arredondado 52x40 com borda escura e texto centralizado."""
    surf = pygame.Surface((52, 40), pygame.SRCALPHA)
    rect = surf.get_rect()
    pygame.draw.rect(surf, (20, 20, 20), rect, border_radius=8)
    pygame.draw.rect(surf, fill, rect.inflate(-4, -4), border_radius=6)
    label = font.render(text, True, WHITE)
    surf.blit(label, label.get_rect(center=rect.center))
    return surf


def _draw_check(screen: pygame.Surface, x: int, y: int, color: tuple) -> None:
    """Desenha um visto (✔) com linhas; a fonte padrão não tem esse caractere."""
    pygame.draw.lines(screen, (0, 0, 0), False, [(x, y + 8), (x + 6, y + 14), (x + 16, y)], 6)
    pygame.draw.lines(screen, color, False, [(x, y + 8), (x + 6, y + 14), (x + 16, y)], 3)


class LevelSelectScreen:
    """Gerencia a seleção e carregamento de fases pelo jogador."""

    def __init__(self, assets: AssetManager, font: pygame.font.Font, font_bold: pygame.font.Font):
        self.assets = assets
        self.font = font
        self.font_bold = font_bold
        self.small_font = pygame.font.SysFont(FONT_NAME, 22, bold=True)
        self.badge_font = pygame.font.SysFont(FONT_NAME, 19, bold=True)
        self.level_buttons: list[button.Button] = []

        gamepad_spacing = 20
        sample_img = self.assets.get_image('gamepad1')
        total_width = (sample_img.get_width() * 4) + (gamepad_spacing * 3)
        start_x = (SCREEN_WIDTH - total_width) // 2
        btn_y = SCREEN_HEIGHT // 2 - sample_img.get_height() // 2 - 60

        for i in range(1, 5):
            btn_x = start_x + (i - 1) * (sample_img.get_width() + gamepad_spacing)
            btn = button.Button(
                btn_x, btn_y,
                self.assets.get_image(f'gamepad{i}'), 1,
            )
            self.level_buttons.append(btn)

        # Botão do Modo Desafio em duas versões (bloqueado / liberado), mesmo rect.
        self.challenge_locked = button.Button(
            0, 0, _challenge_surface('MODO DESAFIO', LOCKED_GREY, self.font_bold), 1)
        self.challenge_open = button.Button(
            0, 0, _challenge_surface('MODO DESAFIO', CHALLENGE_RED, self.font_bold), 1)
        for btn in (self.challenge_locked, self.challenge_open):
            btn.rect.midtop = (SCREEN_WIDTH // 2, btn_y + sample_img.get_height() + 90)

        # Botões de início rápido para treino no Modo Desafio (fases 1 a 5)
        self.challenge_start_buttons: list[button.Button] = []
        small_btn_w = 52
        small_spacing = 12
        total_small_w = (small_btn_w * 5) + (small_spacing * 4)
        small_start_x = (SCREEN_WIDTH - total_small_w) // 2
        small_btn_y = self.challenge_open.rect.bottom + 62

        for i in range(5):
            bx = small_start_x + i * (small_btn_w + small_spacing)
            btn = button.Button(
                bx, small_btn_y,
                _small_button_surface(str(i + 1), CHALLENGE_RED, self.badge_font), 1,
            )
            btn.rect.top = small_btn_y
            self.challenge_start_buttons.append(btn)

        # Seletor de cor do boneco (painel à direita da tela)
        panel_x = SCREEN_WIDTH - 150
        panel_y = SCREEN_HEIGHT // 2 - 10
        self.color_picker = ColorPicker((panel_x, panel_y), self.font_bold, title="SEU BONECO")
        self.prev_mouse_pressed = False
        self._last_active_tick = 0

    def update(self, screen: pygame.Surface, game) -> None:
        game._draw_bg()
        now = pygame.time.get_ticks()
        if now - self._last_active_tick > 250:
            self.color_picker.reload()
        self._last_active_tick = now

        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed and not self.prev_mouse_pressed:
            self.color_picker.handle_click(pygame.mouse.get_pos())
        self.prev_mouse_pressed = mouse_pressed

        saved = progress.carregar()  # relê do disco só quando o arquivo muda
        done = set(saved['fases_concluidas'])

        # Título centralizado
        title = 'MULTIPLAYER: ESCOLHA A FASE' if getattr(game, 'mp_host_pick', False) else 'SELECIONE A FASE'
        draw_text_with_shadow(screen, title, self.font_bold, WHITE, SCREEN_WIDTH // 2, 80)

        # Rótulos acima, contorno verde e selo "CONCLUÍDA" abaixo das fases vencidas
        for i, btn in enumerate(self.level_buttons):
            draw_text_with_shadow(screen, f'Fase {i + 1}', self.font, WHITE, btn.rect.centerx, btn.rect.top - 35)
            if i + 1 in done:
                pygame.draw.rect(screen, DONE_GREEN, btn.rect.inflate(14, 14), 4, border_radius=12)
                # Medalha com visto no canto superior direito do contorno
                badge = (btn.rect.right + 4, btn.rect.top - 4)
                pygame.draw.circle(screen, (0, 0, 0), badge, 14)
                pygame.draw.circle(screen, DONE_GREEN, badge, 12)
                _draw_check(screen, badge[0] - 8, badge[1] - 7, WHITE)
                draw_text_with_outline(screen, 'CONCLUÍDA', self.badge_font, DONE_GREEN,
                                       btn.rect.centerx, btn.rect.bottom + 14)

        # Desenhar botões e checar cliques (todas as fases continuam abertas)
        for i, btn in enumerate(self.level_buttons):
            if btn.draw(screen):
                if getattr(game, 'mp_host_pick', False):
                    game.mp_host_pick = False
                    ok = game.start_multiplayer_host(level=i + 1)
                    if not ok:
                        game.multiplayer_screen.status_msg = "Erro ao iniciar o servidor na porta 5555."
                        game.multiplayer_screen.status_color = RED
                        game.state = GameState.MULTIPLAYER_MENU
                else:
                    game.challenge_mode = False
                    game.level = i + 1
                    game.lives = SHARED_LIVES
                    game.bg_scroll = 0
                    game.run_frames = 0
                    game.start_intro = True
                    game._load_level(game.level)
                    game.state = GameState.PLAYING

        # Modo Desafio: cinza e sem ação até a campanha ser zerada
        if saved['campanha_zerada']:
            clicked = self.challenge_open.draw(screen)
            record = saved['recorde_desafio']
            info = f'Recorde: {format_time(int(record * FPS))}' if record is not None else 'Sem recorde ainda'
            draw_text_with_outline(screen, info, self.small_font, WHITE,
                                   SCREEN_WIDTH // 2, self.challenge_open.rect.bottom + 8)
            if clicked:
                if getattr(game, 'mp_host_pick', False):
                    game.mp_host_pick = False
                    ok = game.start_multiplayer_host(challenge=True)
                    if not ok:
                        game.multiplayer_screen.status_msg = "Erro ao iniciar o servidor na porta 5555."
                        game.multiplayer_screen.status_color = RED
                        game.state = GameState.MULTIPLAYER_MENU
                else:
                    game.start_challenge()

            if record is not None and not getattr(game, 'mp_host_pick', False):
                draw_text_with_outline(screen, 'Treino: começar na fase', self.small_font, WHITE,
                                       SCREEN_WIDTH // 2, self.challenge_open.rect.bottom + 36)
                for i, btn in enumerate(self.challenge_start_buttons):
                    if btn.draw(screen):
                        game.start_challenge(start_index=i)
        else:
            self.challenge_locked.draw(screen)
            draw_text_with_outline(screen, 'Zere a campanha para liberar', self.small_font, LOCKED_GREY,
                                   SCREEN_WIDTH // 2, self.challenge_locked.rect.bottom + 8)

        # Seletor de cor do soldado
        self.color_picker.draw(screen)

        # Dica para voltar
        hint = "ESC volta para o Multiplayer" if getattr(game, 'mp_host_pick', False) else 'Pressione ESC para voltar ao menu'
        draw_text_with_shadow(
            screen, hint, self.font_bold, PINK, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60
        )
