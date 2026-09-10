"""
entities/enemies/standard.py — Inimigo Soldado padrão e Sniper.
"""

import random
import pygame
from config import (
    TILE_SIZE, ENEMY_SCALE, ENEMY_SPEED, ENEMY_AMMO, ENEMY_GRENADES,
    ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT,
)
from asset_manager import AssetManager
from entities.base import Character
from entities.combat.projectiles import Bullet


# ======================================================================
#  ENEMY
# ======================================================================
class Enemy(Character):
    """Soldado inimigo com IA de patrulha e ataque."""

    def __init__(self, x: int, y: int, scale: float = ENEMY_SCALE,
                 speed: int = ENEMY_SPEED, ammo: int = ENEMY_AMMO,
                 grenades: int = ENEMY_GRENADES):
        super().__init__('enemy', x, y, scale, speed, ammo, grenades)
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT)
        self.idling = False
        self.idling_counter = 0
        self.flip_cooldown = 0

    def _on_horizontal_collision(self):
        """Inverte a direção ao colidir com uma parede."""
        if self.flip_cooldown == 0:
            self.direction *= -1
            self.move_counter = 0
            self.flip_cooldown = 30  # Força 30 frames antes de virar de novo

    def _is_edge_ahead(self, obstacle_list: list) -> bool:
        """Detecta se não há chão sólido à frente dos pés do inimigo."""
        if self.in_air:
            return False  # Ignorar detecção de borda se já estiver no ar

        if self.direction == 1:
            check_x = self.rect.right + 2
        else:
            check_x = self.rect.left - 2

        test_rect = pygame.Rect(check_x - 1, self.rect.bottom + 1, 2, TILE_SIZE)
        for tile in obstacle_list:
            if tile[1].colliderect(test_rect):
                return False   # Chão encontrado — sem borda
        return True            # Sem chão à frente — borda detectada!

    def move(self, moving_left: bool, moving_right: bool, obstacle_list: list, water_group):
        """Movimento simplificado (sem scroll nem saída)."""
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0

        self._apply_gravity()
        dy += self.vel_y

        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list)
        self._check_environment(water_group)

        self.rect.x += dx
        self.rect.y += dy

    def ai(self, player, screen_scroll: int, obstacle_list: list, water_group,
           bullet_group):
        """Lógica de IA: patrulha, detecção e ataque."""
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            # Chance aleatória de parar (idling)
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)           # Idle
                self.idling = True
                self.idling_counter = 50

            # Jogador dentro do campo de visão → atirar
            if self.vision.colliderect(player.rect):
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False

                self.update_action(0)           # Idle (mira)
                self.shoot(bullet_group)
            else:
                if not self.idling:
                    # Detecção de borda — inverter ANTES de cair
                    if self._is_edge_ahead(obstacle_list):
                        self.direction *= -1
                        self.move_counter = 0
                        self.flip_cooldown = 30

                    ai_moving_right = (self.direction == 1)
                    ai_moving_left = not ai_moving_right

                    self.move(ai_moving_left, ai_moving_right,
                              obstacle_list, water_group)
                    self.update_action(1)       # Run
                    self.move_counter += 1

                    # Inverter ao fim do percurso de patrulha
                    if self.move_counter > TILE_SIZE * 3:
                        if self.flip_cooldown == 0:
                            self.direction *= -1
                            self.move_counter = 0
                            self.flip_cooldown = 30
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        # Scroll do mundo
        self.rect.x += screen_scroll

        # Atualizar retângulo de visão
        self.vision.center = (
            self.rect.centerx + 75 * self.direction,
            self.rect.centery,
        )


# ======================================================================
#  SNIPER
# ======================================================================
class Sniper(Enemy):
    """Atirador de elite com visão ampliada, tiro mais rápido e cooldown maior."""

    def __init__(self, x: int, y: int, scale: float = 1.2, speed: int = 1,
                 ammo: int = 9999, grenades: int = 0):
        super().__init__(x, y, scale, speed, ammo, grenades)
        self.vision = pygame.Rect(0, 0, 300, 20)

        # Override animation list com o extrator de sprite strips do sniper
        self.animation_list = []
        animations = [
            'Idle',     # action 0
            'Walk',     # action 1
            'Shot_1',   # action 2
            'Dead',     # action 3
            'Hurt'      # action 4
        ]

        for anim in animations:
            img = pygame.image.load(f'img/sniper/{anim}.png').convert_alpha()
            frame_height = img.get_height()
            frame_width = frame_height  # Frames quadrados
            num_frames = img.get_width() // frame_width

            temp_list = []
            for i in range(num_frames):
                frame = img.subsurface((i * frame_width, 0, frame_width, frame_height))
                frame = pygame.transform.scale(
                    frame,
                    (int(frame_width * scale), int(frame_height * scale))
                )
                temp_list.append(frame)
            self.animation_list.append(temp_list)

        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)

        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def shoot(self, bullet_group):
        """Dispara exatamente no frame 2 da animação de tiro (Shot_1)."""
        if self.shoot_cooldown == 0 and self.ammo > 0 and self.action == 2 and self.frame_index == 2:
            self.shoot_cooldown = 60
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5

            bullet = Bullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet.speed = 15
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('shot').play()

    def ai(self, player, screen_scroll: int, obstacle_list: list, water_group, bullet_group):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)           # Idle
                self.idling = True
                self.idling_counter = 50

            if self.vision.colliderect(player.rect):
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False

                self.update_action(2)           # Attack (Shot_1)
                self.shoot(bullet_group)
            else:
                if not self.idling:
                    if self._is_edge_ahead(obstacle_list):
                        if self.flip_cooldown == 0:
                            self.direction *= -1
                            self.move_counter = 0
                            self.flip_cooldown = 30
                            self.flip = not self.flip

                    ai_moving_right = (self.direction == 1)
                    ai_moving_left = not ai_moving_right

                    self.move(ai_moving_left, ai_moving_right, obstacle_list, water_group)
                    self.update_action(1)       # Walk
                    self.move_counter += 1

                    if self.move_counter > TILE_SIZE * 3:
                        if self.flip_cooldown == 0:
                            self.direction *= -1
                            self.move_counter = 0
                            self.flip_cooldown = 30
                            self.flip = not self.flip
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        self.rect.x += screen_scroll
        self.vision.center = (
            self.rect.centerx + 75 * self.direction,
            self.rect.centery,
        )
