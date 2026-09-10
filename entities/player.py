"""
entities/player.py — Jogador (Player) do PyShooter.
"""

import pygame
from config import (
    JUMP_VELOCITY, SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_SIZE, SCROLL_THRESH,
    PLAYER_SCALE, PLAYER_SPEED, PLAYER_START_AMMO, PLAYER_START_GRENADES,
)
from .base import Character


class Player(Character):
    """Personagem controlado pelo jogador; gerencia scroll de câmera e invencibilidade."""

    def __init__(self, x: int, y: int, scale: float = PLAYER_SCALE,
                 speed: int = PLAYER_SPEED, ammo: int = PLAYER_START_AMMO,
                 grenades: int = PLAYER_START_GRENADES):
        super().__init__('player', x, y, scale, speed, ammo, grenades)
        self.invincible = 0

    def update(self, enemy_group=None):
        super().update()

        # Lógica de I-Frames
        if self.invincible > 0:
            self.invincible -= 1

        # Dano de Contato
        if enemy_group and self.invincible == 0:
            for enemy in enemy_group:
                if type(enemy).__name__ == 'SkeletonEnemy':
                    continue  # Ignora o dano de contato passivo

                # Reduz a largura do retângulo invisível para ignorar a transparência
                hitbox_inimigo = enemy.rect.inflate(-50, -10)
                if enemy.alive and self.rect.colliderect(hitbox_inimigo):
                    self.health -= 10
                    self.invincible = 60
                    break

    def draw(self, screen: pygame.Surface):
        # Efeito visual de piscar durante a invencibilidade
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return  # Pula o frame, fazendo o personagem sumir
        super().draw(screen)

    def _check_environment(self, water_group):
        """Verifica perigos ambientais com hitbox perdoável para água.

        O jogador só morre se o centro do corpo estiver abaixo da
        superfície da água, evitando mortes injustas por encostar 1 pixel.
        """
        for water in water_group:
            if (water.rect.colliderect(self.rect)
                    and self.rect.centery > water.rect.top):
                self.health = 0
                break
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

    def move(self, moving_left: bool, moving_right: bool, obstacle_list: list,
             water_group, exit_group, bg_scroll: int, level_length: int,
             ramp_list: list = None):
        if ramp_list is None:
            ramp_list = []

        screen_scroll = 0
        dx = 0
        dy = 0

        # Movimento horizontal constante (base)
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # Modificador de controle no ar (Air Control)
        if self.in_air:
            dx = int(dx * 0.7)  # Reduz ganho horizontal no ar para precisão de plataformas

        # Pulo
        if self.jump and not self.in_air:
            self.vel_y = JUMP_VELOCITY
            self.jump = False
            self.in_air = True

        # Gravidade
        self._apply_gravity()
        dy += self.vel_y

        # Colisão com tiles
        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list, ramp_list)

        # Perigos ambientais
        self._check_environment(water_group)

        # Saída de fase
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # Limites da tela
        if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
            dx = 0

        # Atualizar posição
        self.rect.x += dx
        self.rect.y += dy

        # Scroll da câmera
        if ((self.rect.right > SCREEN_WIDTH - SCROLL_THRESH
                and bg_scroll < (level_length * TILE_SIZE) - SCREEN_WIDTH)
                or (self.rect.left < SCROLL_THRESH
                    and bg_scroll > abs(dx))):
            self.rect.x -= dx
            screen_scroll = -dx

        return screen_scroll, level_complete
