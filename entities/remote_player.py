"""
entities/remote_player.py — Representação visual de jogadores remotos via LAN.

Utiliza interpolação LERP para movimentação fluida, reproduz animações
sincronizadas e desenha indicadores de identificação (ex: "P2") e vida sobre a entidade.
"""

import pygame
from config import PLAYER_SCALE, ANIMATION_COOLDOWN, WHITE, GREEN, RED, BLACK
from asset_manager import AssetManager
from entities.combat.projectiles import Bullet


class RemotePlayer(pygame.sprite.Sprite):
    """Sprite representativo de um jogador conectado remotamente na LAN."""

    def __init__(self, player_id: str, x: float, y: float):
        super().__init__()
        self.player_id = player_id
        self.world_x = float(x)
        self.world_y = float(y)
        self.direction = 1
        self.action = 0
        self.health = 100
        self.max_health = 100
        self.alive = True

        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.shoot_cooldown = 0

        # Carrega animações idênticas ao jogador local via cache do AssetManager
        assets = AssetManager()
        self.animation_list = assets.load_character_animations('player', PLAYER_SCALE)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))

        # Fonte para identificação sobre a cabeça
        self.font = pygame.font.SysFont('Futura', 16, bold=True)

    def update_from_network(
        self,
        data: dict,
        bg_scroll: int = 0,
        bullet_group: pygame.sprite.Group | None = None
    ) -> None:
        """Atualiza estado, interpolação, animação e combate conforme dados da rede."""
        curr_pos = data.get("current", [self.world_x, self.world_y])
        self.world_x = float(curr_pos[0])
        self.world_y = float(curr_pos[1])
        new_action = data.get("action", 0)
        self.direction = data.get("direction", 1)
        self.health = data.get("health", 100)
        self.alive = self.health > 0

        # Atualiza a ação da animação se mudou
        if new_action != self.action and new_action < len(self.animation_list):
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

        # Atualiza frames de animação
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 3:  # Animação de morte
                    self.frame_index = len(self.animation_list[self.action]) - 1
                else:
                    self.frame_index = 0

        current_frame = self.animation_list[self.action][self.frame_index]
        flip = self.direction < 0
        self.image = pygame.transform.flip(current_frame, flip, False)

        # Ajusta posição na tela considerando a rolagem acumulada da câmera (bg_scroll)
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.world_x - bg_scroll), int(self.world_y))

        # Disparo remoto sincronizado
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        is_shooting = data.get("shooting", False)
        if is_shooting and self.shoot_cooldown == 0 and self.alive and bullet_group is not None:
            self.shoot_cooldown = 20
            bullet_x = self.rect.centerx + (0.75 * self.rect.size[0] * self.direction)
            bullet_y = self.rect.centery
            bullet = Bullet(bullet_x, bullet_y, self.direction)
            bullet_group.add(bullet)
            AssetManager().get_sound('shot').play()

    def draw(self, screen: pygame.Surface) -> None:
        """Renderiza o jogador remoto com tag de identificação e mini barra de HP."""
        screen.blit(self.image, self.rect)

        if self.alive:
            # Tag com nome / ID do jogador (ex: "P2" ou player_id)
            tag_text = self.player_id.upper()
            tag_surf = self.font.render(tag_text, True, WHITE)
            tag_rect = tag_surf.get_rect(centerx=self.rect.centerx, bottom=self.rect.top - 8)
            # Fundo preto para destaque
            bg_rect = tag_rect.inflate(6, 2)
            pygame.draw.rect(screen, BLACK, bg_rect, border_radius=3)
            screen.blit(tag_surf, tag_rect)

            # Mini barra de vida sobre a cabeça
            bar_w = 40
            bar_h = 5
            bar_x = self.rect.centerx - bar_w // 2
            bar_y = self.rect.top - 5

            hp_ratio = max(0.0, min(1.0, self.health / self.max_health))
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
            pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_w, bar_h), 1)
