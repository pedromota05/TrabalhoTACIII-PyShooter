"""
button.py — Classe Button com controle de clique único, anti click-through e cursor estável.
"""

import pygame


class Button:
    """Botão gráfico com debounce global de clique e controle estável de cursor."""

    _global_mouse_down = False
    _cursor_hovered = False
    _active_cursor = None

    def __init__(self, x: int, y: int, image: pygame.Surface, scale: float = 1.0):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    @classmethod
    def update_cursor(cls) -> None:
        """Atualiza o cursor do sistema apenas quando o estado de hover mudar (evita flicker)."""
        target = pygame.SYSTEM_CURSOR_HAND if cls._cursor_hovered else pygame.SYSTEM_CURSOR_ARROW
        if cls._active_cursor != target:
            try:
                pygame.mouse.set_cursor(target)
                cls._active_cursor = target
            except Exception:
                pass
        cls._cursor_hovered = False

    @classmethod
    def reset_click_state(cls) -> None:
        """Trava o clique se o botão do mouse já estiver pressionado na troca de tela."""
        try:
            cls._global_mouse_down = pygame.mouse.get_pressed()[0] == 1
        except Exception:
            cls._global_mouse_down = False

    def draw(self, surface: pygame.Surface) -> bool:
        """Desenha o botão e retorna True apenas em cliques novos."""
        action = False
        pos = pygame.mouse.get_pos()
        left_down = pygame.mouse.get_pressed()[0] == 1

        # Libera o clique global assim que o usuário soltar o botão do mouse
        if not left_down:
            self.clicked = False
            Button._global_mouse_down = False

        # Verifica se o mouse está sobre o botão
        if self.rect.collidepoint(pos):
            Button._cursor_hovered = True

            # Dispara somente no início do clique (novo) e se não tiver sido consumido em outra tela
            if left_down and not self.clicked and not Button._global_mouse_down:
                action = True
                self.clicked = True
                Button._global_mouse_down = True

        surface.blit(self.image, (self.rect.x, self.rect.y))
        return action