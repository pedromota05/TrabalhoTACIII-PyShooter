"""
entities/enemies/robot.py — Inimigo Robô com tiro direcional.
"""

import math
import random
import pygame
from config import (
    TILE_SIZE, ENEMY_SCALE, ENEMY_AMMO, ENEMY_GRENADES,
    ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT,
    BULLET_SPEED, SHOOT_COOLDOWN,
)
from asset_manager import AssetManager
from entities.base import Character
from entities.combat.projectiles import RobotBullet


class RobotEnemy(Character):
    """Inimigo robô com IA de patrulha e disparos de projéteis energéticos em direção ao jogador."""

    def __init__(self, x: int, y: int, scale: float = ENEMY_SCALE, speed: int = 1,
                 ammo: int = ENEMY_AMMO, grenades: int = ENEMY_GRENADES):
        super().__init__('enemy', x, y, scale, speed, ammo, grenades)
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT)
        self.idling = False
        self.idling_counter = 0
        self.flip_cooldown = 0
        self.turn_after_idle = False

        # Override animation list com o extrator de sprite strips do robô
        self.animation_list = []
        animations = [
            ('Idle', 4),    # action 0
            ('Walk', 4),    # action 1
            ('Attack', 4),  # action 2
            ('Death', 4),   # action 3
            ('Hurt', 2)     # action 4
        ]

        for anim, num_frames in animations:
            img = pygame.image.load(f'img/robot/{anim}.png').convert_alpha()
            frame_width = img.get_width() // num_frames
            frame_height = img.get_height()

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
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def _is_edge_ahead(self, obstacle_list: list) -> bool:
        if self.in_air:
            return False
        if self.direction == 1:
            check_x = self.rect.right + 2
        else:
            check_x = self.rect.left - 2
        test_rect = pygame.Rect(check_x - 1, self.rect.bottom + 1, 2, TILE_SIZE)
        for tile in obstacle_list:
            if tile[1].colliderect(test_rect):
                return False
        return True

    def _on_horizontal_collision(self):
        if self.flip_cooldown == 0:
            self.idling = True
            self.idling_counter = 60
            self.turn_after_idle = True
            self.move_counter = 0
            self.flip_cooldown = 60

    def move(self, moving_left: bool, moving_right: bool, obstacle_list: list, water_group):
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0
        self._apply_gravity()
        dy += self.vel_y
        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list)
        self._check_environment(water_group)
        self.rect.x += dx
        self.rect.y += dy

    def shoot(self, bullet_group, target_x: float, target_y: float):
        """Sobrescreve tiro para usar RobotBullet e mira vetorial."""
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5

            dx = target_x - spawn_x
            dy = target_y - spawn_y
            distancia = math.hypot(dx, dy)

            if distancia > 0:
                vel_x = (dx / distancia) * BULLET_SPEED
                vel_y = (dy / distancia) * BULLET_SPEED
            else:
                vel_x = self.direction * BULLET_SPEED
                vel_y = 0.0

            bullet = RobotBullet(spawn_x, spawn_y, vel_x, vel_y)
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('robot_shoot').play()

    def ai(self, player, screen_scroll: int, obstacle_list: list, water_group, bullet_group):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            # Jogador dentro do campo de visão -> atirar
            if self.vision.colliderect(player.rect):
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False

                self.update_action(2)  # Attack animation (action 2)
                self.shoot(bullet_group, player.rect.centerx, player.rect.centery)
            else:
                if not self.idling and random.randint(1, 200) == 1:
                    self.update_action(0)  # Idle
                    self.idling = True
                    self.idling_counter = 50
                    self.turn_after_idle = False

                if not self.idling:
                    if self.direction == 1:
                        moving_right = True
                        moving_left = False
                    else:
                        moving_right = False
                        moving_left = True

                    self.update_action(1)  # Walk animation (action 1)
                    self.move(moving_left, moving_right, obstacle_list, water_group)
                    self.move_counter += 1

                    if self._is_edge_ahead(obstacle_list):
                        if self.flip_cooldown == 0:
                            self.idling = True
                            self.idling_counter = 60
                            self.turn_after_idle = True
                            self.move_counter = 0
                            self.flip_cooldown = 60
                else:
                    self.update_action(0)
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                        if self.turn_after_idle:
                            self.direction *= -1
                            self.turn_after_idle = False

        self.rect.x += screen_scroll
        self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
