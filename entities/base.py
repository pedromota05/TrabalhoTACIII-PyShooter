"""
entities/base.py — Classe base para personagens animados no PyShooter.
"""

import pygame
from config import (
    GRAVITY, TERMINAL_VELOCITY,
    SCREEN_HEIGHT, SHOOT_COOLDOWN, ANIMATION_COOLDOWN,
)
from asset_manager import AssetManager
from entities.combat.projectiles import Bullet


class Character(pygame.sprite.Sprite):
    """Entidade animada com vida, física (gravidade + colisão) e tiro."""

    def __init__(self, char_type: str, x: int, y: int, scale: float,
                 speed: int, ammo: int, grenades: int):
        super().__init__()
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        self.base_speed = speed
        self.speed_boost = False
        self.speed_boost_timer = 0

        # Carregar animações via AssetManager (com cache)
        assets = AssetManager()
        self.animation_list = assets.load_character_animations(char_type, scale)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    # ------------------------------------------------------------------
    #  Atualização por frame
    # ------------------------------------------------------------------
    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.speed_boost:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost = False
                self.speed = self.base_speed

    # ------------------------------------------------------------------
    #  Física compartilhada
    # ------------------------------------------------------------------
    def _calculate_movement(self, moving_left: bool, moving_right: bool) -> int:
        """Define dx com base nas flags de direção."""
        dx = 0
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        return dx

    def _apply_gravity(self):
        """Acumula gravidade e aplica clamping de velocidade terminal."""
        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY

    def _check_tile_collisions(self, dx: int, dy: int, obstacle_list: list, ramp_list: list = None):
        if ramp_list is None:
            ramp_list = []
        """Detecta e resolve colisões AABB com tiles sólidos."""
        # Cria uma margem de ~20% na largura para ignorar a ponta da arma/sprite solto
        margin = int(self.width * 0.2)
        col_width = self.width - (margin * 2)

        for tile in obstacle_list:
            # Colisão horizontal (usa hitbox mais fina)
            if tile[1].colliderect(self.rect.x + dx + margin, self.rect.y,
                                   col_width, self.height):
                dx = 0
                self._on_horizontal_collision()

            # Colisão vertical
            if tile[1].colliderect(self.rect.x + dx + margin, self.rect.y + dy,
                                   col_width, self.height):
                if self.vel_y < 0:                  # subindo (pulo)
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:               # caindo
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # Colisão com Rampas
        for tile in ramp_list:
            ramp = tile[1]
            future_centerx = self.rect.centerx + dx
            if ramp.left <= future_centerx <= ramp.right:
                local_x = future_centerx - ramp.left
                chao_y = ramp.bottom - local_x
                if self.rect.bottom + dy >= chao_y:
                    dy = chao_y - self.rect.bottom
                    self.vel_y = 0
                    self.in_air = False

        return dx, dy

    def _on_horizontal_collision(self):
        """Hook para subclasses reagirem a colisão com parede."""
        pass

    def _check_environment(self, water_group):
        """Verifica perigos ambientais (água e queda do mapa)."""
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

    # ------------------------------------------------------------------
    #  Combate
    # ------------------------------------------------------------------
    def shoot(self, bullet_group):
        """Dispara um projétil se houver munição e o cooldown permitir."""
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5

            bullet = Bullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('shot').play()

    # ------------------------------------------------------------------
    #  Animação
    # ------------------------------------------------------------------
    def update_animation(self):
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:        # Death: congela no último frame
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action: int):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    # ------------------------------------------------------------------
    #  Renderização
    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        screen.blit(pygame.transform.flip(self.image, self.flip, False),
                    self.rect)
